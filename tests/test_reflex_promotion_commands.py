import pytest
import os
from unittest.mock import MagicMock, AsyncMock, patch
from main import MainOrchestrator
from core.task_envelope import TaskEnvelope

@pytest.fixture
def mock_orchestrator(tmp_path):
    memory_dir = tmp_path / "memory"
    memory_dir.mkdir()
    
    router = AsyncMock()
    planner = AsyncMock()
    dispatcher = AsyncMock()
    cognitive = AsyncMock()
    genesis = AsyncMock()
    loader = AsyncMock()
    auditor = MagicMock()
    
    orchestrator = MainOrchestrator(
        router, planner, dispatcher, cognitive, genesis, loader, auditor
    )
    # Re-inyectar con memoria temporal para el gate
    from core.reflex_promotion_gate import ReflexPromotionGate
    orchestrator.reflex_promotion_gate = ReflexPromotionGate(memory_dir=str(memory_dir))
    return orchestrator

@pytest.mark.asyncio
async def test_reflex_approve_command(mock_orchestrator):
    # Simular entrada de comando
    with patch("sys.stdin.readline", side_effect=["/reflex-approve p1 approved_by_test\n", "/quit\n"]):
        with patch("builtins.print") as mock_print:
            await mock_orchestrator.run_interactive()
            
            # Verificar que se imprimió el mensaje de éxito
            mock_print.assert_any_call("[Sistema]: Reflejo p1 APROBADO y ACTIVADO para ruteo local.")
            
            # Verificar que el patrón está activo
            assert "p1" in mock_orchestrator.reflex_promotion_gate.get_active_reflexes()

@pytest.mark.asyncio
async def test_reflex_disable_command(mock_orchestrator):
    # Primero aprobar
    mock_orchestrator.reflex_promotion_gate.approve_promotion("p1", "initial")
    
    # Luego desactivar vía comando
    with patch("sys.stdin.readline", side_effect=["/reflex-disable p1 reason\n", "/quit\n"]):
        with patch("builtins.print") as mock_print:
            await mock_orchestrator.run_interactive()
            
            mock_print.assert_any_call("[Sistema]: Reflejo p1 DESACTIVADO.")
            assert "p1" not in mock_orchestrator.reflex_promotion_gate.get_active_reflexes()
