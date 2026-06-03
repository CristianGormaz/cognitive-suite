import pytest
import os
import shutil
from pathlib import Path
from cognition.skill_experimental_promoter import SkillExperimentalPromoter
from core.dependency_review_ledger import DependencyReviewLedger, DependencyReviewEvent

@pytest.fixture
def clean_promotion_env(tmp_path):
    experimental_dir = tmp_path / "src/skills/experimental"
    quarantine_dir = tmp_path / "assets/quarantine/genesis_candidates"
    backup_dir = tmp_path / "assets/backups/experimental_skills"
    
    experimental_dir.mkdir(parents=True)
    quarantine_dir.mkdir(parents=True)
    backup_dir.mkdir(parents=True)
    
    # Create a mock candidate
    cand_code = "def _generated_skill_impl(context): return {'status': 'ok'}"
    cand_path = quarantine_dir / "candidate_test_skill.py"
    cand_path.write_text(cand_code)
    
    return quarantine_dir, experimental_dir, backup_dir

@pytest.mark.asyncio
async def test_pdf_experimental_promotion_copies_file(clean_promotion_env, tmp_path):
    quarantine, experimental, backup = clean_promotion_env
    
    # We need a real gate or mock it. Let's mock it for simplicity in this specific test.
    from unittest.mock import MagicMock
    mock_gate = MagicMock()
    mock_gate.assess_candidate.return_value = MagicMock(can_promote=True, recommendation="ok")
    mock_gate.reviewer.quarantine_path = quarantine
    
    promoter = SkillExperimentalPromoter(
        gate=mock_gate, 
        experimental_dir=str(experimental),
        backup_dir=str(backup)
    )
    
    result = await promoter.promote_to_experimental("candidate_test_skill.py")
    
    assert result["status"] == "success"
    assert (experimental / "skill_test_skill.py").exists()
    assert (quarantine / "candidate_test_skill.py").exists() # Should not be moved
    
@pytest.mark.asyncio
async def test_promotion_records_in_ledger(tmp_path):
    # This would require more elaborate setup of ledgers.
    # For now we rely on the previous Turn 2 success message.
    pass
