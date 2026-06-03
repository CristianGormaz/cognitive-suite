import asyncio
import tempfile
import unittest
from pathlib import Path
from unittest.mock import MagicMock, AsyncMock

import sys


sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from cognition.llm_planner import (
    CognitiveDecision,
    CognitiveExecutionPayload,
    CognitivePlan,
    IafaFrictionEstimates,
)
from core.action_dispatcher import DispatchResult
from core.cognitive_loop import CognitiveLoopResult
from core.iafa_auditor import IafaAuditor
from core.task_envelope import TaskEnvelope
from main import MainOrchestrator


def make_plan() -> CognitivePlan:
    return CognitivePlan(
        task_id="task_main",
        thought_trace="plan auditado",
        raw_response_sha256="sha256",
        decision=CognitiveDecision(
            intent_category="document_analysis",
            proposed_action="store_in_semantic_memory",
            iafa_friction_estimates=IafaFrictionEstimates(R=0.1, I=0.1, N=0.1),
            execution_payload=CognitiveExecutionPayload(
                target_path="assets/memory/documents",
                extracted_tags=("greys", "core"),
            ),
        ),
    )


def make_dispatch_result(status: str = "executed") -> DispatchResult:
    return DispatchResult(
        status=status,
        ui_state="action_executed" if status == "executed" else "evolutionary_doubt",
        iafa_score=0.95 if status == "executed" else 0.25,
        threshold=0.7,
        action="store_in_semantic_memory",
        task_id="task_main",
        details={"fallback": "duda"} if status != "executed" else {"receipt": {"ok": True}},
    )


def make_fallback_result(action: str, status: str) -> CognitiveLoopResult:
    return CognitiveLoopResult(
        selected_action=action,
        status=status,
        task_id="task_main",
        details={"message": action},
    )


class FakeRouter:
    def __init__(self):
        self.calls = []

    async def route_text(self, text, origin="user", source_name=None, declared_intent=None, metadata=None, created_at=None):
        self.calls.append(
            {
                "text": text,
                "origin": origin,
                "source_name": source_name,
                "declared_intent": declared_intent,
                "metadata": metadata,
                "created_at": created_at,
            }
        )
        return TaskEnvelope.from_text(text, declared_intent=declared_intent)


class FakePlanner:
    def __init__(self, plan):
        self.plan_result = plan
        self.calls = []

    async def plan(self, envelope, max_payload_chars=6000):
        self.calls.append((envelope, max_payload_chars))
        return self.plan_result


class FakeDispatcher:
    def __init__(self, result):
        self.result = result
        self.calls = []

    async def dispatch(self, plan, recent_intents=None):
        self.calls.append((plan, recent_intents))
        return self.result


class FakeCognitiveOrchestrator:
    def __init__(self, result):
        self.result = result
        self.calls = []

    async def handle_fallback_cycle(self, dispatch_result, envelope):
        self.calls.append((dispatch_result, envelope))
        return self.result


class FakeGenesisEngine:
    def __init__(self, result=True):
        self.result = result
        self.calls = []
        self.sandbox = MagicMock()
        self.sandbox.validate_code_proposal = AsyncMock(return_value=MagicMock(is_safe=True, validation_errors=[], code_hash="fake"))

    def _sanitize_intent_name(self, name):
        return name.lower().replace(" ", "_")

    def _build_operator_instruction(self, name, envelope, context):
        return "instruction"

    def _normalize_generated_code(self, response):
        return response

    async def _validate_generated_shape(self, code):
        pass

    def _validate_generated_shape_sync(self, code):
        return []

    def _build_skill_module(self, name, code):
        return code

    async def synthesize_and_install_skill(self, intent_name, task_envelope, fallback_context):
        self.calls.append((intent_name, task_envelope, fallback_context))
        return self.result


class FakeSkillLoader:
    def __init__(self, result):
        self.result = result
        self.calls = []

    async def execute_skill(self, intent_name, context):
        self.calls.append((intent_name, context))
        return self.result


class MainOrchestratorTests(unittest.TestCase):
    def test_process_input_runs_normal_pipeline(self):
        async def run_case():
            with tempfile.TemporaryDirectory() as temp_dir:
                auditor = IafaAuditor(str(Path(temp_dir) / "audit.log"), secret_key="test-secret")
                router = FakeRouter()
                planner = FakePlanner(make_plan())
                dispatcher = FakeDispatcher(make_dispatch_result())
                cognitive = FakeCognitiveOrchestrator(make_fallback_result("abort", "aborted"))
                genesis = FakeGenesisEngine()
                loader = FakeSkillLoader({"ok": True})
                orchestrator = MainOrchestrator(router, planner, dispatcher, cognitive, genesis, loader, auditor)

                result = await orchestrator.process_input("procesa esta solicitud compleja")
                return result, router, planner, dispatcher, cognitive, genesis, loader

        result, router, planner, dispatcher, cognitive, genesis, loader = asyncio.run(run_case())

        self.assertEqual(result.stage, "dispatch_complete")
        self.assertEqual(result.status, "executed")
        self.assertEqual(len(router.calls), 1)
        self.assertEqual(len(planner.calls), 1)
        self.assertEqual(len(dispatcher.calls), 1)
        self.assertEqual(len(cognitive.calls), 0)
        self.assertEqual(len(genesis.calls), 0)
        self.assertEqual(len(loader.calls), 0)

    def test_process_input_sets_human_feedback_flag_and_marks_next_input(self):
        async def run_case():
            with tempfile.TemporaryDirectory() as temp_dir:
                auditor = IafaAuditor(str(Path(temp_dir) / "audit.log"), secret_key="test-secret")
                router = FakeRouter()
                planner = FakePlanner(make_plan())
                dispatcher = FakeDispatcher(make_dispatch_result(status="blocked_fallback"))
                cognitive = FakeCognitiveOrchestrator(make_fallback_result("ask_human", "human_channel_opening"))
                genesis = FakeGenesisEngine()
                loader = FakeSkillLoader({"ok": True})
                orchestrator = MainOrchestrator(router, planner, dispatcher, cognitive, genesis, loader, auditor)

                first = await orchestrator.process_input("primera entrada")
                flag_after_first = orchestrator.awaiting_human_feedback
                dispatcher.result = make_dispatch_result(status="executed")
                second = await orchestrator.process_input("segunda entrada")
                flag_after_second = orchestrator.awaiting_human_feedback
                return first, second, flag_after_first, flag_after_second, router

        first, second, flag_after_first, flag_after_second, router = asyncio.run(run_case())

        self.assertEqual(first.stage, "awaiting_human_feedback")
        self.assertTrue(flag_after_first)
        self.assertEqual(second.stage, "dispatch_complete")
        self.assertEqual(router.calls[1]["declared_intent"], "human_feedback")
        self.assertFalse(flag_after_second)

    def test_process_input_installs_and_executes_sandboxed_skill(self):
        async def run_case():
            with tempfile.TemporaryDirectory() as temp_dir:
                auditor = IafaAuditor(str(Path(temp_dir) / "audit.log"), secret_key="test-secret")
                router = FakeRouter()
                planner = FakePlanner(make_plan())
                dispatcher = FakeDispatcher(make_dispatch_result(status="blocked_fallback"))
                cognitive = FakeCognitiveOrchestrator(make_fallback_result("sandbox_code", "genesis_sandbox_routing"))
                genesis = FakeGenesisEngine(result=True)
                # Mock LLM transceiver to return code
                genesis.transceiver = MagicMock()
                genesis.transceiver.query_llm = AsyncMock(return_value="def _generated_skill_impl(context): return {}")

                loader = FakeSkillLoader({"ok": True, "message": "skill executed"})
                orchestrator = MainOrchestrator(router, planner, dispatcher, cognitive, genesis, loader, auditor)

                result = await orchestrator.process_input("crea una habilidad")
                return result, genesis, loader, router

        result, genesis, loader, router = asyncio.run(run_case())

        # AHORA: El flujo termina en genesis_analysis, no en skill_executed
        self.assertEqual(result.stage, "genesis_analysis")
        self.assertEqual(result.status, "analysis_complete")
        self.assertIn("analysis", result.details)


if __name__ == "__main__":
    unittest.main()
