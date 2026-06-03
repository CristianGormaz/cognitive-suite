import asyncio
import pytest
from unittest.mock import MagicMock, patch
from cognition.spark_engine import SparkEngine, SparkProposal
from core.semantic_tension_ledger import SemanticTensionLedger
from core.system_stress_guard import SystemStressGuard

@pytest.mark.asyncio
async def test_spark_suppresses_high_damage_proposal():
    # Setup
    mock_ledger = MagicMock(spec=SemanticTensionLedger)
    # Simulamos que la propuesta está suprimida por daño acumulado
    mock_ledger.should_suppress_proposal.return_value = True
    
    mock_guard = MagicMock(spec=SystemStressGuard)
    mock_guard.is_host_under_stress.return_value = False
    
    spark = SparkEngine(
        enabled=True,
        stress_guard=mock_guard,
        tension_ledger=mock_ledger
    )
    spark.idle_probe = MagicMock(return_value=True)
    
    # Mock señales y planner
    proposal = SparkProposal("t1", "reason", "annoying_intent", {})
    with patch.object(spark, "_collect_signals", return_value=[MagicMock()]):
        with patch.object(spark, "_ask_planner", return_value=proposal):
            with patch.object(spark, "_emit_evolutionary_doubt") as mock_emit:
                await spark.pulse()
                
                # Debería haber consultado el ledger
                mock_ledger.should_suppress_proposal.assert_called_with("annoying_intent:reflection")
                # NO debería haber emitido la duda
                mock_emit.assert_not_called()

@pytest.mark.asyncio
async def test_spark_emits_when_no_suppression():
    mock_ledger = MagicMock(spec=SemanticTensionLedger)
    mock_ledger.should_suppress_proposal.return_value = False
    
    mock_guard = MagicMock(spec=SystemStressGuard)
    mock_guard.is_host_under_stress.return_value = False
    
    mock_fail = MagicMock()
    mock_fail.get_top_missing_capabilities.return_value = []
    
    spark = SparkEngine(
        enabled=True,
        stress_guard=mock_guard,
        tension_ledger=mock_ledger,
        failure_ledger=mock_fail,
        dry_run=True # Para que IAFA pase si no hay motor real
    )
    spark.idle_probe = MagicMock(return_value=True)
    
    proposal = SparkProposal("t1", "reason", "good_intent", {})
    with patch.object(spark, "_collect_signals", return_value=[MagicMock()]):
        with patch.object(spark, "_ask_planner", return_value=proposal):
            with patch.object(spark, "_emit_evolutionary_doubt") as mock_emit:
                await spark.pulse()
                
                # Debería haber emitido la duda
                mock_emit.assert_called_once()
                # Debería haber registrado el evento
                mock_ledger.append_event.assert_called()
