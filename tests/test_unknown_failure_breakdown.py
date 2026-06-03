import time
from unittest.mock import MagicMock
from cognition.morning_brief import MorningBrief
from core.ingestion_failure_ledger import IngestionFailureEvent

def test_morning_brief_unknown_failure_breakdown(tmp_path):
    failure_path = tmp_path / "failures.jsonl"
    
    # Create unknown failures in different stages
    f1 = IngestionFailureEvent(
        event_id="f1", timestamp=time.time(), source="test", task_id="t1",
        source_type="text", payload_mime_type="text/plain", payload_size_bytes=10,
        payload_sha256="abc", declared_intent="chat", detected_intent="chat",
        proposed_action="respond", failure_type="unknown_failure",
        failure_stage="stage_alpha", error_type="RuntimeError",
        error_summary="err1", supported_actions=[], missing_capability_signature="sig",
        suggested_skill_category="cat"
    )
    f2 = IngestionFailureEvent(
        event_id="f2", timestamp=time.time(), source="test", task_id="t2",
        source_type="text", payload_mime_type="text/plain", payload_size_bytes=10,
        payload_sha256="abc", declared_intent="chat", detected_intent="chat",
        proposed_action="respond", failure_type="unknown_failure",
        failure_stage="stage_alpha", error_type="RuntimeError",
        error_summary="err2", supported_actions=[], missing_capability_signature="sig",
        suggested_skill_category="cat"
    )
    
    with open(failure_path, "a") as f:
        f.write(f1.to_json() + "\n")
        f.write(f2.to_json() + "\n")
        
    brief_gen = MorningBrief(
        journal_path=str(tmp_path / "journal.jsonl"),
        option_queue_path=str(tmp_path / "queue.jsonl"),
        failure_ledger=MagicMock(), # We'll mock load_recent
        memory_dir=str(tmp_path)
    )
    brief_gen.failure_ledger.load_recent.return_value = [f1, f2]
    brief_gen.failure_ledger.ledger_path = failure_path
    
    brief = brief_gen.generate_brief()
    
    assert "unknown_failure: 2" in brief
    assert "Principal etapa: stage_alpha" in brief
