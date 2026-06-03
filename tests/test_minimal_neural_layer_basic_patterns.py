import pytest
import json
import os
from pathlib import Path
from core.minimal_neural_layer import MinimalNeuralLayer

@pytest.fixture
def mock_memory(tmp_path):
    memory_dir = tmp_path / "memory"
    memory_dir.mkdir()
    ledger = memory_dir / "distilled_reasoning_ledger.jsonl"
    patterns = [
        {"pattern_name": "greeting", "trigger_signature": "hola", "recommended_action": "respond", "decision_category": "chat", "confidence": 1.0},
        {"pattern_name": "pdf", "trigger_signature": "application/pdf", "recommended_action": "pdf_reader_basic", "decision_category": "pdf_analysis", "confidence": 1.0}
    ]
    with open(ledger, "w") as f:
        for p in patterns:
            f.write(json.dumps(p) + "\n")
    return memory_dir

def test_minimal_layer_matches_greeting(mock_memory):
    layer = MinimalNeuralLayer(memory_dir=str(mock_memory))
    match = layer.match_pattern({"trigger_signature": "hola"})
    assert match is not None
    assert match["pattern_name"] == "greeting"
    assert match["match_confidence"] == 0.8 # 0.8 base for signature

def test_minimal_layer_matches_category(mock_memory):
    layer = MinimalNeuralLayer(memory_dir=str(mock_memory))
    # No signature, but category matches
    match = layer.match_pattern({"intent_category": "pdf_analysis"})
    assert match is not None
    assert match["pattern_name"] == "pdf"
    assert match["match_confidence"] == 0.4 # 0.4 base for category
