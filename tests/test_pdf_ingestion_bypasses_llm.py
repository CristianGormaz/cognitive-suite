import pytest
import os
import tempfile
from unittest.mock import MagicMock, AsyncMock
from cognition.ingestion_router import IngestionRouter
from core.task_envelope import TaskEnvelope
from main import MainOrchestrator

@pytest.fixture
def mock_orchestrator():
    router = IngestionRouter()
    planner = AsyncMock() # Mock planner to detect calls
    dispatcher = AsyncMock()
    cognitive = AsyncMock()
    genesis = AsyncMock()
    loader = AsyncMock()
    auditor = MagicMock()
    
    # El dispatcher debe autorizar la acción respond o pdf_reader_basic
    from core.action_dispatcher import DispatchResult
    async def fake_dispatch(plan):
        return DispatchResult(
            status="executed",
            ui_state="action_executed",
            iafa_score=0.95,
            threshold=0.7,
            action=plan.decision.proposed_action,
            task_id=plan.task_id,
            details={"receipt": {"ok": True}} if plan.decision.proposed_action == "respond" else {"dynamic_routing": True}
        )
    dispatcher.dispatch.side_effect = fake_dispatch
    
    orchestrator = MainOrchestrator(router, planner, dispatcher, cognitive, genesis, loader, auditor)
    return orchestrator

@pytest.mark.asyncio
async def test_pdf_ingestion_without_allowlist_bypasses_llm(mock_orchestrator):
    with pytest.MonkeyPatch().context() as mp:
        mp.setenv("GREYS_EXPERIMENTAL_SKILLS_ENABLED", "1")
        mp.setenv("GREYS_EXPERIMENTAL_SKILL_ALLOWLIST", "") # Empty
        
        pdf_bytes = b"%PDF-1.4 test"
        envelope = await mock_orchestrator.ingestion_router.route_file_bytes(pdf_bytes, "test.pdf")
        
        result = await mock_orchestrator.process_envelope(envelope)
        
        # Debe haber procesado localmente
        assert result.status == "executed"
        assert "no está autorizado en tu lista de permisos" in result.details["response_text"]
        
        # VERIFICACIÓN CRÍTICA: El planificador NO debe haber sido llamado
        assert mock_orchestrator.planner.plan.call_count == 0

@pytest.mark.asyncio
async def test_pdf_ingestion_with_allowlist_bypasses_llm(mock_orchestrator):
    with pytest.MonkeyPatch().context() as mp:
        mp.setenv("GREYS_EXPERIMENTAL_SKILLS_ENABLED", "1")
        mp.setenv("GREYS_EXPERIMENTAL_SKILL_ALLOWLIST", "pdf_reader_basic")
        
        # Necesitamos un path real para la metadata
        with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as tmp:
            tmp.write(b"%PDF-1.4 test")
            tmp_path = tmp.name
            
        try:
            envelope = await mock_orchestrator.ingestion_router.route_path(tmp_path)
            
            # Mock skill result
            mock_orchestrator.skill_loader.execute_skill.return_value = {
                "status": "success",
                "response_text": "Extraído localmente"
            }
            
            result = await mock_orchestrator.process_envelope(envelope)
            
            assert result.status == "executed"
            assert "Extraído localmente" in result.details["response_text"]
            
            # VERIFICACIÓN CRÍTICA: El planificador NO debe haber sido llamado
            assert mock_orchestrator.planner.plan.call_count == 0
            
        finally:
            if os.path.exists(tmp_path):
                os.remove(tmp_path)
