import pytest
from core.fast_path_reflex_gate import FastPathReflexGate

@pytest.fixture
def gate(tmp_path):
    return FastPathReflexGate(memory_dir=str(tmp_path))

def test_certified_reflex_allowed(gate):
    assessment = gate.assess_reflex(
        pattern_id="p1", reflex_name="basic_greeting_reflex", input_signature="hola",
        active_local=True, risk_score=0.0, human_approved=True, rollback_available=True
    )
    assert assessment.fast_path_allowed is True
    assert assessment.block_reason is None

def test_certified_help_allowed(gate):
    assessment = gate.assess_reflex(
        pattern_id="p2", reflex_name="help_command_reflex", input_signature="ayuda",
        active_local=True, risk_score=0.0, human_approved=True, rollback_available=True
    )
    assert assessment.fast_path_allowed is True

def test_certified_status_allowed(gate):
    assessment = gate.assess_reflex(
        pattern_id="p3", reflex_name="system_status_reflex", input_signature="estado",
        active_local=True, risk_score=0.0, human_approved=True, rollback_available=True
    )
    assert assessment.fast_path_allowed is True

def test_certified_identity_allowed(gate):
    assessment = gate.assess_reflex(
        pattern_id="p4", reflex_name="identity_query_reflex", input_signature="quien eres",
        active_local=True, risk_score=0.0, human_approved=True, rollback_available=True
    )
    assert assessment.fast_path_allowed is True

def test_uncertified_reflex_blocked(gate):
    assessment = gate.assess_reflex(
        pattern_id="p5", reflex_name="some_other_reflex", input_signature="test",
        active_local=True, risk_score=0.0, human_approved=True, rollback_available=True
    )
    assert assessment.fast_path_allowed is False
    assert assessment.block_reason == "not_certified_for_fast_path"

def test_not_active_blocked(gate):
    assessment = gate.assess_reflex(
        pattern_id="p1", reflex_name="basic_greeting_reflex", input_signature="hola",
        active_local=False, risk_score=0.0, human_approved=True, rollback_available=True
    )
    assert assessment.fast_path_allowed is False
    assert assessment.block_reason == "not_active_local"

def test_risk_above_zero_blocked(gate):
    assessment = gate.assess_reflex(
        pattern_id="p1", reflex_name="basic_greeting_reflex", input_signature="hola",
        active_local=True, risk_score=0.1, human_approved=True, rollback_available=True
    )
    assert assessment.fast_path_allowed is False
    assert assessment.block_reason == "risk_score_above_zero"

def test_no_human_approval_blocked(gate):
    assessment = gate.assess_reflex(
        pattern_id="p1", reflex_name="basic_greeting_reflex", input_signature="hola",
        active_local=True, risk_score=0.0, human_approved=False, rollback_available=True
    )
    assert assessment.fast_path_allowed is False
    assert assessment.block_reason == "not_human_approved"

def test_no_rollback_blocked(gate):
    assessment = gate.assess_reflex(
        pattern_id="p1", reflex_name="basic_greeting_reflex", input_signature="hola",
        active_local=True, risk_score=0.0, human_approved=True, rollback_available=False
    )
    assert assessment.fast_path_allowed is False
    assert assessment.block_reason == "no_rollback_available"

def test_fast_path_persistence(gate):
    assessment = gate.assess_reflex(
        pattern_id="p1", reflex_name="basic_greeting_reflex", input_signature="hola",
        active_local=True, risk_score=0.0, human_approved=True, rollback_available=True
    )
    metrics = gate.summarize_metrics()
    assert metrics["fast_path_hits"] == 1
    assert "basic_greeting_reflex" in metrics["reflex_usage"]
