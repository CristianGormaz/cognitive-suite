import pytest
import os
import json
from pathlib import Path
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
    router.route_text.return_value = TaskEnvelope.from_text("hola greys")
    
    orchestrator = MainOrchestrator(
        router, planner, dispatcher, cognitive, genesis, loader, auditor,
        memory_dir=str(memory_dir)
    )
    return orchestrator, memory_dir

@pytest.mark.asyncio
async def test_classifier_shadow_mode_records_prediction(mock_orchestrator):
    orchestrator, memory_dir = mock_orchestrator
    
    # IMPORTANTE: Forzar el path del ledger al directorio temporal del test
    ledger_path = memory_dir / "local_classifier_shadow_ledger.jsonl"
    
    with pytest.MonkeyPatch().context() as mp:
        mp.setenv("GREYS_LOCAL_CLASSIFIER_SHADOW_ENABLED", "1")
        
        # En src/main.py el path está hardcoded a assets/memory/...
        # Para el test, vamos a mockear el open o simplemente verificar el default
        # si no queremos cambiar src/main.py ahora.
        # Pero mejor vamos a usar el path real del proyecto si el test corre en el repo.
        
        # Simular input
        await orchestrator.process_input("hola greys")
        
        # Verificar que se creó el ledger en el directorio temporal
        assert ledger_path.exists()
        
        # Leer última entrada
        with open(ledger_path, "r") as f:
            lines = f.readlines()
            last = json.loads(lines[-1])
            assert last["predicted_intent"] == "greeting"
            assert "agreement_with_router" in last

def test_morning_brief_shows_classifier_section(tmp_path):
    from cognition.morning_brief import MorningBrief
    memory_dir = tmp_path / "memory"
    memory_dir.mkdir()
    
    # Crear ledger ficticio
    ledger = memory_dir / "local_classifier_shadow_ledger.jsonl"
    ledger.write_text(json.dumps({
        "predicted_intent": "greeting", "agreement_with_router": True, "confidence": 0.9,
        "classifier_version": "v0"
    }) + "\n")
    
    brief_gen = MorningBrief(memory_dir=str(memory_dir))
    brief = brief_gen.generate_brief()
    
    assert "Madurez del Clasificador Local" in brief
    assert "Predicciones totales (Sombra): 1" in brief
