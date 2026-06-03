import pytest
from unittest.mock import MagicMock, patch, AsyncMock
from main import MainOrchestrator
from core.task_envelope import TaskEnvelope
from core.action_dispatcher import DispatchResult
from core.cognitive_loop import CognitiveLoopResult
from cognition.iafa_transceiver import IafaTransceiver
from cognition.genesis_sandbox import GenesisSandbox
from core.iafa_auditor import IafaAuditor
from cognition.genesis_engine import GenesisEngine

@pytest.mark.asyncio
async def test_ledger_records_sandbox_analysis():
    # Setup mocks
    mock_router = MagicMock()
    mock_planner = MagicMock()
    mock_dispatcher = MagicMock()
    mock_cog = MagicMock()
    
    mock_transceiver = MagicMock(spec=IafaTransceiver)
    mock_sandbox = MagicMock(spec=GenesisSandbox)
    mock_auditor = MagicMock(spec=IafaAuditor)
    
    # Mock genesis_analysis
    mock_analysis = MagicMock()
    mock_analysis.analyze_missing_capability = AsyncMock()
    mock_analysis.analyze_missing_capability.return_value = MagicMock(
        sandbox_status=True, 
        to_dict=lambda: {"mock": "analysis"}, 
        recommendation="ok"
    )
    
    with patch("cognition.genesis_engine.IafaTransceiver", IafaTransceiver), \
         patch("cognition.genesis_engine.GenesisSandbox", GenesisSandbox), \
         patch("cognition.genesis_engine.IafaAuditor", IafaAuditor):
         
        mock_genesis = MagicMock(spec=GenesisEngine)
        mock_loader = MagicMock()
        
        orchestrator = MainOrchestrator(
            mock_router, mock_planner, mock_dispatcher, mock_cog, mock_genesis, mock_loader, mock_auditor,
            genesis_analysis=mock_analysis
        )
        
        # MOCK LEDGERS AFTER INIT
        orchestrator.tension_ledger = MagicMock()
        orchestrator.failure_ledger = MagicMock()
        orchestrator.stress_guard = MagicMock()
        orchestrator.stress_guard.get_stress_snapshot.return_value = {
            "is_mem_stressed": False, "is_cpu_stressed": False, "load_1m": 0.1, "mem_available_mb": 1000
        }
        
        envelope = TaskEnvelope.from_text("integrate x^2")
        plan = MagicMock()
        plan.to_dict.return_value = {"intent": "math"}
        dispatch_result = DispatchResult("fail", "evolutionary_doubt", 0.5, 0.7, "respond", "t1", {})
        
        fallback_result = CognitiveLoopResult("sandbox_code", "genesis_sandbox_routing", "t1", {})
        
        await orchestrator._handle_fallback_selection(envelope, plan, dispatch_result, fallback_result)
        
        # Verificar registro en ledger
        orchestrator.tension_ledger.mark_user_outcome.assert_called_with(envelope.task_id, "sandbox_code")
        
        # Verificar que se registró el evento de análisis específico
        orchestrator.tension_ledger.append_event.assert_called()
        analysis_events = [
            args[0] for args, _ in orchestrator.tension_ledger.append_event.call_args_list 
            if args[0].event_type == "genesis_sandbox_analysis"
        ]
        assert len(analysis_events) > 0
