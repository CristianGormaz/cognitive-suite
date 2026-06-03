import pytest
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
            status="executed",
            ui_state="action_executed",
            iafa_score=0.95,
            threshold=0.7,
            action=plan.decision.proposed_action,
            task_id=plan.task_id,
            details={"receipt": {"ok": True}}
        )
    dispatcher.dispatch.side_effect = fake_dispatch
    
    orchestrator = MainOrchestrator(router, planner, dispatcher, cognitive, genesis, loader, auditor)
    return orchestrator

@pytest.mark.asyncio
async def test_hello_bypasses_llm(mock_orchestrator):
    result = await mock_orchestrator.process_input("hola")
    
    assert result.status == "executed"
    assert "soy Greys-v3" in result.details["response_text"]
    assert mock_orchestrator.planner.plan.call_count == 0

@pytest.mark.asyncio
async def test_status_bypasses_llm(mock_orchestrator):
    result = await mock_orchestrator.process_input("estado del sistema")
    
    assert result.status == "executed"
    assert "Sistemas operativos" in result.details["response_text"]
    assert mock_orchestrator.planner.plan.call_count == 0

@pytest.mark.asyncio
async def test_help_bypasses_llm(mock_orchestrator):
    result = await mock_orchestrator.process_input("ayuda")
    
    assert result.status == "executed"
    assert "Puedo conversar contigo" in result.details["response_text"]
    assert mock_orchestrator.planner.plan.call_count == 0
