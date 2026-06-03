import pytest
import os
import json
import time
from pathlib import Path
from core.canonical_state_resolver import CanonicalStateResolver

@pytest.fixture
def mock_assets(tmp_path):
    memory_dir = tmp_path / "memory"
    memory_dir.mkdir()
    skills_dir = tmp_path / "src/skills"
    (skills_dir / "experimental").mkdir(parents=True)
    
    return memory_dir, skills_dir

def test_resolve_dependency_state_approved(mock_assets):
    memory_dir, _ = mock_assets
    ledger = memory_dir / "dependency_review_ledger.jsonl"
    
    # Simular aprobación tras un pending
    with open(ledger, "w") as f:
        f.write(json.dumps({"dependency_name": "os", "review_status": "pending_human_review", "timestamp": time.time() - 100}) + "\n")
        f.write(json.dumps({"dependency_name": "os", "review_status": "approved_for_installation", "timestamp": time.time()}) + "\n")
        
    resolver = CanonicalStateResolver(memory_dir=str(memory_dir))
    state = resolver.resolve_dependency_state("os")
    
    assert state.canonical_status == "approved_installed"
    assert state.entity_id == "os"

def test_resolve_skill_state_disabled_by_config(mock_assets):
    memory_dir, skills_dir = mock_assets
    # Crear archivo de skill
    (skills_dir / "experimental/skill_test.py").write_text("")
    
    os.environ["GREYS_EXPERIMENTAL_SKILLS_ENABLED"] = "0"
    
    resolver = CanonicalStateResolver(memory_dir=str(memory_dir), skills_dir=str(skills_dir))
    state = resolver.resolve_skill_state("test")
    
    assert state.canonical_status == "disabled_by_global_config"

def test_resolve_failure_family_active(mock_assets):
    memory_dir, _ = mock_assets
    ledger = memory_dir / "ingestion_failure_ledger.jsonl"
    
    # Fallo muy reciente (hace 10 segundos)
    with open(ledger, "w") as f:
        f.write(json.dumps({"failure_type": "llm_timeout", "timestamp": time.time() - 10}) + "\n")
        
    resolver = CanonicalStateResolver(memory_dir=str(memory_dir))
    state = resolver.resolve_failure_family_state("llm_timeout")
    
    assert state.canonical_status == "active_failure"

def test_resolve_failure_family_recent_debt(mock_assets):
    memory_dir, _ = mock_assets
    ledger = memory_dir / "ingestion_failure_ledger.jsonl"
    
    # Fallo reciente pero no activo (hace 2 horas)
    with open(ledger, "w") as f:
        f.write(json.dumps({"failure_type": "llm_timeout", "timestamp": time.time() - 7200}) + "\n")
        
    resolver = CanonicalStateResolver(memory_dir=str(memory_dir))
    state = resolver.resolve_failure_family_state("llm_timeout")
    
    assert state.canonical_status == "recent_debt"

def test_resolve_llm_health_ledger(mock_assets):
    memory_dir, _ = mock_assets
    ledger = memory_dir / "llm_health_ledger.jsonl"
    
    # Simular timeout en health ledger
    with open(ledger, "w") as f:
        f.write(json.dumps({"status": "llm_timeout", "timestamp": time.time() - 10}) + "\n")
        
    resolver = CanonicalStateResolver(memory_dir=str(memory_dir))
    state = resolver.resolve_failure_family_state("llm_timeout")
    
    assert state.canonical_status == "active_failure"

def test_resolve_runtime_gate(mock_assets):
    os.environ["GREYS_EXPERIMENTAL_SKILLS_ENABLED"] = "0"
    resolver = CanonicalStateResolver()
    state = resolver.resolve_runtime_gate_state("allowlist")
    assert state.canonical_status == "disabled_by_design"
    
    os.environ["GREYS_EXPERIMENTAL_SKILLS_ENABLED"] = "1"
    state = resolver.resolve_runtime_gate_state("allowlist")
    assert state.canonical_status == "active_protection"

def test_system_summary(mock_assets):
    memory_dir, skills_dir = mock_assets
    resolver = CanonicalStateResolver(memory_dir=str(memory_dir), skills_dir=str(skills_dir))
    summary = resolver.get_system_summary()
    assert "pypdf" in summary
    assert "llm_health" in summary
