import pytest
import os
from unittest.mock import MagicMock, AsyncMock
from cognition.ingestion_router import IngestionRouter
from core.task_envelope import TaskEnvelope
from main import MainOrchestrator

@pytest.fixture
def mock_orchestrator(tmp_path):
    memory_dir = tmp_path / "memory"
    memory_dir.mkdir()
    
    router = IngestionRouter()
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
    from core.reflex_shadow_evaluator import ReflexShadowEvaluator
    
    minimal_neural_layer = MinimalNeuralLayer(memory_dir=str(memory_dir))
    shadow_evaluator = ReflexShadowEvaluator(memory_dir=str(memory_dir))
    
    orchestrator = MainOrchestrator(
        router, planner, dispatcher, cognitive, genesis, loader, auditor,
        minimal_neural_layer=minimal_neural_layer,
        shadow_evaluator=shadow_evaluator
    )
    return orchestrator

@pytest.mark.asyncio
async def test_shadow_mode_records_evaluation_without_affecting_real_flow(mock_orchestrator):
    with pytest.MonkeyPatch().context() as mp:
        mp.setenv("GREYS_REFLEX_SHADOW_ENABLED", "1")
        
        # Simular un patrón en la capa neural
        mock_orchestrator.minimal_neural_layer.patterns = [{
            "pattern_id": "p1",
            "pattern_name": "hola_reflex",
            "trigger_signature": "hola",
            "recommended_action": "respond",
            "confidence": 0.95,
            "local_rule_summary": "rule"
        }]
        
        result = await mock_orchestrator.process_input("hola")
        
        assert result.status == "executed"
        
        # Verificar que se registró una evaluación en sombra
        stats = mock_orchestrator.shadow_evaluator.summarize_performance()
        assert stats["total_evaluations"] == 1
        assert stats["agreement_rate"] == 1.0

@pytest.mark.asyncio
async def test_shadow_mode_disabled_by_default(mock_orchestrator):
    # Por defecto no debe haber evaluaciones
    await mock_orchestrator.process_input("hola")
    stats = mock_orchestrator.shadow_evaluator.summarize_performance()
    assert stats["total_evaluations"] == 0
