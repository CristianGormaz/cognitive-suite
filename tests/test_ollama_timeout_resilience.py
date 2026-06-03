import asyncio
import pytest
from unittest.mock import AsyncMock, patch, MagicMock

from core.task_envelope import TaskEnvelope
from main import MainOrchestrator, MainProcessResult
from cognition.iafa_transceiver import IafaTransceiver

@pytest.mark.asyncio
async def test_process_input_handles_timeout_gracefully():
    # Mocking transceiver to raise the expected TimeoutError
    transceiver = IafaTransceiver(timeout_seconds=1)
    
    # We force `query_llm` to raise the custom RuntimeError indicating timeout
    transceiver.query_llm = AsyncMock(side_effect=RuntimeError("Ollama no respondió dentro del tiempo configurado (1s)."))
    
    # Mock auditor to avoid file IO
    auditor = MagicMock()
    
    # Instantiate planner with this transceiver
    from cognition.llm_planner import LLMPlanner
    planner = LLMPlanner(transceiver, auditor)
    
    # Mock ingestion router to just pass through
    router = AsyncMock()
    async def fake_route(text, **kwargs):
        return TaskEnvelope.from_text(text)
    router.route_text.side_effect = fake_route
    
    # Instantiate MainOrchestrator with specific mocks
    orchestrator = MainOrchestrator(
        ingestion_router=router,
        planner=planner,
        dispatcher=AsyncMock(),
        cognitive_orchestrator=AsyncMock(),
        genesis_engine=AsyncMock(),
        skill_loader=AsyncMock(),
        auditor=auditor
    )
    
    # Configure dispatcher mock to return a failed result to avoid handle_fallback_cycle if reached
    from core.action_dispatcher import DispatchResult
    orchestrator.dispatcher.dispatch.return_value = DispatchResult(
        status="blocked", ui_state="error", iafa_score=0.0, threshold=0.7,
        action="none", task_id="task_1", details={"error": "should not reach here"}
    )
    
    # Call process_input
    result = await orchestrator.process_input("procesa esta consulta compleja")
    
    # Verify we get a clean error result
    assert isinstance(result, MainProcessResult)
    assert result.stage == "error"
    assert result.status == "error"
    assert "error" in result.details
    assert "Ollama no respondió" in result.details["error"]
