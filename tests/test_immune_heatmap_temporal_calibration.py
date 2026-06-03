import pytest
import time
from cognition.immune_heatmap import ImmuneHeatmapEngine

@pytest.fixture
def engine(tmp_path):
    return ImmuneHeatmapEngine(memory_dir=str(tmp_path))

def test_heatmap_distinguishes_recent_vs_historical(engine):
    now = time.time()
    # 2 days ago (Historical)
    old_ts = now - (2 * 24 * 3600)
    # 1 hour ago (Recent)
    new_ts = now - 3600
    
    events = [
        {"failure_type": "old_error", "timestamp": old_ts},
        {"failure_type": "old_error", "timestamp": old_ts},
        {"failure_type": "new_error", "timestamp": new_ts}
    ]
    
    report = engine.build_failure_family_heatmap(events, now)
    
    # Historical hotspot should be old_error
    assert "old_error" in report.dominant_historical_hotspots
    # Recent hotspot should be new_error (because it's the only one in the last 24h)
    assert "new_error" in report.dominant_recent_hotspots
    assert "old_error" not in report.dominant_recent_hotspots

def test_trend_detection_rising(engine):
    now = time.time()
    old_ts = now - (2 * 24 * 3600)
    new_ts = now - 3600
    
    # old_error was frequent, but new_error is emergent
    events = [
        {"failure_type": "old_error", "timestamp": old_ts},
        {"failure_type": "old_error", "timestamp": old_ts},
        {"failure_type": "old_error", "timestamp": old_ts},
        {"failure_type": "new_error", "timestamp": new_ts}
    ]
    
    report = engine.build_failure_family_heatmap(events, now)
    
    new_cell = next(c for c in report.cells if c.axis_x == "new_error")
    # Historical intensity for new_error: 1/3 (max is old_error with 3) -> 0.33
    # Recent intensity for new_error: 1/1 (max is new_error with 1) -> 1.0
    # Delta: 0.66 -> Rising
    assert "rising" in new_cell.trend_label
    assert "Priorizar" in report.recommended_focus

def test_trend_detection_falling(engine):
    now = time.time()
    old_ts = now - (2 * 24 * 3600)
    new_ts = now - 3600
    
    # old_error was frequent, and now it's gone
    events = [
        {"failure_type": "old_error", "timestamp": old_ts} for _ in range(10)
    ]
    events.append({"failure_type": "other_error", "timestamp": new_ts})
    
    report = engine.build_failure_family_heatmap(events, now)
    
    old_cell = next(c for c in report.cells if c.axis_x == "old_error")
    assert "falling" in old_cell.trend_label
