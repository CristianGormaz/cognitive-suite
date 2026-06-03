import time
from unittest.mock import MagicMock
from cognition.morning_brief import MorningBrief
from core.ingestion_failure_ledger import IngestionFailureEvent

def test_unknown_failure_process_envelope_suggestion(tmp_path):
    f1 = IngestionFailureEvent(
        event_id="f1", timestamp=time.time(), source="test", task_id="t1",
        source_type="text", payload_mime_type="text/plain", payload_size_bytes=10,
        payload_sha256="abc", declared_intent="chat", detected_intent="chat",
        proposed_action="respond", failure_type="unknown_failure",
        failure_stage="process_envelope", error_type="RuntimeError",
        error_summary="err1", supported_actions=[], missing_capability_signature="sig",
        suggested_skill_category="cat"
    )
    
    brief_gen = MorningBrief(memory_dir=str(tmp_path))
    brief_gen.failure_ledger = MagicMock()
    brief_gen.failure_ledger.load_recent.return_value = [f1]
    
    brief = brief_gen.generate_brief()
    
    assert "unknown_failure: 1" in brief
    assert "Principal etapa: process_envelope" in brief
    assert "[Sugerencia: Sprint Process Envelope Triage]" in brief
