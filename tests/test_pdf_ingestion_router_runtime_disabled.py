import pytest
import os
from unittest.mock import MagicMock, AsyncMock
from cognition.ingestion_router import IngestionRouter
from core.task_envelope import TaskEnvelope
from main import MainOrchestrator

@pytest.fixture
def mock_orchestrator():
    # Mocking basic dependencies
    router = IngestionRouter()
    planner = MagicMock()
    dispatcher = AsyncMock()
    cognitive = MagicMock()
    genesis = MagicMock()
    loader = MagicMock()
    auditor = MagicMock()
    
    from core.action_dispatcher import DispatchResult
    dispatcher.dispatch.return_value = DispatchResult(
        status="executed",
        ui_state="action_executed",
        iafa_score=0.95,
        threshold=0.7,
        action="respond",
        task_id="task_1",
        details={"receipt": {"ok": True}}
    )
    
    orchestrator = MainOrchestrator(router, planner, dispatcher, cognitive, genesis, loader, auditor)
    return orchestrator

@pytest.mark.asyncio
async def test_pdf_runtime_disabled_globally(mock_orchestrator):
    # Asegurar que experimental esté desactivado
    with pytest.MonkeyPatch().context() as mp:
        mp.setenv("GREYS_EXPERIMENTAL_SKILLS_ENABLED", "0")
        
        pdf_bytes = b"%PDF-1.4 test"
        envelope = await mock_orchestrator.ingestion_router.route_file_bytes(pdf_bytes, "test.pdf")
        
        result = await mock_orchestrator.process_envelope(envelope)
        
        assert result.status == "executed"
        assert "desactivado por configuración global" in result.details["response_text"]
        # No se debió llamar al planificador
        assert not mock_orchestrator.planner.plan.called

@pytest.mark.asyncio
async def test_pdf_runtime_not_allowlisted(mock_orchestrator):
    with pytest.MonkeyPatch().context() as mp:
        mp.setenv("GREYS_EXPERIMENTAL_SKILLS_ENABLED", "1")
        mp.setenv("GREYS_EXPERIMENTAL_SKILL_ALLOWLIST", "other_skill") # No pdf_reader_basic
        
        pdf_bytes = b"%PDF-1.4 test"
        envelope = await mock_orchestrator.ingestion_router.route_file_bytes(pdf_bytes, "test.pdf")
        
        result = await mock_orchestrator.process_envelope(envelope)
        
        assert result.status == "executed"
        assert "no está autorizado en tu lista de permisos" in result.details["response_text"]
