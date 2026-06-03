import pytest
import json
import os
from pathlib import Path
from cognition.morning_brief import MorningBrief

@pytest.fixture
def mock_assets(tmp_path):
    memory_dir = tmp_path / "memory"
    memory_dir.mkdir()
    skills_dir = tmp_path / "src/skills"
    (skills_dir / "experimental").mkdir(parents=True)
    
    # Simular fallo de timeout en el ledger
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
    
    # Simular evaluación de nivel 3
    immune_ledger = memory_dir / "immune_quarantine_ledger.jsonl"
    immune_event = {
        "item_id": "unsafe.py", "timestamp": 124.0, "recommended_quarantine_level": 3,
        "reason_summary": "dangerous", "schema_version": "immune-quarantine-evaluation.v1"
    }
    immune_ledger.write_text(json.dumps(immune_event) + "\n")
    
    return memory_dir, skills_dir

def test_morning_brief_shows_intrusive_signal_translations(mock_assets):
    memory_dir, skills_dir = mock_assets
    
    brief_gen = MorningBrief(
        memory_dir=str(memory_dir),
        skills_dir=str(skills_dir)
    )
    
    brief = brief_gen.generate_brief()
    
    assert "Traducción de Alertas / Señales Intrusivas" in brief
    assert "Señal: llm_timeout" in brief
    assert "Resumen: El canal de razonamiento profundo mostró latencia" in brief
    assert "Señal: candidate_unsafe" in brief
    assert "Acción: immune_training_sample -> Se conserva como muestra inmune para fortalecer mis defensas" in brief
