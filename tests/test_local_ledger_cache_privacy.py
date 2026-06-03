import pytest
from pathlib import Path
from core.local_ledger_cache import LocalLedgerCache

@pytest.fixture
def mock_memory(tmp_path):
    memory_dir = tmp_path / "memory"
    memory_dir.mkdir()
    return memory_dir

def test_cache_blocks_reading_outside_memory(mock_memory, tmp_path):
    cache = LocalLedgerCache(memory_dir=str(mock_memory))
    
    outside_file = tmp_path / "secrets.txt"
    outside_file.write_text('{"secret": "data"}\n')
    
    records = cache.get_records(str(outside_file))
    assert len(records) == 0
    assert cache.get_stats().cache_misses == 0
    assert cache.get_stats().cache_hits == 0

def test_cache_handles_nonexistent_file(mock_memory):
    cache = LocalLedgerCache(memory_dir=str(mock_memory))
    missing_file = mock_memory / "missing.jsonl"
    
    records = cache.get_records(str(missing_file))
    assert len(records) == 0
    assert cache.get_stats().cache_misses == 1 # Miss but gracefully handles FileNotFound
