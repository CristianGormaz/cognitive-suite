import pytest
import os
import time
import json
from unittest.mock import MagicMock, patch, AsyncMock
from cognition.evolution_option_queue import EvolutionOptionQueue, EvolutionOption
from cognition.morning_brief import MorningBrief
from cognition.dream_mode import DreamMode
from cognition.iafa_transceiver import IafaTransceiver
from core.semantic_tension_ledger import SemanticTensionLedger
from core.ingestion_failure_ledger import IngestionFailureLedger
from core.system_stress_guard import SystemStressGuard
from pathlib import Path
import tempfile

@pytest.mark.asyncio
async def test_evolution_option_queue_persistence():
    with tempfile.TemporaryDirectory() as temp_dir:
        queue_path = os.path.join(temp_dir, "queue.jsonl")
        queue = EvolutionOptionQueue(queue_path=queue_path)
        
        opt = EvolutionOption(
            option_id="opt1",
            timestamp=time.time(),
            title="Test Option",
            summary="Testing queue",
            priority_score=0.8
        )
        queue.append_option(opt)
        
        pending = queue.list_pending()
        assert len(pending) == 1
        assert pending[0].title == "Test Option"

@pytest.mark.asyncio
async def test_dream_mode_generates_options():
    mock_trans = MagicMock(spec=IafaTransceiver)
    # Mock LLM reflection with options
    reflection = {
        "summary": "Dreaming about skills",
        "observed_patterns": ["need pdf"],
        "evolution_options": [
            {
                "title": "Build PDF Reader",
                "summary": "Lots of PDF failures",
                "expected_benefit": 0.9,
                "estimated_risk": 0.2,
                "suggested_micro_sprint": "pdf_v1"
            }
        ]
    }
    mock_trans.query_llm = AsyncMock(return_value=json.dumps(reflection))
    
    with tempfile.TemporaryDirectory() as temp_dir:
        journal_path = os.path.join(temp_dir, "journal.jsonl")
        queue_path = os.path.join(temp_dir, "queue.jsonl")
        q_ledger_path = os.path.join(temp_dir, "q_ledger.jsonl")
        
        from cognition.dream_question_ledger import DreamQuestionLedger
        
        dream = DreamMode(
            transceiver=mock_trans,
            tension_ledger=MagicMock(spec=SemanticTensionLedger),
            failure_ledger=MagicMock(spec=IngestionFailureLedger),
            stress_guard=MagicMock(spec=SystemStressGuard),
            journal_path=journal_path,
            option_queue=EvolutionOptionQueue(queue_path=queue_path),
            question_ledger=DreamQuestionLedger(ledger_path=q_ledger_path)
        )
        dream.tension_ledger.load_recent.return_value = []
        dream.failure_ledger.load_recent.return_value = []
        dream.failure_ledger.get_top_missing_capabilities.return_value = [("pdf", 5)]
        dream.stress_guard.is_host_under_stress.return_value = False
        dream.stress_guard.get_stress_snapshot.return_value = {}
        
        with patch.dict(os.environ, {"GREYS_DREAM_MODE_ENABLED": "1", "GREYS_DREAM_LLM_ENABLED": "1"}):
            await dream.run_session(max_cycles=1)
            
        # Verify option queue
        queue = EvolutionOptionQueue(queue_path=queue_path)
        pending = queue.list_pending()
        assert len(pending) == 1
        assert pending[0].title == "Build PDF Reader"
        assert pending[0].priority_score > 0.0

@pytest.mark.asyncio
async def test_morning_brief_summary():
    with tempfile.TemporaryDirectory() as temp_dir:
        journal_path = Path(temp_dir) / "journal.jsonl"
        queue_path = Path(temp_dir) / "queue.jsonl"
        
        # Populate mock journal
        journal_path.write_text(json.dumps({
            "llm_reflection": {"summary": "Stable night", "observed_patterns": ["P1"]}
        }) + "\n")
        
        # Populate mock queue
        queue_path.write_text(json.dumps({
            "option_id": "o1", "timestamp": time.time(), "title": "Option A", "priority_score": 0.9, "status": "pending_human_review", "summary": "X",
            "evidence_refs": [], "related_ledgers": [], "schema_version": "evolution-option.v1"
        }) + "\n")
        
        curated_path = Path(temp_dir) / "curated.jsonl"
        brief = MorningBrief(
            journal_path=str(journal_path),
            option_queue_path=str(queue_path),
            curated_ledger_path=str(curated_path),
            memory_dir=str(temp_dir)
        )
        output = brief.generate_brief()
        
        assert "MORNING BRIEF" in output
        assert "Option A" in output
        assert "Stable night" in output
