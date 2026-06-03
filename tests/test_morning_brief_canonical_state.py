import pytest
import os
import json
import time
from pathlib import Path
from cognition.morning_brief import MorningBrief

@pytest.fixture
def mock_morning_assets(tmp_path):
    memory_dir = tmp_path / "memory"
    memory_dir.mkdir()
    skills_dir = tmp_path / "src" / "skills"
    (skills_dir / "experimental").mkdir(parents=True)
    
    # Pre-populate ledgers
    (memory_dir / "dependency_review_ledger.jsonl").write_text(json.dumps({
        "dependency_name": "pypdf", "review_status": "approved_for_installation", "timestamp": time.time()
    }) + "\n")
    
    (skills_dir / "experimental/skill_pdf_reader_basic.py").write_text("")
    
    return memory_dir, skills_dir

def test_morning_brief_uses_canonical_state(mock_morning_assets):
    memory_dir, skills_dir = mock_morning_assets
    
    os.environ["GREYS_EXPERIMENTAL_SKILLS_ENABLED"] = "1"
    os.environ["GREYS_EXPERIMENTAL_SKILL_ALLOWLIST"] = "pdf_reader_basic"
    
    brief_gen = MorningBrief(
        memory_dir=str(memory_dir),
        skills_dir=str(skills_dir)
    )
    
    brief = brief_gen.generate_brief()
    
    assert "[DISPONIBLE] Lector PDF experimental instalado." in brief
    assert "[ACTIVO] Runtime PDF autorizado por allowlist." in brief

def test_morning_brief_shows_failure_labels(mock_morning_assets):
    memory_dir, skills_dir = mock_morning_assets
    
    # Simular fallo activo con campos requeridos por el dataclass
    event = {
        "event_id": "err_123",
        "timestamp": time.time() - 10,
        "source": "test",
        "task_id": "task_1",
        "source_type": "text",
        "payload_mime_type": "text/plain",
        "payload_size_bytes": 0,
        "payload_sha256": "abc",
        "declared_intent": None,
        "detected_intent": None,
        "proposed_action": None,
        "failure_type": "llm_timeout",
        "failure_stage": "execution",
        "error_type": "timeout",
        "error_summary": "timeout",
        "supported_actions": [],
        "missing_capability_signature": "none",
        "suggested_skill_category": "none",
        "schema_version": "ingestion-failure.v1"
    }
    
    (memory_dir / "ingestion_failure_ledger.jsonl").write_text(json.dumps(event) + "\n")
    
    brief_gen = MorningBrief(
        memory_dir=str(memory_dir),
        skills_dir=str(skills_dir)
    )
    
    brief = brief_gen.generate_brief()
    assert "llm_timeout: 1 [ACTIVO]" in brief

def test_morning_brief_shows_disabled_pdf(mock_morning_assets):
    memory_dir, skills_dir = mock_morning_assets
    
    os.environ["GREYS_EXPERIMENTAL_SKILLS_ENABLED"] = "0"
    
    brief_gen = MorningBrief(
        memory_dir=str(memory_dir),
        skills_dir=str(skills_dir)
    )
    
    brief = brief_gen.generate_brief()
    assert "[INACTIVO] Runtime desactivado por configuración global." in brief
