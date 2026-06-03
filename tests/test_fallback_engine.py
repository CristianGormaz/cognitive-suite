import asyncio
import sys
import tempfile
import unittest
from pathlib import Path


sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from cognition.fallback_engine import (
    FALLBACK_SYSTEM_PROMPT,
    EvolutionaryFallbackEngine,
    FallbackEngineError,
)
from core.action_dispatcher import DispatchResult
from core.iafa_auditor import IafaAuditor
from core.task_envelope import TaskEnvelope


VALID_RESPONSE = """<think>
El bloqueo viene por incertidumbre y conviene ofrecer una salida segura.
</think>
{
  "hypotheses": [
    {"id": "opt_1", "action_type": "ask_human", "label": "Pedir aclaracion", "description": "Solicitar al usuario el objetivo exacto antes de continuar."},
    {"id": "opt_2", "action_type": "sandbox_code", "label": "Generar script seguro", "description": "Preparar una rutina aislada que no toque memoria persistente."},
    {"id": "opt_3", "action_type": "abort", "label": "Descartar tarea", "description": "Detener el flujo y conservar solo la auditoria."}
  ]
}"""


class FakeTransceiver:
    def __init__(self, response):
        self.response = response
        self.calls = []

    async def query_llm(self, *args, **kwargs):
        self.calls.append((args, kwargs))
        return self.response


def make_dispatch_result():
    return DispatchResult(
        status="blocked_fallback",
        ui_state="evolutionary_doubt",
        iafa_score=0.42,
        threshold=0.7,
        action="store_in_semantic_memory",
        task_id="task_test",
        details={
            "fallback": "duda",
            "reason": "iafa_score_below_threshold",
        },
    )


class EvolutionaryFallbackEngineTests(unittest.TestCase):
    def setUp(self):
        self.dispatch_result = make_dispatch_result()
        self.envelope = TaskEnvelope.from_text(
            "contenido bloqueado",
            declared_intent="document_analysis",
            created_at="2026-05-31T12:00:00Z",
        )

    def test_generate_hypotheses_returns_three_valid_options_and_audits(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            auditor = IafaAuditor(str(Path(temp_dir) / "audit.log"), secret_key="test-secret")
            transceiver = FakeTransceiver(VALID_RESPONSE)
            engine = EvolutionaryFallbackEngine(transceiver, auditor)

            options = asyncio.run(engine.generate_hypotheses(self.dispatch_result, self.envelope))
            entries = list(auditor.iter_verified_entries())

        self.assertFalse(options.used_default)
        self.assertEqual(options.task_id, self.envelope.task_id)
        self.assertEqual(options.source_status, "blocked_fallback")
        self.assertEqual(options.ui_state, "evolutionary_doubt")
        self.assertEqual(len(options.hypotheses), 3)
        self.assertEqual(options.hypotheses[0].id, "opt_1")
        self.assertEqual(options.hypotheses[0].action_type, "ask_human")
        self.assertEqual(options.hypotheses[1].action_type, "sandbox_code")
        self.assertEqual(options.hypotheses[2].action_type, "abort")
        self.assertIn("incertidumbre", options.thought_trace)

        self.assertEqual(len(transceiver.calls), 1)
        args, kwargs = transceiver.calls[0]
        self.assertEqual(args[0], self.envelope)
        self.assertEqual(kwargs["system_prompt"], FALLBACK_SYSTEM_PROMPT)
        self.assertFalse(kwargs["json_format"])
        self.assertIn("blocked_dispatch", kwargs["operator_instruction"])

        self.assertEqual(len(entries), 1)
        payload = entries[0]["payload"]
        self.assertEqual(payload["record_type"], "evolutionary_fallback_options")
        self.assertEqual(payload["task"]["task_id"], self.envelope.task_id)
        self.assertEqual(payload["options"]["hypotheses"][0]["id"], "opt_1")

    def test_invalid_llm_json_returns_single_safe_abort_and_audits(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            auditor = IafaAuditor(str(Path(temp_dir) / "audit.log"), secret_key="test-secret")
            engine = EvolutionaryFallbackEngine(FakeTransceiver("Claro, puedo ayudarte."), auditor)

            options = asyncio.run(engine.generate_hypotheses(self.dispatch_result, self.envelope))
            entries = list(auditor.iter_verified_entries())

        self.assertTrue(options.used_default)
        self.assertEqual(len(options.hypotheses), 1)
        self.assertEqual(options.hypotheses[0].id, "opt_safe_abort")
        self.assertEqual(options.hypotheses[0].action_type, "abort")
        self.assertEqual(options.hypotheses[0].label, "Abortar por seguridad")
        self.assertIn("JSON object", options.error)
        self.assertEqual(entries[0]["payload"]["options"]["used_default"], True)

    def test_parse_rejects_extra_root_key(self):
        json_text = """{
          "hypotheses": [
            {"id": "opt_1", "action_type": "ask_human", "label": "A", "description": "B"},
            {"id": "opt_2", "action_type": "sandbox_code", "label": "C", "description": "D"},
            {"id": "opt_3", "action_type": "abort", "label": "E", "description": "F"}
          ],
          "extra": true
        }"""

        with self.assertRaises(FallbackEngineError):
            EvolutionaryFallbackEngine.parse_options(json_text, "task", "blocked_fallback", "evolutionary_doubt")

    def test_parse_rejects_wrong_option_count(self):
        json_text = """{
          "hypotheses": [
            {"id": "opt_1", "action_type": "ask_human", "label": "A", "description": "B"}
          ]
        }"""

        with self.assertRaises(FallbackEngineError):
            EvolutionaryFallbackEngine.parse_options(json_text, "task", "blocked_fallback", "evolutionary_doubt")

    def test_parse_rejects_wrong_action_type(self):
        json_text = """{
          "hypotheses": [
            {"id": "opt_1", "action_type": "ask_human", "label": "A", "description": "B"},
            {"id": "opt_2", "action_type": "delete_files", "label": "C", "description": "D"},
            {"id": "opt_3", "action_type": "abort", "label": "E", "description": "F"}
          ]
        }"""

        with self.assertRaises(FallbackEngineError):
            EvolutionaryFallbackEngine.parse_options(json_text, "task", "blocked_fallback", "evolutionary_doubt")

    def test_rejects_invalid_inputs_before_calling_llm(self):
        transceiver = FakeTransceiver(VALID_RESPONSE)
        engine = EvolutionaryFallbackEngine(transceiver)

        with self.assertRaises(FallbackEngineError):
            asyncio.run(engine.generate_hypotheses({"bad": "result"}, self.envelope))

        self.assertEqual(transceiver.calls, [])


if __name__ == "__main__":
    unittest.main()
