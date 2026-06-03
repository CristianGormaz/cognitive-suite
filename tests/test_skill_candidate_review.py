import os
import json
import unittest
import tempfile
from pathlib import Path
from cognition.skill_candidate_review import SkillCandidateReview, VALID_STATUSES

class TestSkillCandidateReview(unittest.TestCase):
    def setUp(self):
        self.test_dir = tempfile.TemporaryDirectory()
        self.quarantine_dir = os.path.join(self.test_dir.name, "quarantine")
        self.ledger_path = os.path.join(self.test_dir.name, "review_ledger.jsonl")
        os.makedirs(self.quarantine_dir)
        
        # Create a mock candidate
        self.candidate_file = Path(self.quarantine_dir) / "candidate_test_123.py"
        self.candidate_file.write_text("def _generated_skill_impl(context): return {}", encoding="utf-8")
        
        self.reviewer = SkillCandidateReview(
            quarantine_dir=self.quarantine_dir,
            ledger_path=self.ledger_path
        )

    def tearDown(self):
        self.test_dir.cleanup()

    def test_list_candidates(self):
        candidates = self.reviewer.list_candidates()
        self.assertEqual(len(candidates), 1)
        self.assertEqual(candidates[0].candidate_id, "candidate_test_123.py")

    def test_summarize_candidate(self):
        summary = self.reviewer.summarize_candidate("candidate_test_123.py")
        self.assertEqual(summary["candidate_id"], "candidate_test_123.py")
        self.assertIn("preview", summary)

    def test_mark_candidate_status(self):
        self.reviewer.mark_candidate_status("candidate_test_123.py", "approved_for_future_promotion", "Looks good")
        
        status = self.reviewer.get_candidate_status("candidate_test_123.py")
        self.assertEqual(status, "approved_for_future_promotion")
        
        history = self.reviewer.load_review_history()
        self.assertEqual(len(history), 1)
        self.assertEqual(history[0].status, "approved_for_future_promotion")

    def test_invalid_status_raises_error(self):
        with self.assertRaises(ValueError):
            self.reviewer.mark_candidate_status("candidate_test_123.py", "invalid_status")

if __name__ == "__main__":
    unittest.main()
