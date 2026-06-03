import pytest
from core.immune_quarantine_policy import ImmuneQuarantinePolicy

def test_calculate_iss_balanced():
    policy = ImmuneQuarantinePolicy()
    # R=0.1, U=0.1, D=0, H=0.1, C=0.1 -> 0.4
    # V=0.5, T=0.8, A=0.9 -> 2.2
    # ISS = 0.4 - 2.2 = -1.8
    iss = policy.calculate_iss(0.1, 0.1, 0.0, 0.1, 0.1, 0.5, 0.8, 0.9)
    assert iss == -1.8

def test_classify_quarantine_level():
    policy = ImmuneQuarantinePolicy()
    assert policy.classify_quarantine_level(-1.0) == 0
    assert policy.classify_quarantine_level(0.6) == 1
    assert policy.classify_quarantine_level(1.6) == 2
    assert policy.classify_quarantine_level(3.5) == 3

def test_assess_unsafe_item():
    policy = ImmuneQuarantinePolicy()
    # Unsafe should trigger level 3 or high ISS
    metadata = {
        "risk": 0.9,
        "contains_dangerous_calls": True,
        "isolation": 0.1 # Hard to isolate
    }
    assessment = policy.assess_item("candidate_unsafe.py", "candidate", metadata)
    assert assessment.recommended_quarantine_level == 3
    assert assessment.recommended_action == "preserve_as_immune_training_sample"
    assert "peligrosas" in assessment.reason_summary

def test_assess_experimental_skill():
    policy = ImmuneQuarantinePolicy()
    metadata = {
        "risk": 0.3,
        "in_runtime": False
    }
    assessment = policy.assess_item("pdf_reader_basic.py", "experimental_skill", metadata)
    # With refined weights, 'pdf' in name triggers Level 2
    assert assessment.recommended_quarantine_level == 2

def test_assess_legacy_corrupt():
    policy = ImmuneQuarantinePolicy()
    metadata = {
        "is_legacy": True,
        "is_corrupt": True
    }
    assessment = policy.assess_item("legacy.py", "legacy_code", metadata)
    assert assessment.recommended_quarantine_level >= 2
