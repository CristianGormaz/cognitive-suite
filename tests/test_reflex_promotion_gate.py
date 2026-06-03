import pytest
import os
import json
from pathlib import Path
from core.reflex_promotion_gate import ReflexPromotionGate, ReflexPromotionAssessment

@pytest.fixture
def mock_memory(tmp_path):
    memory_dir = tmp_path / "memory"
    memory_dir.mkdir()
    return memory_dir

@pytest.fixture
def mock_context_frame():
    class MockDim:
        def __init__(self, score, status):
            self.score = score
            self.status = status
            
    class MockFrame:
        def __init__(self, score, status):
            self.overall_context_score = score
            self.constraint_context = MockDim(score, status)
            self.missing_context = []
            
    return MockFrame

def test_assess_pattern_low_agreement(mock_memory, mock_context_frame):
    # Crear ledger de sombra con bajo acuerdo
    shadow_ledger = mock_memory / "reflex_shadow_ledger.jsonl"
    with open(shadow_ledger, "w") as f:
        f.write(json.dumps({"matched_pattern_id": "p1", "agreement_with_real_route": False}) + "\n")
        
    # Crear ledger de destilación
    dist_ledger = mock_memory / "distilled_reasoning_ledger.jsonl"
    with open(dist_ledger, "w") as f:
        f.write(json.dumps({"pattern_id": "p1", "pattern_name": "test", "risk_score": 0.05}) + "\n")
        
    gate = ReflexPromotionGate(memory_dir=str(mock_memory))
    ctx = mock_context_frame(0.9, "stable")
    
    assessment = gate.assess_pattern_for_promotion("p1", ctx)
    assert assessment.promotion_allowed is False
    assert "Agreement rate" in assessment.reason_summary

def test_assess_pattern_low_context(mock_memory, mock_context_frame):
    shadow_ledger = mock_memory / "reflex_shadow_ledger.jsonl"
    with open(shadow_ledger, "w") as f:
        f.write(json.dumps({"matched_pattern_id": "p1", "agreement_with_real_route": True}) + "\n")
        
    dist_ledger = mock_memory / "distilled_reasoning_ledger.jsonl"
    with open(dist_ledger, "w") as f:
        f.write(json.dumps({"pattern_id": "p1", "pattern_name": "test", "risk_score": 0.05}) + "\n")
        
    gate = ReflexPromotionGate(memory_dir=str(mock_memory))
    ctx = mock_context_frame(0.5, "stable") # Contexto bajo
    
    assessment = gate.assess_pattern_for_promotion("p1", ctx)
    assert assessment.promotion_allowed is False
    assert "Context score" in assessment.reason_summary

def test_approve_and_get_active(mock_memory):
    gate = ReflexPromotionGate(memory_dir=str(mock_memory))
    gate.approve_promotion("p1", "test reason")
    
    active = gate.get_active_reflexes()
    assert "p1" in active

def test_disable_reflex(mock_memory):
    gate = ReflexPromotionGate(memory_dir=str(mock_memory))
    gate.approve_promotion("p1", "approve")
    gate.disable_reflex("p1", "disable")
    
    active = gate.get_active_reflexes()
    assert "p1" not in active
