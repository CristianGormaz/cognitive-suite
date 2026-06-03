import pytest
from unittest.mock import MagicMock
from cognition.skill_promotion_gate import SkillPromotionGate, SkillCandidateSummary
from core.dependency_review_ledger import DependencyReviewLedger, DependencyReviewEvent

def test_pdf_candidate_blocked_by_dependency(tmp_path):
    ledger_path = tmp_path / "dep.jsonl"
    dep_ledger = DependencyReviewLedger(ledger_path=str(ledger_path))
    
    # Pendiente
    dep_ledger.append_review(DependencyReviewEvent(
        event_id="e1", timestamp=1.0, dependency_name="pypdf", purpose="x", candidate_id="pdf_reader",
        risk_level="medium", required_by="pdf", installed_status="missing", approved_status="pending",
        review_status="pending_human_review", notes_summary="y"
    ))
    
    mock_reviewer = MagicMock()
    mock_reviewer.list_candidates.return_value = [
        SkillCandidateSummary("pdf_reader", "file:pdf_reader", "hash", "approved_for_future_promotion", [], "high")
    ]
    
    gate = SkillPromotionGate(reviewer=mock_reviewer, dependency_ledger=dep_ledger, ledger_path=str(tmp_path / "prom.jsonl"))
    
    # Debe ser bloqueado
    assessment = gate.assess_candidate("pdf_reader")
    assert assessment.can_promote is False
    assert any("dependency_review_pending:pypdf" in b for b in assessment.blockers)
    assert "Aprobar dependency review pendiente" in assessment.recommendation
