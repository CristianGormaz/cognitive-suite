import pytest
import json
import time
from pathlib import Path
from cognition.morning_brief import MorningBrief

@pytest.fixture
def mock_assets_with_trends(tmp_path):
    journal = tmp_path / "journal.jsonl"
    queue = tmp_path / "queue.jsonl"
    curated = tmp_path / "curated.jsonl"
    fail = tmp_path / "ingestion_failure_ledger.jsonl"
    tension = tmp_path / "semantic_tension_ledger.jsonl"
    report_ledger = tmp_path / "immune_heatmap_reports.jsonl"
    
    now = time.time()
    # 2 days ago (Historical)
    old_ts = now - (2 * 24 * 3600)
    # 10 minutes ago (Active)
    new_ts = now - 600
    
    # Write some failures to trigger trends
    with open(fail, "w") as f:
        # Many old timeouts
        for i in range(20):
            f.write(json.dumps({"failure_type": "llm_timeout", "timestamp": old_ts, "event_id": f"o{i}"}) + "\n")
        # One recent error
        f.write(json.dumps({"failure_type": "new_threat", "timestamp": new_ts, "event_id": "r1"}) + "\n")
        
    journal.write_text("")
    queue.write_text("")
    curated.write_text("")
    tension.write_text("")
    
    return journal, queue, curated, fail, tension, report_ledger, tmp_path

def test_morning_brief_shows_heatmap_trends(mock_assets_with_trends):
    journal, queue, curated, fail, tension, report_ledger, memory_dir = mock_assets_with_trends
    
    brief_gen = MorningBrief(
        journal_path=str(journal),
        option_queue_path=str(queue),
        curated_ledger_path=str(curated),
        memory_dir=str(memory_dir)
    )
    brief_gen.heatmap_engine.report_ledger_path = report_ledger
    
    brief = brief_gen.generate_brief()
    
    assert "Mapa de Calor Inmunológico" in brief
    assert "Histórico: llm_timeout" in brief
    assert "Reciente: new_threat" in brief
    assert "[!] Tendencia new_threat: rising" in brief
    assert "Foco: Priorizar mitigación de new_threat (falla ACTIVA)" in brief
