import asyncio
import sys
import tempfile
import threading
import unittest
from pathlib import Path


sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from cognition.genesis_engine import GENERATED_FUNCTION_NAME, GenesisEngine, GenesisEngineError
from cognition.genesis_sandbox import GenesisSandbox
from cognition.iafa_transceiver import IafaTransceiver
from core.iafa_auditor import IafaAuditor
from core.task_envelope import TaskEnvelope


SAFE_GENERATED_CODE = f"""def {GENERATED_FUNCTION_NAME}(context: dict) -> dict:
    import json
    title = str(context.get("title", ""))
    mode = str(context.get("mode", "default"))
    return {{
        "ok": True,
        "payload": json.loads(json.dumps({{"title": title.strip(), "mode": mode}})),
    }}
"""


class FakeTransceiver(IafaTransceiver):
    def __init__(self, response=None, error=None):
        super().__init__(host="http://127.0.0.1:11434", default_model="test-model")
        self.response = response
        self.error = error
        self.calls = []

    async def query_llm(self, *args, **kwargs):
        self.calls.append((args, kwargs))
        if self.error:
            raise self.error
        return self.response


class ThreadRecordingGenesisEngine(GenesisEngine):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.write_thread_ids = []

    def _write_skill_file_sync(self, target_path: str, module_code: str) -> None:
        self.write_thread_ids.append(threading.get_ident())
        super()._write_skill_file_sync(target_path, module_code)


class GenesisEngineTests(unittest.TestCase):
    def setUp(self):
        self.envelope = TaskEnvelope.from_text(
            "crear habilidad",
            declared_intent="skill_synthesis",
            created_at="2026-05-31T12:00:00Z",
        )
        self.fallback_context = {
            "mode": "sandbox_code",
            "blocked_reason": "iafa_score_below_threshold",
        }

    def test_synthesize_and_install_skill_writes_wrapped_module_after_sandbox(self):
        async def run_case():
            with tempfile.TemporaryDirectory() as temp_dir:
                auditor = IafaAuditor(str(Path(temp_dir) / "audit.log"), secret_key="test-secret")
                sandbox = GenesisSandbox(auditor)
                transceiver = FakeTransceiver(
                    response=f"<think>plan interno</think>\n{SAFE_GENERATED_CODE}"
                )
                engine = ThreadRecordingGenesisEngine(
                    transceiver=transceiver,
                    sandbox=sandbox,
                    auditor=auditor,
                    skills_directory=temp_dir,
                )
                loop_thread_id = threading.get_ident()

                success = await engine.synthesize_and_install_skill(
                    "Summarize Doc",
                    self.envelope,
                    self.fallback_context,
                )
                target_file = Path(temp_dir) / "skill_summarize_doc.py"
                file_exists = target_file.exists()
                installed_code = target_file.read_text(encoding="utf-8")
                entries = list(auditor.iter_verified_entries())

                return success, transceiver, engine, loop_thread_id, str(target_file), file_exists, installed_code, entries

        success, transceiver, engine, loop_thread_id, target_path, file_exists, installed_code, entries = asyncio.run(run_case())

        self.assertTrue(success)
        self.assertEqual(len(transceiver.calls), 1)
        self.assertTrue(file_exists)
        self.assertIn("import json", installed_code)
        self.assertIn(f"async def {GENERATED_FUNCTION_NAME}(context: dict) -> dict:", installed_code)
        self.assertIn("except Exception as exc", installed_code)
        self.assertLess(installed_code.index("import json"), installed_code.index(f"async def {GENERATED_FUNCTION_NAME}"))
        self.assertNotIn("def skill_summarize_doc(", installed_code)
        self.assertTrue(engine.write_thread_ids)
        self.assertNotEqual(engine.write_thread_ids[0], loop_thread_id)

        self.assertEqual(entries[0]["payload"]["record_type"], "genesis_sandbox_validation")
        self.assertEqual(entries[1]["payload"]["record_type"], "genesis_skill_installed")
        self.assertEqual(entries[1]["payload"]["intent_name"], "summarize_doc")
        self.assertEqual(entries[1]["payload"]["task"]["task_id"], self.envelope.task_id)
        self.assertEqual(entries[1]["payload"]["target_path"], target_path)

    def test_synthesize_and_install_skill_rejects_sandbox_failures_without_writing(self):
        unsafe_code = f"""import os

def {GENERATED_FUNCTION_NAME}(context: dict) -> dict:
    return {{"ok": True}}
"""

        async def run_case():
            with tempfile.TemporaryDirectory() as temp_dir:
                auditor = IafaAuditor(str(Path(temp_dir) / "audit.log"), secret_key="test-secret")
                sandbox = GenesisSandbox(auditor)
                transceiver = FakeTransceiver(response=unsafe_code)
                engine = GenesisEngine(transceiver, sandbox, auditor, skills_directory=temp_dir)

                success = await engine.synthesize_and_install_skill("persist skill", self.envelope, self.fallback_context)
                target_file = Path(temp_dir) / "skill_persist_skill.py"
                file_exists = target_file.exists()
                entries = list(auditor.iter_verified_entries())
                return success, file_exists, entries

        success, file_exists, entries = asyncio.run(run_case())

        self.assertFalse(success)
        self.assertFalse(file_exists)
        self.assertEqual(entries[0]["payload"]["record_type"], "genesis_sandbox_validation")
        self.assertFalse(entries[0]["payload"]["result"]["is_safe"])
        self.assertEqual(entries[1]["payload"]["record_type"], "genesis_skill_rejected")
        self.assertEqual(entries[1]["payload"]["reason"], "sandbox_rejected")

    def test_synthesize_and_install_skill_rejects_markdown_response_before_writing(self):
        markdown_response = f"""```python
def {GENERATED_FUNCTION_NAME}(context: dict) -> dict:
    return {{"ok": True}}
```"""

        async def run_case():
            with tempfile.TemporaryDirectory() as temp_dir:
                auditor = IafaAuditor(str(Path(temp_dir) / "audit.log"), secret_key="test-secret")
                sandbox = GenesisSandbox(auditor)
                transceiver = FakeTransceiver(response=markdown_response)
                engine = GenesisEngine(transceiver, sandbox, auditor, skills_directory=temp_dir)

                success = await engine.synthesize_and_install_skill("markdown skill", self.envelope, self.fallback_context)
                entries = list(auditor.iter_verified_entries())
                return success, entries

        success, entries = asyncio.run(run_case())

        self.assertFalse(success)
        self.assertEqual(len(entries), 1)
        self.assertEqual(entries[0]["payload"]["record_type"], "genesis_skill_failed")
        self.assertIn("Markdown fences", entries[0]["payload"]["error"])

    def test_synthesize_and_install_skill_audits_transceiver_failures(self):
        async def run_case():
            with tempfile.TemporaryDirectory() as temp_dir:
                auditor = IafaAuditor(str(Path(temp_dir) / "audit.log"), secret_key="test-secret")
                sandbox = GenesisSandbox(auditor)
                transceiver = FakeTransceiver(error=RuntimeError("ollama unavailable"))
                engine = GenesisEngine(transceiver, sandbox, auditor, skills_directory=temp_dir)

                success = await engine.synthesize_and_install_skill("network skill", self.envelope, self.fallback_context)
                entries = list(auditor.iter_verified_entries())
                return success, entries

        success, entries = asyncio.run(run_case())

        self.assertFalse(success)
        self.assertEqual(len(entries), 1)
        self.assertEqual(entries[0]["payload"]["record_type"], "genesis_skill_failed")
        self.assertEqual(entries[0]["payload"]["error_type"], "RuntimeError")
        self.assertIn("ollama unavailable", entries[0]["payload"]["error"])

    def test_synthesize_and_install_skill_rejects_wrong_function_shape(self):
        invalid_shape_code = """def custom_skill(context: dict) -> dict:
    return {"ok": True}
"""

        async def run_case():
            with tempfile.TemporaryDirectory() as temp_dir:
                auditor = IafaAuditor(str(Path(temp_dir) / "audit.log"), secret_key="test-secret")
                sandbox = GenesisSandbox(auditor)
                transceiver = FakeTransceiver(response=invalid_shape_code)
                engine = GenesisEngine(transceiver, sandbox, auditor, skills_directory=temp_dir)

                success = await engine.synthesize_and_install_skill("shape skill", self.envelope, self.fallback_context)
                entries = list(auditor.iter_verified_entries())
                return success, entries

        success, entries = asyncio.run(run_case())

        self.assertFalse(success)
        self.assertEqual(len(entries), 1)
        self.assertEqual(entries[0]["payload"]["record_type"], "genesis_skill_failed")
        self.assertIn(GENERATED_FUNCTION_NAME, entries[0]["payload"]["error"])

    def test_rejects_invalid_json_unserializable_context(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            auditor = IafaAuditor(str(Path(temp_dir) / "audit.log"), secret_key="test-secret")
            sandbox = GenesisSandbox(auditor)
            transceiver = FakeTransceiver(response=SAFE_GENERATED_CODE)
            engine = GenesisEngine(transceiver, sandbox, auditor, skills_directory=temp_dir)

            with self.assertRaises(GenesisEngineError):
                GenesisEngine._validate_inputs(self.envelope, {"bad": object()})


if __name__ == "__main__":
    unittest.main()
