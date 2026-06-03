import pytest
import os
import json
import asyncio
from unittest.mock import MagicMock, patch, AsyncMock
from cognition.dream_mode import DreamMode
from cognition.dream_question_ledger import DreamQuestionLedger, DreamQuestionEntry
from cognition.evolution_option_queue import EvolutionOptionQueue
from core.system_stress_guard import SystemStressGuard
from core.semantic_tension_ledger import SemanticTensionLedger
from core.ingestion_failure_ledger import IngestionFailureLedger
import tempfile
from pathlib import Path

@pytest.mark.asyncio
async def test_dream_recurrence_guard_blocks_duplicate():
    mock_trans = MagicMock()
    mock_guard = MagicMock(spec=SystemStressGuard)
    mock_guard.is_host_under_stress.return_value = False
    mock_guard.get_stress_snapshot.return_value = {}
    
    with tempfile.TemporaryDirectory() as temp_dir:
        journal_path = os.path.join(temp_dir, "journal.jsonl")
        q_ledger_path = os.path.join(temp_dir, "questions.jsonl")
        
        dream = DreamMode(
            transceiver=mock_trans,
            tension_ledger=MagicMock(spec=SemanticTensionLedger),
            failure_ledger=MagicMock(spec=IngestionFailureLedger),
            stress_guard=mock_guard,
            journal_path=journal_path,
            question_ledger=DreamQuestionLedger(ledger_path=q_ledger_path)
        )
        
        # Pre-poblar el ledger con 2 repeticiones (límite por defecto es 2)
        # Usamos una firma fija
        sig = "fixed_sig"
        for i in range(2):
            entry = DreamQuestionEntry(
                "id", 1.0, 1, "topic", "h", "c", [], sig, 0, "observation", repetition_count=i+1
            )
            dream.question_ledger.append_entry(entry)
            
        # Mock de firma para que el siguiente ciclo genere la misma
        with patch.object(dream.question_ledger, "generate_semantic_signature", return_value=sig):
            with patch.dict(os.environ, {"GREYS_DREAM_MODE_ENABLED": "1", "GREYS_DREAM_LLM_ENABLED": "1"}):
                # Debería suprimir el ciclo
                await dream.run_session(max_cycles=1)
                
        # Verificar que NO se llamó al LLM
        mock_trans.query_llm.assert_not_called()

@pytest.mark.asyncio
async def test_dream_depth_ladder_escalation():
    mock_trans = MagicMock()
    # Respuesta con alto entendido score
    reflection = {"summary": "understood", "evolution_options": [], "observed_patterns": []}
    mock_trans.query_llm = AsyncMock(return_value=json.dumps(reflection))
    
    with tempfile.TemporaryDirectory() as temp_dir:
        dream = DreamMode(
            transceiver=mock_trans,
            tension_ledger=MagicMock(spec=SemanticTensionLedger),
            failure_ledger=MagicMock(spec=IngestionFailureLedger),
            stress_guard=MagicMock(spec=SystemStressGuard),
            question_ledger=DreamQuestionLedger(ledger_path=os.path.join(temp_dir, "q.jsonl"))
        )
        dream.stress_guard.is_host_under_stress.return_value = False
        dream.stress_guard.get_stress_snapshot.return_value = {}
        
        with patch.dict(os.environ, {"GREYS_DREAM_MODE_ENABLED": "1", "GREYS_DREAM_LLM_ENABLED": "1"}):
            # Ciclo 1: Nivel 0
            result1 = await dream.run_once(1)
            assert result1.depth_level == 0
            
            # Ciclo 2: Debería ser Nivel 1 (porque el anterior fue entendido)
            result2 = await dream.run_once(2)
            assert result2.depth_level == 1

def test_morning_brief_recurrence_info():
    from cognition.morning_brief import MorningBrief
    with tempfile.TemporaryDirectory() as temp_dir:
        journal_path = Path(temp_dir) / "journal.jsonl"
        # Evento suprimido
        journal_path.write_text(json.dumps({
            "next_action": "suppress", "depth_level": 2, "cycle": 1
        }) + "\n")
        
        brief = MorningBrief(
            journal_path=str(journal_path), 
            option_queue_path=os.path.join(temp_dir, "opt.jsonl"),
            memory_dir=str(temp_dir)
        )
        output = brief.generate_brief()
        
        assert "suprimieron 1 ciclos" in output
        assert "máximo de profundidad alcanzado: 2" in output
