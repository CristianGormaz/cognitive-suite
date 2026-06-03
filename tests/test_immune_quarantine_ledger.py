import pytest
import os
import json
from pathlib import Path
from core.immune_quarantine_policy import ImmuneQuarantinePolicy

def test_immune_quarantine_ledger_write_read(tmp_path):
    ledger_path = tmp_path / "immune.jsonl"
    policy = ImmuneQuarantinePolicy()
    
    assessment = policy.assess_item("test", "candidate", {"risk": 0.5})
    
    # Simular escritura
    with open(ledger_path, "a") as f:
        f.write(assessment.to_json() + "\n")
        
    # Simular lectura
    with open(ledger_path, "r") as f:
        data = json.loads(f.read().strip())
        assert data["item_id"] == "test"
        assert "healthy_separation_index" in data
