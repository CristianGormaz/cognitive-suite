import asyncio
import pytest
from unittest.mock import MagicMock, AsyncMock, patch
from core.cognitive_loop import CognitiveOrchestrator, CognitiveLoopResult
from cognition.fallback_engine import FallbackOptions, FallbackHypothesis
from core.task_envelope import TaskEnvelope
from core.action_dispatcher import DispatchResult

@pytest.mark.asyncio
async def test_cognitive_orchestrator_handles_evolutionary_doubt_method():
    # Setup
    mock_fallback = MagicMock()
    orchestrator = CognitiveOrchestrator(fallback_engine=mock_fallback)
    
    # Mock dialog and its behavior
    mock_dialog = MagicMock()
    mock_dialog.actionSelected = MagicMock()
    
    # We need to mock the connection and emission
    def mock_show():
        # Simulate user selecting 'sandbox_code'
        for call in mock_dialog.actionSelected.connect.call_args_list:
            callback = call.args[0]
            callback("sandbox_code")

    mock_dialog.show = mock_show
    orchestrator.dialog_factory = MagicMock(return_value=mock_dialog)
    
    # Create fake FallbackOptions
    options = FallbackOptions(
        task_id="test_spark_task",
        source_status="spark_reflection",
        ui_state="evolutionary_doubt",
        hypotheses=(
            FallbackHypothesis("opt_1", "sandbox_code", "Test Label", "Test Desc"),
            FallbackHypothesis("opt_2", "abort", "Abort", "Abort Desc"),
            FallbackHypothesis("opt_3", "ask_human", "Ask", "Ask Desc"),
        )
    )
    
    # Execute
    # We need to add this method to CognitiveOrchestrator
    if hasattr(orchestrator, "handle_evolutionary_doubt"):
        result = await orchestrator.handle_evolutionary_doubt(options)
        
        # Verify
        assert result.selected_action == "sandbox_code"
        assert result.task_id.startswith("task_")
        orchestrator.dialog_factory.assert_called_once_with(options)
    else:
        pytest.fail("CognitiveOrchestrator does not have handle_evolutionary_doubt method")

@pytest.mark.asyncio
async def test_main_orchestrator_routes_to_ui_when_enabled():
    from main import MainOrchestrator
    
    # Mock dependencies
    mock_cog = AsyncMock()
    mock_cog.handle_evolutionary_doubt.return_value = CognitiveLoopResult(
        selected_action="sandbox_code",
        status="genesis_sandbox_routing",
        task_id="spark_task_123",
        details={}
    )
    
    orchestrator = MainOrchestrator(
        ingestion_router=MagicMock(),
        planner=MagicMock(),
        dispatcher=MagicMock(),
        cognitive_orchestrator=mock_cog,
        genesis_engine=MagicMock(),
        skill_loader=MagicMock(),
        auditor=AsyncMock()
    )
    
    payload = {
        "proposal": {
            "task_id": "spark_task_123",
            "suggested_intent": "test_intent",
            "reasoning": "test reasoning",
            "friction_estimates": {"R": 0.1, "I": 0.2, "N": 0.3}
        },
        "signals": []
    }
    
    with patch.dict("os.environ", {"GREYS_EVOLUTION_UI_ENABLED": "1"}):
        await orchestrator.handle_evolutionary_doubt(payload)
        
    # Verify handle_evolutionary_doubt was called on cognitive_orchestrator
    assert mock_cog.handle_evolutionary_doubt.called
    args, _ = mock_cog.handle_evolutionary_doubt.call_args
    options = args[0]
    assert isinstance(options, FallbackOptions)
    assert options.task_id == "spark_task_123"
    assert any(h.action_type == "sandbox_code" for h in options.hypotheses)

@pytest.mark.asyncio
async def test_main_orchestrator_skips_ui_when_disabled():
    from main import MainOrchestrator
    
    mock_cog = AsyncMock()
    orchestrator = MainOrchestrator(
        ingestion_router=MagicMock(),
        planner=MagicMock(),
        dispatcher=MagicMock(),
        cognitive_orchestrator=mock_cog,
        genesis_engine=MagicMock(),
        skill_loader=MagicMock(),
        auditor=AsyncMock()
    )
    
    payload = {"proposal": {"suggested_intent": "test"}, "signals": []}
    
    with patch.dict("os.environ", {"GREYS_EVOLUTION_UI_ENABLED": "0"}):
        await orchestrator.handle_evolutionary_doubt(payload)
        
    assert not mock_cog.handle_evolutionary_doubt.called
