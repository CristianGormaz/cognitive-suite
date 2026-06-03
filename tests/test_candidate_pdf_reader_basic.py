import pytest
import os
import asyncio
from unittest.mock import MagicMock, patch, AsyncMock
from cognition.genesis_analysis import GenesisAnalysis
from cognition.genesis_engine import GenesisEngine
from cognition.genesis_sandbox import GenesisSandbox
from cognition.iafa_transceiver import IafaTransceiver
from core.iafa_auditor import IafaAuditor
from core.task_envelope import TaskEnvelope
from pathlib import Path

@pytest.mark.asyncio
async def test_candidate_pdf_reader_sandbox_analysis():
    # Setup mocks
    mock_transceiver = MagicMock(spec=IafaTransceiver)
    mock_sandbox = GenesisSandbox() # Use real sandbox to verify blocking
    mock_auditor = MagicMock(spec=IafaAuditor)
    
    with patch("cognition.genesis_engine.IafaTransceiver", IafaTransceiver), \
         patch("cognition.genesis_engine.GenesisSandbox", GenesisSandbox), \
         patch("cognition.genesis_engine.IafaAuditor", IafaAuditor):
         
        engine = GenesisEngine(mock_transceiver, mock_sandbox, mock_auditor)
        analysis = GenesisAnalysis(engine)
        
        # Simular carga de código del candidato
        cand_path = Path("src/skills/experimental/skill_pdf_reader_basic.py")
        if not cand_path.exists():
            pytest.skip("skill_pdf_reader_basic.py not found for analysis")
            
        code = cand_path.read_text()
        mock_transceiver.query_llm = AsyncMock(return_value=code)
        
        envelope = TaskEnvelope.from_text("test pdf")
        result = await analysis.analyze_missing_capability("file:pdf_reader", envelope, {})
        
        assert result.capability_signature == "file:pdf_reader"
        # The sandbox should reject it because of 'os' and 'open' (implicit in pypdf or explicit in candidate)
        # In our case, the candidate uses 'os'.
        assert result.sandbox_status is False
        assert any("dangerous import rejected: os" in err for err in result.validation_errors)
        # Sandbox failure usually forces High Risk until human review
        assert result.risk_level == "high"
