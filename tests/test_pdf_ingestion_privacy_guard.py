import pytest
import os
from pathlib import Path
from main import MainOrchestrator
from unittest.mock import AsyncMock

@pytest.mark.asyncio
async def test_pdf_ingestion_privacy_guard(tmp_path):
    pdf_path = Path("tests/fixtures/ingestion/sample.pdf")
    if not pdf_path.exists():
        pytest.skip("sample.pdf fixture not found")
        
    os.environ["GREYS_EXPERIMENTAL_SKILLS_ENABLED"] = "1"
    os.environ["GREYS_EXPERIMENTAL_SKILL_ALLOWLIST"] = "pdf_reader_basic"
    
    try:
        orchestrator = await MainOrchestrator.create_default()
        
        from cognition.llm_planner import (
            CognitivePlan, 
            CognitiveDecision, 
            IafaFrictionEstimates, 
            CognitiveExecutionPayload
        )
        from core.action_dispatcher import DispatchResult
        
        mock_decision = CognitiveDecision(
            intent_category="file_processing",
            proposed_action="pdf_reader_basic",
            iafa_friction_estimates=IafaFrictionEstimates(R=0.3, I=0.4, N=0.2),
            execution_payload=CognitiveExecutionPayload(target_path=str(pdf_path), extracted_tags=())
        )
        
        mock_plan = CognitivePlan(
            task_id="test_privacy",
            decision=mock_decision,
            thought_trace="mocked",
            raw_response_sha256="hash",
            planner_version="v1"
        )
        orchestrator.planner.plan = AsyncMock(return_value=mock_plan)
        
        # Mock dispatcher to return success and avoid fallback/UI
        orchestrator.dispatcher.dispatch = AsyncMock(return_value=DispatchResult(
            status="executed",
            ui_state="action_executed",
            iafa_score=1.0,
            threshold=0.7,
            action="pdf_reader_basic",
            task_id="test_privacy",
            details={"iafa_context": {}}
        ))
        
        envelope = await orchestrator.ingestion_router.route_path(str(pdf_path))
        result = await orchestrator.process_envelope(envelope)
        
        # Verify privacy: no absolute paths in response_text or details
        res_text = result.details.get("response_text", "")
        assert str(pdf_path.parent) not in res_text
        # Note: os.path.basename(target_path) IS allowed in current skill impl, but not full path
        
        metadata = result.details["skill_result"]["metadata"]
        assert metadata["metadata_redacted"] is True
        assert "file_ref" in metadata
        assert str(pdf_path.parent) not in metadata["file_ref"]
        
    finally:
        del os.environ["GREYS_EXPERIMENTAL_SKILLS_ENABLED"]
        del os.environ["GREYS_EXPERIMENTAL_SKILL_ALLOWLIST"]
