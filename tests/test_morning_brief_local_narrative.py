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
    
    # Simular fallo de timeout
    ledger = memory_dir / "ingestion_failure_ledger.jsonl"
    event = {
        "event_id": "err1", "timestamp": 123.0, "failure_type": "llm_timeout",
        "schema_version": "ingestion-failure.v1", "source": "test", "task_id": "t1",
        "source_type": "text", "payload_mime_type": "text/plain", "payload_size_bytes": 0,
        "payload_sha256": "abc", "declared_intent": None, "detected_intent": None,
        "proposed_action": None, "failure_stage": "exec", "error_type": "timeout",
        "error_summary": "timeout", "supported_actions": [], "missing_capability_signature": "n/a",
        "suggested_skill_category": "n/a"
    }
    ledger.write_text(json.dumps(event) + "\n")
    
    return memory_dir, skills_dir

def test_morning_brief_uses_narrative_translations(mock_assets):
    memory_dir, skills_dir = mock_assets
    
    brief_gen = MorningBrief(
        memory_dir=str(memory_dir),
        skills_dir=str(skills_dir)
    )
    
    brief = brief_gen.generate_brief()
    
    assert "Traducción de Alertas / Señales Intrusivas" in brief
    assert "Resumen: El canal de razonamiento profundo mostró latencia" in brief
    assert "Técnico: LlmTimeoutError registrado" in brief
    assert "Acción: strengthen_local_routing -> Puedo continuar operando" in brief
