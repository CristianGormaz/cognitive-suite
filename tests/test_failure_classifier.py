import pytest
from core.failure_classifier import FailureClassifier

def test_classify_llm_timeout():
    class DummyTimeout(Exception): pass
    exc = DummyTimeout("Ollama no respondió en 30s")
    cls = FailureClassifier.classify_exception(exc)
    assert cls.failure_type == "llm_timeout"
    assert cls.error_family == "llm"
    assert cls.severity == "high"

def test_classify_dispatcher_unsupported():
    class DummyError(Exception): pass
    exc = DummyError("Action not supported by dispatcher")
    cls = FailureClassifier.classify_exception(exc)
    assert cls.failure_type == "dispatcher_unsupported_action"
    assert cls.error_family == "dispatcher"

def test_classify_ledger_error():
    class DummyError(Exception): pass
    exc = DummyError("Failed to write to ledger file")
    cls = FailureClassifier.classify_exception(exc)
    assert cls.failure_type == "ledger_write_error"
    assert cls.error_family == "memory"
    
def test_classify_planner_contract():
    class LLMPlanValidationError(ValueError): pass
    exc = LLMPlanValidationError("Keys missing in response")
    cls = FailureClassifier.classify_exception(exc)
    assert cls.failure_type == "planner_contract_error"
    assert cls.error_family == "planner"

def test_classify_unexpected_exception():
    class RandomError(Exception): pass
    exc = RandomError("Something completely unexpected happened")
    cls = FailureClassifier.classify_exception(exc, {"stage": "dispatch_complete"})
    assert cls.failure_type == "unknown_failure"
    assert cls.error_family == "unknown"
    assert cls.failure_stage == "dispatch_complete"
