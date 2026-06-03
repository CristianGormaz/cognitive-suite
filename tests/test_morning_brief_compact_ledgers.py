import pytest
import json
import time
from pathlib import Path
from cognition.morning_brief import MorningBrief

@pytest.fixture
def mock_assets_with_compact(tmp_path):
    journal_path = tmp_path / "journal.jsonl"
    queue_path = tmp_path / "queue.jsonl"
    curated_path = tmp_path / "curated.jsonl"
    failure_path = tmp_path / "fail.jsonl"
    tension_path = tmp_path / "tension.jsonl"
    compact_dir = tmp_path / "compact"
    compact_dir.mkdir()
    
    # Historical failure summary
    summary_path = compact_dir / "fail_summary.jsonl"
    summary = {
        "ledger_name": "fail.jsonl",
        "generated_at": time.time(),
        "archived_event_count": 1000,
        "failure_type_counts": {"old_failure": 500, "llm_timeout": 500},
        "schema_version": "ledger-compact-summary.v1"
    }
    summary_path.write_text(json.dumps(summary) + "\n")
    
    queue_path.write_text("")
    curated_path.write_text("")
    journal_path.write_text("")
    failure_path.write_text("")
    tension_path.write_text("")
    
    return journal_path, queue_path, curated_path, failure_path, tension_path, tmp_path

def test_morning_brief_reads_compact_summaries(mock_assets_with_compact):
    journal, queue, curated, fail, tension, memory_dir = mock_assets_with_compact
    
    brief_gen = MorningBrief(
        journal_path=str(journal),
        option_queue_path=str(queue),
        curated_ledger_path=str(curated),
        memory_dir=str(memory_dir),
        # Pass dummy ledgers to avoid real file interaction
        failure_ledger=None,
        tension_ledger=None
    )
    
    # We need to ensure failure_ledger uses the tmp failure_path
    from core.ingestion_failure_ledger import IngestionFailureLedger
    brief_gen.failure_ledger = IngestionFailureLedger(ledger_path=str(fail))
    
    brief = brief_gen.generate_brief()
    
    assert "Historia Archivada (1000 eventos previos)" in brief
    assert "old_failure: 500 (histórico)" in brief
    assert "llm_timeout: 500 (histórico)" in brief
