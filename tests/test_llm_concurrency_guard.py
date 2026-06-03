import asyncio
import pytest
from unittest.mock import MagicMock, patch
from cognition.iafa_transceiver import IafaTransceiver, LlmHostStressedError
from core.task_envelope import TaskEnvelope
from core.system_stress_guard import SystemStressGuard

@pytest.mark.asyncio
async def test_transceiver_semaphore_serialization():
    # Mock stress guard to always say NOT stressed
    mock_guard = MagicMock(spec=SystemStressGuard)
    mock_guard.is_host_under_stress.return_value = False
    
    transceiver = IafaTransceiver(stress_guard=mock_guard)
    envelope = TaskEnvelope.from_text("test")
    
    call_count = 0
    async def mock_safe_request(endpoint, payload):
        nonlocal call_count
        call_count += 1
        await asyncio.sleep(0.1)  # Simulate some latency
        return {"response": f"ok {call_count}"}

    with patch.object(transceiver, "_safe_request", side_effect=mock_safe_request):
        # Lanza dos consultas al mismo tiempo
        task1 = asyncio.create_task(transceiver.query_llm(envelope))
        task2 = asyncio.create_task(transceiver.query_llm(envelope))
        
        results = await asyncio.gather(task1, task2)
        
        # Ambos deberían terminar bien pero uno tras otro (el semáforo funciona)
        assert "ok 1" in results
        assert "ok 2" in results
        assert call_count == 2

@pytest.mark.asyncio
async def test_transceiver_stress_block():
    # Mock stress guard to always say STRESSED
    mock_guard = MagicMock(spec=SystemStressGuard)
    mock_guard.is_host_under_stress.return_value = True
    
    transceiver = IafaTransceiver(stress_guard=mock_guard)
    envelope = TaskEnvelope.from_text("test")
    
    with pytest.raises(LlmHostStressedError, match="System host is under stress"):
        await transceiver.query_llm(envelope)

@pytest.mark.asyncio
async def test_spark_engine_stress_skip():
    from cognition.spark_engine import SparkEngine
    
    mock_guard = MagicMock(spec=SystemStressGuard)
    mock_guard.is_host_under_stress.return_value = True
    
    spark = SparkEngine(enabled=True, stress_guard=mock_guard)
    
    # Mock idle_probe to return True
    spark.idle_probe = MagicMock(return_value=True)
    
    with patch.object(spark, "_collect_signals") as mock_collect:
        await spark.pulse()
        # No debería recolectar señales porque el host está bajo estrés
        mock_collect.assert_not_called()
