import pytest
import time
import json
from pathlib import Path
from unittest.mock import MagicMock
from cognition.morning_brief import MorningBrief, TAXONOMY_TIMESTAMP
from core.ingestion_failure_ledger import IngestionFailureEvent

def test_morning_brief_unknown_reconciliation_display(tmp_path):
    # Historical unknown
    f1 = IngestionFailureEvent(
        event_id="f1", timestamp=TAXONOMY_TIMESTAMP - 1000, source="test", task_id="t1",
        source_type="text", payload_mime_type="text/plain", payload_size_bytes=10,
        payload_sha256="abc", declared_intent="chat", detected_intent="chat",
        proposed_action="respond", failure_type="unknown_failure",
        failure_stage="process_envelope", error_type="TypeError",
        error_summary="coroutine is not iterable", supported_actions=[], missing_capability_signature="sig",
        suggested_skill_category="cat"
    )
    
    # Post-taxonomy unknown
    f2 = IngestionFailureEvent(
        event_id="f2", timestamp=TAXONOMY_TIMESTAMP + 1000, source="test", task_id="t2",
        source_type="text", payload_mime_type="text/plain", payload_size_bytes=10,
        payload_sha256="abc", declared_intent="chat", detected_intent="chat",
        proposed_action="respond", failure_type="unknown_failure",
        failure_stage="process_envelope", error_type="RuntimeError",
        error_summary="contract missing field", supported_actions=[], missing_capability_signature="sig",
        suggested_skill_category="cat"
    )
    
    brief_gen = MorningBrief(memory_dir=str(tmp_path))
    brief_gen.failure_ledger = MagicMock()
    brief_gen.failure_ledger.load_recent.return_value = [f1, f2]
    
    brief = brief_gen.generate_brief()
    
    assert "[Reconciliación de Deuda Unknown]:" in brief
    assert "Deuda Histórica: 1" in brief
    assert "Unknown Post-Taxonomía: 1 [ALERTA]" in brief
    assert "process_envelope_unhandled_exception: 1" in brief
    assert "process_envelope_contract_error: 1" in brief
