import pytest
from core.failure_classifier import FailureClassifier

def test_classify_process_envelope_missing_field():
    exc = ValueError("missing field: payload")
    res = FailureClassifier.classify_exception(exc, {"stage": "process_envelope"})
    assert res.failure_type == "process_envelope_contract_error"
    assert res.error_family == "contract"

def test_classify_process_envelope_missing_task_id():
    exc = ValueError("task_id is missing")
    res = FailureClassifier.classify_exception(exc, {"stage": "process_envelope"})
    assert res.failure_type == "process_envelope_missing_task_id"

def test_classify_process_envelope_planner_error():
    exc = RuntimeError("planner contract failure")
    res = FailureClassifier.classify_exception(exc, {"stage": "process_envelope"})
    assert res.failure_type == "process_envelope_planner_result_invalid"

def test_classify_process_envelope_policy_block():
    exc = PermissionError("action blocked by policy")
    res = FailureClassifier.classify_exception(exc, {"stage": "process_envelope"})
    assert res.failure_type == "process_envelope_policy_block"

def test_classify_process_envelope_unhandled():
    exc = Exception("something unexpected happened")
    res = FailureClassifier.classify_exception(exc, {"stage": "process_envelope"})
    # In my logic, if it doesn't match keywords, it falls to 'unknown_failure_process_envelope'
    # unless it has unhandled/unexpected in err_str
    assert res.failure_type == "process_envelope_unhandled_exception"
