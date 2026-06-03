import asyncio
import sys
import tempfile
import unittest
from pathlib import Path


sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from cognition.llm_planner import (
    LLMPlanParseError,
    LLMPlanValidationError,
    LLMPlanner,
    PLANNER_OPERATOR_INSTRUCTION,
    PLANNER_SYSTEM_PROMPT,
)
from core.iafa_auditor import IafaAuditor
from core.task_envelope import TaskEnvelope


VALID_RESPONSE = """<think>
El contenido parece un documento de arquitectura. El riesgo es bajo.
</think>
{
  "intent_category": "document_analysis",
  "proposed_action": "store_in_semantic_memory",
  "iafa_friction_estimates": {
    "R": 0.1,
    "I": 0.2,
    "N": 0.05
  },
  "execution_payload": {
    "target_path": "assets/memory/documents",
    "extracted_tags": ["simulacion", "arquitectura"]
  }
}"""


class FakeTransceiver:
    def __init__(self, response):
        self.response = response
        self.calls = []

    async def query_llm(self, *args, **kwargs):
        self.calls.append((args, kwargs))
        return self.response


class LLMPlannerTests(unittest.TestCase):
    def setUp(self):
        self.envelope = TaskEnvelope.from_text(
            "contenido de arquitectura",
            declared_intent="classify",
            created_at="2026-05-31T12:00:00Z",
        )

    def test_parse_response_extracts_thought_and_validates_decision(self):
        planner = LLMPlanner(FakeTransceiver(VALID_RESPONSE))

        plan = planner.parse_response(self.envelope, VALID_RESPONSE)

        self.assertEqual(plan.task_id, self.envelope.task_id)
        self.assertIn("riesgo es bajo", plan.thought_trace)
        self.assertEqual(plan.decision.intent_category, "document_analysis")
        self.assertEqual(plan.decision.proposed_action, "store_in_semantic_memory")
        self.assertEqual(plan.decision.iafa_friction_estimates.R, 0.1)
        self.assertEqual(plan.to_iafa_context_overlay(), {"R": 0.1, "I": 0.2, "N": 0.05})
        self.assertEqual(plan.decision.execution_payload.target_path, "assets/memory/documents")
        self.assertEqual(plan.decision.execution_payload.extracted_tags, ("simulacion", "arquitectura"))

    def test_plan_calls_transceiver_with_planner_prompt_and_audits(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            auditor = IafaAuditor(str(Path(temp_dir) / "audit.log"), secret_key="test-secret")
            transceiver = FakeTransceiver(VALID_RESPONSE)
            planner = LLMPlanner(transceiver, auditor)

            plan = asyncio.run(planner.plan(self.envelope, max_payload_chars=42))
            entries = list(auditor.iter_verified_entries())

        self.assertEqual(plan.decision.intent_category, "document_analysis")
        self.assertEqual(len(transceiver.calls), 1)
        args, kwargs = transceiver.calls[0]
        self.assertEqual(args[0], self.envelope)
        self.assertEqual(kwargs["system_prompt"], PLANNER_SYSTEM_PROMPT)
        self.assertEqual(kwargs["operator_instruction"], PLANNER_OPERATOR_INSTRUCTION)
        self.assertFalse(kwargs["json_format"])
        self.assertEqual(kwargs["max_payload_chars"], 42)
        self.assertEqual(len(entries), 1)
        payload = entries[0]["payload"]
        self.assertEqual(payload["record_type"], "llm_cognitive_plan")
        self.assertEqual(payload["task"]["task_id"], self.envelope.task_id)
        self.assertEqual(payload["plan"]["decision"]["iafa_friction_estimates"]["R"], 0.1)
        self.assertIn("riesgo es bajo", payload["plan"]["thought_trace"])

    def test_rejects_conversational_response(self):
        planner = LLMPlanner(FakeTransceiver("Claro, puedo ayudarte con eso."))

        with self.assertRaises(LLMPlanParseError):
            planner.parse_response(self.envelope, "Claro, puedo ayudarte con eso.")

    def test_plan_audits_rejected_response_thought_trace(self):
        response = "<think>Estoy dudando.</think>\nClaro, puedo ayudarte."
        with tempfile.TemporaryDirectory() as temp_dir:
            auditor = IafaAuditor(str(Path(temp_dir) / "audit.log"), secret_key="test-secret")
            planner = LLMPlanner(FakeTransceiver(response), auditor)

            with self.assertRaises(LLMPlanParseError):
                asyncio.run(planner.plan(self.envelope))
            entries = list(auditor.iter_verified_entries())

        self.assertEqual(len(entries), 1)
        payload = entries[0]["payload"]
        self.assertEqual(payload["record_type"], "llm_cognitive_plan_rejected")
        self.assertEqual(payload["task"]["task_id"], self.envelope.task_id)
        self.assertEqual(payload["thought_trace"], "Estoy dudando.")
        self.assertIn("Could not find a valid JSON object", payload["error"])

    def test_rejects_json_with_extra_top_level_key(self):
        response = """{
          "intent_category": "document_analysis",
          "proposed_action": "store_in_semantic_memory",
          "iafa_friction_estimates": {"R": 0.1, "I": 0.2, "N": 0.05},
          "execution_payload": {"target_path": "assets/memory/documents", "extracted_tags": []},
          "chatty_note": "listo"
        }"""

        with self.assertRaises(LLMPlanValidationError):
            LLMPlanner(FakeTransceiver(response)).parse_response(self.envelope, response)

    def test_rejects_out_of_range_friction(self):
        response = """{
          "intent_category": "document_analysis",
          "proposed_action": "store_in_semantic_memory",
          "iafa_friction_estimates": {"R": 1.1, "I": 0.2, "N": 0.05},
          "execution_payload": {"target_path": "assets/memory/documents", "extracted_tags": []}
        }"""

        with self.assertRaises(LLMPlanValidationError):
            LLMPlanner(FakeTransceiver(response)).parse_response(self.envelope, response)

    def test_rejects_parent_traversal_target_path(self):
        response = """{
          "intent_category": "code_generation",
          "proposed_action": "send_to_sandbox",
          "iafa_friction_estimates": {"R": 0.8, "I": 0.4, "N": 0.2},
          "execution_payload": {"target_path": "../outside", "extracted_tags": ["codigo"]}
        }"""

        with self.assertRaises(LLMPlanValidationError):
            LLMPlanner(FakeTransceiver(response)).parse_response(self.envelope, response)


if __name__ == "__main__":
    unittest.main()
