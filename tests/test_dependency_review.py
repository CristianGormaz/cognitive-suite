import pytest
import os
import json
from pathlib import Path
from core.dependency_review_ledger import DependencyReviewLedger, DependencyReviewEvent

def test_dependency_ledger_append_and_load(tmp_path):
    ledger_path = tmp_path / "dep_ledger.jsonl"
    ledger = DependencyReviewLedger(ledger_path=str(ledger_path))
    
    event = DependencyReviewEvent(
        event_id="e1", timestamp=123.0, dependency_name="pypdf", purpose="pdf parsing",
        candidate_id="pdf_cand", risk_level="medium", required_by="pdf_cand",
        installed_status="missing", approved_status="pending", review_status="pending_human_review",
        notes_summary="Testing"
    )
    
    ledger.append_review(event)
    events = ledger.load_all()
    
    assert len(events) == 1
    assert events[0].dependency_name == "pypdf"
    
def test_dependency_approval_logic(tmp_path):
    ledger_path = tmp_path / "dep_ledger.jsonl"
    ledger = DependencyReviewLedger(ledger_path=str(ledger_path))
    
    # 1. Unapproved
    event1 = DependencyReviewEvent(
        event_id="e1", timestamp=123.0, dependency_name="pypdf", purpose="pdf parsing",
        candidate_id="pdf_cand", risk_level="medium", required_by="pdf_cand",
        installed_status="missing", approved_status="pending", review_status="pending_human_review",
        notes_summary="Testing", install_allowed=False
    )
    ledger.append_review(event1)
    
    assert ledger.is_dependency_approved("pypdf") is False
    assert len(ledger.get_pending_reviews()) == 1
    
    # 2. Approved
    event2 = DependencyReviewEvent(
        event_id="e2", timestamp=124.0, dependency_name="pypdf", purpose="pdf parsing",
        candidate_id="pdf_cand", risk_level="medium", required_by="pdf_cand",
        installed_status="missing", approved_status="approved", review_status="approved",
        notes_summary="Testing", install_allowed=True
    )
    ledger.append_review(event2)
    
    assert ledger.is_dependency_approved("pypdf") is True
    assert len(ledger.get_pending_reviews()) == 0
