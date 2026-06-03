import pytest
from cognition.semantic_dream_miner import SemanticDreamMiner

def test_miner_detects_intrusive_signal_principle():
    miner = SemanticDreamMiner()
    
    # Simular evidencia de alarma intensa (muchos timeouts)
    class FakeFailure:
        def __init__(self, ftype): self.failure_type = ftype
        
    failures = [FakeFailure("llm_timeout") for _ in range(15)]
    evals = [] # Sin evals de nivel 3 en este caso
    
    principles = miner._mine_from_signals(failures, evals)
    
    assert len(principles) == 1
    assert principles[0].principle_name == "alarma_como_senal_no_como_orden"
    assert principles[0].context_dimension == "autorregulacion"

def test_miner_detects_intrusive_signal_from_unsafe_eval():
    miner = SemanticDreamMiner()
    
    failures = []
    evals = [{"recommended_quarantine_level": 3, "item_id": "bad.py"}]
    
    principles = miner._mine_from_signals(failures, evals)
    
    assert len(principles) == 1
    assert principles[0].principle_name == "alarma_como_senal_no_como_orden"
