import pytest
import json
from pathlib import Path
from cognition.morning_brief import MorningBrief

def test_morning_brief_fast_path_metrics(tmp_path):
    memory_dir = tmp_path / "memory"
    memory_dir.mkdir()
    ledger = memory_dir / "fast_path_reflex_ledger.jsonl"
    
    with open(ledger, "w") as f:
        f.write(json.dumps({
            "fast_path_allowed": True,
            "duration_ms": 1.5,
            "reflex_name": "basic_greeting_reflex"
        }) + "\n")
        f.write(json.dumps({
            "fast_path_allowed": False,
            "duration_ms": 0.5,
            "reflex_name": "some_other_reflex",
            "block_reason": "not_certified"
        }) + "\n")
        
    brief_gen = MorningBrief(memory_dir=str(memory_dir))
    brief = brief_gen.generate_brief()
    
    assert "Ruta Mielinizada / Fast-Path:" in brief
    assert "Ejecuciones Rápidas (Hits): 1" in brief
    assert "Evaluaciones Bloqueadas: 1" in brief
    assert "basic_greeting_reflex: 1 veces" in brief
