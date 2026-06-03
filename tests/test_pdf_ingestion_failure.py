import pytest
from unittest.mock import MagicMock, patch
from cognition.ingestion_router import IngestionRouter, IngestionRouterError
import asyncio
from core.iafa_auditor import IafaAuditor
import tempfile
import os
import pytest
from cognition.ingestion_router import IngestionRouter

@pytest.mark.asyncio
async def test_pdf_ingestion_accepted_conditionally():
    with tempfile.TemporaryDirectory() as temp_dir:
        secret = "test-secret-123"
        auditor = IafaAuditor(os.path.join(temp_dir, "audit.log"), secret_key=secret)
        router = IngestionRouter(auditor=auditor)

        pdf_path = "tests/fixtures/ingestion/sample.pdf"
        if not os.path.exists(pdf_path):
            # Fallback
            envelope = await router.route_file_bytes(b"%PDF-1.4", filename="test.pdf")
        else:
            envelope = await router.route_path(pdf_path)

        assert envelope.payload.mime_type == "application/pdf"
        assert envelope.metadata["ingestion"]["status"] == "pdf_detected"
        # Verificar auditoría
        await asyncio.sleep(0.1)
        entries = list(auditor.iter_verified_entries())
        assert any(e.get("payload", {}).get("event") in ["ingestion.file.accepted", "ingestion.pdf.detected"] for e in entries)

