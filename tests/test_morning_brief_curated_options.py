import pytest
import json
from pathlib import Path
from cognition.morning_brief import MorningBrief

@pytest.fixture
def mock_assets(tmp_path):
    journal_path = tmp_path / "dream_journal.jsonl"
    queue_path = tmp_path / "evolution_option_queue.jsonl"
    curated_path = tmp_path / "evolution_option_curated.jsonl"
    
    # Write one redundant set of options
    with open(queue_path, "w") as f:
        f.write(json.dumps({
            "option_id": "opt_1", "timestamp": 123.0, "title": "Timeout 1", "summary": "s1", "priority_score": 1.0, "status": "pending_human_review", "evidence_refs": [], "related_ledgers": [], "schema_version": "evolution-option.v1"
        }) + "\n")
        f.write(json.dumps({
            "option_id": "opt_2", "timestamp": 124.0, "title": "Timeout 2", "summary": "s2", "priority_score": 1.5, "status": "pending_human_review", "evidence_refs": [], "related_ledgers": [], "schema_version": "evolution-option.v1"
        }) + "\n")
    
    return journal_path, queue_path, curated_path

def test_morning_brief_shows_curated_options(mock_assets):
    journal_path, queue_path, curated_path = mock_assets
    brief_gen = MorningBrief(
        journal_path=str(journal_path),
        option_queue_path=str(queue_path),
        curated_ledger_path=str(curated_path)
    )
    
    brief = brief_gen.generate_brief()
    
    assert "Bandeja de Evolución Curada" in brief
    assert "Consolidación: Estabilizar y Optimizar Timeouts LLM" in brief
    assert "(2 señales fusionadas)" in brief
    assert "ID Curado: cur_" in brief
    assert curated_path.exists()
