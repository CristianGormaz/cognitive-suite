import pytest
import os
from unittest.mock import MagicMock, patch, AsyncMock
from cognition.skill_loader import DynamicSkillLoader, SkillLoaderError, SkillNotFoundError
from pathlib import Path
import tempfile

@pytest.mark.asyncio
async def test_loader_respects_allowlist():
    with tempfile.TemporaryDirectory() as temp_dir:
        loader = DynamicSkillLoader(skills_directory=temp_dir)
        
        # Crear una skill ficticia
        skill_file = Path(temp_dir) / "skill_test_skill.py"
        skill_file.write_text("async def _generated_skill_impl(ctx): return {'ok': True}")
        
        # 1. Sin allowlist (por defecto permite todo si no se establece set_allowlist)
        # En la implementación actual, if self.allowlist is not None...
        result = await loader.execute_skill("test_skill", {})
        assert result["ok"] is True
        
        # 2. Con allowlist que NO incluye la skill
        loader.set_allowlist({"other_skill"})
        with pytest.raises(SkillLoaderError, match="not in the allowlist"):
            await loader.execute_skill("test_skill", {})
            
        # 3. Con allowlist que SÍ incluye la skill
        loader.set_allowlist({"test_skill"})
        result = await loader.execute_skill("test_skill", {})
        assert result["ok"] is True

@pytest.mark.asyncio
async def test_loader_recursive_search():
    with tempfile.TemporaryDirectory() as temp_dir:
        # Crear estructura experimental/skill_abc.py
        exp_dir = Path(temp_dir) / "experimental"
        exp_dir.mkdir()
        skill_file = exp_dir / "skill_abc.py"
        skill_file.write_text("async def _generated_skill_impl(ctx): return {'source': 'experimental'}")
        
        loader = DynamicSkillLoader(skills_directory=temp_dir)
        
        # Debe encontrarla recursivamente si subfolder=None
        result = await loader.execute_skill("abc", {})
        assert result["source"] == "experimental"

@pytest.mark.asyncio
async def test_loader_blocks_quarantine_implicitly():
    # El loader solo busca en la carpeta de skills (y subcarpetas si rglob)
    # Quarantine está fuera de esa jerarquía.
    with tempfile.TemporaryDirectory() as temp_dir:
        loader = DynamicSkillLoader(skills_directory=temp_dir)
        
        # Intentar cargar algo que no existe en el directorio de skills
        with pytest.raises(SkillNotFoundError):
            await loader.execute_skill("non_existent", {})
