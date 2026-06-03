import pytest
import json
from pathlib import Path
from cognition.morning_brief import MorningBrief

@pytest.fixture
def mock_assets(tmp_path):
    journal_path = tmp_path / "journal.jsonl"
    queue_path = tmp_path / "queue.jsonl"
    curated_path = tmp_path / "curated.jsonl"
    failure_path = tmp_path / "fail.jsonl"
    tension_path = tmp_path / "tension.jsonl"
    dep_path = tmp_path / "dependency_review_ledger.jsonl"
    
    # Pendiente
    with open(dep_path, "w") as f:
        f.write(json.dumps({
            "event_id": "e1", "timestamp": 123.0, "dependency_name": "pypdf", "purpose": "x",
            "candidate_id": "pdf_reader", "risk_level": "medium", "required_by": "pdf",
            "installed_status": "missing", "approved_status": "pending", "review_status": "pending_human_review",
            "notes_summary": "y", "requires_human_approval": True, "install_allowed": False,
            "schema_version": "dependency-review.v1"
        }) + "\n")

    queue_path.write_text("")
    curated_path.write_text("")
    journal_path.write_text("")
    failure_path.write_text("")
    tension_path.write_text("")
    
    return journal_path, queue_path, curated_path, failure_path, tension_path, dep_path

def test_morning_brief_shows_pending_dependencies(mock_assets):
    journal, queue, curated, fail, tension, dep = mock_assets
    
    from core.dependency_review_ledger import DependencyReviewLedger
    from unittest.mock import patch
    import importlib.util
    
    dep_ledger = DependencyReviewLedger(ledger_path=str(dep))
    
    with patch("importlib.util.find_spec", return_value=None):
        brief_gen = MorningBrief(
            journal_path=str(journal),
            option_queue_path=str(queue),
            curated_ledger_path=str(curated),
            dependency_ledger=dep_ledger,
            memory_dir=str(dep.parent)
        )
    
        brief = brief_gen.generate_brief()
    
        assert "Estado de Dependencias" in brief
        assert "[!] pypdf (PENDIENTE de revisión)" in brief
