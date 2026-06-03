import pytest
import json
from pathlib import Path
from cognition.morning_brief import MorningBrief

@pytest.fixture
def mock_shadow_assets(tmp_path):
    memory_dir = tmp_path / "memory"
    memory_dir.mkdir()
    skills_dir = tmp_path / "src/skills"
    (skills_dir / "experimental").mkdir(parents=True)
    
    # Simular evaluaciones en sombra
    ledger = memory_dir / "reflex_shadow_ledger.jsonl"
    ledger.write_text(json.dumps({
        "event_id": "shd1", "timestamp": 123.0, "input_signature": "hola",
        "real_route": "respond", "suggested_reflex": "respond",
        "agreement_with_real_route": True, "confidence": 0.95,
        "risk_estimate": 0.1, "recommendation": "promote_to_local_router",
        "schema_version": "reflex-shadow-evaluation.v1"
    }) + "\n")
    
    return memory_dir, skills_dir

def test_morning_brief_shows_shadow_evaluation(mock_shadow_assets):
    memory_dir, skills_dir = mock_shadow_assets
    
    brief_gen = MorningBrief(
        memory_dir=str(memory_dir),
        skills_dir=str(skills_dir)
    )
    
    brief = brief_gen.generate_brief()
    
    assert "Evaluación en Sombra de Reflejos (Reflex Kernel)" in brief
    assert "Observaciones totales: 1" in brief
    assert "Tasa de coincidencia (Agreement): 100.0%" in brief
    assert "RECOMENDACIÓN: El núcleo local es altamente confiable" in brief
