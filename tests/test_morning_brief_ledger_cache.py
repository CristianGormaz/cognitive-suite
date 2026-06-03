import pytest
import json
from pathlib import Path
from cognition.morning_brief import MorningBrief

def test_morning_brief_uses_ledger_cache(tmp_path):
    memory_dir = tmp_path / "memory"
    memory_dir.mkdir()
    
    # Simular algunos ledgers
    journal_path = memory_dir / "dream_journal.jsonl"
    journal_path.write_text(json.dumps({"test": "journal"}) + "\n")
    
    immune_path = memory_dir / "immune_quarantine_ledger.jsonl"
    immune_path.write_text(json.dumps({"item_id": "i1", "recommended_action": "test"}) + "\n")
    
    brief_gen = MorningBrief(memory_dir=str(memory_dir), journal_path=str(journal_path))
    
    # Forzar la lectura a través de generate_brief (que llama a _load_journal y _load_immune_state)
    brief = brief_gen.generate_brief()
    
    assert "Memoria Local / Ledger Cache" in brief
    
    # Verificar estadísticas de caché
    stats = brief_gen.ledger_cache.get_stats()
    assert stats.files_tracked >= 2
    assert stats.cache_misses >= 2 # Primera lectura de journal e immune
    
    # Llamar de nuevo debería usar la caché
    brief_gen.generate_brief()
    stats_after = brief_gen.ledger_cache.get_stats()
    
    assert stats_after.cache_hits >= 2
