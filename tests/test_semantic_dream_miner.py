import pytest
import os
import json
import time
from pathlib import Path
from cognition.semantic_dream_miner import SemanticDreamMiner, SemanticPrincipleRecord

@pytest.fixture
def mock_miner(tmp_path):
    ledger_path = tmp_path / "semantic_principle_ledger.jsonl"
    return SemanticDreamMiner(ledger_path=str(ledger_path))

def test_semantic_miner_detects_immune_principle(mock_miner):
    # Simular evaluación de nivel 3
    immune_evals = [
        {"item_id": "unsafe.py", "recommended_quarantine_level": 3, "recommended_action": "block"}
    ]
    
    principles = mock_miner.run_semantic_mining_session([], [], immune_evals)
    
    # Ahora detecta 2: cuarentena_como_aprendizaje Y alarma_como_senal_no_como_orden
    assert len(principles) == 2
    assert any(p.principle_name == "cuarentena_como_aprendizaje" for p in principles)
    assert any(p.principle_name == "alarma_como_senal_no_como_orden" for p in principles)
    assert "unsafe.py" in principles[0].source_evidence_refs

def test_semantic_miner_detects_resilience_principle(mock_miner):
    # Simular fallos LLM
    class MockFail:
        def __init__(self, ftype): self.failure_type = ftype
        
    recent_failures = [MockFail("llm_timeout") for _ in range(6)]
    
    principles = mock_miner.run_semantic_mining_session(recent_failures, [], [])
    
    assert len(principles) == 1
    assert principles[0].principle_name == "degradacion_local_como_resiliencia"

def test_semantic_miner_suppresses_redundancy(mock_miner):
    immune_evals = [{"item_id": "unsafe.py", "recommended_quarantine_level": 3}]
    
    # Primera sesión: detecta 2
    p1 = mock_miner.run_semantic_mining_session([], [], immune_evals)
    assert len(p1) == 2
    
    # Segunda sesión: ya existe, no debe repetir
    p2 = mock_miner.run_semantic_mining_session([], [], immune_evals)
    assert len(p2) == 0

def test_semantic_miner_persistence(mock_miner):
    immune_evals = [{"item_id": "unsafe.py", "recommended_quarantine_level": 3}]
    mock_miner.run_semantic_mining_session([], [], immune_evals)
    
    assert os.path.exists(mock_miner.ledger_path)
    lines = Path(mock_miner.ledger_path).read_text().splitlines()
    assert len(lines) == 2
    data = json.loads(lines[0])
    assert data["principle_name"] == "cuarentena_como_aprendizaje"
