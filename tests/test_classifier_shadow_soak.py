import pytest
import json
from pathlib import Path
from core.classifier_shadow_soak import ClassifierShadowSoakEvaluator

@pytest.fixture
def mock_memory(tmp_path):
    memory_dir = tmp_path / "memory"
    memory_dir.mkdir()
    return memory_dir

def test_soak_summarize_performance(mock_memory):
    ledger = mock_memory / "classifier_shadow_candidates.jsonl"
    candidates = [
        {"predicted_intent": "greeting", "confidence": 1.0, "input_signature": "hola", "risk_score": 0.0},
        {"predicted_intent": "greeting", "confidence": 0.9, "input_signature": "buenas", "risk_score": 0.0},
        {"predicted_intent": "unknown_safe", "confidence": 0.0, "input_signature": "xyz", "risk_score": 0.0}
    ]
    with open(ledger, "w") as f:
        for c in candidates:
            f.write(json.dumps(c) + "\n")
            
    evaluator = ClassifierShadowSoakEvaluator(memory_dir=str(mock_memory))
    summary = evaluator.summarize_performance()
    
    assert summary.total_candidates == 3
    assert summary.candidates_by_intent["greeting"] == 2
    assert summary.unknown_safe_rate == 0.33
    assert summary.average_confidence == 0.63 # (1.0 + 0.9 + 0.0) / 3

def test_soak_detects_duplicates(mock_memory):
    ledger = mock_memory / "classifier_shadow_candidates.jsonl"
    # Misma signature 'hola' repetida
    candidates = [
        {"predicted_intent": "greeting", "confidence": 1.0, "input_signature": "hola"},
        {"predicted_intent": "greeting", "confidence": 1.0, "input_signature": "hola"}
    ]
    with open(ledger, "w") as f:
        for c in candidates:
            f.write(json.dumps(c) + "\n")
            
    evaluator = ClassifierShadowSoakEvaluator(memory_dir=str(mock_memory))
    summary = evaluator.summarize_performance()
    
    assert summary.duplicate_rate == 1.0 # 1 signature con dupes / 1 signature total

def test_soak_no_data(mock_memory):
    evaluator = ClassifierShadowSoakEvaluator(memory_dir=str(mock_memory))
    summary = evaluator.summarize_performance()
    assert summary.total_candidates == 0
    assert summary.promotion_readiness == "no_data"
