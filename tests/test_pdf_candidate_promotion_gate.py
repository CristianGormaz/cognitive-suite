import pytest
import os
from pathlib import Path
from unittest.mock import MagicMock
from cognition.skill_promotion_gate import SkillPromotionGate, SkillCandidateSummary
from core.dependency_review_ledger import DependencyReviewLedger, DependencyReviewEvent

def test_pdf_candidate_promotion_gate_success(tmp_path):
    # Setup dependency ledger as approved
    dep_path = tmp_path / "dep.jsonl"
    dep_ledger = DependencyReviewLedger(ledger_path=str(dep_path))
    dep_ledger.append_review(DependencyReviewEvent(
        event_id="e1", timestamp=1.0, dependency_name="pypdf", purpose="x", candidate_id="pdf_reader",
        risk_level="medium", required_by="pdf", installed_status="installed", approved_status="approved",
        review_status="approved_for_installation", notes_summary="y", install_allowed=True
    ))
    
    # Mock reviewer with approved status
    mock_reviewer = MagicMock()
    mock_reviewer.list_candidates.return_value = [
        SkillCandidateSummary(
            "candidate_pdf_reader_basic.py", "pdf", "hash", 100, 1.0, ["os"], "approved_for_future_promotion"
        )
    ]
    
    gate = SkillPromotionGate(reviewer=mock_reviewer, dependency_ledger=dep_ledger, ledger_path=str(tmp_path / "prom.jsonl"))
    
    assessment = gate.assess_candidate("candidate_pdf_reader_basic.py")
    assert assessment.can_promote is True
    assert assessment.risk_level == "medium"
    assert assessment.ast_safe is True # os is allowed now

def test_pdf_candidate_promotion_gate_blocked_by_human_status(tmp_path):
    dep_path = tmp_path / "dep.jsonl"
    dep_ledger = DependencyReviewLedger(ledger_path=str(dep_path))
    dep_ledger.append_review(DependencyReviewEvent(
        event_id="e1", timestamp=1.0, dependency_name="pypdf", purpose="x", candidate_id="pdf_reader",
        risk_level="medium", required_by="pdf", installed_status="installed", approved_status="approved",
        review_status="approved_for_installation", notes_summary="y", install_allowed=True
    ))
    
    mock_reviewer = MagicMock()
    mock_reviewer.list_candidates.return_value = [
        SkillCandidateSummary(
            "candidate_pdf_reader_basic.py", "pdf", "hash", 100, 1.0, ["os"], "pending_review"
        )
    ]
    
    gate = SkillPromotionGate(reviewer=mock_reviewer, dependency_ledger=dep_ledger, ledger_path=str(tmp_path / "prom.jsonl"))
    
    assessment = gate.assess_candidate("candidate_pdf_reader_basic.py")
    assert assessment.can_promote is False
    assert "human_review_status:pending_review" in assessment.blockers
