from __future__ import annotations

import asyncio
import importlib
import importlib.util
import os
import sys
from pathlib import Path
from typing import Any, Dict, Optional, Set


GENERATED_SKILL_FUNCTION = "_generated_skill_impl"
SKILL_FILE_PREFIX = "skill_"
MODULE_NAME_PREFIX = "greys_dynamic_skill_"


class SkillLoaderError(RuntimeError):
    """Base error for dynamic skill loading failures."""


class SkillNotFoundError(SkillLoaderError):
    """Raised when a requested skill file does not exist on disk."""


class InvalidSkillModuleError(SkillLoaderError):
    """Raised when a skill module does not expose the expected async entrypoint."""


class SkillExecutionError(SkillLoaderError):
    """Raised when loading or executing a skill fails."""


class DynamicSkillLoader:
    """
    Hot-reloading loader for runtime-generated Greys skills.

    The loader invalidates import caches, evicts the module from ``sys.modules``,
    removes stale bytecode when possible, and then loads the fresh file from
    ``src/skills/skill_{intent_name}.py``. The module must expose exactly one
    async entrypoint named ``_generated_skill_impl(context: dict) -> dict``.
    """

    def __init__(self, skills_directory: str = "src/skills") -> None:
        if not isinstance(skills_directory, str) or not skills_directory.strip():
            raise TypeError("skills_directory must be a non-empty string")
        self.skills_directory = Path(skills_directory.strip())
        self.allowlist: Optional[Set[str]] = None

    def set_allowlist(self, allowlist: Set[str]) -> None:
        """Establece una lista permitida de habilidades."""
        self.allowlist = allowlist

    async def execute_skill(self, intent_name: str, context: dict, subfolder: Optional[str] = None) -> dict:
        safe_intent_name = self._sanitize_intent_name(intent_name)
        
        # Si la allowlist está establecida, verificar pertenencia.
        # Si es None, el comportamiento depende de la política (por defecto permitimos si no hay restricción,
        # pero para Greys-v3 queremos restricción explícita en experimental).
        if self.allowlist is not None and safe_intent_name not in self.allowlist:
            raise SkillLoaderError(f"Skill '{safe_intent_name}' is not in the allowlist.")
        
        # Para mayor seguridad en Greys-v3, si estamos en modo experimental y no hay allowlist, bloqueamos.
        if subfolder == "experimental" and (self.allowlist is None or safe_intent_name not in self.allowlist):
             raise SkillLoaderError(f"Experimental skill '{safe_intent_name}' requires explicit allowlist entry.")

        if not isinstance(context, dict):
            raise TypeError("context must be a dict")

        module = await self._load_skill_module(safe_intent_name, subfolder=subfolder)
        skill_function = self._resolve_skill_function(module, safe_intent_name)

        try:
            result = await skill_function(dict(context))
        except Exception as exc:
            raise SkillExecutionError(
                f"Skill '{safe_intent_name}' execution failed: {exc.__class__.__name__}: {exc}"
            ) from exc

        if not isinstance(result, dict):
            raise SkillExecutionError(f"Skill '{safe_intent_name}' must return a dict")
        return result

    async def _load_skill_module(self, safe_intent_name: str, subfolder: Optional[str] = None):
        loop = asyncio.get_running_loop()
        return await loop.run_in_executor(None, self._load_skill_module_sync, safe_intent_name, subfolder)

    def _load_skill_module_sync(self, safe_intent_name: str, subfolder: Optional[str] = None):
        skill_path = self._skill_path(safe_intent_name, subfolder=subfolder)
        if not skill_path.is_file():
            # Intentar búsqueda recursiva si no se especificó subfolder y el archivo no está en la raíz
            if subfolder is None:
                found_path = next(self.skills_directory.rglob(f"{SKILL_FILE_PREFIX}{safe_intent_name}.py"), None)
                if found_path:
                    skill_path = found_path
                else:
                    raise SkillNotFoundError(f"Skill file not found for intent '{safe_intent_name}' in {self.skills_directory}")
            else:
                raise SkillNotFoundError(f"Skill file not found for intent '{safe_intent_name}' in {subfolder}: {skill_path}")

        module_name = self._module_name(safe_intent_name)
        self._invalidate_skill_cache(module_name, skill_path)

        spec = importlib.util.spec_from_file_location(module_name, skill_path)
        if spec is None or spec.loader is None:
            raise SkillLoaderError(f"Could not build an import spec for skill '{safe_intent_name}'")

        module = importlib.util.module_from_spec(spec)
        sys.modules[module_name] = module
        try:
            spec.loader.exec_module(module)
        except Exception as exc:
            sys.modules.pop(module_name, None)
            raise SkillExecutionError(
                f"Failed to load skill '{safe_intent_name}': {exc.__class__.__name__}: {exc}"
            ) from exc
        return module

    @staticmethod
    def _resolve_skill_function(module, safe_intent_name: str):
        skill_function = getattr(module, GENERATED_SKILL_FUNCTION, None)
        if skill_function is None:
            raise InvalidSkillModuleError(
                f"Skill '{safe_intent_name}' does not export {GENERATED_SKILL_FUNCTION}"
            )
        if not callable(skill_function):
            raise InvalidSkillModuleError(
                f"Skill '{safe_intent_name}' attribute {GENERATED_SKILL_FUNCTION} is not callable"
            )
        if not asyncio.iscoroutinefunction(skill_function):
            raise InvalidSkillModuleError(
                f"Skill '{safe_intent_name}' entrypoint {GENERATED_SKILL_FUNCTION} must be async"
            )
        return skill_function

    def _invalidate_skill_cache(self, module_name: str, skill_path: Path) -> None:
        importlib.invalidate_caches()
        sys.modules.pop(module_name, None)

        try:
            pyc_path = Path(importlib.util.cache_from_source(os.fspath(skill_path)))
        except (NotImplementedError, ValueError):
            return

        if pyc_path.exists():
            try:
                pyc_path.unlink()
            except OSError:
                return

    def _skill_path(self, safe_intent_name: str, subfolder: Optional[str] = None) -> Path:
        base = self.skills_directory
        if subfolder:
            base = base / subfolder
        return base / f"{SKILL_FILE_PREFIX}{safe_intent_name}.py"

    @staticmethod
    def _module_name(safe_intent_name: str) -> str:
        return f"{MODULE_NAME_PREFIX}{safe_intent_name}"

    @staticmethod
    def _sanitize_intent_name(intent_name: str) -> str:
        if not isinstance(intent_name, str) or not intent_name.strip():
            raise SkillLoaderError("intent_name must be a non-empty string")

        normalized_chars = []
        for character in intent_name.strip().lower():
            if character.isalnum() or character == "_":
                normalized_chars.append(character)
            else:
                normalized_chars.append("_")

        normalized = "".join(normalized_chars).strip("_")
        while "__" in normalized:
            normalized = normalized.replace("__", "_")

        if not normalized:
            raise SkillLoaderError("intent_name must contain at least one alphanumeric character")
        if normalized[0].isdigit():
            normalized = f"intent_{normalized}"
        return normalized
