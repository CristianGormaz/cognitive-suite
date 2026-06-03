import pytest
import os
import asyncio
from unittest.mock import MagicMock, patch, AsyncMock
from cognition.dream_mode import DreamMode, DreamCycleResult
from cognition.iafa_transceiver import IafaTransceiver
from core.semantic_tension_ledger import SemanticTensionLedger
from core.ingestion_failure_ledger import IngestionFailureLedger
from core.system_stress_guard import SystemStressGuard
from pathlib import Path
import tempfile

@pytest.mark.asyncio
async def test_dream_mode_respects_max_cycles():
    mock_trans = MagicMock(spec=IafaTransceiver)
    mock_tension = MagicMock(spec=SemanticTensionLedger)
    mock_tension.load_recent.return_value = []
    
    mock_failure = MagicMock(spec=IngestionFailureLedger)
    mock_failure.load_recent.return_value = []
    mock_failure.get_top_missing_capabilities.return_value = []
    
    mock_guard = MagicMock(spec=SystemStressGuard)
    mock_guard.is_host_under_stress.return_value = False
    mock_guard.get_stress_snapshot.return_value = {"stress": "none"}
    
    with tempfile.TemporaryDirectory() as temp_dir:
        journal_path = os.path.join(temp_dir, "dream.jsonl")
        q_ledger_path = os.path.join(temp_dir, "q_ledger.jsonl")
        opt_queue_path = os.path.join(temp_dir, "opt_queue.jsonl")
        
        from cognition.dream_question_ledger import DreamQuestionLedger
        from cognition.evolution_option_queue import EvolutionOptionQueue
        
        q_ledger = DreamQuestionLedger(ledger_path=q_ledger_path)
        opt_queue = EvolutionOptionQueue(queue_path=opt_queue_path)
        
        dream = DreamMode(
            mock_trans, mock_tension, mock_failure, mock_guard, 
            journal_path=journal_path,
            question_ledger=q_ledger,
            option_queue=opt_queue
        )
        
        with patch.dict(os.environ, {"GREYS_DREAM_MODE_ENABLED": "1", "GREYS_DREAM_LLM_ENABLED": "0"}):
            # Ejecutamos 2 ciclos con 0 segundos de sueño para rapidez
            await dream.run_session(max_cycles=2, sleep_seconds=0)
            
        # Verificar que se escribieron 2 eventos
        p = Path(journal_path)
        lines = p.read_text().splitlines()
        assert len(lines) == 2
        
        event1 = json.loads(lines[0])
        event2 = json.loads(lines[1])
        assert event1["cycle"] == 1
        assert event2["cycle"] == 2

@pytest.mark.asyncio
async def test_dream_mode_stops_on_stress():
    mock_trans = MagicMock(spec=IafaTransceiver)
    mock_tension = MagicMock(spec=SemanticTensionLedger)
    mock_failure = MagicMock(spec=IngestionFailureLedger)
    mock_guard = MagicMock(spec=SystemStressGuard)
    # Simulamos estrés
    mock_guard.is_host_under_stress.return_value = True
    
    with tempfile.TemporaryDirectory() as temp_dir:
        journal_path = os.path.join(temp_dir, "dream.jsonl")
        dream = DreamMode(mock_trans, mock_tension, mock_failure, mock_guard, journal_path=journal_path)
        
        with patch.dict(os.environ, {"GREYS_DREAM_MODE_ENABLED": "1"}):
            await dream.run_session(max_cycles=5)
            
        # No debería haber escrito nada porque se detuvo al inicio
        assert not os.path.exists(journal_path)

import json
