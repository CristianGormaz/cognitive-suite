import pytest
from core.reflex_shadow_evaluator import ReflexShadowEvaluator

@pytest.fixture
def mock_stress_guard():
    class MockStress:
        def __init__(self): self.stressed = False
        def is_host_under_stress(self): return self.stressed
    return MockStress()

def test_promotion_candidate_requires_stable_context(tmp_path, mock_stress_guard):
    evaluator = ReflexShadowEvaluator(memory_dir=str(tmp_path), stress_guard=mock_stress_guard)
    
    suggestion = {
        "pattern_id": "p1",
        "recommended_action": "respond",
        "match_confidence": 0.95,
        "risk_score": 0.05
    }
    
    # 1. Contexto estable -> Promover
    res1 = evaluator.evaluate("hola", "respond", suggestion)
    assert res1.classification == "candidate_for_promotion"
    assert res1.recommendation == "promote_to_local_router"
    
    # 2. Host bajo estrés -> Bloquear promoción contextual
    mock_stress_guard.stressed = True
    res2 = evaluator.evaluate("hola", "respond", suggestion)
    assert res2.classification == "redundant_but_safe" # Ya no es candidate_for_promotion por contexto
    assert res2.recommendation == "wait_for_context_critical"
