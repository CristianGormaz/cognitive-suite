import asyncio
import pytest
from unittest.mock import MagicMock, patch, AsyncMock
from cognition.spark_engine import SparkEngine, SparkProposal
from core.ingestion_failure_ledger import IngestionFailureLedger
from core.semantic_tension_ledger import SemanticTensionLedger
from core.system_stress_guard import SystemStressGuard

@pytest.mark.asyncio
async def test_spark_proposes_skill_on_repeated_failures():
    # Setup mocks
    mock_failure_ledger = MagicMock(spec=IngestionFailureLedger)
    # Simulamos 3 fallos de una capacidad
    mock_failure_ledger.get_top_missing_capabilities.return_value = [("pdf_reader:extract", 3)]
    
    mock_tension_ledger = MagicMock(spec=SemanticTensionLedger)
    mock_tension_ledger.should_suppress_proposal.return_value = False
    
    mock_guard = MagicMock(spec=SystemStressGuard)
    mock_guard.is_host_under_stress.return_value = False
    mock_guard.get_stress_snapshot.return_value = {
        "is_mem_stressed": False, "is_cpu_stressed": False, "load_1m": 0.1, "mem_available_mb": 8000
    }
    
    mock_orchestrator = MagicMock()
    mock_orchestrator.handle_evolutionary_doubt = AsyncMock()
    
    spark = SparkEngine(
        enabled=True,
        stress_guard=mock_guard,
        tension_ledger=mock_tension_ledger,
        failure_ledger=mock_failure_ledger,
        orchestrator=mock_orchestrator
    )
    spark.idle_probe = MagicMock(return_value=True)
    
    # Executing pulse
    await spark.pulse()
    
    # Verificamos que propuso la capacidad faltante
    mock_orchestrator.handle_evolutionary_doubt.assert_called_once()
    args, _ = mock_orchestrator.handle_evolutionary_doubt.call_args
    payload = args[0]
    assert payload["missing_capability"] == "pdf_reader:extract"
    assert payload["failure_count"] == 3
    assert payload["proposal"]["suggested_intent"] == "missing_capability_evolution"

@pytest.mark.asyncio
async def test_spark_skips_skill_proposal_if_suppressed():
    mock_failure_ledger = MagicMock(spec=IngestionFailureLedger)
    mock_failure_ledger.get_top_missing_capabilities.return_value = [("annoying:intent", 5)]
    
    mock_tension_ledger = MagicMock(spec=SemanticTensionLedger)
    # Propuesta suprimida por fatiga cognitiva
    mock_tension_ledger.should_suppress_proposal.return_value = True
    
    mock_guard = MagicMock(spec=SystemStressGuard)
    mock_guard.is_host_under_stress.return_value = False
    
    mock_orchestrator = MagicMock()
    
    spark = SparkEngine(
        enabled=True,
        stress_guard=mock_guard,
        tension_ledger=mock_tension_ledger,
        failure_ledger=mock_failure_ledger,
        orchestrator=mock_orchestrator
    )
    spark.idle_probe = MagicMock(return_value=True)
    
    with patch.object(spark, "_ask_planner") as mock_ask:
        await spark.pulse()
        # No debería proponer la capacidad faltante por estar suprimida
        # Debería continuar con el flujo normal de señales (si las hubiera)
        mock_orchestrator.handle_evolutionary_doubt.assert_not_called()
