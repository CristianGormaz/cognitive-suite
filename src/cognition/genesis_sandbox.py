from __future__ import annotations

import ast
import asyncio
import hashlib
import time
from dataclasses import asdict, dataclass
from typing import Any, Dict, Optional

from core.iafa_auditor import IafaAuditor


GENESIS_SANDBOX_VERSION = "genesis-sandbox.v1"

ALLOWED_IMPORT_ROOTS = frozenset(
    {
        "__future__",
        "collections",
        "dataclasses",
        "datetime",
        "decimal",
        "enum",
        "functools",
        "itertools",
        "json",
        "logging",
        "math",
        "operator",
        "pypdf",
        "re",
        "statistics",
        "string",
        "typing",
    }
)

DANGEROUS_IMPORT_ROOTS = frozenset(
    {
        "asyncio",
        "builtins",
        "compileall",
        "ctypes",
        "dbm",
        "faulthandler",
        "fcntl",
        "glob",
        "importlib",
        "io",
        "multiprocessing",
        "os",
        "pathlib",
        "pickle",
        "pipes",
        "platform",
        "pty",
        "runpy",
        "shelve",
        "shlex",
        "shutil",
        "signal",
        "socket",
        "subprocess",
        "sys",
        "tempfile",
        "threading",
        "traceback",
        "types",
        "venv",
    }
)

DANGEROUS_CALL_NAMES = frozenset(
    {
        "__import__",
        "breakpoint",
        "compile",
        "eval",
        "exec",
        "exit",
        "getattr",
        "globals",
        "input",
        "locals",
        "mkdir",
        "open",
        "popen",
        "quit",
        "remove",
        "rename",
        "rmdir",
        "setattr",
        "spawn",
        "system",
        "vars",
    }
)

DANGEROUS_ATTRIBUTE_NAMES = frozenset(
    {
        "__class__",
        "__dict__",
        "__globals__",
        "__mro__",
        "__subclasses__",
        "__bases__",
        "__code__",
        "__getattribute__",
        "__getattr__",
        "__setattr__",
        "__delattr__",
    }
)

BLOCKED_NODE_TYPES = (
    ast.AsyncFunctionDef,
    ast.Await,
    ast.ClassDef,
    ast.Delete,
    ast.Global,
    ast.Lambda,
    ast.Nonlocal,
    ast.With,
    ast.AsyncWith,
)


@dataclass(frozen=True)
class SandboxResult:
    is_safe: bool
    validation_errors: list[str]
    code_hash: str

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class StrictCodeVisitor(ast.NodeVisitor):
    """AST visitor that rejects unsafe imports, calls, and introspection."""

    def __init__(self) -> None:
        self.errors: list[str] = []

    def visit_Import(self, node: ast.Import) -> None:
        for alias in node.names:
            root = _module_root(alias.name)
            if root in DANGEROUS_IMPORT_ROOTS:
                self.errors.append(f"dangerous import rejected: {alias.name}")
            elif root not in ALLOWED_IMPORT_ROOTS:
                self.errors.append(f"import not in allowlist: {alias.name}")
            if alias.asname in DANGEROUS_CALL_NAMES:
                self.errors.append(f"dangerous alias rejected: {alias.asname}")
        self.generic_visit(node)

    def visit_ImportFrom(self, node: ast.ImportFrom) -> None:
        if node.level and node.level > 0:
            self.errors.append("relative imports are rejected")
        root = _module_root(node.module or "")
        if root in DANGEROUS_IMPORT_ROOTS:
            self.errors.append(f"dangerous import rejected: {node.module}")
        elif root not in ALLOWED_IMPORT_ROOTS:
            self.errors.append(f"import not in allowlist: {node.module}")
        for alias in node.names:
            if alias.asname in DANGEROUS_CALL_NAMES or alias.name in DANGEROUS_CALL_NAMES:
                self.errors.append(f"dangerous imported name rejected: {alias.asname or alias.name}")
        self.generic_visit(node)

    def visit_Call(self, node: ast.Call) -> None:
        call_name = _call_name(node.func)
        if call_name in DANGEROUS_CALL_NAMES:
            self.errors.append(f"dangerous call rejected: {call_name}")
        self.generic_visit(node)

    def visit_Attribute(self, node: ast.Attribute) -> None:
        if node.attr in DANGEROUS_ATTRIBUTE_NAMES or node.attr.startswith("__"):
            self.errors.append(f"dangerous attribute access rejected: {node.attr}")
        self.generic_visit(node)

    def generic_visit(self, node: ast.AST) -> None:
        if isinstance(node, BLOCKED_NODE_TYPES):
            self.errors.append(f"node type rejected: {node.__class__.__name__}")
        super().generic_visit(node)


class GenesisSandbox:
    """
    Static immune layer for LLM-generated Python code.

    This module never executes code. It parses and inspects AST only, then
    writes an audit record for approval or rejection.
    """

    def __init__(self, auditor: Optional[IafaAuditor] = None):
        self.auditor = auditor

    async def validate_code_proposal(self, code_string: str, original_task_id: str) -> SandboxResult:
        if not isinstance(code_string, str):
            raise TypeError("code_string must be a string")
        if not isinstance(original_task_id, str) or not original_task_id.strip():
            raise ValueError("original_task_id must be a non-empty string")

        code_hash = hashlib.sha256(code_string.encode("utf-8")).hexdigest()
        loop = asyncio.get_running_loop()
        validation_errors = await loop.run_in_executor(None, self._validate_ast_sync, code_string)
        result = SandboxResult(
            is_safe=len(validation_errors) == 0,
            validation_errors=validation_errors,
            code_hash=code_hash,
        )
        await self._audit_result(result, original_task_id.strip())
        return result

    @staticmethod
    def _validate_ast_sync(code_string: str) -> list[str]:
        try:
            tree = ast.parse(code_string)
        except SyntaxError as exc:
            return [f"syntax error: {exc.msg} at line {exc.lineno}"]

        visitor = StrictCodeVisitor()
        visitor.visit(tree)
        return visitor.errors

    async def _audit_result(self, result: SandboxResult, original_task_id: str) -> None:
        if not self.auditor:
            return

        payload = {
            "timestamp": time.time(),
            "record_type": "genesis_sandbox_validation",
            "sandbox_version": GENESIS_SANDBOX_VERSION,
            "original_task_id": original_task_id,
            "result": result.to_dict(),
        }
        loop = asyncio.get_running_loop()
        await loop.run_in_executor(None, self._write_audit_payload_sync, payload)

    def _write_audit_payload_sync(self, payload: Dict[str, Any]) -> None:
        log_entry = self.auditor.encode_payload(payload)
        self.auditor._write_to_disk_sync(log_entry)


def _module_root(module_name: str) -> str:
    return module_name.split(".", 1)[0]


def _call_name(node: ast.AST) -> Optional[str]:
    if isinstance(node, ast.Name):
        return node.id
    if isinstance(node, ast.Attribute):
        return node.attr
    return None
