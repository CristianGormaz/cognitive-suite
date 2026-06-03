import json
import os
import time
from pathlib import Path
from core.unknown_failure_reconciler import UnknownFailureReconciler, TAXONOMY_TIMESTAMP

def test_reconciliation_ledger_idempotency(tmp_path):
    reco_path = tmp_path / "reco_ledger.jsonl"
    reconciler = UnknownFailureReconciler(taxonomy_timestamp=TAXONOMY_TIMESTAMP, reconciliation_path=str(reco_path))
    
    event = {
        "event_id": "fail_orig_1",
        "timestamp": TAXONOMY_TIMESTAMP - 100,
        "failure_type": "unknown_failure",
        "failure_stage": "process_envelope",
        "error_summary": "missing field: payload"
    }
    
    # First call
    reconciler.reconcile_event(event)
    
    # Second call
    reconciler.reconcile_event(event)
    
    # Read the ledger file
    with open(reco_path, "r") as f:
        lines = f.readlines()
    
    # It should have 2 lines because reconcile_event appends.
    # MorningBrief handles idempotency at its level.
    # But let's check load_all_reclassifications handles it too (prefers latest).
    assert len(lines) == 2
    
    reclassifications = reconciler.load_all_reclassifications()
    assert len(reclassifications) == 1
    assert "fail_orig_1" in reclassifications

def test_reconciliation_ledger_file_creation(tmp_path):
    reco_path = tmp_path / "new_dir" / "reco_ledger.jsonl"
    reconciler = UnknownFailureReconciler(taxonomy_timestamp=TAXONOMY_TIMESTAMP, reconciliation_path=str(reco_path))
    
    assert reco_path.parent.exists()
    
    event = {
        "event_id": "fail_orig_2",
        "timestamp": TAXONOMY_TIMESTAMP + 100,
        "failure_type": "unknown_failure",
        "failure_stage": "process_envelope",
        "error_summary": "coroutine is not iterable"
    }
    reconciler.reconcile_event(event)
    assert reco_path.exists()
