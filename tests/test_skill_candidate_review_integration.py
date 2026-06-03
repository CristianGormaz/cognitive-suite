import pytest
from unittest.mock import MagicMock, patch, AsyncMock
from main import MainOrchestrator
from core.task_envelope import TaskEnvelope
from core.iafa_auditor import IafaAuditor
from cognition.skill_candidate_review import SkillCandidateReview
from pathlib import Path
import tempfile
import os

@pytest.mark.asyncio
async def test_main_orchestrator_review_commands():
    # Setup mocks
    mock_router = MagicMock()
    mock_planner = MagicMock()
    mock_dispatcher = MagicMock()
    mock_cog = MagicMock()
    
    # We need a mock for GenesisEngine that has a 'sandbox' attribute
    mock_genesis = MagicMock()
    mock_genesis.sandbox = MagicMock()
    
    mock_loader = MagicMock()
    
    with tempfile.TemporaryDirectory() as temp_dir:
        auditor = IafaAuditor(os.path.join(temp_dir, "audit.log"), secret_key="test")
        
        # Create a real-ish reviewer with temp paths
        quarantine_dir = os.path.join(temp_dir, "quarantine")
        review_ledger = os.path.join(temp_dir, "review.jsonl")
        os.makedirs(quarantine_dir)
        
        # Create mock candidate
        candidate_file = Path(quarantine_dir) / "candidate_math_123.py"
        candidate_file.write_text("def _generated_skill_impl(context): return {}", encoding="utf-8")
        
        reviewer = SkillCandidateReview(quarantine_dir=quarantine_dir, ledger_path=review_ledger)
        
        # We need to mock GenesisAnalysis too to avoid it failing if it tries to use the engine
        mock_analysis = MagicMock()
        
        orchestrator = MainOrchestrator(
            mock_router, mock_planner, mock_dispatcher, mock_cog, mock_genesis, mock_loader, auditor,
            skill_reviewer=reviewer,
            genesis_analysis=mock_analysis
        )
        
        # Mock tension ledger
        orchestrator.tension_ledger = MagicMock()
        orchestrator.stress_guard = MagicMock()
        orchestrator.stress_guard.get_stress_snapshot.return_value = {
            "is_mem_stressed": False, "is_cpu_stressed": False, "load_1m": 0.1, "mem_available_mb": 1000
        }
        
        # Test /review command processing in run_interactive (indirectly)
        cid = "candidate_math_123.py"
        status = "needs_dependency"
        reason = "missing sympy"
        
        # Process review via orchestrator helper logic
        orchestrator.skill_reviewer.mark_candidate_status(cid, status, reason)
        
        # Registrar tension semántica como hace run_interactive
        orchestrator._register_tension_event(f"review_{cid[:8]}", "human_candidate_review", {
            "analysis": {"recommendation": reason or status, "sandbox_status": True},
            "user_outcome": "needs_dependency"
        })
        
        # Verify
        assert orchestrator.skill_reviewer.get_candidate_status(cid) == "needs_dependency"
        orchestrator.tension_ledger.append_event.assert_called()
        args = orchestrator.tension_ledger.append_event.call_args[0][0]
        assert args.event_type == "human_candidate_review"
        assert "missing sympy" in args.notes
