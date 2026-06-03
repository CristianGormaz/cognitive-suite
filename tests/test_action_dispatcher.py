import asyncio
import sys
import tempfile
import unittest
from pathlib import Path


sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from cognition.llm_planner import (
    CognitiveDecision,
    CognitiveExecutionPayload,
    CognitivePlan,
    IafaFrictionEstimates,
)
from core.action_dispatcher import ActionDispatcher, ActionDispatcherError, InMemoryMemoryWriter
from core.iafa_auditor import IafaAuditor
from core.iafa_engine import IAFAEngine


WEIGHTS = {"O": 0.1, "M": 0.2, "P": 0.3, "V": 0.2, "K": 0.2, "R": -0.4, "I": -0.3, "N": -0.2, "A": 0.8}


class SpyIAFAEngine:
    def __init__(self):
        self.calls = []

    def calculate_iafa_score(self, current_variables, recent_intents, current_hz):
        self.calls.append((dict(current_variables), list(recent_intents), current_hz))
        return 1.0


def make_plan(
    action="store_in_semantic_memory",
    target_path="assets/memory/documents",
    friction=None,
):
    friction = friction or IafaFrictionEstimates(R=0.1, I=0.2, N=0.05)
    return CognitivePlan(
        task_id="task_test",
        thought_trace="razonamiento auditado",
        raw_response_sha256="abc123",
        decision=CognitiveDecision(
            intent_category="document_analysis",
            proposed_action=action,
            iafa_friction_estimates=friction,
            execution_payload=CognitiveExecutionPayload(
                target_path=target_path,
                extracted_tags=("simulacion", "arquitectura"),
            ),
        ),
    )


class ActionDispatcherTests(unittest.TestCase):
    def test_approved_semantic_memory_action_writes_to_memory_and_audits(self):
        plan = make_plan()

        with tempfile.TemporaryDirectory() as temp_dir:
            auditor = IafaAuditor(str(Path(temp_dir) / "audit.log"), secret_key="test-secret")
            memory_writer = InMemoryMemoryWriter()
            dispatcher = ActionDispatcher(
                IAFAEngine(WEIGHTS, bias=0.1),
                auditor=auditor,
                memory_writer=memory_writer,
                threshold=0.7,
            )

            result = asyncio.run(dispatcher.dispatch(plan))
            entries = list(auditor.iter_verified_entries())

        self.assertEqual(result.status, "executed")
        self.assertEqual(result.ui_state, "action_executed")
        self.assertGreaterEqual(result.iafa_score, result.threshold)
        self.assertEqual(len(memory_writer.records), 1)
        self.assertEqual(memory_writer.records[0]["target_path"], "assets/memory/documents")
        self.assertEqual(memory_writer.records[0]["payload"]["task_id"], "task_test")
        self.assertEqual(entries[0]["payload"]["record_type"], "iafa_execution_approved")
        self.assertEqual(entries[0]["payload"]["result"]["status"], "executed")

    def test_blocked_low_iafa_score_audits_and_returns_evolutionary_doubt(self):
        plan = make_plan(friction=IafaFrictionEstimates(R=1.0, I=1.0, N=1.0))

        with tempfile.TemporaryDirectory() as temp_dir:
            auditor = IafaAuditor(str(Path(temp_dir) / "audit.log"), secret_key="test-secret")
            memory_writer = InMemoryMemoryWriter()
            dispatcher = ActionDispatcher(
                IAFAEngine(WEIGHTS, bias=0.0),
                auditor=auditor,
                memory_writer=memory_writer,
                threshold=0.7,
                internal_context={"O": 0.1, "M": 0.1, "P": 0.1, "V": 0.1, "K": 0.1, "A": 0.1},
            )

            result = asyncio.run(dispatcher.dispatch(plan))
            entries = list(auditor.iter_verified_entries())

        self.assertEqual(result.status, "blocked_fallback")
        self.assertEqual(result.ui_state, "evolutionary_doubt")
        self.assertEqual(result.details["fallback"], "duda")
        self.assertLess(result.iafa_score, result.threshold)
        self.assertEqual(memory_writer.records, [])
        self.assertEqual(entries[0]["payload"]["record_type"], "iafa_execution_blocked")
        self.assertEqual(entries[0]["payload"]["result"]["status"], "blocked_fallback")

    def test_build_iafa_context_injects_llm_friction_over_internal_context(self):
        plan = make_plan(friction=IafaFrictionEstimates(R=0.7, I=0.6, N=0.5))
        dispatcher = ActionDispatcher(
            IAFAEngine(WEIGHTS, bias=0.1),
            internal_context={"P": 0.85, "K": 0.75, "R": 0.0, "I": 0.0, "N": 0.0},
        )

        context = dispatcher.build_iafa_context(plan)

        self.assertEqual(context["P"], 0.85)
        self.assertEqual(context["K"], 0.75)
        self.assertEqual(context["R"], 0.7)
        self.assertEqual(context["I"], 0.6)
        self.assertEqual(context["N"], 0.5)

    def test_dispatch_calls_calculate_iafa_score_with_plan_friction(self):
        plan = make_plan(friction=IafaFrictionEstimates(R=0.3, I=0.4, N=0.5))
        spy_engine = SpyIAFAEngine()
        dispatcher = ActionDispatcher(
            spy_engine,
            threshold=0.7,
            internal_context={"P": 0.8, "K": 0.9},
        )

        result = asyncio.run(dispatcher.dispatch(plan, recent_intents=["intent"]))

        self.assertEqual(result.status, "executed")
        self.assertEqual(len(spy_engine.calls), 1)
        current_variables, recent_intents, current_hz = spy_engine.calls[0]
        self.assertEqual(current_variables["P"], 0.8)
        self.assertEqual(current_variables["K"], 0.9)
        self.assertEqual(current_variables["R"], 0.3)
        self.assertEqual(current_variables["I"], 0.4)
        self.assertEqual(current_variables["N"], 0.5)
        self.assertEqual(recent_intents, ["intent"])
        self.assertEqual(current_hz, 0.5)

    def test_unsupported_action_returns_fallback_without_memory_write(self):
        plan = make_plan(action="send_to_sandbox", friction=IafaFrictionEstimates(R=0.1, I=0.1, N=0.1))
        memory_writer = InMemoryMemoryWriter()
        dispatcher = ActionDispatcher(
            IAFAEngine(WEIGHTS, bias=0.1),
            memory_writer=memory_writer,
            threshold=0.7,
        )

        result = asyncio.run(dispatcher.dispatch(plan))

        self.assertEqual(result.status, "unsupported_fallback")
        self.assertEqual(result.ui_state, "evolutionary_doubt")
        self.assertEqual(result.details["reason"], "unsupported_action")
        self.assertEqual(memory_writer.records, [])

    def test_rejects_non_plan(self):
        dispatcher = ActionDispatcher(IAFAEngine(WEIGHTS, bias=0.1))

        with self.assertRaises(ActionDispatcherError):
            asyncio.run(dispatcher.dispatch({"not": "a plan"}))


if __name__ == "__main__":
    unittest.main()
