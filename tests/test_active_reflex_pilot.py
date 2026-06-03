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
    
    # Patrón piloto
    pattern_id = "dist_pilot"
    minimal.patterns = [{
        "pattern_id": pattern_id,
        "pattern_name": "pilot_reflex",
        "trigger_signature": "test pilot",
        "recommended_action": "respond",
        "decision_category": "chat",
        "confidence": 1.0,
        "risk_score": 0.0
    }]
    
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
async def test_active_reflex_pilot_lifecycle(mock_orchestrator):
    pattern_id = "dist_pilot"
    
    # 1. Antes de aprobación: cae a flujo normal (planner llamado)
    with patch.object(mock_orchestrator.ingestion_router, "route_text", AsyncMock(return_value=TaskEnvelope.from_text("test pilot"))):
        await mock_orchestrator.process_input("test pilot")
        assert mock_orchestrator.planner.plan.called is True
        mock_orchestrator.planner.plan.reset_mock()

    # 2. Aprobar reflejo
    mock_orchestrator.reflex_promotion_gate.approve_promotion(pattern_id, "pilot activation")
    assert pattern_id in mock_orchestrator.reflex_promotion_gate.get_active_reflexes()

    # 3. Después de aprobación: bypass LLM
    with patch.object(mock_orchestrator.ingestion_router, "route_text", AsyncMock(return_value=TaskEnvelope.from_text("test pilot"))):
        result = await mock_orchestrator.process_input("test pilot")
        assert mock_orchestrator.planner.plan.called is False
        assert result.status == "executed"

    # 4. Rollback: desactivar reflejo
    mock_orchestrator.reflex_promotion_gate.disable_reflex(pattern_id, "rollback pilot")
    assert pattern_id not in mock_orchestrator.reflex_promotion_gate.get_active_reflexes()

    # 5. Después de rollback: vuelve a flujo normal (planner llamado)
    with patch.object(mock_orchestrator.ingestion_router, "route_text", AsyncMock(return_value=TaskEnvelope.from_text("test pilot"))):
        await mock_orchestrator.process_input("test pilot")
        assert mock_orchestrator.planner.plan.called is True
