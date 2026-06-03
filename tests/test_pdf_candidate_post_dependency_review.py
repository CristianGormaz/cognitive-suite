import pytest
import os
from pathlib import Path
from skills.experimental.skill_pdf_reader_basic import _generated_skill_impl

@pytest.mark.asyncio
async def test_pdf_candidate_handles_missing_path():
    result = await _generated_skill_impl({})
    assert result["status"] == "error"
    assert result["error_type"] == "missing_input"

@pytest.mark.asyncio
async def test_pdf_candidate_handles_large_file(tmp_path):
    large_file = tmp_path / "large.pdf"
    # Create a 6MB file
    with open(large_file, "wb") as f:
        f.seek(6 * 1024 * 1024 - 1)
        f.write(b"\0")
        
    result = await _generated_skill_impl({"target_path": str(large_file)})
    assert result["status"] == "error"
    assert result["error_type"] == "file_too_large"

@pytest.mark.asyncio
async def test_pdf_candidate_extraction_with_fixture():
    pdf_path = Path("tests/fixtures/ingestion/sample.pdf")
    if not pdf_path.exists():
        pytest.skip("sample.pdf fixture not found")
        
    result = await _generated_skill_impl({"target_path": str(pdf_path)})
    assert result["status"] == "success"
    assert "extracted_text_preview" in result
    assert "full_text_hash" in result
    assert result["capability"] == "file:pdf_reader"

@pytest.mark.asyncio
async def test_pdf_candidate_handles_corrupt_file(tmp_path):
    corrupt_file = tmp_path / "corrupt.pdf"
    corrupt_file.write_text("not a pdf")
    
    result = await _generated_skill_impl({"target_path": str(corrupt_file)})
    assert result["status"] == "error"
    assert result["error_type"] == "pdf_parse_error"
