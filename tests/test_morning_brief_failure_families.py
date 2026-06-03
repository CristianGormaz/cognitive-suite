import pytest
import json
from pathlib import Path
from cognition.morning_brief import MorningBrief

@pytest.fixture
def mock_assets(tmp_path):
    journal_path = tmp_path / "dream_journal.jsonl"
    queue_path = tmp_path / "evolution_option_queue.jsonl"
    curated_path = tmp_path / "evolution_option_curated.jsonl"
    failure_path = tmp_path / "ingestion_failure_ledger.jsonl"
    
    def make_fail(ftype):
        return {
            "event_id": "test", "timestamp": 123.0, "source": "test", "task_id": "t1",
            "source_type": "text", "payload_mime_type": "text/plain", "payload_size_bytes": 1,
            "payload_sha256": "hash", "declared_intent": None, "detected_intent": None,
            "proposed_action": None, "failure_type": ftype, "failure_stage": "test",
            "error_type": "Error", "error_summary": "Error", "supported_actions": [],
            "missing_capability_signature": "unknown:unknown", "suggested_skill_category": "unknown",
            "host_under_stress": False, "iafa_score": 0.0, "schema_version": "ingestion-failure.v1"
        }

    failures = [
        make_fail("planner_contract_error"),
        make_fail("planner_contract_error"),
        make_fail("ledger_read_error"),
        make_fail("unexpected_exception"),
    ]
    with open(failure_path, "w") as f:
        for fail in failures:
            f.write(json.dumps(fail) + "\n")
            
    # Need at least an empty array for others
    queue_path.write_text("")
    curated_path.write_text("")
    journal_path.write_text("")
    
    return journal_path, queue_path, curated_path, failure_path

def test_morning_brief_shows_failure_families(mock_assets):
    journal_path, queue_path, curated_path, failure_path = mock_assets
    
    from core.ingestion_failure_ledger import IngestionFailureLedger
    failure_ledger = IngestionFailureLedger(ledger_path=str(failure_path))
    
    brief_gen = MorningBrief(
        journal_path=str(journal_path),
        option_queue_path=str(queue_path),
        curated_ledger_path=str(curated_path),
        failure_ledger=failure_ledger
    )
    
    brief = brief_gen.generate_brief()
    
    assert "Últimos" in brief and "eventos registrados" in brief
    assert "planner_contract_error: 2" in brief
    assert "ledger_read_error: 1" in brief
    assert "unexpected_exception: 1" in brief
