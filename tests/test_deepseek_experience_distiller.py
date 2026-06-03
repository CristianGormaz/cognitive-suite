import pytest
import os
import json
import time
from pathlib import Path
from cognition.deepseek_experience_distiller import DeepseekExperienceDistiller, DistilledReasoningPattern

@pytest.fixture
def mock_memory(tmp_path):
    memory_dir = tmp_path / "memory"
    memory_dir.mkdir()
    return memory_dir

def test_distill_from_llm_failures(mock_memory):
    # Crear ledger de salud con muchos timeouts
    health_ledger = mock_memory / "llm_health_ledger.jsonl"
    with open(health_ledger, "w") as f:
        for _ in range(15):
            f.write(json.dumps({"status": "llm_timeout", "timestamp": time.time()}) + "\n")
            
    distiller = DeepseekExperienceDistiller(memory_dir=str(mock_memory))
    patterns = distiller.distill_from_llm_failures()
    
    assert len(patterns) == 1
    assert patterns[0].pattern_name == "avoid_llm_for_known_intents"
    assert patterns[0].target_module == "LocalIntentRouter"

def test_distill_from_semantic_principles(mock_memory):
    principle_ledger = mock_memory / "semantic_principle_ledger.jsonl"
    with open(principle_ledger, "w") as f:
        f.write(json.dumps({
            "event_id": "sem_1", "principle_name": "cuarentena_como_aprendizaje", 
            "timestamp": time.time(), "schema_version": "semantic-principle.v1"
        }) + "\n")
        
    distiller = DeepseekExperienceDistiller(memory_dir=str(mock_memory))
    patterns = distiller.distill_from_semantic_principles()
    
    assert len(patterns) == 1
    assert patterns[0].pattern_name == "quarantine_as_training_sample"

def test_persist_and_load_patterns(mock_memory):
    distiller = DeepseekExperienceDistiller(memory_dir=str(mock_memory))
    pattern = DistilledReasoningPattern(
        pattern_id="p1", pattern_name="test", source_refs=[], trigger_signature="sig",
        local_rule_summary="rule", recommended_action="act", confidence=1.0,
        usefulness_score=1.0, risk_score=0.0, target_module="m"
    )
    
    distiller.persist_distilled_pattern(pattern)
    loaded = distiller.load_distilled_patterns()
    
    assert len(loaded) == 1
    assert loaded[0].pattern_name == "test"
    assert loaded[0].pattern_id == "p1"
