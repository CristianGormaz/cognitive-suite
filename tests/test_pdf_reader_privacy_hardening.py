import pytest
import os
from pathlib import Path
from skills.experimental.skill_pdf_reader_basic import _generated_skill_impl

@pytest.mark.asyncio
async def test_pdf_reader_sanitizes_errors(tmp_path):
    # Pass a path that doesn't exist to trigger OSError
    fake_path = "/home/user/non_existent.pdf"
    result = await _generated_skill_impl({"target_path": fake_path})
    
    assert result["status"] == "error"
    assert "/home/[REDACTED]" in result["response_text"]
    assert "user" not in result["response_text"]

@pytest.mark.asyncio
async def test_pdf_reader_metadata_redacted_by_default(tmp_path):
    pdf_path = Path("tests/fixtures/ingestion/sample.pdf")
    if not pdf_path.exists():
        pytest.skip("sample.pdf fixture not found")
        
    result = await _generated_skill_impl({"target_path": str(pdf_path)})
    
    assert result["status"] == "success"
    metadata = result["metadata"]
    assert metadata["metadata_redacted"] is True
    assert "author" not in metadata
    assert "title" not in metadata
    assert "file_ref" in metadata
    assert "user" not in metadata["file_ref"]

@pytest.mark.asyncio
async def test_pdf_reader_respects_metadata_flag(tmp_path):
    pdf_path = Path("tests/fixtures/ingestion/sample.pdf")
    if not pdf_path.exists():
        pytest.skip("sample.pdf fixture not found")
        
    os.environ["GREYS_PDF_INCLUDE_METADATA"] = "1"
    try:
        result = await _generated_skill_impl({"target_path": str(pdf_path)})
        assert result["status"] == "success"
        assert "author" in result["metadata"]
    finally:
        del os.environ["GREYS_PDF_INCLUDE_METADATA"]
