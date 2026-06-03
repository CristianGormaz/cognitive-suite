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
        "pattern_id": "p1", "pattern_name": "test_reflex", "trigger_signature": "sig",
        "recommended_action": "respond", "confidence": 1.0, "local_rule_summary": "rule",
        "source_refs": [], "target_module": "LocalIntentRouter", "risk_score": 0.05,
        "requires_human_review": True, "usefulness_score": 1.0, "can_become_local_heuristic": True
    }) + "\n")
    
    # Shadow evaluation con alto acuerdo
    shadow = memory_dir / "reflex_shadow_ledger.jsonl"
    shadow.write_text(json.dumps({
        "event_id": "shd1", "matched_pattern_id": "p1", "agreement_with_real_route": True,
        "match_confidence": 1.0, "classification": "candidate_for_promotion",
        "timestamp": 123.0, "schema_version": "reflex-shadow-evaluation.v1"
    }) + "\n")
    
    return memory_dir, skills_dir

def test_morning_brief_shows_promotion_section(mock_assets):
    memory_dir, skills_dir = mock_assets
    
    brief_gen = MorningBrief(
        memory_dir=str(memory_dir),
        skills_dir=str(skills_dir)
    )
    
    brief = brief_gen.generate_brief()
    
    assert "Promoción Supervisada de Reflejos" in brief
    assert "Reflejo: test_reflex [CANDIDATE]" in brief
    assert "ACCIÓN: Viable para promoción activa. Usa: /reflex-approve p1" in brief
