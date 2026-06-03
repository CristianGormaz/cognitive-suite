import asyncio
import pytest
from unittest.mock import MagicMock, patch
from cognition.spark_engine import SparkEngine
from core.system_stress_guard import SystemStressGuard

@pytest.mark.asyncio
async def test_spark_observability_logs(caplog):
    import logging
    caplog.set_level(logging.DEBUG)
    
    mock_guard = MagicMock(spec=SystemStressGuard)
    mock_guard.is_host_under_stress.return_value = False
    
    spark = SparkEngine(
        enabled=True,
        stress_guard=mock_guard,
        pulse_interval_seconds=1,
        cooldown_seconds=0
    )
    
    # Mock idle_probe to return True
    spark.idle_probe = MagicMock(return_value=True)
    
    # Mock components to avoid real calls
    with patch.object(spark, "_collect_signals", return_value=[]):
        await spark.pulse()
        
    assert "SparkEngine pulse tick" in caplog.text
    assert "SparkEngine system idle: True" in caplog.text
    assert "SparkEngine host under stress: False" in caplog.text
    assert "SparkEngine signals collected: 0" in caplog.text

@pytest.mark.asyncio
async def test_spark_skipped_logs(caplog):
    import logging
    caplog.set_level(logging.DEBUG)
    
    mock_guard = MagicMock(spec=SystemStressGuard)
    mock_guard.is_host_under_stress.return_value = True
    
    spark = SparkEngine(
        enabled=True,
        stress_guard=mock_guard
    )
    
    spark.idle_probe = MagicMock(return_value=True)
    
    await spark.pulse()
    
    assert "SparkEngine pulse skipped: Host is under stress." in caplog.text

@pytest.mark.asyncio
async def test_spark_cooldown_logs(caplog):
    import logging
    caplog.set_level(logging.DEBUG)
    
    mock_guard = MagicMock(spec=SystemStressGuard)
    mock_guard.is_host_under_stress.return_value = False
    
    spark = SparkEngine(
        enabled=True,
        stress_guard=mock_guard,
        cooldown_seconds=3600
    )
    spark.idle_probe = MagicMock(return_value=True)
    spark._last_proposal_time = 1234567890.0 # Way in the past but cooldown is 1h
    
    # We set last_proposal_time to just now
    import time
    spark._last_proposal_time = time.time() - 10
    
    await spark.pulse()
    
    assert "SparkEngine pulse skipped: Cooldown active" in caplog.text
