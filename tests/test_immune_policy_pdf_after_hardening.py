import pytest
from core.immune_quarantine_policy import ImmuneQuarantinePolicy

def test_immune_policy_reclasifies_after_hardening():
    policy = ImmuneQuarantinePolicy()
    
    # Before hardening (Level 3)
    metadata_before = {
        "risk": 0.3,
        "value": 0.9,
        "in_runtime": False,
        "metadata_leak_risk": True,
        "handles_user_file": True
    }
    assessment_before = policy.assess_item("pdf_reader.py", "experimental_skill", metadata_before)
    assert assessment_before.recommended_quarantine_level == 3
    assert assessment_before.recommended_action == "needs_privacy_review"
    
    # After hardening (Should be Level 2 or 1)
    metadata_after = {
        "risk": 0.3,
        "value": 0.9,
        "in_runtime": False,
        "metadata_leak_risk": True,
        "metadata_redacted": True, # Hardened
        "handles_user_file": True
    }
    assessment_after = policy.assess_item("pdf_reader.py", "experimental_skill", metadata_after)
    assert assessment_after.recommended_quarantine_level < 3
    assert assessment_after.recommended_action != "needs_privacy_review"
