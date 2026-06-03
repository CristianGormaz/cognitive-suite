import asyncio
import pytest
from unittest.mock import MagicMock, patch
from core.action_dispatcher import ActionDispatcher, DispatchResult
from cognition.llm_planner import CognitivePlan, CognitiveDecision, IafaFrictionEstimates, CognitiveExecutionPayload
from core.iafa_engine import IAFAEngine

@pytest.mark.asyncio
async def test_action_dispatcher_supports_respond():
    # Setup IAFA Engine to allow everything
    mock_iafa = MagicMock(spec=IAFAEngine)
    mock_iafa.calculate_iafa_score.return_value = 1.0
    
    dispatcher = ActionDispatcher(iafa_engine=mock_iafa)
    
    # Create a plan with 'respond' action
    decision = CognitiveDecision(
        intent_category="chat",
        proposed_action="respond",
        iafa_friction_estimates=IafaFrictionEstimates(R=0.1, I=0.1, N=0.1),
        execution_payload=CognitiveExecutionPayload(target_path="n/a", extracted_tags=())
    )
    plan = CognitivePlan(
        task_id="test_task",
        decision=decision,
        thought_trace="thinking...",
        raw_response_sha256="fake_sha"
    )
    
    result = await dispatcher.dispatch(plan)
    
    assert result.status == "executed"
    assert result.action == "respond"
    assert "message" in result.details
    assert result.details["message"] == "Response pending execution by orchestrator"

@pytest.mark.asyncio
async def test_main_orchestrator_handles_respond():
    from main import MainOrchestrator
    from unittest.mock import AsyncMock
    
    # Mock dependencies
    mock_router = MagicMock()
    mock_planner = MagicMock()
    mock_dispatcher = MagicMock()
    mock_cog = MagicMock()
    mock_genesis = MagicMock()
    mock_loader = MagicMock()
    mock_auditor = MagicMock()
    
    orchestrator = MainOrchestrator(
        mock_router, mock_planner, mock_dispatcher, mock_cog, mock_genesis, mock_loader, mock_auditor
    )
    
    # Setup mock returns
    from core.task_envelope import TaskEnvelope
    envelope = TaskEnvelope.from_text("hola")
    mock_router.route_text = AsyncMock(return_value=envelope)
    
    decision = CognitiveDecision(
        intent_category="chat",
        proposed_action="respond",
        iafa_friction_estimates=IafaFrictionEstimates(R=0.1, I=0.1, N=0.1),
        execution_payload=CognitiveExecutionPayload(target_path="n/a", extracted_tags=())
    )
    plan = CognitivePlan(
        task_id="test_task",
        decision=decision,
        thought_trace="thinking...",
        raw_response_sha256="fake_sha"
    )
    mock_planner.plan = AsyncMock(return_value=plan)
    
    dispatch_result = DispatchResult(
        status="executed",
        ui_state="action_executed",
        iafa_score=1.0,
        threshold=0.7,
        action="respond",
        task_id="test_task",
        details={"iafa_context": {}}
    )
    mock_dispatcher.dispatch = AsyncMock(return_value=dispatch_result)
    
    result = await orchestrator.process_input("hola")
    
    assert result.status == "executed"
    assert "response_text" in result.details
    assert "Hola, soy Greys-v3" in result.details["response_text"]
