import pytest
import json
import time
from pathlib import Path
from cognition.morning_brief import MorningBrief

@pytest.fixture
def mock_assets_with_semantics(tmp_path):
    journal = tmp_path / "journal.jsonl"
    queue = tmp_path / "queue.jsonl"
    curated = tmp_path / "curated.jsonl"
    fail = tmp_path / "fail.jsonl"
    tension = tmp_path / "tension.jsonl"
    semantic = tmp_path / "semantic_principle_ledger.jsonl"
    
    # Write one semantic principle
    with open(semantic, "w") as f:
        f.write(json.dumps({
            "event_id": "sem_1",
            "timestamp": time.time(),
            "principle_name": "test_principle",
            "context_dimension": "testing",
            "interpretation_summary": "Summary",
            "source_evidence_refs": [],
            "related_modules": [],
            "confidence": 0.95,
            "novelty_score": 1.0,
            "usefulness_score": 1.0,
            "risk_of_overinterpretation": 0.0,
            "suggested_application": "Apply it",
            "requires_human_review": True,
            "schema_version": "semantic-principle.v1"
        }) + "\n")
        
    journal.write_text("")
    queue.write_text("")
    curated.write_text("")
    fail.write_text("")
    tension.write_text("")
    
    return journal, queue, curated, fail, tension, semantic, tmp_path

def test_morning_brief_shows_semantic_evolution(mock_assets_with_semantics):
    journal, queue, curated, fail, tension, semantic, memory_dir = mock_assets_with_semantics
    
    # IngestionFailureLedger uses default path unless we pass it. 
    # MorningBrief.generate_brief loads it.
    
    brief_gen = MorningBrief(
        journal_path=str(journal),
        option_queue_path=str(queue),
        curated_ledger_path=str(curated),
        memory_dir=str(memory_dir)
    )
    
    brief = brief_gen.generate_brief()
    
    assert "Evolución del Entendimiento Semántico" in brief
    assert "Principio: test_principle" in brief
    assert "Dimensión: testing" in brief
    assert "Confianza: 0.95" in brief
