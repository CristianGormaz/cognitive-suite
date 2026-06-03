import asyncio
import os
import sys
import tempfile
import unittest
from pathlib import Path


sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from cognition.skill_loader import (
    DynamicSkillLoader,
    InvalidSkillModuleError,
    SkillExecutionError,
    SkillNotFoundError,
)


def write_skill_file(directory: str, intent_name: str, code: str) -> Path:
    target = Path(directory) / f"skill_{intent_name}.py"
    target.write_text(code, encoding="utf-8")
    os.utime(target, None)
    return target


class DynamicSkillLoaderTests(unittest.TestCase):
    def test_execute_skill_loads_async_generated_function(self):
        async def run_case():
            with tempfile.TemporaryDirectory() as temp_dir:
                write_skill_file(
                    temp_dir,
                    "saludar",
                    """async def _generated_skill_impl(context: dict) -> dict:
    return {"ok": True, "message": f"hola {context['name']}"}
""",
                )
                loader = DynamicSkillLoader(skills_directory=temp_dir)
                return await loader.execute_skill("saludar", {"name": "Greys"})

        result = asyncio.run(run_case())

        self.assertEqual(result, {"ok": True, "message": "hola Greys"})

    def test_execute_skill_hot_reloads_updated_module(self):
        async def run_case():
            with tempfile.TemporaryDirectory() as temp_dir:
                loader = DynamicSkillLoader(skills_directory=temp_dir)
                write_skill_file(
                    temp_dir,
                    "saludar",
                    """async def _generated_skill_impl(context: dict) -> dict:
    return {"version": 1}
""",
                )
                first_result = await loader.execute_skill("saludar", {})

                write_skill_file(
                    temp_dir,
                    "saludar",
                    """async def _generated_skill_impl(context: dict) -> dict:
    return {"version": 2, "mode": context.get("mode", "n/a")}
""",
                )
                second_result = await loader.execute_skill("saludar", {"mode": "reloaded"})
                return first_result, second_result

        first_result, second_result = asyncio.run(run_case())

        self.assertEqual(first_result, {"version": 1})
        self.assertEqual(second_result, {"version": 2, "mode": "reloaded"})

    def test_execute_skill_raises_not_found_for_missing_file(self):
        async def run_case():
            with tempfile.TemporaryDirectory() as temp_dir:
                loader = DynamicSkillLoader(skills_directory=temp_dir)
                with self.assertRaises(SkillNotFoundError):
                    await loader.execute_skill("inexistente", {})

        asyncio.run(run_case())

    def test_execute_skill_rejects_missing_generated_entrypoint(self):
        async def run_case():
            with tempfile.TemporaryDirectory() as temp_dir:
                write_skill_file(
                    temp_dir,
                    "rota",
                    """async def otra_funcion(context: dict) -> dict:
    return {"ok": True}
""",
                )
                loader = DynamicSkillLoader(skills_directory=temp_dir)
                with self.assertRaises(InvalidSkillModuleError):
                    await loader.execute_skill("rota", {})

        asyncio.run(run_case())

    def test_execute_skill_rejects_non_async_entrypoint(self):
        async def run_case():
            with tempfile.TemporaryDirectory() as temp_dir:
                write_skill_file(
                    temp_dir,
                    "sincrona",
                    """def _generated_skill_impl(context: dict) -> dict:
    return {"ok": True}
""",
                )
                loader = DynamicSkillLoader(skills_directory=temp_dir)
                with self.assertRaises(InvalidSkillModuleError):
                    await loader.execute_skill("sincrona", {})

        asyncio.run(run_case())

    def test_execute_skill_wraps_runtime_errors(self):
        async def run_case():
            with tempfile.TemporaryDirectory() as temp_dir:
                write_skill_file(
                    temp_dir,
                    "falla",
                    """async def _generated_skill_impl(context: dict) -> dict:
    raise ValueError("boom")
""",
                )
                loader = DynamicSkillLoader(skills_directory=temp_dir)
                with self.assertRaises(SkillExecutionError) as caught:
                    await loader.execute_skill("falla", {})
                return caught.exception

        error = asyncio.run(run_case())

        self.assertIn("ValueError", str(error))
        self.assertIn("boom", str(error))
        self.assertIsInstance(error.__cause__, ValueError)

    def test_execute_skill_rejects_non_dict_result(self):
        async def run_case():
            with tempfile.TemporaryDirectory() as temp_dir:
                write_skill_file(
                    temp_dir,
                    "lista",
                    """async def _generated_skill_impl(context: dict):
    return ["bad"]
""",
                )
                loader = DynamicSkillLoader(skills_directory=temp_dir)
                with self.assertRaises(SkillExecutionError):
                    await loader.execute_skill("lista", {})

        asyncio.run(run_case())


if __name__ == "__main__":
    unittest.main()
