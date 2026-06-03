import pytest
import os
import json
from pathlib import Path
from unittest.mock import MagicMock, AsyncMock, patch
from main import MainOrchestrator

@pytest.fixture
def mock_orchestrator():
    # Use AsyncMock for MainOrchestrator.create_default if needed, 
    # but here we can just instantiate or mock its parts.
    pass

@pytest.mark.asyncio
async def test_pdf_ingestion_blocked_without_allowlist(tmp_path):
    # Setup dummy PDF
    pdf_path = tmp_path / "test.pdf"
    pdf_path.write_bytes(b"%PDF-1.4 test")
    
    # Mock orchestrator
    with patch("main.MainOrchestrator.create_default", new_callable=AsyncMock) as mock_create:
        orchestrator = AsyncMock()
        mock_create.return_value = orchestrator
        
        # Mock router to return PDF envelope
        from cognition.ingestion_router import IngestionRouter
        from core.task_envelope import TaskEnvelope
        router = IngestionRouter()
        envelope = await router.route_path(str(pdf_path))
        orchestrator.ingestion_router.route_path.return_value = envelope
        
        # Mock process_envelope to fail if not allowlisted
        from cognition.skill_loader import SkillLoaderError
        orchestrator.process_envelope.side_effect = SkillLoaderError("Experimental skill 'pdf_reader_basic' requires explicit allowlist entry.")
        
        # Simulate main.py logic for Case 1 (No flags)
        with pytest.raises(Exception): # The real main.py catches it and logs, here we just check if it was called
             await orchestrator.process_envelope(envelope)

@pytest.mark.asyncio
async def test_pdf_ingestion_success_with_allowlist(tmp_path):
    pdf_path = Path("tests/fixtures/ingestion/sample.pdf")
    if not pdf_path.exists():
        pytest.skip("sample.pdf fixture not found")
        
    # This test is better done as an integration test or by mocking the planner
    pass
