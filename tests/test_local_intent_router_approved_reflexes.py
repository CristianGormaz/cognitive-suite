import pytest
import os
import json
from unittest.mock import MagicMock, AsyncMock
from core.task_envelope import TaskEnvelope
from main import MainOrchestrator
from core.local_intent_router import LocalIntentRouter

@pytest.fixture
def mock_orchestrator(tmp_path):
    memory_dir = tmp_path / "memory"
    memory_dir.mkdir()
    
    router = IngestionRouter_Mock()
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
    
    # Inyectar dependencias con memoria temporal
    from core.minimal_neural_layer import MinimalNeuralLayer
    from core.reflex_promotion_gate import ReflexPromotionGate
    from core.reflex_shadow_evaluator import ReflexShadowEvaluator
    
    minimal = MinimalNeuralLayer(memory_dir=str(memory_dir))
    gate = ReflexPromotionGate(memory_dir=str(memory_dir))
    shadow = ReflexShadowEvaluator(memory_dir=str(memory_dir))
    
    # Patrón de prueba
    minimal.patterns = [{
        "pattern_id": "p_test",
        "pattern_name": "test_reflex",
        "trigger_signature": "activar reflejo",
        "recommended_action": "respond",
        "decision_category": "chat",
        "confidence": 1.0,
        "risk_score": 0.0
    }]
    
    orchestrator = MainOrchestrator(
        router, planner, dispatcher, cognitive, genesis, loader, auditor,
        minimal_neural_layer=minimal,
        reflex_promotion_gate=gate,
        shadow_evaluator=shadow
    )
    return orchestrator

class IngestionRouter_Mock:
    async def route_text(self, text, **kwargs):
        return TaskEnvelope.from_text(text)

@pytest.mark.asyncio
async def test_router_ignores_unapproved_reflex(mock_orchestrator):
    # 'activar reflejo' matchea patrón p_test, pero no está aprobado
    result = await mock_orchestrator.process_input("activar reflejo")
    
    # Si no está aprobado, el LocalIntentRouter debería devolver matched=False (o caer en keywords fijas)
    # y el pipeline real llamaría al planificador
    assert mock_orchestrator.planner.plan.called is True

@pytest.mark.asyncio
async def test_router_uses_approved_reflex(mock_orchestrator):
    # Aprobar el patrón
    mock_orchestrator.reflex_promotion_gate.approve_promotion("p_test", "manual approval")
    
    result = await mock_orchestrator.process_input("activar reflejo")
    
    # VERIFICACIÓN CRÍTICA: El planificador NO debe haber sido llamado
    assert mock_orchestrator.planner.plan.called is False
    assert result.status == "executed"
