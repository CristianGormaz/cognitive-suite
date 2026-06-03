import pytest
from unittest.mock import MagicMock, AsyncMock
from cognition.dream_mode import DreamMode

def test_dream_focus_rotation():
    dream = DreamMode(AsyncMock(), MagicMock(), MagicMock(), MagicMock())
    
    f1 = dream.select_next_dream_focus(None)
    assert f1 == "quorum_readiness"
    
    f2 = dream.select_next_dream_focus(f1)
    assert f2 == "unknown_failure_classification"
    
    f3 = dream.select_next_dream_focus(f2)
    assert f3 == "evolution_queue_hygiene"
    
    # Test wrap around
    last = "ledger_cache_efficiency"
    first = dream.select_next_dream_focus(last)
    assert first == "quorum_readiness"
