import pytest
import os
from unittest.mock import MagicMock, AsyncMock
from cognition.ingestion_router import IngestionRouter
from main import MainOrchestrator

@pytest.fixture
def mock_orchestrator():
    router = IngestionRouter()
    planner = AsyncMock()
    dispatcher = AsyncMock()
    cognitive = AsyncMock()
    genesis = AsyncMock()
    loader = AsyncMock()
    auditor = MagicMock()
    
    from core.action_dispatcher import DispatchResult
    async def fake_dispatch(plan):
        return DispatchResult(
            status="executed", ui_state="action_executed", iafa_score=0.95,
            threshold=0.7, action=plan.decision.proposed_action, task_id=plan.task_id,
            details={"receipt": {"ok": True}}
        )
    dispatcher.dispatch.side_effect = fake_dispatch
    
    orchestrator = MainOrchestrator(router, planner, dispatcher, cognitive, genesis, loader, auditor)
    return orchestrator

@pytest.mark.asyncio
async def test_force_local_only_blocks_unknown_intents(mock_orchestrator):
    with pytest.MonkeyPatch().context() as mp:
        mp.setenv("GREYS_FORCE_LOCAL_ONLY", "1")
        # unknown_text no matcheará en LocalIntentRouter
        unknown_text = "mensaje complejo que requiere LLM"
        
        from cognition.llm_planner import LLMServiceError
        mock_orchestrator.planner.plan.side_effect = LLMServiceError("LLM calls blocked by ExternalChannelGate")
        
        result = await mock_orchestrator.process_input(unknown_text)
        
        assert result.status == "error"
        assert "ExternalChannelGate" in str(result.details.get("error", "")) or "LLM calls blocked" in str(result.details.get("error", ""))
