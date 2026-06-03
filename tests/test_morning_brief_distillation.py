import pytest
import json
import os
from pathlib import Path
from cognition.morning_brief import MorningBrief

@pytest.fixture
def mock_brief_assets(tmp_path):
    memory_dir = tmp_path / "memory"
    memory_dir.mkdir()
    skills_dir = tmp_path / "src/skills"
    (skills_dir / "experimental").mkdir(parents=True)
    
    # Ledger de destilación
    ledger = memory_dir / "distilled_reasoning_ledger.jsonl"
    ledger.write_text(json.dumps({
        "pattern_id": "p1", "pattern_name": "avoid_llm", "trigger_signature": "sig",
        "recommended_action": "act", "confidence": 0.9, "local_rule_summary": "Una regla útil",
        "source_refs": ["ref1"], "target_module": "Mod1", "can_become_local_heuristic": True,
        "requires_human_review": True, "usefulness_score": 1.0, "risk_score": 0.1
    }) + "\n")
    
    # Journal vacío para evitar errores
    (memory_dir / "dream_journal.jsonl").write_text("")
    
    return memory_dir, skills_dir

def test_morning_brief_shows_distillation_section(mock_brief_assets):
    memory_dir, skills_dir = mock_brief_assets
    
    brief_gen = MorningBrief(
        memory_dir=str(memory_dir),
        skills_dir=str(skills_dir)
    )
    
    brief = brief_gen.generate_brief()
    
    assert "Destilación de Experiencia DeepSeek" in brief
    assert "Patrón: avoid_llm [REQUIERE REVISIÓN]" in brief
    assert "Aplicación: Mod1 (Puede ser Heurística)" in brief
    assert "Motivo: Una regla útil" in brief
