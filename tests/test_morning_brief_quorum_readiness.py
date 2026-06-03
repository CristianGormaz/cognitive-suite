import pytest
import json
from pathlib import Path
from cognition.morning_brief import MorningBrief

def test_morning_brief_quorum_readiness_section(tmp_path):
    memory_dir = tmp_path / "memory"
    memory_dir.mkdir()
    
    # Simular candidato en el bridge
    bridge_ledger = memory_dir / "classifier_shadow_candidates.jsonl"
    bridge_ledger.write_text(json.dumps({
        "candidate_id": "c1", "proposed_reflex_name": "test_reflex",
        "predicted_intent": "greeting", "confidence": 0.9, "risk_score": 0.0,
        "input_signature": "hola", "timestamp": 123.0,
        "source_prediction_id": "p1", "proposed_action": "respond",
        "target_module": "LocalIntentRouter", "shadow_only": True,
        "requires_human_review": True, "schema_version": "v1"
    }) + "\n")
    
    brief_gen = MorningBrief(memory_dir=str(memory_dir))
    brief = brief_gen.generate_brief()
    
    assert "Quorum de Promoción / Readiness Dry-Run:" in brief
    assert "Candidato: test_reflex" in brief
    assert "Promoción real bloqueada por política dry-run." in brief
