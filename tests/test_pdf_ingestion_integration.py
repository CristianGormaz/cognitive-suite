import pytest
import os
import asyncio
from pathlib import Path
from main import MainOrchestrator

@pytest.mark.asyncio
async def test_pdf_ingestion_full_flow_success(tmp_path):
    pdf_path = Path("tests/fixtures/ingestion/sample.pdf")
    if not pdf_path.exists():
        pytest.skip("sample.pdf fixture not found")
        
    # Enable experimental PDF reader
    os.environ["GREYS_EXPERIMENTAL_SKILLS_ENABLED"] = "1"
    os.environ["GREYS_EXPERIMENTAL_SKILL_ALLOWLIST"] = "pdf_reader_basic"
    os.environ["GREYS_PLANNER_FAST_MODE"] = "1"
    
    try:
        orchestrator = await MainOrchestrator.create_default()
        
        # Mock planner to always return pdf_reader action for PDF mime type
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
            iafa_friction_estimates=IafaFrictionEstimates(R=0.1, I=0.1, N=0.1),
            execution_payload=CognitiveExecutionPayload(target_path=str(pdf_path), extracted_tags=())
        )
        
        mock_plan = CognitivePlan(
            task_id="test_pdf",
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
            task_id="test_pdf",
            details={"iafa_context": {}}
        ))
        
        envelope = await orchestrator.ingestion_router.route_path(str(pdf_path))
        print(f"DEBUG: envelope metadata: {envelope.metadata}")
        result = await orchestrator.process_envelope(envelope)
        
        assert result.status == "executed"
        assert "Se extrajeron" in result.details["response_text"]
        assert result.details["skill_result"]["status"] == "success"
        
    finally:
        del os.environ["GREYS_EXPERIMENTAL_SKILLS_ENABLED"]
        del os.environ["GREYS_EXPERIMENTAL_SKILL_ALLOWLIST"]
        del os.environ["GREYS_PLANNER_FAST_MODE"]

from unittest.mock import AsyncMock, MagicMock
