import pytest
import asyncio
from unittest.mock import MagicMock, patch
from main import MainOrchestrator

@pytest.mark.asyncio
async def test_main_orchestrator_registers_failure_on_timeout():
    # Setup mocks
    mock_router = MagicMock()
    mock_planner = MagicMock()
    mock_dispatcher = MagicMock()
    mock_cog = MagicMock()
    mock_genesis = MagicMock()
    mock_loader = MagicMock()
    mock_auditor = MagicMock()
    
    orchestrator = MainOrchestrator(
        mock_router, mock_planner, mock_dispatcher, mock_cog, mock_genesis, mock_loader, mock_auditor
    )
    
    # Mock failure_ledger
    orchestrator.failure_ledger = MagicMock()
    orchestrator.tension_ledger = MagicMock()
    orchestrator.stress_guard = MagicMock()
    orchestrator.stress_guard.get_stress_snapshot.return_value = {
        "is_mem_stressed": False, "is_cpu_stressed": False, "load_1m": 0.5, "mem_available_mb": 4000
    }
    
    # Simulate a timeout error
    exc = RuntimeError("Ollama no respondió")
    result = orchestrator._error_result("process_input", "hola", exc)
    
    assert result.status == "error"
    # Verificamos que se llamó al ledger de fallos
    orchestrator.failure_ledger.append_failure.assert_called_once()
    args, _ = orchestrator.failure_ledger.append_failure.call_args
    event = args[0]
    assert event.failure_type == "llm_timeout"
    assert "Ollama no respondió" in event.error_summary
