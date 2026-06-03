import pytest
import os
from unittest.mock import MagicMock, AsyncMock
from core.experimental_risk_profile import ExperimentalRiskProfile

def test_pdf_reader_risk_profile():
    # El PDF reader debe ser Medium Risk
    profile = ExperimentalRiskProfile.for_skill(
        skill_name="pdf_reader_basic",
        is_allowlisted=True,
        human_review_status="approved_for_future_promotion",
        sandbox_safe=True
    )
    
    assert profile.risk_level == "medium"
    
def test_pdf_reader_blocked_if_not_allowlisted():
    profile = ExperimentalRiskProfile.for_skill(
        skill_name="pdf_reader_basic",
        is_allowlisted=False,
        human_review_status="pending_human_review",
        sandbox_safe=True
    )
    
    assert profile.risk_level == "critical" # No está en allowlist y es experimental
