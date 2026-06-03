import pytest
import os
from unittest.mock import MagicMock, AsyncMock, patch
from cognition.skill_loader import DynamicSkillLoader, SkillLoaderError

@pytest.fixture
def mock_loader(tmp_path):
    skills_dir = tmp_path / "src/skills"
    experimental_dir = skills_dir / "experimental"
    experimental_dir.mkdir(parents=True)
    
    # Create mock skill
    skill_code = """
async def _generated_skill_impl(context):
    return {"status": "success", "response_text": "PDF processed"}
"""
    (experimental_dir / "skill_pdf_reader_basic.py").write_text(skill_code)
    
    return DynamicSkillLoader(skills_directory=str(skills_dir))

@pytest.mark.asyncio
async def test_pdf_reader_blocked_when_experimental_disabled(mock_loader):
    # Verify that without allowlist, experimental skills are blocked
    with pytest.raises(SkillLoaderError) as excinfo:
        await mock_loader.execute_skill("pdf_reader_basic", {}, subfolder="experimental")
    assert "requires explicit allowlist entry" in str(excinfo.value)

@pytest.mark.asyncio
async def test_pdf_reader_blocked_when_not_in_allowlist(mock_loader):
    mock_loader.set_allowlist({"other_skill"})
    
    with pytest.raises(SkillLoaderError) as excinfo:
        await mock_loader.execute_skill("pdf_reader_basic", {}, subfolder="experimental")
    assert "not in the allowlist" in str(excinfo.value)

@pytest.mark.asyncio
async def test_pdf_reader_allowed_when_in_allowlist(mock_loader):
    mock_loader.set_allowlist({"pdf_reader_basic"})
    result = await mock_loader.execute_skill("pdf_reader_basic", {}, subfolder="experimental")
    assert result["status"] == "success"
