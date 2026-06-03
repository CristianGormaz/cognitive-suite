import pytest
import json
from pathlib import Path
from cognition.morning_brief import MorningBrief

@pytest.fixture
def mock_assets(tmp_path):
    memory_dir = tmp_path / "memory"
    memory_dir.mkdir()
    skills_dir = tmp_path / "src/skills"
    (skills_dir / "experimental").mkdir(parents=True)
    
    # Patrón destilado
    dist = memory_dir / "distilled_reasoning_ledger.jsonl"
    dist.write_text(json.dumps({
        "pattern_id": "p_active", "pattern_name": "pilot_active", "trigger_signature": "sig",
        "recommended_action": "respond", "confidence": 1.0, "local_rule_summary": "rule",
        "source_refs": [], "target_module": "LocalIntentRouter", "risk_score": 0.05,
        "requires_human_review": True, "usefulness_score": 1.0, "can_become_local_heuristic": True
    }) + "\n")
    
    # Promoción aprobada
    prom = memory_dir / "reflex_promotion_ledger.jsonl"
    prom.write_text(json.dumps({
        "pattern_id": "p_active", "activation_status": "active_local", "human_approved": True,
        "timestamp": 123.0, "schema_version": "reflex-promotion-record.v1"
    }) + "\n")
    
    return memory_dir, skills_dir

def test_morning_brief_shows_active_reflex(mock_assets):
    memory_dir, skills_dir = mock_assets
    
    brief_gen = MorningBrief(
        memory_dir=str(memory_dir),
        skills_dir=str(skills_dir)
    )
    
    brief = brief_gen.generate_brief()
    
    assert "Promoción Supervisada de Reflejos" in brief
    assert "Reflejo: pilot_active [ACTIVE_LOCAL]" in brief
