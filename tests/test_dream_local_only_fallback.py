import os
import pytest
import asyncio
from unittest.mock import MagicMock, AsyncMock, patch
from cognition.iafa_transceiver import LlmTimeoutError
from cognition.dream_mode import DreamMode
from core.semantic_tension_ledger import SemanticTensionLedger, SemanticTensionEvent
from core.ingestion_failure_ledger import IngestionFailureLedger, IngestionFailureEvent
from core.system_stress_guard import SystemStressGuard
from cognition.iafa_transceiver import IafaTransceiver
from cognition.dream_question_ledger import DreamQuestionLedger
from cognition.evolution_option_queue import EvolutionOptionQueue
import time

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
async def test_dream_local_only_generation(mock_components, tmp_path):
    transceiver, tension_ledger, failure_ledger, stress_guard = mock_components
    journal = tmp_path / "dream_journal.jsonl"
    opt_queue_path = tmp_path / "opt_queue.jsonl"
    
    opt_queue = EvolutionOptionQueue(queue_path=str(opt_queue_path))
    
    # Inject evidence into ledgers
    failure_ledger.get_top_missing_capabilities.return_value = [("missing_cap_1", 5)]
    
    f1 = MagicMock()
    f1.failure_type = "timeout"
    failure_ledger.load_recent.return_value = [f1]
    
    t1 = MagicMock()
    t1.tension_tau = 0.7
    t1.proposal_signature = "tension_sig_1"
    tension_ledger.load_recent.return_value = [t1]
    
    dream = DreamMode(
        transceiver=transceiver,
        tension_ledger=tension_ledger,
        failure_ledger=failure_ledger,
        stress_guard=stress_guard,
        journal_path=str(journal),
        option_queue=opt_queue
    )
    
    # Force local-only
    with patch.dict(os.environ, {
        "GREYS_DREAM_MODE_ENABLED": "1",
        "GREYS_DREAM_LLM_ENABLED": "0", # Force local-only
        "GREYS_DREAM_MAX_OPTIONS_PER_CYCLE": "5"
    }):
        result = await dream.run_once(cycle=1)
        
        assert result.mode == "local_only"
        assert result.generated_option_count > 0
        assert not result.no_new_evidence
        
        # Verify options in queue
        options = opt_queue.load_all()
        assert len(options) >= 2
        titles = [o.title for o in options]
        assert any("missing_cap_1" in t for t in titles)
        assert any("tension_sig_1" in t for t in titles)

@pytest.mark.asyncio
async def test_dream_local_only_no_duplicates(mock_components, tmp_path):
    transceiver, tension_ledger, failure_ledger, stress_guard = mock_components
    journal = tmp_path / "dream_journal.jsonl"
    opt_queue_path = tmp_path / "opt_queue.jsonl"
    
    opt_queue = EvolutionOptionQueue(queue_path=str(opt_queue_path))
    
    failure_ledger.get_top_missing_capabilities.return_value = [("missing_cap_1", 5)]
    
    dream = DreamMode(
        transceiver=transceiver,
        tension_ledger=tension_ledger,
        failure_ledger=failure_ledger,
        stress_guard=stress_guard,
        journal_path=str(journal),
        option_queue=opt_queue
    )
    
    with patch.dict(os.environ, {
        "GREYS_DREAM_MODE_ENABLED": "1",
        "GREYS_DREAM_LLM_ENABLED": "0"
    }):
        # Cycle 1: Generates option
        result1 = await dream.run_once(cycle=1)
        assert result1.generated_option_count == 1
        
        # Cycle 2: Evidence is the same, should not generate duplicate
        result2 = await dream.run_once(cycle=2)
        assert result2.generated_option_count == 0
        assert result2.no_new_evidence is True
