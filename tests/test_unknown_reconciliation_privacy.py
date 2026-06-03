import json
import time
from core.unknown_failure_reconciler import UnknownFailureReconciler, TAXONOMY_TIMESTAMP

def test_reconciliation_privacy_no_sensitive_data(tmp_path):
    reco_path = tmp_path / "reco_ledger.jsonl"
    reconciler = UnknownFailureReconciler(taxonomy_timestamp=TAXONOMY_TIMESTAMP, reconciliation_path=str(reco_path))
    
    sensitive_summary = "error in processing payload: 'user confidential data'"
    event = {
        "event_id": "fail_priv_1",
        "timestamp": TAXONOMY_TIMESTAMP - 100,
        "failure_type": "unknown_failure",
        "failure_stage": "process_envelope",
        "error_type": "ValueError",
        "error_summary": sensitive_summary
    }
    
    reco = reconciler.reconcile_event(event)
    
    # Check the result object
    reco_dict = reco.to_json()
    assert "user confidential data" not in reco_dict
    assert "sensitive_summary" not in reco_dict
    
    # Check the file content
    with open(reco_path, "r") as f:
        line = f.read()
        assert "user confidential data" not in line
        # It should only contain metadata
        data = json.loads(line)
        expected_keys = {
            "event_id", "timestamp", "original_event_ref", "original_failure_type",
            "original_stage", "inferred_failure_type", "confidence", "historical_debt",
            "post_taxonomy_event", "safe_reason", "evidence_fields_used", "schema_version"
        }
        assert set(data.keys()) == expected_keys
