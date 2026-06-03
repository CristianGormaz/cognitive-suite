import pytest
import os
import json
import time
from core.local_ledger_cache import LocalLedgerCache

@pytest.fixture
def mock_memory(tmp_path):
    memory_dir = tmp_path / "memory"
    memory_dir.mkdir()
    return memory_dir

def test_cache_reads_valid_jsonl(mock_memory):
    ledger = mock_memory / "test_ledger.jsonl"
    with open(ledger, "w") as f:
        f.write('{"test": 1}\n')
        f.write('{"test": 2}\n')
        
    cache = LocalLedgerCache(memory_dir=str(mock_memory))
    records = cache.get_records(str(ledger))
    
    assert len(records) == 2
    assert records[0]["test"] == 1
    assert cache.get_stats().cache_misses == 1
    
    # Second read should hit cache
    records2 = cache.get_records(str(ledger))
    assert len(records2) == 2
    assert cache.get_stats().cache_hits == 1

def test_cache_get_recent(mock_memory):
    ledger = mock_memory / "test_ledger.jsonl"
    with open(ledger, "w") as f:
        for i in range(10):
            f.write(json.dumps({"val": i}) + "\n")
            
    cache = LocalLedgerCache(memory_dir=str(mock_memory))
    recent = cache.get_recent(str(ledger), limit=3)
    
    assert len(recent) == 3
    assert recent[0]["val"] == 7
    assert recent[-1]["val"] == 9

def test_cache_handles_corrupt_line(mock_memory):
    ledger = mock_memory / "test_ledger.jsonl"
    with open(ledger, "w") as f:
        f.write('{"test": 1}\n')
        f.write('corrupt json line\n')
        f.write('{"test": 2}\n')
        
    cache = LocalLedgerCache(memory_dir=str(mock_memory))
    records = cache.get_records(str(ledger))
    
    assert len(records) == 2
    assert records[1]["test"] == 2
