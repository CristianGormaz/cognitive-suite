import pytest
import os
from pathlib import Path
from unittest.mock import MagicMock, AsyncMock
from cognition.ingestion_router import IngestionRouter
from core.privacy_sanitizer import sanitize_path_for_logs

@pytest.mark.asyncio
async def test_pdf_path_privacy():
    router = IngestionRouter()
    
    # Usar el fixture real del proyecto
    fixture_path = str(Path(__file__).parent / "fixtures/ingestion/sample.pdf")
    
    # Si no existe, crear un dummy algo más robusto o saltar
    if not os.path.exists(fixture_path):
        pytest.skip("Fixture sample.pdf not found")
        
    try:
        envelope = await router.route_path(fixture_path)
        
        # El nombre del archivo debe estar en el sobre, pero no la ruta completa
        assert envelope.source_name == "sample.pdf"
        
        # El test real de privacidad es que cuando se loguea o se registra en ledgers, se use el sanitizer.
        from skills.experimental.skill_pdf_reader_basic import _generated_skill_impl
        skill_result = await _generated_skill_impl({"target_path": fixture_path})
        
        # Si pypdf está instalado, debería funcionar. Si no, saltar.
        if skill_result["status"] == "missing_dependency":
            pytest.skip("pypdf not installed")

        if skill_result["status"] == "error":
            pytest.fail(f"PDF reader failed on sample.pdf: {skill_result.get('response_text')}")
            
        # El resultado debe contener file_ref sanitizado, no la ruta completa
        assert "file_ref" in skill_result["metadata"]
        assert skill_result["metadata"]["file_ref"] == sanitize_path_for_logs(fixture_path)
        assert fixture_path not in skill_result["response_text"]
    except Exception as exc:
        raise exc
