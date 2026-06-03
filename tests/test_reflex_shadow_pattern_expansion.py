import pytest
import os
import json
from pathlib import Path
from core.reflex_shadow_evaluator import ReflexShadowEvaluator

@pytest.fixture
def mock_memory(tmp_path):
    return tmp_path

def test_shadow_classification_aligned(mock_memory):
    evaluator = ReflexShadowEvaluator(memory_dir=str(mock_memory))
    suggestion = {
        "pattern_id": "p1", "recommended_action": "respond", 
        "match_confidence": 0.9, "risk_score": 0.05
    }
    res = evaluator.evaluate("hola", "respond", suggestion)
    assert res.classification == "candidate_for_promotion" # aligned + high conf + low risk

def test_shadow_classification_misaligned(mock_memory):
    evaluator = ReflexShadowEvaluator(memory_dir=str(mock_memory))
    suggestion = {
        "pattern_id": "p1", "recommended_action": "other", 
        "match_confidence": 0.9, "risk_score": 0.1
    }
    res = evaluator.evaluate("hola", "respond", suggestion)
    assert res.classification == "risky_divergence"

def test_shadow_classification_missing(mock_memory):
    evaluator = ReflexShadowEvaluator(memory_dir=str(mock_memory))
    res = evaluator.evaluate("unknown", "respond", None)
    assert res.classification == "missing_pattern"
