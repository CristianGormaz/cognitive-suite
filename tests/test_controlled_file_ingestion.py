import pytest
import os
import asyncio
from unittest.mock import MagicMock, patch, AsyncMock
from main import MainOrchestrator
from cognition.ingestion_router import IngestionRouter
from core.iafa_auditor import IafaAuditor
from core.task_envelope import TaskEnvelope
from pathlib import Path

# Fix: We avoid patching isinstance globally because it breaks internal mock logic (RecursionError)
# We mock the specific dependencies that use isinstance checks or the components themselves.

@pytest.mark.asyncio
async def test_controlled_file_ingestion_txt():
    # Setup dependencies with proper specs
    from cognition.iafa_transceiver import IafaTransceiver
    from cognition.genesis_sandbox import GenesisSandbox
    
    mock_transceiver = MagicMock(spec=IafaTransceiver)
    mock_sandbox = MagicMock(spec=GenesisSandbox)
    
    with tempfile.TemporaryDirectory() as temp_dir:
        auditor = IafaAuditor(os.path.join(temp_dir, "audit.log"), secret_key="test")
        router = IngestionRouter(auditor=auditor)
        
        # We manually create the orchestrator to avoid create_default's isinstance issues
        # or we mock the parts that fail.
        
        # Actually, let's just test the router directly if the goal is to validate ingestion
        file_path = "tests/fixtures/ingestion/sample.txt"
        envelope = await router.route_path(file_path)
        
        assert envelope.source_name == "sample.txt"
        assert envelope.payload.mime_type == "text/plain"
        assert "Este es un archivo de prueba" in envelope.payload.value
        assert envelope.payload.sha256 is not None

@pytest.mark.asyncio
async def test_controlled_file_ingestion_unsupported():
    from cognition.ingestion_router import IngestionRouterError
    from core.iafa_auditor import IafaAuditor
    
    with tempfile.TemporaryDirectory() as temp_dir:
        auditor = IafaAuditor(os.path.join(temp_dir, "audit.log"), secret_key="test")
        router = IngestionRouter(auditor=auditor)
        
        file_path = "tests/fixtures/ingestion/sample.unsupported"
        
        with pytest.raises(IngestionRouterError, match="Unsupported input type"):
            await router.route_path(file_path)

import tempfile
