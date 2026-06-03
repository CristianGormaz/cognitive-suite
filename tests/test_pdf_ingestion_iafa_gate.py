import pytest
import os
from pathlib import Path
from main import MainOrchestrator
from unittest.mock import AsyncMock

@pytest.mark.asyncio
async def test_pdf_ingestion_iafa_blocks_if_stress(tmp_path):
    pdf_path = Path("tests/fixtures/ingestion/sample.pdf")
    if not pdf_path.exists():
        pytest.skip("sample.pdf fixture not found")
        
    os.environ["GREYS_EXPERIMENTAL_SKILLS_ENABLED"] = "1"
    os.environ["GREYS_EXPERIMENTAL_SKILL_ALLOWLIST"] = "pdf_reader_basic"
    
    try:
        orchestrator = await MainOrchestrator.create_default()
        
        # Simulate host stress
        orchestrator.stress_guard.is_host_under_stress = MagicMock(return_value=True)
        
        envelope = await orchestrator.ingestion_router.route_path(str(pdf_path))
        
        from cognition.llm_planner import LLMServiceError
        # IAFA doesn't block planner, but planner calls LLM which might be stressed.
        # Actually IAFA gate is in dispatcher. 
        # But if host is under stress, LLMPlanner.plan raises LlmHostStressedError.
        
        result = await orchestrator.process_envelope(envelope)
        assert result.status == "executed"
        assert "host físico está bajo alta carga" in result.details["response_text"]
    finally:
        del os.environ["GREYS_EXPERIMENTAL_SKILLS_ENABLED"]
        del os.environ["GREYS_EXPERIMENTAL_SKILL_ALLOWLIST"]

from unittest.mock import MagicMock
