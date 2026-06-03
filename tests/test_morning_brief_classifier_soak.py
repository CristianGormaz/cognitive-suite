import pytest
import json
from pathlib import Path
from cognition.morning_brief import MorningBrief

@pytest.fixture
def mock_soak_assets(tmp_path):
    memory_dir = tmp_path / "memory"
    memory_dir.mkdir()
    skills_dir = tmp_path / "src/skills"
    (skills_dir / "experimental").mkdir(parents=True)
    
    # Simular candidatos para el soak test
    ledger = memory_dir / "classifier_shadow_candidates.jsonl"
    candidates = [
        {"predicted_intent": "greeting", "confidence": 1.0, "input_signature": "hola", "risk_score": 0.0},
        {"predicted_intent": "unknown_safe", "confidence": 0.0, "input_signature": "xyz", "risk_score": 0.0}
    ]
    with open(ledger, "w") as f:
        for c in candidates:
            f.write(json.dumps(c) + "\n")
            
    return memory_dir, skills_dir

def test_morning_brief_shows_soak_test_section(mock_soak_assets):
    memory_dir, skills_dir = mock_soak_assets
    
    brief_gen = MorningBrief(
        memory_dir=str(memory_dir),
        skills_dir=str(skills_dir)
    )
    
    brief = brief_gen.generate_brief()
    
    assert "Madurez del Clasificador Local" in brief
    assert "Estabilidad en Inferencia (Soak): 2 muestras" in brief
    assert "Salud unknown_safe (Soak): 50.0%" in brief
