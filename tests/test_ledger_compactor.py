import pytest
import json
import os
import time
from pathlib import Path
from core.ledger_compactor import LedgerCompactor, CompactSummary

def test_inventory_ledgers(tmp_path):
    # Create dummy ledgers
    (tmp_path / "ledger1.jsonl").write_text('{"id": 1}\n')
    (tmp_path / "ledger2.jsonl").write_text('{"id": 2}\n')
    (tmp_path / "not_a_ledger.txt").write_text('ignore me')
    
    compactor = LedgerCompactor(memory_dir=str(tmp_path))
    ledgers = compactor.inventory_ledgers()
    
    assert len(ledgers) == 2
    assert "ledger1.jsonl" in [p.name for p in ledgers]
    assert "ledger2.jsonl" in [p.name for p in ledgers]

def test_compact_jsonl_ledger_dry_run(tmp_path):
    ledger_path = tmp_path / "test.jsonl"
    events = [{"event_id": f"e{i}", "timestamp": time.time()} for i in range(250)]
    with open(ledger_path, "w") as f:
        for e in events:
            f.write(json.dumps(e) + "\n")
            
    archive_dir = tmp_path / "archive"
    compactor = LedgerCompactor(memory_dir=str(tmp_path))
    
    result = compactor.compact_jsonl_ledger(ledger_path, archive_dir, keep_recent=200, dry_run=True)
    
    assert result["status"] == "dry_run_ready"
    assert result["archived"] == 50
    assert result["retained"] == 200
    
    # Files should not be modified
    assert len(ledger_path.read_text().splitlines()) == 250
    assert not archive_dir.exists()

def test_compact_jsonl_ledger_real(tmp_path):
    ledger_path = tmp_path / "test.jsonl"
    events = [{"event_id": f"e{i}", "timestamp": time.time(), "event_type": "typeA"} for i in range(250)]
    with open(ledger_path, "w") as f:
        for e in events:
            f.write(json.dumps(e) + "\n")
            
    compactor = LedgerCompactor(memory_dir=str(tmp_path))
    archive_dir = tmp_path / "archive" / "today"
    archive_dir.mkdir(parents=True)
    compactor.compact_dir.mkdir(parents=True)
    
    result = compactor.compact_jsonl_ledger(ledger_path, archive_dir, keep_recent=200, dry_run=False)
    
    assert result["status"] == "compacted"
    assert len(ledger_path.read_text().splitlines()) == 200
    
    # Archive should exist
    archive_files = list(archive_dir.glob("*.jsonl"))
    assert len(archive_files) == 1
    assert len(archive_files[0].read_text().splitlines()) == 50
    
    # Compact summary should exist
    summary_path = compactor.compact_dir / "test_summary.jsonl"
    assert summary_path.exists()
    summary_data = json.loads(summary_path.read_text().splitlines()[0])
    assert summary_data["archived_event_count"] == 50
    assert summary_data["event_type_counts"]["typeA"] == 50

def test_compact_jsonl_ledger_below_threshold(tmp_path):
    ledger_path = tmp_path / "test.jsonl"
    events = [{"id": i} for i in range(50)]
    with open(ledger_path, "w") as f:
        for e in events:
            f.write(json.dumps(e) + "\n")
            
    compactor = LedgerCompactor(memory_dir=str(tmp_path))
    result = compactor.compact_jsonl_ledger(ledger_path, tmp_path, keep_recent=200, dry_run=False)
    
    assert result["status"] == "skipped"
    assert len(ledger_path.read_text().splitlines()) == 50
