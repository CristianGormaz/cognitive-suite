from __future__ import annotations

import ast
import asyncio
import json
import logging
import re
import textwrap
import time
from pathlib import Path
from typing import Any

from cognition.genesis_sandbox import GenesisSandbox, SandboxResult
from cognition.iafa_transceiver import IafaTransceiver
from core.iafa_auditor import IafaAuditor
from core.task_envelope import TaskEnvelope


logger = logging.getLogger("GenesisEngine")

GENESIS_ENGINE_VERSION = "genesis-engine.v2"
GENERATED_FUNCTION_NAME = "_generated_skill_impl"
THINK_BLOCK_RE = re.compile(r"<think>.*?</think>", re.IGNORECASE | re.DOTALL)
INVALID_INTENT_CHARS_RE = re.compile(r"[^a-z0-9_]+")

GENESIS_SYSTEM_PROMPT = f"""You are the Greys Genesis Engine.
Return only valid Python 3.10+ source code with no Markdown, no commentary, and no <think> tags.
Generate exactly one top-level synchronous function named {GENERATED_FUNCTION_NAME}.
Required signature:
def {GENERATED_FUNCTION_NAME}(context: dict) -> dict:
Constraints:
- Return a dict
- Use only the provided context dict as runtime input
- No filesystem, subprocess, network, dynamic imports, eval, or exec
- No top-level execution
- Deterministic logic only
- Use imports only if strictly necessary and limited to safe standard-library modules
- Do not use async def; GenesisEngine will wrap the function body into the final async skill file"""


class GenesisEngineError(ValueError):
    """Raised when a generated skill cannot be synthesized safely."""


class GenesisEngine:
    """
    Safe skill synthesis boundary for Greys-v3.

    The engine requests pure Python from the LLM, validates the generated code
    shape, sends it through the GenesisSandbox, and only then persists a wrapped
    skill module to disk. It never executes generated code.
    """

    def __init__(
        self,
        transceiver: IafaTransceiver,
        sandbox: GenesisSandbox,
        auditor: IafaAuditor,
        skills_directory: str = "src/skills",
    ) -> None:
        if not isinstance(transceiver, IafaTransceiver):
            raise TypeError("transceiver must be an IafaTransceiver")
        if not isinstance(sandbox, GenesisSandbox):
            raise TypeError("sandbox must be a GenesisSandbox")
        if not isinstance(auditor, IafaAuditor):
            raise TypeError("auditor must be an IafaAuditor")
        if not isinstance(skills_directory, str) or not skills_directory.strip():
            raise TypeError("skills_directory must be a non-empty string")

        self.transceiver = transceiver
        self.sandbox = sandbox
        self.auditor = auditor
        self.skills_directory = skills_directory.strip()

    async def synthesize_and_install_skill(
        self,
        intent_name: str,
        task_envelope: TaskEnvelope,
        fallback_context: dict,
    ) -> bool:
        try:
            safe_intent_name = self._sanitize_intent_name(intent_name)
            self._validate_inputs(task_envelope, fallback_context)

            operator_instruction = self._build_operator_instruction(
                safe_intent_name,
                task_envelope,
                fallback_context,
            )
            raw_response = await self.transceiver.query_llm(
                task_envelope,
                system_prompt=GENESIS_SYSTEM_PROMPT,
                operator_instruction=operator_instruction,
                json_format=False,
                max_payload_chars=2400,
            )
            generated_code = self._normalize_generated_code(raw_response)
            await self._validate_generated_shape(generated_code)

            sandbox_result = await self.sandbox.validate_code_proposal(generated_code, task_envelope.task_id)
            if not sandbox_result.is_safe:
                await self._audit_rejection(
                    intent_name=safe_intent_name,
                    task_envelope=task_envelope,
                    fallback_context=fallback_context,
                    reason="sandbox_rejected",
                    sandbox_result=sandbox_result,
                )
                return False

            module_code = self._build_skill_module(safe_intent_name, generated_code)
            target_path = self._skill_file_path(safe_intent_name)
            loop = asyncio.get_running_loop()
            await loop.run_in_executor(None, self._write_skill_file_sync, target_path, module_code)
            await self._audit_install_success(
                intent_name=safe_intent_name,
                task_envelope=task_envelope,
                fallback_context=fallback_context,
                target_path=target_path,
                sandbox_result=sandbox_result,
            )
            return True
        except GenesisEngineError as exc:
            await self._audit_failure(intent_name, task_envelope, fallback_context, exc)
            logger.warning("Genesis skill synthesis rejected for intent '%s': %s", intent_name, exc)
            return False
        except Exception as exc:
            await self._audit_failure(intent_name, task_envelope, fallback_context, exc)
            logger.exception("Genesis skill synthesis failed for intent '%s'", intent_name)
            return False

    def _build_operator_instruction(
        self,
        intent_name: str,
        task_envelope: TaskEnvelope,
        fallback_context: dict,
    ) -> str:
        payload = {
            "intent_name": intent_name,
            "target_function_name": GENERATED_FUNCTION_NAME,
            "target_skill_wrapper": f"skill_{intent_name}",
            "original_task": task_envelope.to_audit_record_details(),
            "fallback_context": fallback_context,
            "instruction": "Generate a pure Python function for this intent using context only. Return source code only.",
        }
        return json.dumps(payload, ensure_ascii=False, sort_keys=True)

    @staticmethod
    def _normalize_generated_code(raw_response: str) -> str:
        if not isinstance(raw_response, str) or not raw_response.strip():
            raise GenesisEngineError("LLM returned an empty skill proposal")

        cleaned = THINK_BLOCK_RE.sub("", raw_response).strip()
        if "```" in cleaned:
            raise GenesisEngineError("LLM skill proposal must not contain Markdown fences")
        if cleaned.lower().startswith("python\n"):
            cleaned = cleaned.split("\n", 1)[1].strip()
        if "<think>" in cleaned.lower() or "</think>" in cleaned.lower():
            raise GenesisEngineError("LLM skill proposal contains malformed <think> tags")
        if not cleaned:
            raise GenesisEngineError("LLM skill proposal is empty after normalization")
        return cleaned

    async def _validate_generated_shape(self, generated_code: str) -> None:
        loop = asyncio.get_running_loop()
        errors = await loop.run_in_executor(None, self._validate_generated_shape_sync, generated_code)
        if errors:
            raise GenesisEngineError("; ".join(errors))

    @staticmethod
    def _validate_generated_shape_sync(generated_code: str) -> list[str]:
        try:
            module = ast.parse(generated_code)
        except SyntaxError as exc:
            return [f"generated skill has syntax error: {exc.msg} at line {exc.lineno}"]

        errors: list[str] = []
        try:
            _imports, function_def = GenesisEngine._split_generated_module(module)
        except GenesisEngineError as exc:
            return [str(exc)]

        if function_def.name != GENERATED_FUNCTION_NAME:
            errors.append(f"generated function must be named {GENERATED_FUNCTION_NAME}")

        if function_def.decorator_list:
            errors.append("generated function must not use decorators")

        argument_names = [argument.arg for argument in function_def.args.args]
        if argument_names != ["context"]:
            errors.append("generated function signature must be (context)")

        non_import_body_nodes = [node for node in function_def.body if not isinstance(node, (ast.Import, ast.ImportFrom))]
        if not non_import_body_nodes:
            errors.append("generated function must contain at least one non-import statement")
        return errors

    @staticmethod
    def _build_skill_module(_intent_name: str, generated_code: str) -> str:
        parsed_module = ast.parse(generated_code)
        imports, function_def = GenesisEngine._split_generated_module(parsed_module)
        import_lines = [ast.unparse(import_node).strip() for import_node in imports]
        
        # Determine if we should wrap or use as is
        is_already_async = isinstance(function_def, ast.AsyncFunctionDef)
        
        if is_already_async:
             # Just combine imports and the function
             module_parts = import_lines + ["", ast.unparse(function_def)]
             return "\n".join(module_parts)

        body_nodes = [node for node in function_def.body if not isinstance(node, (ast.Import, ast.ImportFrom))]
        body_block = "\n".join(
            textwrap.indent(ast.unparse(statement).strip(), "        ")
            for statement in body_nodes
        )
        if not body_block:
            body_block = "        return {}\n"

        module_parts = [
            '"""Auto-generated Greys skill module.',
            "",
            "This file was synthesized by GenesisEngine after static AST validation.",
            '"""',
            "",
        ]
        if import_lines:
            module_parts.extend(import_lines)
            module_parts.append("")

        module_parts.extend(
            [
                f"async def {GENERATED_FUNCTION_NAME}(context: dict) -> dict:",
                "    try:",
                body_block,
                "    except Exception as exc:",
                '        return {"ok": False, "error_type": exc.__class__.__name__, "error": str(exc)}',
                "",
            ]
        )
        return "\n".join(module_parts)

    @staticmethod
    def _split_generated_module(module: ast.Module) -> tuple[list[ast.AST], ast.FunctionDef]:
        imports: list[ast.AST] = []
        function_def: ast.FunctionDef | None = None

        for node in module.body:
            if isinstance(node, (ast.Import, ast.ImportFrom)):
                imports.append(node)
                continue

            if isinstance(node, ast.FunctionDef):
                if function_def is not None:
                    raise GenesisEngineError("generated skill must contain exactly one top-level function")
                function_def = node
                continue

            if isinstance(node, ast.AsyncFunctionDef):
                if function_def is not None:
                    raise GenesisEngineError("generated skill must contain exactly one top-level function")
                function_def = node
                continue

            raise GenesisEngineError(f"unsupported top-level node: {node.__class__.__name__}")

        if function_def is None:
            raise GenesisEngineError("generated skill must contain exactly one top-level function")

        for statement in function_def.body:
            if isinstance(statement, (ast.Import, ast.ImportFrom)):
                imports.append(statement)

        return imports, function_def

    def _skill_file_path(self, intent_name: str) -> str:
        return str(Path(self.skills_directory) / f"skill_{intent_name}.py")

    def _write_skill_file_sync(self, target_path: str, module_code: str) -> None:
        target_file = Path(target_path)
        target_file.parent.mkdir(parents=True, exist_ok=True)
        with target_file.open("w", encoding="utf-8") as handle:
            handle.write(module_code)

    async def _audit_install_success(
        self,
        intent_name: str,
        task_envelope: TaskEnvelope,
        fallback_context: dict,
        target_path: str,
        sandbox_result: SandboxResult,
    ) -> None:
        await self.auditor.append_payload(
            {
                "timestamp": time.time(),
                "record_type": "genesis_skill_installed",
                "genesis_engine_version": GENESIS_ENGINE_VERSION,
                "intent_name": intent_name,
                "task": task_envelope.to_audit_record_details(),
                "fallback_context": self._safe_fallback_context(fallback_context),
                "target_path": target_path,
                "code_hash": sandbox_result.code_hash,
                "sandbox_result": sandbox_result.to_dict(),
            }
        )

    async def _audit_rejection(
        self,
        intent_name: str,
        task_envelope: TaskEnvelope,
        fallback_context: dict,
        reason: str,
        sandbox_result: SandboxResult,
    ) -> None:
        await self.auditor.append_payload(
            {
                "timestamp": time.time(),
                "record_type": "genesis_skill_rejected",
                "genesis_engine_version": GENESIS_ENGINE_VERSION,
                "intent_name": intent_name,
                "task": task_envelope.to_audit_record_details(),
                "fallback_context": self._safe_fallback_context(fallback_context),
                "reason": reason,
                "code_hash": sandbox_result.code_hash,
                "sandbox_result": sandbox_result.to_dict(),
            }
        )

    async def _audit_failure(
        self,
        intent_name: str,
        task_envelope: TaskEnvelope,
        fallback_context: dict,
        exc: Exception,
    ) -> None:
        try:
            safe_intent_name = self._sanitize_intent_name(intent_name)
        except Exception:
            safe_intent_name = "invalid_intent"

        try:
            task_payload = task_envelope.to_audit_record_details()
        except Exception:
            task_payload = {"task_id": "unknown"}

        try:
            await self.auditor.append_payload(
                {
                    "timestamp": time.time(),
                    "record_type": "genesis_skill_failed",
                    "genesis_engine_version": GENESIS_ENGINE_VERSION,
                    "intent_name": safe_intent_name,
                    "task": task_payload,
                    "fallback_context": self._safe_fallback_context(fallback_context),
                    "error_type": exc.__class__.__name__,
                    "error": str(exc),
                }
            )
        except Exception:
            logger.exception("Failed to audit GenesisEngine failure for intent '%s'", safe_intent_name)

    @staticmethod
    def _sanitize_intent_name(intent_name: str) -> str:
        if not isinstance(intent_name, str) or not intent_name.strip():
            raise GenesisEngineError("intent_name must be a non-empty string")

        normalized = INVALID_INTENT_CHARS_RE.sub("_", intent_name.strip().lower()).strip("_")
        if not normalized:
            raise GenesisEngineError("intent_name must contain at least one alphanumeric character")
        if normalized[0].isdigit():
            normalized = f"intent_{normalized}"
        return normalized

    @staticmethod
    def _validate_inputs(task_envelope: TaskEnvelope, fallback_context: dict) -> None:
        if not isinstance(task_envelope, TaskEnvelope):
            raise GenesisEngineError("task_envelope must be a TaskEnvelope")
        if not isinstance(fallback_context, dict):
            raise GenesisEngineError("fallback_context must be a dict")

        try:
            json.dumps(fallback_context, ensure_ascii=False, sort_keys=True)
        except (TypeError, ValueError) as exc:
            raise GenesisEngineError("fallback_context must be JSON-serializable") from exc

    @staticmethod
    def _safe_fallback_context(fallback_context: Any) -> dict:
        if not isinstance(fallback_context, dict):
            return {}

        try:
            json.dumps(fallback_context, ensure_ascii=False, sort_keys=True)
        except (TypeError, ValueError):
            return {"_invalid_fallback_context": True}
        return fallback_context
