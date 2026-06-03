import pytest
import time
from unittest.mock import MagicMock
from cognition.immune_heatmap import ImmuneHeatmapEngine

def test_heatmap_distinguishes_historical_unknown(tmp_path):
    engine = ImmuneHeatmapEngine(memory_dir=str(tmp_path))
    engine.state_resolver = MagicMock()
    
    # Mock state resolver to return historical debt for unknown_failure
    class FakeState:
        canonical_status = "historical_debt"
    
    engine.state_resolver.resolve_failure_family_state.return_value = FakeState()
    
    # Create some events
    now = time.time()
    events = [
        {"failure_type": "unknown_failure", "timestamp": now - 100000, "event_id": "1"}, # very old
        {"failure_type": "unknown_failure", "timestamp": now - 100000, "event_id": "2"}
    ]
    
    report = engine.build_failure_family_heatmap(events, now)
    
    # Should say historical_debt in focus if it is top
    assert report.dominant_historical_hotspots[0] == "unknown_failure"
    assert "Monitorear unknown_failure (deuda histórica)" in report.recommended_focus
