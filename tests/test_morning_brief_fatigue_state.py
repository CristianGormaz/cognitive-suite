import pytest
import json
from pathlib import Path
from cognition.morning_brief import MorningBrief

@pytest.fixture
def mock_assets(tmp_path):
    journal_path = tmp_path / "dream_journal.jsonl"
    queue_path = tmp_path / "evolution_option_queue.jsonl"
    curated_path = tmp_path / "evolution_option_curated.jsonl"
    failure_path = tmp_path / "ingestion_failure_ledger.jsonl"
    tension_path = tmp_path / "semantic_tension_ledger.jsonl"
    
    # Write some tension events
    events = [
        {
            "event_id": "test1", "timestamp": 123.0, "source": "test", "task_id": "t1",
            "event_type": "llm_circuit_open", "intent_category": "c", "proposed_action": "a",
            "proposal_signature": "c:a", "user_outcome": "pending", "damage_delta": 2.0, "schema_version": "semantic-tension.v1"
        },
        {
            "event_id": "test2", "timestamp": 123.0, "source": "test", "task_id": "t2",
            "event_type": "llm_timeout", "intent_category": "c", "proposed_action": "a",
            "proposal_signature": "c:a", "user_outcome": "pending", "damage_delta": 1.0, "schema_version": "semantic-tension.v1"
        }
    ]
    with open(tension_path, "w") as f:
        for ev in events:
            f.write(json.dumps(ev) + "\n")
            
    # Need at least an empty array for others
    queue_path.write_text("")
    curated_path.write_text("")
    journal_path.write_text("")
    failure_path.write_text("")
    
    return journal_path, queue_path, curated_path, failure_path, tension_path

def test_morning_brief_shows_fatigue_state(mock_assets):
    journal_path, queue_path, curated_path, failure_path, tension_path = mock_assets
    
    from core.ingestion_failure_ledger import IngestionFailureLedger
    from core.semantic_tension_ledger import SemanticTensionLedger
    failure_ledger = IngestionFailureLedger(ledger_path=str(failure_path))
    tension_ledger = SemanticTensionLedger(ledger_path=str(tension_path))
    
    # Disable decay for predictable values in test
    tension_ledger.fatigue_policy.decay_enabled = False
    
    brief_gen = MorningBrief(
        journal_path=str(journal_path),
        option_queue_path=str(queue_path),
        curated_ledger_path=str(curated_path),
        failure_ledger=failure_ledger,
        tension_ledger=tension_ledger
    )
    
    brief = brief_gen.generate_brief()
    
    assert "Estado de Fatiga Semántica" in brief
    assert "llm_circuit_open: 2.00" in brief
    assert "llm_timeout: 1.00" in brief
    assert "Señales Críticas Activas" in brief
    assert "llm_circuit_open" in brief
