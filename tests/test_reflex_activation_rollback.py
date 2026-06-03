import pytest
import os
import json
from core.reflex_promotion_gate import ReflexPromotionGate

def test_rollback_sequence(tmp_path):
    memory_dir = tmp_path / "memory"
    memory_dir.mkdir()
    gate = ReflexPromotionGate(memory_dir=str(memory_dir))
    
    pid = "p1"
    
    # 1. Active
    gate.approve_promotion(pid, "approve")
    assert pid in gate.get_active_reflexes()
    
    # 2. Disable (Rollback)
    gate.disable_reflex(pid, "disable")
    assert pid not in gate.get_active_reflexes()
    
    # 3. Re-enable
    gate.approve_promotion(pid, "re-approve")
    assert pid in gate.get_active_reflexes()

def test_promotion_ledger_persistence(tmp_path):
    memory_dir = tmp_path / "memory"
    memory_dir.mkdir()
    gate = ReflexPromotionGate(memory_dir=str(memory_dir))
    
    gate.approve_promotion("p1", "reason1")
    
    # Nueva instancia debe cargar el estado
    gate2 = ReflexPromotionGate(memory_dir=str(memory_dir))
    assert "p1" in gate2.get_active_reflexes()
