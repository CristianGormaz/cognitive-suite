import pytest
from cognition.morning_brief import MorningBrief

@pytest.fixture
def mock_assets(tmp_path):
    memory_dir = tmp_path / "memory"
    memory_dir.mkdir()
    skills_dir = tmp_path / "src/skills"
    (skills_dir / "experimental").mkdir(parents=True)
    return memory_dir, skills_dir

def test_morning_brief_shows_context_frame(mock_assets):
    memory_dir, skills_dir = mock_assets
    
    brief_gen = MorningBrief(
        memory_dir=str(memory_dir),
        skills_dir=str(skills_dir)
    )
    
    brief = brief_gen.generate_brief()
    
    assert "Marco de Contexto Arquitectónico" in brief
    assert "Dimensión Entorno" in brief
    assert "Puntaje Contextual Global" in brief
    assert "Dimensión Crítica" in brief
