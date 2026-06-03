import pytest
import json
import time
from pathlib import Path
from cognition.morning_brief import MorningBrief

@pytest.fixture
def mock_assets_with_heatmap(tmp_path):
    journal = tmp_path / "journal.jsonl"
    queue = tmp_path / "queue.jsonl"
    curated = tmp_path / "curated.jsonl"
    
    # Correct filenames for the engine
    fail = tmp_path / "ingestion_failure_ledger.jsonl"
    tension = tmp_path / "semantic_tension_ledger.jsonl"
    report_ledger = tmp_path / "immune_heatmap_reports.jsonl"
    
    # Pre-populate some evidence with recent timestamps
    with open(fail, "w") as f:
        f.write(json.dumps({"failure_type": "llm_timeout", "event_id": "f1", "timestamp": time.time()}) + "\n")
        f.write(json.dumps({"failure_type": "llm_timeout", "event_id": "f2", "timestamp": time.time()}) + "\n")
        
    journal.write_text("")
    queue.write_text("")
    curated.write_text("")
    tension.write_text("")
    
    return journal, queue, curated, fail, tension, report_ledger, tmp_path

def test_morning_brief_shows_heatmap(mock_assets_with_heatmap):
    journal, queue, curated, fail, tension, report_ledger, memory_dir = mock_assets_with_heatmap
    
    brief_gen = MorningBrief(
        journal_path=str(journal),
        option_queue_path=str(queue),
        curated_ledger_path=str(curated),
        memory_dir=str(memory_dir)
    )
    
    # We need to make sure MorningBrief uses our report_ledger_path
    brief_gen.heatmap_engine.report_ledger_path = report_ledger
    
    brief = brief_gen.generate_brief()
    
    assert "Mapa de Calor Inmunológico" in brief
    assert "Mapa de Calor: Familias de Fallo" in brief
    assert "Histórico: llm_timeout" in brief
    assert "Reciente: llm_timeout" in brief
