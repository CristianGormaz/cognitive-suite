import pytest
from core.failure_classifier import FailureClassifier

def test_process_envelope_classification():
    # Planner Contract error
    exc = RuntimeError("Validation contract failed")
    res = FailureClassifier.classify_exception(exc, {"stage": "process_envelope"})
    assert res.failure_type == "process_envelope_planner_result_invalid"
    
    # Route missing
    exc = ValueError("No route for intent")
    res = FailureClassifier.classify_exception(exc, {"stage": "process_envelope"})
    assert res.failure_type == "process_envelope_local_router_error"
    
    # Unhandled
    exc = Exception("Unhandled unexpected error")
    res = FailureClassifier.classify_exception(exc, {"stage": "process_envelope"})
    assert res.failure_type == "process_envelope_unhandled_exception"
    
    # Fallback in process_envelope
    exc = Exception("Something else")
    res = FailureClassifier.classify_exception(exc, {"stage": "process_envelope"})
    assert res.failure_type == "unknown_failure_process_envelope"
