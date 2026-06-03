import pytest
from unittest.mock import MagicMock, AsyncMock
from core.task_envelope import TaskEnvelope
from main import MainOrchestrator

@pytest.mark.asyncio
async def test_live_classification_missing_task_id():
    # Setup orchestrator with mocks
    m = MagicMock()
    # We only need the ones used by _error_result
    m.stress_guard.get_stress_snapshot.return_value = {"is_mem_stressed": False, "is_cpu_stressed": False}
    
    # Simulate a TaskEnvelope with missing task_id
    envelope = TaskEnvelope.from_text("test")
    # Manually break it
    object.__setattr__(envelope, "task_id", None)
    
    orchestrator = MainOrchestrator(MagicMock(), MagicMock(), MagicMock(), MagicMock(), MagicMock(), MagicMock(), MagicMock())
    orchestrator.failure_ledger = MagicMock()
    
    # Trigger process_envelope which will fail contract validation
    res = await orchestrator.process_envelope(envelope)
    
    assert res.status == "error"
    # Check that failure_ledger.append_failure was called with process_envelope_missing_task_id
    # Wait, it's called inside _register_ingestion_failure
    args, _ = orchestrator.failure_ledger.append_failure.call_args
    event = args[0]
    assert event.failure_type == "process_envelope_missing_task_id"

@pytest.mark.asyncio
async def test_live_classification_planner_contract_error():
    orchestrator = MainOrchestrator(MagicMock(), MagicMock(), MagicMock(), MagicMock(), MagicMock(), MagicMock(), MagicMock())
    orchestrator.planner = AsyncMock()
    orchestrator.planner.plan.return_value = MagicMock(decision=None) # Break contract
    orchestrator.failure_ledger = MagicMock()
    
    envelope = TaskEnvelope.from_text("test")
    res = await orchestrator.process_envelope(envelope)
    
    assert res.status == "error"
    args, _ = orchestrator.failure_ledger.append_failure.call_args
    event = args[0]
    assert event.failure_type == "process_envelope_planner_result_invalid"
