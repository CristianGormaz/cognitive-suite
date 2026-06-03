import pytest
import json
from pathlib import Path
from cognition.morning_brief import MorningBrief

@pytest.fixture
def mock_assets_with_immune(tmp_path):
    journal = tmp_path / "journal.jsonl"
    queue = tmp_path / "queue.jsonl"
    curated = tmp_path / "curated.jsonl"
    fail = tmp_path / "fail.jsonl"
    tension = tmp_path / "tension.jsonl"
    immune = tmp_path / "immune_quarantine_ledger.jsonl"
    
    # Write one level 3 item
    with open(immune, "w") as f:
        f.write(json.dumps({
            "item_id": "unsafe_sample.py",
            "recommended_quarantine_level": 3,
            "recommended_action": "preserve_as_immune_training_sample",
            "reason_summary": "Peligroso"
        }) + "\n")
        
    journal.write_text("")
    queue.write_text("")
    curated.write_text("")
    fail.write_text("")
    tension.write_text("")
    
    return journal, queue, curated, fail, tension, immune, tmp_path

def test_morning_brief_shows_immune_section(mock_assets_with_immune):
    journal, queue, curated, fail, tension, immune, memory_dir = mock_assets_with_immune
    
    brief_gen = MorningBrief(
        journal_path=str(journal),
        option_queue_path=str(queue),
        curated_ledger_path=str(curated),
        memory_dir=str(memory_dir)
    )
    
    brief = brief_gen.generate_brief()
    
    assert "Sistema Inmune / Corte Sano (Dry-Run)" in brief
    assert "Nivel 3 (Inmunológica):" in brief
    assert "unsafe_sample.py -> preserve_as_immune_training_sample" in brief
    assert "[Peligroso]" in brief
