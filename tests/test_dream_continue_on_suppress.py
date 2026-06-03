import os
import pytest
from unittest.mock import MagicMock, AsyncMock
from cognition.dream_mode import DreamMode, DreamCycleResult

@pytest.mark.asyncio
async def test_dream_continues_on_suppress_if_enabled():
    # Setup mocks
    transceiver = AsyncMock()
    tension_ledger = MagicMock()
    failure_ledger = MagicMock()
    stress_guard = MagicMock()
    stress_guard.is_host_under_stress.return_value = False
    stress_guard.get_stress_snapshot.return_value = {}
    
    dream = DreamMode(transceiver, tension_ledger, failure_ledger, stress_guard)
    
    # Mock run_once to return suppress
    dream.run_once = AsyncMock()
    dream.run_once.return_value = DreamCycleResult(
        event_id="test", timestamp=0, cycle=1, summary_of_failures={},
        top_missing_capabilities=[], top_tension_sources=[], host_stress_snapshot={},
        depth_level=1, question_type="test", semantic_signature="sig",
        repetition_count=3, next_action="suppress"
    )
    
    # Enable continue on suppress
    os.environ["GREYS_DREAM_CONTINUE_ON_SUPPRESS"] = "1"
    os.environ["GREYS_DREAM_MODE_ENABLED"] = "1"
    os.environ["GREYS_DREAM_SUPPRESS_SLEEP_SECONDS"] = "0"
    
    try:
        # Run 2 cycles
        await dream.run_session(max_cycles=2, sleep_seconds=0)
        
        # Check that run_once was called twice despite suppression
        assert dream.run_once.call_count == 2
    finally:
        os.environ.pop("GREYS_DREAM_CONTINUE_ON_SUPPRESS", None)
        os.environ.pop("GREYS_DREAM_MODE_ENABLED", None)

@pytest.mark.asyncio
async def test_dream_stops_on_suppress_if_disabled():
    # Setup mocks
    transceiver = AsyncMock()
    tension_ledger = MagicMock()
    failure_ledger = MagicMock()
    stress_guard = MagicMock()
    stress_guard.is_host_under_stress.return_value = False
    
    dream = DreamMode(transceiver, tension_ledger, failure_ledger, stress_guard)
    dream.run_once = AsyncMock()
    dream.run_once.return_value = DreamCycleResult(
        event_id="test", timestamp=0, cycle=1, summary_of_failures={},
        top_missing_capabilities=[], top_tension_sources=[], host_stress_snapshot={},
        depth_level=1, question_type="test", semantic_signature="sig",
        repetition_count=3, next_action="suppress"
    )
    
    os.environ["GREYS_DREAM_CONTINUE_ON_SUPPRESS"] = "0"
    os.environ["GREYS_DREAM_MODE_ENABLED"] = "1"
    
    try:
        await dream.run_session(max_cycles=2, sleep_seconds=0)
        # Should stop after 1st cycle
        assert dream.run_once.call_count == 1
    finally:
        os.environ.pop("GREYS_DREAM_CONTINUE_ON_SUPPRESS", None)
        os.environ.pop("GREYS_DREAM_MODE_ENABLED", None)
