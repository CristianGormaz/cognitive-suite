import pytest
import os
import time
from core.local_ledger_cache import LocalLedgerCache

@pytest.fixture
def mock_memory(tmp_path):
    memory_dir = tmp_path / "memory"
    memory_dir.mkdir()
    return memory_dir

def test_cache_invalidates_on_size_change(mock_memory):
    ledger = mock_memory / "test_ledger.jsonl"
    with open(ledger, "w") as f:
        f.write('{"test": 1}\n')
        
    cache = LocalLedgerCache(memory_dir=str(mock_memory))
    cache.get_records(str(ledger)) # Miss
    assert cache.get_stats().cache_misses == 1
    
    # Append to file
    with open(ledger, "a") as f:
        f.write('{"test": 2}\n')
        
    # Read again, should miss due to size change
    records = cache.get_records(str(ledger))
    assert len(records) == 2
    assert cache.get_stats().cache_misses == 2

def test_manual_invalidation(mock_memory):
    ledger = mock_memory / "test_ledger.jsonl"
    with open(ledger, "w") as f:
        f.write('{"test": 1}\n')
        
    cache = LocalLedgerCache(memory_dir=str(mock_memory))
    cache.get_records(str(ledger))
    
    cache.invalidate(str(ledger))
    assert cache.get_stats().invalidations == 1
    
    cache.get_records(str(ledger))
    assert cache.get_stats().cache_misses == 2
