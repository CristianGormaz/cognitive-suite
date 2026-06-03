import os
import json
import unittest
import tempfile
from pathlib import Path
from unittest.mock import MagicMock
from cognition.skill_promotion_gate import SkillPromotionGate
from cognition.skill_candidate_review import SkillCandidateReview, SkillCandidateSummary

class TestSkillPromotionGate(unittest.TestCase):
    def setUp(self):
        self.test_dir = tempfile.TemporaryDirectory()
        self.ledger_path = os.path.join(self.test_dir.name, "promotion_ledger.jsonl")
        
        # Mock reviewer
        self.mock_reviewer = MagicMock(spec=SkillCandidateReview)
        
        self.gate = SkillPromotionGate(
            reviewer=self.mock_reviewer,
            ledger_path=self.ledger_path
        )

    def tearDown(self):
        self.test_dir.cleanup()

    def test_assess_candidate_blocked_by_status(self):
        # Candidato en estado 'pending_review' no puede promoverse
        summary = SkillCandidateSummary(
            candidate_id="cand1.py",
            capability_signature="test:sig",
            code_sha256="abc",
            file_size=100,
            created_at=123.0,
            dangerous_calls_detected=[],
            current_status="pending_review"
        )
        self.mock_reviewer.list_candidates.return_value = [summary]
        
        assessment = self.gate.assess_candidate("cand1.py")
        
        self.assertFalse(assessment.can_promote)
        self.assertIn("human_review_status:pending_review", assessment.blockers)

    def test_assess_candidate_blocked_by_unsafe_calls(self):
        summary = SkillCandidateSummary(
            candidate_id="unsafe.py",
            capability_signature="test:unsafe",
            code_sha256="abc",
            file_size=100,
            created_at=123.0,
            dangerous_calls_detected=["subprocess"],
            current_status="approved_for_future_promotion"
        )
        self.mock_reviewer.list_candidates.return_value = [summary]
        
        assessment = self.gate.assess_candidate("unsafe.py")
        
        self.assertFalse(assessment.can_promote)
        self.assertIn("critical_unsafe_calls:['subprocess']", assessment.blockers)

    def test_dry_run_promote_does_not_install(self):
        # Incluso si fuera promovible, dry_run no hace nada físico
        summary = SkillCandidateSummary(
            candidate_id="good.py",
            capability_signature="test:good",
            code_sha256="abc",
            file_size=100,
            created_at=123.0,
            dangerous_calls_detected=[],
            current_status="approved_for_future_promotion"
        )
        # Note: missing_tests blocker will still be there in the current implementation
        self.mock_reviewer.list_candidates.return_value = [summary]
        
        result = self.gate.dry_run_promote("good.py")
        
        self.assertTrue(result["dry_run"])
        # Verificar que el ledger se escribió
        self.assertTrue(os.path.exists(self.ledger_path))

if __name__ == "__main__":
    unittest.main()
