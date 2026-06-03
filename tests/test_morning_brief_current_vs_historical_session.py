import json
import time
from pathlib import Path
from cognition.morning_brief import MorningBrief

def test_morning_brief_separates_last_session(tmp_path):
    journal_path = tmp_path / "dream_journal.jsonl"
    
    # Session 1 (Historical)
    t1 = time.time() - 10000
    e1 = {"timestamp": t1, "cycle": 1, "topic": "historical_focus", "next_action": "completed"}
    e2 = {"timestamp": t1 + 60, "cycle": 2, "topic": "historical_focus", "next_action": "completed"}
    
    # Session 2 (Current) - 3 hours later
    t2 = time.time() - 100
    e3 = {"timestamp": t2, "cycle": 1, "topic": "current_focus", "next_action": "completed"}
    e4 = {"timestamp": t2 + 60, "cycle": 2, "topic": "current_focus", "next_action": "max_cycles"}
    
    with open(journal_path, "w") as f:
        f.write(json.dumps(e1) + "\n")
        f.write(json.dumps(e2) + "\n")
        f.write(json.dumps(e3) + "\n")
        f.write(json.dumps(e4) + "\n")
        
    brief_gen = MorningBrief(journal_path=str(journal_path), memory_dir=str(tmp_path))
    brief = brief_gen.generate_brief()
    
    assert "Última sesión nocturna (2 ciclos):" in brief
    assert "Foco dominante: current_focus" in brief
    assert "Estado final: max_cycles" in brief
    
    assert "Estadísticas Históricas:" in brief
    assert "Ciclos acumulados: 4" in brief
