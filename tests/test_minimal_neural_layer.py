import pytest
import json
from pathlib import Path
from core.minimal_neural_layer import MinimalNeuralLayer

@pytest.fixture
def mock_ledger(tmp_path):
    ledger = tmp_path / "distilled_reasoning_ledger.jsonl"
    ledger.write_text(json.dumps({
        "pattern_id": "p1", "pattern_name": "avoid_llm", "trigger_signature": "high_timeouts",
        "recommended_action": "bypass", "confidence": 0.9, "local_rule_summary": "rule1",
        "source_refs": []
    }) + "\n")
    return tmp_path

def test_minimal_neural_layer_load(mock_ledger):
    layer = MinimalNeuralLayer(memory_dir=str(mock_ledger))
    assert len(layer.patterns) == 1
    assert layer.patterns[0]["pattern_name"] == "avoid_llm"

def test_minimal_neural_layer_match(mock_ledger):
    layer = MinimalNeuralLayer(memory_dir=str(mock_ledger))
    match = layer.match_pattern({"trigger_signature": "high_timeouts"})
    assert match is not None
    assert match["recommended_action"] == "bypass"

def test_minimal_neural_layer_suggest_reflex(mock_ledger):
    layer = MinimalNeuralLayer(memory_dir=str(mock_ledger))
    suggestion = layer.suggest_reflex({"trigger_signature": "high_timeouts"})
    assert suggestion == "bypass"
    
    no_match = layer.suggest_reflex({"trigger_signature": "unknown"})
    assert no_match is None
