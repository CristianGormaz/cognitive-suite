import pytest
import os
import json
from pathlib import Path
from core.reflex_shadow_evaluator import ReflexShadowEvaluator, ReflexShadowEvaluation

@pytest.fixture
def mock_memory(tmp_path):
    return tmp_path

def test_evaluator_agreement(mock_memory):
    evaluator = ReflexShadowEvaluator(memory_dir=str(mock_memory))
    
    suggestion = {
        "pattern_id": "p1",
        "recommended_action": "respond",
        "match_confidence": 0.9,
        "risk_score": 0.05
    }
    
    res = evaluator.evaluate("hola", "respond", suggestion)
    
    assert res.agreement_with_real_route is True
    assert res.usefulness_estimate == 1.0
    assert res.recommendation == "promote_to_local_router"

def test_evaluator_disagreement(mock_memory):
    evaluator = ReflexShadowEvaluator(memory_dir=str(mock_memory))
    
    suggestion = {
        "pattern_id": "p1",
        "recommended_action": "pdf_reader",
        "match_confidence": 0.9,
        "risk_score": 0.1
    }
    
    res = evaluator.evaluate("hola", "respond", suggestion)
    
    assert res.agreement_with_real_route is False
    assert res.usefulness_estimate == 0.0
    assert res.recommendation == "monitor" # Ahora es monitor en lugar de refine_pattern

def test_summarize_performance(mock_memory):
    evaluator = ReflexShadowEvaluator(memory_dir=str(mock_memory))
    
    # 2 agreements, 1 disagreement
    evaluator.evaluate("sig1", "act1", {"recommended_action": "act1", "confidence": 0.9})
    evaluator.evaluate("sig2", "act2", {"recommended_action": "act2", "confidence": 0.9})
    evaluator.evaluate("sig3", "act3", {"recommended_action": "diff", "confidence": 0.9})
    
    stats = evaluator.summarize_performance()
    assert stats["total_evaluations"] == 3
    assert stats["agreement_rate"] == 0.67
