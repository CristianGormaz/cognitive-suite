import os
import json
import unittest
import tempfile
import shutil
import asyncio
from pathlib import Path
from unittest.mock import MagicMock

from cognition.skill_promotion_gate import SkillPromotionGate
from cognition.skill_candidate_review import SkillCandidateReview, SkillCandidateSummary
from cognition.skill_experimental_promoter import SkillExperimentalPromoter

class TestSkillExperimentalPromoter(unittest.TestCase):
    def setUp(self):
        self.test_dir = tempfile.TemporaryDirectory()
        self.quarantine_dir = os.path.join(self.test_dir.name, "quarantine")
        self.experimental_dir = os.path.join(self.test_dir.name, "experimental")
        self.backup_dir = os.path.join(self.test_dir.name, "backups")
        self.ledger_path = os.path.join(self.test_dir.name, "promotion.jsonl")
        
        os.makedirs(self.quarantine_dir)
        os.makedirs(self.experimental_dir)
        os.makedirs(self.backup_dir)
        
        # Mock reviewer
        self.mock_reviewer = MagicMock(spec=SkillCandidateReview)
        self.mock_reviewer.quarantine_path = Path(self.quarantine_dir)
        
        # Gate real but using mock reviewer
        self.gate = SkillPromotionGate(reviewer=self.mock_reviewer, ledger_path=self.ledger_path)
        
        self.promoter = SkillExperimentalPromoter(
            gate=self.gate,
            experimental_dir=self.experimental_dir,
            backup_dir=self.backup_dir
        )

    def tearDown(self):
        self.test_dir.cleanup()

    async def run_promotion_test(self):
        # Create a promotable candidate
        cid = "candidate_test.py"
        source_file = Path(self.quarantine_dir) / cid
        source_file.write_text("def _generated_skill_impl(context): return {}", encoding="utf-8")
        
        # Mock summary to satisfy gate (must be approved and have tests)
        summary = SkillCandidateSummary(
            candidate_id=cid,
            capability_signature="test:sig",
            code_sha256="abc",
            file_size=10,
            created_at=1.0,
            dangerous_calls_detected=[],
            current_status="approved_for_future_promotion"
        )
        self.mock_reviewer.list_candidates.return_value = [summary]
        
        # Mock test file existence
        # The gate checks Path("tests") / f"test_{cid}"
        # We need to patch Path.exists or similar, but simpler is to mock the gate's assessment directly
        # Or better, create the test file since we are in a test environment.
        os.makedirs("tests", exist_ok=True)
        test_file = Path("tests") / f"test_{cid}"
        test_file.touch()
        
        try:
            result = await self.promoter.promote_to_experimental(cid)

            assert result["status"] == "success"
            dest_file = Path(self.experimental_dir) / "skill_test.py"
            assert dest_file.exists()

            assert dest_file.read_text() == source_file.read_text()
        finally:
            if test_file.exists(): os.remove(test_file)

    def test_promote_to_experimental_logic(self):
        asyncio.run(self.run_promotion_test())

    def test_promote_blocked_by_gate(self):
        cid = "unsafe.py"
        summary = SkillCandidateSummary(
            candidate_id=cid,
            capability_signature="test:unsafe",
            code_sha256="abc",
            file_size=10,
            created_at=1.0,
            dangerous_calls_detected=["os"],
            current_status="pending_review"
        )
        self.mock_reviewer.list_candidates.return_value = [summary]
        
        async def run_fail():
            return await self.promoter.promote_to_experimental(cid)
            
        result = asyncio.run(run_fail())
        self.assertEqual(result["status"], "blocked")
        self.assertFalse(os.path.exists(os.path.join(self.experimental_dir, "unsafe.py")))

if __name__ == "__main__":
    unittest.main()
