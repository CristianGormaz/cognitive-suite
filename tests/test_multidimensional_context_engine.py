import pytest
from core.multidimensional_context import MultidimensionalContextEngine, ContextDimension

@pytest.fixture
def mock_stress_guard():
    class MockStress:
        def __init__(self): self.stressed = False
        def is_host_under_stress(self): return self.stressed
    return MockStress()

def test_build_context_frame_stable(mock_stress_guard):
    engine = MultidimensionalContextEngine(stress_guard=mock_stress_guard)
    frame = engine.build_context_frame("test_decision")
    
    assert frame.environment_context.status == "stable"
    assert frame.overall_context_score > 0.8
    assert frame.recommended_decision == "promote"

def test_build_context_frame_stressed(mock_stress_guard):
    mock_stress_guard.stressed = True
    engine = MultidimensionalContextEngine(stress_guard=mock_stress_guard)
    frame = engine.build_context_frame("test_decision")
    
    assert frame.environment_context.status == "stressed"
    assert frame.context_risk_level == "critical"
    assert frame.recommended_decision == "block"

def test_build_context_frame_policy_blocked():
    engine = MultidimensionalContextEngine()
    # Simular violación de política en metadata
    frame = engine.build_context_frame("test_decision", metadata={"policy_violation": True})
    
    assert frame.constraint_context.status == "blocked"
    assert frame.context_risk_level == "critical"
    assert frame.recommended_decision == "block"

def test_overall_score_calculation():
    engine = MultidimensionalContextEngine()
    d1 = ContextDimension("d1", 1.0, "stable", [])
    d2 = ContextDimension("d2", 0.0, "blocked", [])
    
    score = engine.calculate_overall_score(d1, d2)
    assert score == 0.5
