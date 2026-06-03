import pytest
import os
import json
import time
from pathlib import Path
from cognition.immune_heatmap import ImmuneHeatmapEngine

@pytest.fixture
def mock_heatmap_assets(tmp_path):
    memory_dir = tmp_path / "memory"
    memory_dir.mkdir()
    skills_dir = tmp_path / "src" / "skills"
    (skills_dir / "experimental").mkdir(parents=True)
    
    return memory_dir, skills_dir

def test_dependency_heatmap_respects_canonical_approval(mock_heatmap_assets):
    memory_dir, skills_dir = mock_heatmap_assets
    ledger = memory_dir / "dependency_review_ledger.jsonl"
    
    # Simular pending seguido de approval
    with open(ledger, "w") as f:
        f.write(json.dumps({"dependency_name": "pypdf", "review_status": "pending_human_review", "timestamp": time.time() - 3600, "risk_level": "medium"}) + "\n")
        f.write(json.dumps({"dependency_name": "pypdf", "review_status": "approved_for_installation", "timestamp": time.time(), "risk_level": "medium"}) + "\n")
        
    engine = ImmuneHeatmapEngine(
        memory_dir=str(memory_dir),
        report_ledger_path=str(memory_dir / "heatmap_reports.jsonl"),
        skills_dir=str(skills_dir.parent)
    )
    
    report = engine.build_dependency_friction_heatmap(engine._load_ledger_metadata("dependency_review_ledger.jsonl"), time.time())
    
    # Solo debe haber una celda para pypdf (la canónica)
    assert len(report.cells) == 1
    assert report.cells[0].axis_x == "pypdf"
    assert report.cells[0].trend_label == "stable" # Ya no es needs_review
    assert report.cells[0].historical_intensity < 0.5 # Fricción reducida

def test_failure_heatmap_uses_canonical_status(mock_heatmap_assets):
    memory_dir, skills_dir = mock_heatmap_assets
    ledger = memory_dir / "ingestion_failure_ledger.jsonl"
    
    # Fallo antiguo (hace 2 días)
    with open(ledger, "w") as f:
        f.write(json.dumps({"failure_type": "llm_timeout", "timestamp": time.time() - 172800}) + "\n")
        
    engine = ImmuneHeatmapEngine(
        memory_dir=str(memory_dir),
        report_ledger_path=str(memory_dir / "heatmap_reports.jsonl"),
        skills_dir=str(skills_dir.parent)
    )
    
    report = engine.build_failure_family_heatmap(engine._load_ledger_metadata("ingestion_failure_ledger.jsonl"), time.time())
    
    assert "historical_debt" in report.recommended_focus or "Monitorear" in report.recommended_focus
