import pytest
from pathlib import Path

def test_ledger_compaction_policy_exists():
    policy_path = Path("docs/LEDGER_COMPACTION_POLICY.md")
    assert policy_path.exists()
    content = policy_path.read_text()
    assert "Flujo Caliente" in content
    assert "Archivado" in content
    assert "Compactación" in content
