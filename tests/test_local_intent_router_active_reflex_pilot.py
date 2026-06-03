import pytest
import os
import json
from unittest.mock import MagicMock
from core.local_intent_router import LocalIntentRouter
from core.task_envelope import TaskEnvelope

@pytest.fixture
def mock_deps(tmp_path):
    memory_dir = tmp_path / "memory"
    memory_dir.mkdir()
    
    from core.minimal_neural_layer import MinimalNeuralLayer
    from core.reflex_promotion_gate import ReflexPromotionGate
    
    minimal = MinimalNeuralLayer(memory_dir=str(memory_dir))
    gate = ReflexPromotionGate(memory_dir=str(memory_dir))
    
    return minimal, gate

def test_router_matches_active_reflex_over_hardcoded(mock_deps):
    minimal, gate = mock_deps
    
    # Patrón que sobreescribe o complementa 'hola'
    pid = "p_hola"
    minimal.patterns = [{
        "pattern_id": pid,
        "pattern_name": "custom_greeting",
        "trigger_signature": "hola",
        "recommended_action": "respond",
        "decision_category": "chat",
        "confidence": 1.0,
        "risk_score": 0.0
    }]
    
    router = LocalIntentRouter(minimal_neural_layer=minimal, promotion_gate=gate)
    envelope = TaskEnvelope.from_text("hola")
    
    # 1. No aprobado -> Matchea hardcoded keyword 'saludo'
    res1 = router.route_envelope(envelope)
    assert res1.matched is True
    assert res1.reason == "saludo"
    
    # 2. Aprobado -> Matchea reflejo activo
    gate.approve_promotion(pid, "test")
    res2 = router.route_envelope(envelope)
    assert res2.matched is True
    assert res2.reason == "active_reflex_custom_greeting"
