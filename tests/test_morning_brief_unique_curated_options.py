import os
import json
import time
from pathlib import Path
from cognition.morning_brief import MorningBrief
from cognition.evolution_option_curator import CuratedEvolutionOption

def test_morning_brief_shows_unique_families(tmp_path):
    # Setup temp ledgers
    curated_path = tmp_path / "curated.jsonl"
    
    # Create two curated options for the same family
    opt1 = CuratedEvolutionOption(
        curated_id="cur1", timestamp=time.time(), title="Math 1", summary="Sum 1",
        source_option_ids=["s1"], merged_count=1, family="math_integrals",
        evidence_refs=[], best_suggested_micro_sprint="sprint1",
        priority_score=0.8, expected_benefit=0.9, estimated_risk=0.1
    )
    opt2 = CuratedEvolutionOption(
        curated_id="cur2", timestamp=time.time() + 1, title="Math 2", summary="Sum 2",
        source_option_ids=["s2"], merged_count=1, family="math_integrals",
        evidence_refs=[], best_suggested_micro_sprint="sprint2",
        priority_score=0.9, expected_benefit=0.9, estimated_risk=0.1
    )
    
    with open(curated_path, "a") as f:
        f.write(opt1.to_json() + "\n")
        f.write(opt2.to_json() + "\n")
        
    brief_gen = MorningBrief(
        journal_path=str(tmp_path / "journal.jsonl"),
        option_queue_path=str(tmp_path / "queue.jsonl"),
        curated_ledger_path=str(curated_path),
        memory_dir=str(tmp_path)
    )
    
    brief = brief_gen.generate_brief()
    
    # Check that "math_integrals" family appears but only once in the curated list
    # The Top 3 should not have duplicates
    assert brief.count("Familia: math_integrals") == 1
    # Should prefer the one with higher priority (0.9)
    assert "Math 2" in brief
    assert "Math 1" not in brief
