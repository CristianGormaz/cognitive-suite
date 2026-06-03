import pytest
import asyncio
from pathlib import Path
from cognition.ingestion_router import IngestionRouter
from core.task_envelope import TaskEnvelope

@pytest.mark.asyncio
async def test_pdf_detection_by_extension():
    router = IngestionRouter()
    # Simular bytes de un PDF
    pdf_bytes = b"%PDF-1.4 test content"
    
    envelope = await router.route_file_bytes(pdf_bytes, "document.pdf")
    
    assert envelope.payload.mime_type == "application/pdf"
    assert envelope.metadata["ingestion"]["status"] == "pdf_detected"
    assert envelope.metadata["ingestion"]["capability_required"] == "file:pdf_reader"

@pytest.mark.asyncio
async def test_pdf_detection_by_mime():
    router = IngestionRouter()
    pdf_bytes = b"%PDF-1.4 test content"
    
    envelope = await router.route_file_bytes(pdf_bytes, "document.txt", mime_type="application/pdf")
    
    assert envelope.payload.mime_type == "application/pdf"
    assert envelope.metadata["ingestion"]["status"] == "pdf_detected"

@pytest.mark.asyncio
async def test_pdf_size_limit():
    router = IngestionRouter()
    # 6MB (excede los 5MB)
    large_bytes = b"0" * (6 * 1024 * 1024)
    
    from cognition.ingestion_router import IngestionRouterError
    with pytest.raises(IngestionRouterError, match="exceeds maximum allowed size"):
        await router.route_file_bytes(large_bytes, "huge.pdf")
