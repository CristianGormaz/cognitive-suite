import json
import os
from pathlib import Path
from cognition.morning_brief import MorningBrief

def test_morning_brief_no_new_evidence_status(tmp_path):
    journal_path = tmp_path / "dream_journal.jsonl"
    
    # Session with no_new_evidence
    e1 = {"timestamp": 12345, "next_action": "no_new_evidence", "topic": "test"}
    
    with open(journal_path, "w") as f:
        f.write(json.dumps(e1) + "\n")
        
    os.environ["GREYS_DREAM_CONTINUE_ON_NO_NEW_EVIDENCE"] = "1"
    try:
        brief_gen = MorningBrief(journal_path=str(journal_path), memory_dir=str(tmp_path))
        brief = brief_gen.generate_brief()
        
        assert "Ciclos sin evidencia nueva: 1 (Continuado (Mantenimiento Idle))" in brief
    finally:
        os.environ.pop("GREYS_DREAM_CONTINUE_ON_NO_NEW_EVIDENCE", None)
