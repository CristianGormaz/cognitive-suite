import pytest
import os
import json
from unittest.mock import MagicMock, AsyncMock, patch
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
    
    from core.action_dispatcher import DispatchResult
    dispatcher.dispatch.return_value = DispatchResult(
        status="executed", ui_state="action_executed", iafa_score=0.95,
        threshold=0.7, action="respond", task_id="task_1",
        details={"receipt": {"ok": True}}
    )
    
    from core.minimal_neural_layer import MinimalNeuralLayer
    from core.reflex_promotion_gate import ReflexPromotionGate
    from core.reflex_shadow_evaluator import ReflexShadowEvaluator
    from core.local_intent_router import LocalIntentRouter
    
    minimal = MinimalNeuralLayer(memory_dir=str(memory_dir))
    gate = ReflexPromotionGate(memory_dir=str(memory_dir))
    shadow = ReflexShadowEvaluator(memory_dir=str(memory_dir))
    
    # Safe Reflex Pack v1
    minimal.patterns = [
        {"pattern_id": "p_help", "pattern_name": "help_reflex", "trigger_signature": "ayuda", "recommended_action": "respond", "decision_category": "chat", "confidence": 1.0, "risk_score": 0.0},
        {"pattern_id": "p_status", "pattern_name": "status_reflex", "trigger_signature": "estado", "recommended_action": "respond", "decision_category": "chat", "confidence": 1.0, "risk_score": 0.0},
        {"pattern_id": "p_identity", "pattern_name": "identity_reflex", "trigger_signature": "quien eres", "recommended_action": "respond", "decision_category": "chat", "confidence": 1.0, "risk_score": 0.0},
        {"pattern_id": "p_greet", "pattern_name": "basic_greeting_reflex", "trigger_signature": "hola", "recommended_action": "respond", "decision_category": "chat", "confidence": 1.0, "risk_score": 0.0}
    ]
    
    local_router = LocalIntentRouter(
        stress_guard=None,
        minimal_neural_layer=minimal,
        promotion_gate=gate
    )
    
    orchestrator = MainOrchestrator(
        router, planner, dispatcher, cognitive, genesis, loader, auditor,
        minimal_neural_layer=minimal,
        reflex_promotion_gate=gate,
        shadow_evaluator=shadow,
        local_intent_router=local_router
    )
    return orchestrator

@pytest.mark.asyncio
async def test_safe_reflex_pack_v1_activation_and_coexistence(mock_orchestrator):
    p_ids = ["p_help", "p_status", "p_identity"]
    
    # 1. Activate all in the pack
    for pid in p_ids:
        mock_orchestrator.reflex_promotion_gate.approve_promotion(pid, "Pack v1 activation")
    
    # Pre-existing greet reflex (also activate for test)
    mock_orchestrator.reflex_promotion_gate.approve_promotion("p_greet", "Pre-existing")

    # 2. Test each one (should bypass planner)
    test_cases = [
        ("ayuda", "p_help"),
        ("estado", "p_status"),
        ("quien eres", "p_identity"),
        ("hola", "p_greet")
    ]
    
    for text, pid in test_cases:
        with patch.object(mock_orchestrator.ingestion_router, "route_text", AsyncMock(return_value=TaskEnvelope.from_text(text))):
            mock_orchestrator.planner.plan.reset_mock()
            result = await mock_orchestrator.process_input(text)
            assert mock_orchestrator.planner.plan.called is False
            assert result.status == "executed"

@pytest.mark.asyncio
async def test_safe_reflex_pack_v1_rollback(mock_orchestrator):
    p_ids = ["p_help", "p_status", "p_identity"]
    for pid in p_ids:
        mock_orchestrator.reflex_promotion_gate.approve_promotion(pid, "Pack v1 activation")

    # Disable all
    for pid in p_ids:
        mock_orchestrator.reflex_promotion_gate.disable_reflex(pid, "Block rollback")
        
    # Should fall back (planner called or hardcoded keyword)
    # Note: LocalIntentRouter still matches hardcoded keywords if reflex is not active.
    # To really test rollback, we check if planner is called for a non-hardcoded but patterned intent.
    
    # Let's add a non-hardcoded one
    mock_orchestrator.minimal_neural_layer.patterns.append(
        {"pattern_id": "p_extra", "pattern_name": "extra", "trigger_signature": "extra_cmd", "recommended_action": "respond", "decision_category": "chat", "confidence": 1.0, "risk_score": 0.0}
    )
    
    # Approve and then disable
    mock_orchestrator.reflex_promotion_gate.approve_promotion("p_extra", "test")
    mock_orchestrator.reflex_promotion_gate.disable_reflex("p_extra", "rollback")
    
    with patch.object(mock_orchestrator.ingestion_router, "route_text", AsyncMock(return_value=TaskEnvelope.from_text("extra_cmd"))):
        mock_orchestrator.planner.plan.reset_mock()
        await mock_orchestrator.process_input("extra_cmd")
        assert mock_orchestrator.planner.plan.called is True
