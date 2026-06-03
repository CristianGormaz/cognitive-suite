import pytest
import os
import json
from unittest.mock import MagicMock, AsyncMock
from main import MainOrchestrator
from core.task_envelope import TaskEnvelope

@pytest.fixture
def mock_orchestrator(tmp_path):
    memory_dir = tmp_path / "memory"
    memory_dir.mkdir()
    
    router = AsyncMock()
    planner = AsyncMock()
    dispatcher = AsyncMock()
    cognitive = AsyncMock()
    genesis = AsyncMock()
    loader = AsyncMock()
    auditor = MagicMock()
    
    from cognition.llm_planner import CognitivePlan, CognitiveDecision, IafaFrictionEstimates, CognitiveExecutionPayload
    from core.action_dispatcher import DispatchResult
    
    # Mock planner result
    planner.plan.return_value = CognitivePlan(
        task_id="task_1",
        thought_trace="thinking",
        raw_response_sha256="abc",
        decision=CognitiveDecision(
            intent_category="chat",
            proposed_action="respond",
            iafa_friction_estimates=IafaFrictionEstimates(0.1, 0.1, 0.1),
            execution_payload=CognitiveExecutionPayload("n/a", ())
        )
    )
    
    # Mock dispatcher result
    dispatcher.dispatch.return_value = DispatchResult(
        status="executed", ui_state="action_executed", iafa_score=1.0,
        threshold=0.7, action="respond", task_id="task_1",
        details={"test": True}
    )
    
    # Mock ingestion router result
    router.route_text.return_value = TaskEnvelope.from_text("buenas tardes")
    
    orchestrator = MainOrchestrator(
        router, planner, dispatcher, cognitive, genesis, loader, auditor,
        memory_dir=str(memory_dir)
    )
    return orchestrator, memory_dir

@pytest.mark.asyncio
async def test_classifier_to_shadow_reflex_flow(mock_orchestrator):
    orchestrator, memory_dir = mock_orchestrator
    
    with pytest.MonkeyPatch().context() as mp:
        mp.setenv("GREYS_LOCAL_CLASSIFIER_SHADOW_ENABLED", "1")
        
        # 'buenas tardes' debería predecir 'greeting' con alta confianza
        await orchestrator.process_input("buenas tardes")
        
        # Verificar que se creó el candidato shadow
        candidate_ledger = memory_dir / "classifier_shadow_candidates.jsonl"
        assert candidate_ledger.exists()
        
        with open(candidate_ledger, "r") as f:
            lines = f.readlines()
            last = json.loads(lines[-1])
            assert last["predicted_intent"] == "greeting"
            assert last["proposed_reflex_name"] == "generalized_greeting_reflex"
            assert last["shadow_only"] is True
