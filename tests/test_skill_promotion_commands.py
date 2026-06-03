import pytest
import os
from unittest.mock import MagicMock, patch, AsyncMock
from main import MainOrchestrator
from core.iafa_auditor import IafaAuditor
from cognition.skill_candidate_review import SkillCandidateReview, SkillCandidateSummary
from cognition.skill_promotion_gate import SkillPromotionGate
import tempfile

@pytest.mark.asyncio
async def test_main_orchestrator_promotion_commands():
    # Setup mocks
    mock_router = MagicMock()
    mock_planner = MagicMock()
    mock_dispatcher = MagicMock()
    mock_cog = MagicMock()
    mock_genesis = MagicMock()
    mock_genesis.sandbox = MagicMock()
    mock_loader = MagicMock()
    
    with tempfile.TemporaryDirectory() as temp_dir:
        auditor = IafaAuditor(os.path.join(temp_dir, "audit.log"), secret_key="test")
        
        # Mock reviewer
        mock_reviewer = MagicMock(spec=SkillCandidateReview)
        summary = SkillCandidateSummary(
            candidate_id="test_cand.py",
            capability_signature="test:sig",
            code_sha256="abc",
            file_size=100,
            created_at=123.0,
            dangerous_calls_detected=[],
            current_status="approved_for_future_promotion"
        )
        mock_reviewer.list_candidates.return_value = [summary]
        mock_reviewer.get_candidate_status.return_value = "approved_for_future_promotion"
        
        # Mock specific dependencies that MainOrchestrator checks with isinstance in create_default
        # But here we are calling the constructor directly, so we just need to ensure 
        # the parameters are accepted.
        
        # We avoid global isinstance patch to prevent RecursionError in mock.py
        orchestrator = MainOrchestrator(
            mock_router, mock_planner, mock_dispatcher, mock_cog, mock_genesis, mock_loader, auditor,
            skill_reviewer=mock_reviewer,
            stress_guard=MagicMock(),
            tension_ledger=MagicMock(),
            failure_ledger=MagicMock(),
            genesis_analysis=MagicMock()
        )
        
        # Test /promotion command logic
        assessment = orchestrator.skill_promoter.assess_candidate("test_cand.py")
        assert assessment.candidate_id == "test_cand.py"
        # It should be blocked by 'missing_required_tests'
        assert assessment.can_promote is False 
        assert any("missing_required_tests" in b for b in assessment.blockers)
        # Test dry-run promote
        result = orchestrator.skill_promoter.dry_run_promote("test_cand.py", "experimental")
        assert result["status"] == "blocked"
        assert result["dry_run"] is True
