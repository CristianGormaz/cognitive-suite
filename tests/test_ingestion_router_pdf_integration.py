import pytest
import os
from pathlib import Path
from cognition.ingestion_router import IngestionRouter, IngestionRouterError

@pytest.fixture
def router():
    return IngestionRouter()

@pytest.mark.asyncio
async def test_ingestion_router_detects_pdf(router):
    pdf_path = Path("tests/fixtures/ingestion/sample.pdf")
    if not pdf_path.exists():
        pytest.skip("sample.pdf fixture not found")
        
    envelope = await router.route_path(str(pdf_path))
    
    assert envelope.payload.mime_type == "application/pdf"
    assert envelope.source_type == "file"
    assert "ingestion" in envelope.metadata
    assert "source_path" in envelope.metadata["ingestion"]
    assert envelope.metadata["ingestion"]["source_path"] == str(pdf_path.absolute())

@pytest.mark.asyncio
async def test_ingestion_router_blocks_large_pdf(router, tmp_path):
    large_pdf = tmp_path / "large.pdf"
    with open(large_pdf, "wb") as f:
        f.seek(6 * 1024 * 1024 - 1)
        f.write(b"\0")
        
    with pytest.raises(IngestionRouterError) as excinfo:
        await router.route_path(str(large_pdf))
    assert "exceeds maximum allowed size" in str(excinfo.value)
