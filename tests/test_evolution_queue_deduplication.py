import json
import os
import time
from pathlib import Path
from cognition.evolution_option_queue import EvolutionOptionQueue, EvolutionOption

def test_evolution_queue_deduplicates_by_id(tmp_path):
    queue_path = tmp_path / "test_queue.jsonl"
    queue = EvolutionOptionQueue(queue_path=str(queue_path))
    
    opt1 = EvolutionOption(
        option_id="opt1", timestamp=time.time(), title="Test 1", summary="Sum 1", status="pending_human_review"
    )
    
    # Write twice with same ID but different status
    queue.append_option(opt1)
    
    opt1_updated = EvolutionOption(
        **{**opt1.__dict__, "status": "approved", "timestamp": time.time() + 1}
    )
    queue.append_option(opt1_updated)
    
    # Load all
    all_options = queue.load_all()
    
    # Should only have 1 entry (the latest)
    assert len(all_options) == 1
    assert all_options[0].status == "approved"

def test_evolution_queue_list_pending_filters_superseded(tmp_path):
    queue_path = tmp_path / "test_queue.jsonl"
    queue = EvolutionOptionQueue(queue_path=str(queue_path))
    
    opt1 = EvolutionOption(
        option_id="opt1", timestamp=time.time(), title="Test 1", summary="Sum 1", status="pending_human_review"
    )
    queue.append_option(opt1)
    
    # Mark as superseded
    queue.mark_status("opt1", "superseded_by_curated")
    
    pending = queue.list_pending()
    assert len(pending) == 0
