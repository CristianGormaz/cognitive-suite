import os
import pytest
import asyncio
from unittest.mock import MagicMock, AsyncMock, patch
from cognition.dream_mode import DreamMode
from core.semantic_tension_ledger import SemanticTensionLedger
from core.ingestion_failure_ledger import IngestionFailureLedger
from core.system_stress_guard import SystemStressGuard
from cognition.iafa_transceiver import IafaTransceiver, LlmTimeoutError
from cognition.dream_question_ledger import DreamQuestionLedger, DreamQuestionEntry
from cognition.evolution_option_queue import EvolutionOptionQueue

@pytest.fixture
def mock_components():
    transceiver = AsyncMock(spec=IafaTransceiver)
    tension_ledger = MagicMock(spec=SemanticTensionLedger)
    failure_ledger = MagicMock(spec=IngestionFailureLedger)
    stress_guard = MagicMock(spec=SystemStressGuard)
    
    # Defaults
    failure_ledger.load_recent.return_value = []
    failure_ledger.get_top_missing_capabilities.return_value = []
    tension_ledger.load_recent.return_value = []
    stress_guard.get_stress_snapshot.return_value = {
        "is_mem_stressed": False,
        "is_cpu_stressed": False,
        "load_1m": 0.5,
        "mem_available_mb": 4096
    }
    stress_guard.is_host_under_stress.return_value = False
    
    return transceiver, tension_ledger, failure_ledger, stress_guard

@pytest.mark.asyncio
async def test_dream_llm_timeout_degradation(mock_components, tmp_path):
    transceiver, tension_ledger, failure_ledger, stress_guard = mock_components
    journal = tmp_path / "dream_journal.jsonl"
    q_ledger_path = tmp_path / "q_ledger.jsonl"
    opt_queue_path = tmp_path / "opt_queue.jsonl"
    
    q_ledger = DreamQuestionLedger(ledger_path=str(q_ledger_path))
    opt_queue = EvolutionOptionQueue(queue_path=str(opt_queue_path))
    
    dream = DreamMode(
        transceiver=transceiver,
        tension_ledger=tension_ledger,
        failure_ledger=failure_ledger,
        stress_guard=stress_guard,
        journal_path=str(journal),
        question_ledger=q_ledger,
        option_queue=opt_queue
    )
    
    # Mock LLM timeout
    transceiver.query_llm.side_effect = LlmTimeoutError("Timeout simulado")
    
    # Configure environment
    with patch.dict(os.environ, {
        "GREYS_DREAM_MODE_ENABLED": "1",
        "GREYS_DREAM_LLM_ENABLED": "1",
        "GREYS_DREAM_MAX_LLM_FAILURES": "1", # Fail after 1 timeout
        "GREYS_DREAM_LOCAL_ONLY_ON_LLM_FAILURE": "1"
    }):
        # Run once
        result = await dream.run_once(cycle=1)
        
        assert result.event_type == "dream_llm_timeout"
        assert result.mode == "local_only" # Degraded in the same cycle if possible
        assert dream._llm_failure_count == 1
        assert dream._llm_disabled_for_session is True
        
        # Verify tension recorded
        tension_ledger.append_event.assert_called()
        
        # Run second time - should go straight to local-only
        result2 = await dream.run_once(cycle=2)
        # It will be 'no_new_evidence' because ledgers are empty and no new options are generated
        assert result2.event_type in ["dream_local_only_cycle", "no_new_evidence"]
        assert result2.mode == "local_only"
        # transceiver.query_llm should NOT have been called a second time
        assert transceiver.query_llm.call_count == 1

@pytest.mark.asyncio
async def test_dream_no_repetition_after_timeout(mock_components, tmp_path):
    transceiver, tension_ledger, failure_ledger, stress_guard = mock_components
    journal = tmp_path / "dream_journal.jsonl"
    q_ledger_path = tmp_path / "q_ledger.jsonl"
    
    q_ledger = DreamQuestionLedger(ledger_path=str(q_ledger_path))
    
    dream = DreamMode(
        transceiver=transceiver,
        tension_ledger=tension_ledger,
        failure_ledger=failure_ledger,
        stress_guard=stress_guard,
        journal_path=str(journal),
        question_ledger=q_ledger
    )
    
    # Mock LLM timeout
    transceiver.query_llm.side_effect = LlmTimeoutError("Timeout simulado")
    
    with patch.dict(os.environ, {
        "GREYS_DREAM_MODE_ENABLED": "1",
        "GREYS_DREAM_LLM_ENABLED": "1",
        "GREYS_DREAM_MAX_LLM_FAILURES": "5", # Don't disable LLM yet
        "GREYS_DREAM_LOCAL_ONLY_ON_LLM_FAILURE": "1"
    }):
        # Cycle 1: Timeout
        await dream.run_once(cycle=1)
        assert transceiver.query_llm.call_count == 1
        
        # Cycle 2: Should detect previous timeout for same signature and go local-only
        # Even if failure count hasn't reached max
        result2 = await dream.run_once(cycle=2)
        assert result2.mode == "local_only"
        assert result2.local_only_reason == "previous_llm_timeout"
        assert transceiver.query_llm.call_count == 1 # Still 1

@pytest.mark.asyncio
async def test_dream_preflight_failure(mock_components, tmp_path):
    transceiver, tension_ledger, failure_ledger, stress_guard = mock_components
    journal = tmp_path / "dream_journal.jsonl"
    
    dream = DreamMode(
        transceiver=transceiver,
        tension_ledger=tension_ledger,
        failure_ledger=failure_ledger,
        stress_guard=stress_guard,
        journal_path=str(journal)
    )
    
    # Mock preflight failure
    transceiver.preflight_ollama = AsyncMock(side_effect=RuntimeError("Ollama down"))
    
    with patch.dict(os.environ, {
        "GREYS_DREAM_MODE_ENABLED": "1",
        "GREYS_DREAM_LLM_ENABLED": "1",
        "GREYS_DREAM_PREFLIGHT_OLLAMA": "1"
    }):
        # Mocking run_once to see if it's called with local-only
        with patch.object(dream, 'run_once', wraps=dream.run_once) as mock_run_once:
            await dream.run_session(max_cycles=1)
            
            # Preflight should have disabled LLM
            assert dream._llm_disabled_for_session is True
            assert dream._local_only_reason == "preflight_failed"
            
            # Let's check the journal
            import json
            with open(journal, "r") as f:
                line = f.readline()
                data = json.loads(line)
                assert data["mode"] == "local_only"
                assert data["local_only_reason"] == "preflight_failed"
