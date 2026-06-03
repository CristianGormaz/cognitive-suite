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
    
    # Simular candidato del puente
    ledger = memory_dir / "classifier_shadow_candidates.jsonl"
    ledger.write_text(json.dumps({
        "candidate_id": "c1", 
        "timestamp": 123.0, 
        "source_prediction_id": "p1",
        "predicted_intent": "status",
        "confidence": 0.86, 
        "input_signature": "status",
        "proposed_reflex_name": "generalized_status_reflex",
        "proposed_action": "respond", 
        "target_module": "LocalIntentRouter",
        "risk_score": 0.1, 
        "shadow_only": True,
        "requires_human_review": True, 
        "schema_version": "classifier-shadow-candidate.v1"
    }) + "\n")
    
    return memory_dir, skills_dir

def test_morning_brief_shows_classifier_bridge_candidates(mock_assets):
    memory_dir, skills_dir = mock_assets
    
    brief_gen = MorningBrief(
        memory_dir=str(memory_dir),
        skills_dir=str(skills_dir)
    )
    
    brief = brief_gen.generate_brief()
    
    assert "Candidatos de Reflejo (Generalización)" in brief
    assert "Patrón: generalized_status_reflex [SHADOW_ONLY]" in brief
    assert "Intención: status | Confianza: 86.0%" in brief
    assert "RECOMENDACIÓN: Calibrar en Shadow Mode" in brief
