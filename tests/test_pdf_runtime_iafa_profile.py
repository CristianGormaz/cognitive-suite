import pytest
import os
from unittest.mock import MagicMock
from core.experimental_risk_profile import ExperimentalRiskProfile

def test_pdf_reader_iafa_profile_full():
    # pdf_reader should be Medium risk if allowlisted and approved
    profile = ExperimentalRiskProfile.for_skill(
        "pdf_reader_basic", 
        is_allowlisted=True, 
        human_review_status="approved_for_future_promotion",
        sandbox_safe=True
    )
    
    assert profile.risk_level == "medium"
    assert profile.handles_user_file is True
    assert profile.iafa_risk_adjustment["R"] == 0.3

def test_pdf_reader_blocked_if_not_allowlisted():
    profile = ExperimentalRiskProfile.for_skill(
        "pdf_reader_basic", 
        is_allowlisted=False
    )
    assert profile.risk_level == "critical"

def test_pdf_reader_risk_if_not_approved():
    profile = ExperimentalRiskProfile.for_skill(
        "pdf_reader_basic", 
        is_allowlisted=True,
        human_review_status="pending_review",
        sandbox_safe=True
    )
    # If not fully approved but sandbox safe and allowlisted, it should be at least medium
    assert profile.risk_level == "medium"
