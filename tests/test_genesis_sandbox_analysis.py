import asyncio
import pytest
from unittest.mock import MagicMock, patch, AsyncMock
from cognition.genesis_analysis import GenesisAnalysis, QUARANTINE_DIR
from cognition.genesis_engine import GenesisEngine
from cognition.genesis_sandbox import GenesisSandbox
from cognition.iafa_transceiver import IafaTransceiver
from core.iafa_auditor import IafaAuditor
from core.task_envelope import TaskEnvelope
from pathlib import Path

@pytest.mark.asyncio
async def test_analyze_missing_capability_flow():
    # Setup mocks with proper specs
    mock_transceiver = MagicMock(spec=IafaTransceiver)
    mock_transceiver.query_llm = AsyncMock(return_value="def _generated_skill_impl(context): return {'ok': True}")
    
    mock_sandbox = MagicMock(spec=GenesisSandbox)
    mock_sandbox.validate_code_proposal = AsyncMock()
    mock_sandbox.validate_code_proposal.return_value = MagicMock(is_safe=True, validation_errors=[], code_hash="abc")
    
    mock_auditor = MagicMock(spec=IafaAuditor)
    
    # We use a real-ish initialization but mock the check or the objects
    # Let's try to mock the specific check inside GenesisEngine if needed, 
    # but first let's see if spec works.
    
    # RELAXING checks in GenesisEngine for testing might be easier if spec fails
    with patch("cognition.genesis_engine.IafaTransceiver", IafaTransceiver):
        with patch("cognition.genesis_engine.GenesisSandbox", GenesisSandbox):
            with patch("cognition.genesis_engine.IafaAuditor", IafaAuditor):
                engine = GenesisEngine(mock_transceiver, mock_sandbox, mock_auditor)
                analysis = GenesisAnalysis(engine)
                
                envelope = TaskEnvelope.from_text("test")
                
                result = await analysis.analyze_missing_capability("math:solve_integral", envelope, {})
                
                assert result.capability_signature == "math:solve_integral"
                assert result.sandbox_status is True
                assert result.installable is False
                assert result.requires_human_approval is True
                
                # Verificar que se guardó en cuarentena
                quarantine_path = Path(QUARANTINE_DIR)
                candidates = list(quarantine_path.glob("candidate_solve_integral_*.py"))
                assert len(candidates) > 0

@pytest.mark.asyncio
async def test_analyze_rejects_unsafe_code():
    mock_transceiver = MagicMock(spec=IafaTransceiver)
    mock_transceiver.query_llm = AsyncMock(return_value="import os\ndef _generated_skill_impl(context): return os.listdir('.')")
    
    sandbox = GenesisSandbox()
    mock_auditor = MagicMock(spec=IafaAuditor)
    
    with patch("cognition.genesis_engine.IafaTransceiver", IafaTransceiver):
        with patch("cognition.genesis_engine.GenesisSandbox", GenesisSandbox):
            with patch("cognition.genesis_engine.IafaAuditor", IafaAuditor):
                engine = GenesisEngine(mock_transceiver, sandbox, mock_auditor)
                analysis = GenesisAnalysis(engine)
                
                envelope = TaskEnvelope.from_text("unsafe test")
                result = await analysis.analyze_missing_capability("test:unsafe", envelope, {})
                
                assert result.sandbox_status is False
                assert any("dangerous import" in err for err in result.validation_errors)
                assert result.risk_level == "high"
