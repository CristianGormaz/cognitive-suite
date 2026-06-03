import pytest
import os
import json
import time
from pathlib import Path
from cognition.immune_heatmap import ImmuneHeatmapEngine, ImmuneHeatmapReport

@pytest.fixture
def mock_engine(tmp_path):
    memory_dir = tmp_path / "memory"
    memory_dir.mkdir()
    report_ledger = memory_dir / "immune_heatmap_reports.jsonl"
    return ImmuneHeatmapEngine(memory_dir=str(memory_dir), report_ledger_path=str(report_ledger))

def test_build_failure_family_heatmap(mock_engine):
    now = time.time()
    events = [
        {"failure_type": "llm_timeout", "event_id": "f1", "timestamp": now - 10},
        {"failure_type": "llm_timeout", "event_id": "f2", "timestamp": now - 10},
        {"failure_type": "planner_error", "event_id": "f3", "timestamp": now - 10}
    ]
    report = mock_engine.build_failure_family_heatmap(events, now)
    
    assert report.heatmap_type == "failure_family"
    assert len(report.cells) == 2
    assert report.dominant_historical_hotspots == ["llm_timeout", "planner_error"]
    
    timeout_cell = next(c for c in report.cells if c.axis_x == "llm_timeout")
    assert timeout_cell.count == 2
    assert timeout_cell.historical_intensity == 1.0
    assert timeout_cell.risk_level == "high"

def test_build_module_tension_heatmap(mock_engine):
    now = time.time()
    events = [
        {"source": "LLMPlanner", "event_type": "dispatch", "damage_delta": 0.5, "timestamp": now - 10},
        {"source": "LLMPlanner", "event_type": "dispatch", "damage_delta": 0.5, "timestamp": now - 10},
        {"source": "SparkEngine", "event_type": "evolution", "damage_delta": 0.2, "timestamp": now - 10}
    ]
    report = mock_engine.build_module_tension_heatmap(events, now)
    
    assert report.heatmap_type == "module_tension"
    # Max damage is 1.0 (LLMPlanner), Spark is 0.2
    llm_cell = next(c for c in report.cells if c.axis_x == "LLMPlanner")
    assert llm_cell.value == 1.0
    assert llm_cell.historical_intensity == 1.0
    
    spark_cell = next(c for c in report.cells if c.axis_x == "SparkEngine")
    assert spark_cell.value == 0.2
    assert spark_cell.historical_intensity == 0.2

def test_generate_all_reports_empty(mock_engine):
    reports = mock_engine.generate_all_reports()
    assert len(reports) == 0

def test_persist_and_load_latest(mock_engine):
    events = [{"failure_type": "test"}]
    now = time.time()
    report = mock_engine.build_failure_family_heatmap(events, now)
    mock_engine._persist_report(report)
    
    latest = mock_engine.load_latest_report("failure_family")
    assert latest is not None
    assert latest.event_id == report.event_id
    assert latest.title == report.title
