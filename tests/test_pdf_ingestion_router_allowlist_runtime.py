import pytest
import os
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, AsyncMock
from cognition.ingestion_router import IngestionRouter
from core.task_envelope import TaskEnvelope
from main import MainOrchestrator
from cognition.llm_planner import CognitivePlan, CognitiveDecision, IafaFrictionEstimates, CognitiveExecutionPayload

@pytest.fixture
def mock_orchestrator():
    router = IngestionRouter()
    planner = AsyncMock()
    dispatcher = AsyncMock()
    cognitive = AsyncMock()
    genesis = AsyncMock()
    loader = AsyncMock()
    auditor = MagicMock()
    
    # Mocking planner response
    plan = CognitivePlan(
        task_id="task_pdf",
        thought_trace="thinking",
        raw_response_sha256="abc",
        decision=CognitiveDecision(
            intent_category="pdf_analysis",
            proposed_action="pdf_reader_basic",
            iafa_friction_estimates=IafaFrictionEstimates(R=0.1, I=0.1, N=0.1),
            execution_payload=CognitiveExecutionPayload(target_path="n/a", extracted_tags=())
        )
    )
    planner.plan.return_value = plan
    
    # Mocking dispatcher response
    from core.action_dispatcher import DispatchResult
    dispatcher.dispatch.return_value = DispatchResult(
        status="executed",
        ui_state="action_executed",
        iafa_score=0.9,
        threshold=0.7,
        action="pdf_reader_basic",
        task_id="task_pdf",
        details={"dynamic_routing": True}
    )
    
    orchestrator = MainOrchestrator(router, planner, dispatcher, cognitive, genesis, loader, auditor)
    return orchestrator

@pytest.mark.asyncio
async def test_pdf_execution_when_allowlisted(mock_orchestrator):
    with pytest.MonkeyPatch().context() as mp:
        mp.setenv("GREYS_EXPERIMENTAL_SKILLS_ENABLED", "1")
        mp.setenv("GREYS_EXPERIMENTAL_SKILL_ALLOWLIST", "pdf_reader_basic")
        
        # Necesitamos un archivo real porque el skill_pdf_reader_basic hace os.path.getsize
        with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as tmp:
            tmp.write(b"%PDF-1.4 test")
            tmp_path = tmp.name
            
        try:
            envelope = await mock_orchestrator.ingestion_router.route_path(tmp_path)
            
            # Mock skill result
            mock_orchestrator.skill_loader.execute_skill.return_value = {
                "status": "success",
                "response_text": "Se extrajeron 10 caracteres"
            }
            
            result = await mock_orchestrator.process_envelope(envelope)
            
            assert result.stage == "dispatch_complete"
            assert "Se extrajeron 10 caracteres" in result.details["response_text"]
            
            # Verificar que se llamó al loader con subfolder="experimental"
            mock_orchestrator.skill_loader.execute_skill.assert_called_once()
            args, kwargs = mock_orchestrator.skill_loader.execute_skill.call_args
            assert args[0] == "pdf_reader_basic"
            assert kwargs["subfolder"] == "experimental"
            
        finally:
            if os.path.exists(tmp_path):
                os.remove(tmp_path)
