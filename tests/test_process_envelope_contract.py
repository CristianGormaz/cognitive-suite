import pytest
from core.process_envelope_contract import ProcessEnvelopeContract
from core.task_envelope import TaskEnvelope

def test_validate_envelope_valid():
    contract = ProcessEnvelopeContract()
    envelope = TaskEnvelope.from_text("hello")
    res = contract.validate_envelope(envelope)
    assert res.valid is True
    assert res.task_id_present is True

def test_validate_envelope_invalid_type():
    contract = ProcessEnvelopeContract()
    res = contract.validate_envelope("not an envelope")
    assert res.valid is False
    assert "envelope_type" in res.invalid_fields

def test_validate_plan_result_valid():
    class FakePlan:
        def __init__(self):
            self.task_id = "task1"
            self.decision = FakeDecision()
    class FakeDecision:
        def __init__(self):
            self.intent_category = "chat"
            self.proposed_action = "respond"

    contract = ProcessEnvelopeContract()
    res = contract.validate_plan_result(FakePlan())
    assert res.valid is True

def test_validate_plan_result_missing_fields():
    class FakePlan:
        def __init__(self):
            self.task_id = "task1"
            self.decision = None
    
    contract = ProcessEnvelopeContract()
    res = contract.validate_plan_result(FakePlan())
    assert res.valid is False
    assert "decision" in res.missing_fields

def test_validate_dispatch_result_valid():
    class FakeResult:
        def __init__(self):
            self.task_id = "task1"
            self.status = "executed"
            self.action = "respond"
    
    contract = ProcessEnvelopeContract()
    res = contract.validate_dispatch_result(FakeResult())
    assert res.valid is True
