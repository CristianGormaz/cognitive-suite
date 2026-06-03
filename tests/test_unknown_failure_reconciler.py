import pytest
import time
from core.unknown_failure_reconciler import UnknownFailureReconciler, TAXONOMY_TIMESTAMP

def test_reconcile_historical_unknown():
    reconciler = UnknownFailureReconciler(taxonomy_timestamp=time.time() + 1000)
    event = {
        "event_id": "fail_123",
        "timestamp": time.time(),
        "failure_type": "unknown_failure",
        "failure_stage": "process_envelope",
        "error_summary": "missing field: payload"
    }
    reco = reconciler.reconcile_event(event)
    assert reco is not None
    assert reco.historical_debt is True
    assert reco.inferred_failure_type == "process_envelope_contract_error"

def test_reconcile_post_taxonomy_unknown():
    reconciler = UnknownFailureReconciler(taxonomy_timestamp=time.time() - 1000)
    event = {
        "event_id": "fail_456",
        "timestamp": time.time(),
        "failure_type": "unknown_failure",
        "failure_stage": "process_envelope",
        "error_summary": "coroutine is not iterable"
    }
    reco = reconciler.reconcile_event(event)
    assert reco is not None
    assert reco.historical_debt is False
    assert reco.post_taxonomy_event is True
    assert reco.inferred_failure_type == "process_envelope_unhandled_exception"

def test_reconcile_unclassified_legacy():
    reconciler = UnknownFailureReconciler(taxonomy_timestamp=time.time() + 1000)
    event = {
        "event_id": "fail_789",
        "timestamp": time.time(),
        "failure_type": "unknown_failure",
        "failure_stage": "unknown_stage",
        "error_summary": "some weird error"
    }
    reco = reconciler.reconcile_event(event)
    assert reco is not None
    assert reco.inferred_failure_type == "legacy_unknown_unclassified"
