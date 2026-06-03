import pytest
import json
import asyncio
from unittest.mock import AsyncMock, MagicMock, patch
from cognition.dream_mode import DreamMode, DreamCycleResult
from core.task_envelope import TaskEnvelope

from cognition.dream_question_ledger import DreamQuestionLedger

@pytest.fixture
def mock_transceiver():
    return AsyncMock()

@pytest.fixture
def mock_ledgers(tmp_path):
    tension = MagicMock()
    failure = MagicMock()
    stress = MagicMock()
    tension.load_recent.return_value = []
    failure.load_recent.return_value = []
    failure.get_top_missing_capabilities.return_value = []
    stress.is_host_under_stress.return_value = False
    stress.get_stress_snapshot.return_value = {}
    
    question_ledger_path = tmp_path / "dream_question_ledger.jsonl"
    question_ledger = DreamQuestionLedger(ledger_path=str(question_ledger_path))
    
    return tension, failure, stress, question_ledger

@pytest.mark.asyncio
async def test_dream_mode_handles_malformed_json(mock_transceiver, mock_ledgers, tmp_path):
    tension, failure, stress, question_ledger = mock_ledgers
    journal = tmp_path / "dream_journal.jsonl"
    
    dream = DreamMode(
        transceiver=mock_transceiver,
        tension_ledger=tension,
        failure_ledger=failure,
        stress_guard=stress,
        journal_path=str(journal),
        question_ledger=question_ledger
    )
    
    # Simulate malformed JSON response
    mock_transceiver.query_llm.return_value = '{"summary": "incomplete...'
    
    # We want to check if it counts as a failure and eventually falls back to local-only
    with patch.dict("os.environ", {
        "GREYS_DREAM_LLM_ENABLED": "1",
        "GREYS_DREAM_MAX_LLM_FAILURES": "2",
        "GREYS_DREAM_LOCAL_ONLY_ON_LLM_FAILURE": "1",
        "GREYS_DREAM_MAX_REPETITIONS_PER_SIGNATURE": "5"
    }):
        # Cycle 1: Malformed JSON
        result1 = await dream.run_once(1)
        assert result1.llm_reflection is None
        assert dream._llm_failure_count == 1
        
        # Cycle 2: Malformed JSON again, but with different context to avoid per-signature fallback
        new_failure = MagicMock()
        new_failure.failure_type = "new_error"
        failure.load_recent.return_value = [new_failure]
        result2 = await dream.run_once(2)
        assert result2.llm_reflection is None
        assert dream._llm_failure_count == 2
        assert dream._llm_disabled_for_session is True
        
        # Cycle 3: Should be local-only
        result3 = await dream.run_once(3)
        assert result3.mode == "local_only"
        assert result3.local_reflection is not None
