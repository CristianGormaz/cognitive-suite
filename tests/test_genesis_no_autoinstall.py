import pytest
from unittest.mock import MagicMock, patch, AsyncMock
from main import MainOrchestrator
from core.action_dispatcher import DispatchResult
from core.cognitive_loop import CognitiveLoopResult
from core.task_envelope import TaskEnvelope
from cognition.iafa_transceiver import IafaTransceiver
from cognition.genesis_sandbox import GenesisSandbox
from core.iafa_auditor import IafaAuditor
from cognition.genesis_engine import GenesisEngine

@pytest.mark.asyncio
async def test_sandbox_code_does_not_call_loader():
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
        to_dict=lambda: {}, 
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
        
        envelope = TaskEnvelope.from_text("test")
        plan = MagicMock()
        dispatch_result = DispatchResult("fail", "evolutionary_doubt", 0.5, 0.7, "respond", "t1", {})
        
        # Usuario elige 'sandbox_code'
        fallback_result = CognitiveLoopResult("sandbox_code", "genesis_sandbox_routing", "t1", {})
        
        await orchestrator._handle_fallback_selection(envelope, plan, dispatch_result, fallback_result)
        
        # VERIFICACIÓN CRÍTICA
        # 1. Se llamó al análisis
        orchestrator.genesis_analysis.analyze_missing_capability.assert_called_once()
        
        # 2. NO se llamó al motor de instalación real
        mock_genesis.synthesize_and_install_skill.assert_not_called()
        
        # 3. NO se llamó al cargador de habilidades (DynamicSkillLoader)
        mock_loader.execute_skill.assert_not_called()
