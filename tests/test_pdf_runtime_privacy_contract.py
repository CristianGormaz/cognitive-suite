import pytest
import os
import json
from pathlib import Path
from skills.experimental.skill_pdf_reader_basic import _generated_skill_impl

@pytest.mark.asyncio
async def test_pdf_runtime_privacy_contract_with_fixture():
    pdf_path = Path("tests/fixtures/ingestion/sample.pdf")
    if not pdf_path.exists():
        pytest.skip("sample.pdf fixture not found")
        
    context = {
        "target_path": str(pdf_path),
        "source": "manual_runtime_test",
        "privacy_mode": "strict",
        "max_file_size_bytes": 5242880,
        "max_chars": 30000,
        "preview_chars": 500
    }
    
    result = await _generated_skill_impl(context)
    
    assert result["status"] == "success"
    assert "file_ref" in result["metadata"]
    assert "author" not in result["metadata"]
    assert "title" not in result["metadata"]
    assert "extracted_text_preview" in result
    assert "full_text_hash" in result
    assert "doritos" not in result["metadata"]["file_ref"]
    assert "doritos" not in result["response_text"]
    assert not os.path.isabs(result["metadata"]["file_ref"])

@pytest.mark.asyncio
async def test_pdf_runtime_respects_metadata_flag():
    pdf_path = Path("tests/fixtures/ingestion/sample.pdf")
    if not pdf_path.exists():
        pytest.skip("sample.pdf fixture not found")
        
    os.environ["GREYS_PDF_INCLUDE_METADATA"] = "1"
    try:
        context = {"target_path": str(pdf_path)}
        result = await _generated_skill_impl(context)
        assert "author" in result["metadata"]
    finally:
        del os.environ["GREYS_PDF_INCLUDE_METADATA"]

@pytest.mark.asyncio
async def test_pdf_runtime_blocks_large_file(tmp_path):
    large_file = tmp_path / "large.pdf"
    with open(large_file, "wb") as f:
        f.seek(6 * 1024 * 1024 - 1)
        f.write(b"\0")
        
    context = {"target_path": str(large_file)}
    result = await _generated_skill_impl(context)
    assert result["status"] == "error"
    assert result["error_type"] == "file_too_large"
