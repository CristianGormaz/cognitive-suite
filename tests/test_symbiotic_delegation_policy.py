import pytest
import os
import json
from pathlib import Path
from core.symbiotic_delegation_policy import SymbioticDelegationPolicy

@pytest.fixture
def mock_memory(tmp_path):
    memory_dir = tmp_path / "memory"
    memory_dir.mkdir()
    return memory_dir

def test_ers_favors_local_when_latency_high(mock_memory):
    policy = SymbioticDelegationPolicy(memory_dir=str(mock_memory))
    # Baja complejidad, alta latencia LLM, sin estrés de host
    ers = policy.calculate_edge_routing_score(complexity_score=0.1, host_stress=0.0, llm_latency_risk=0.9)
    # local_benefit = 1.0 - 0.1 = 0.9
    # central_cost = 0.9 + 0 = 0.9
    # ERS = 0.0
    
    # Si la complejidad es nula y la latencia máxima:
    ers2 = policy.calculate_edge_routing_score(complexity_score=0.0, host_stress=0.0, llm_latency_risk=1.0)
    assert ers2 == 0.0 # 1.0 - 1.0
    
    # Latencia baja, complejidad media
    ers3 = policy.calculate_edge_routing_score(complexity_score=0.3, host_stress=0.0, llm_latency_risk=0.1)
    assert ers3 == 0.6 # 0.7 - 0.1

def test_sds_favors_delegation_for_complex_tasks(mock_memory):
    policy = SymbioticDelegationPolicy(memory_dir=str(mock_memory))
    # Alta complejidad, baja latencia, sin estrés
    sds = policy.calculate_symbiotic_delegation_score(complexity_score=0.9, host_stress=0.0, llm_latency_risk=0.1)
    # benefit = 0.9, cost = 0.1
    assert sds == 0.8
    
    # Baja complejidad, alto estrés
    sds2 = policy.calculate_symbiotic_delegation_score(complexity_score=0.1, host_stress=0.8, llm_latency_risk=0.1)
    assert sds2 == -0.8 # 0.1 - 0.9

def test_recommend_route_host_stress(mock_memory):
    policy = SymbioticDelegationPolicy(memory_dir=str(mock_memory))
    route, allowed, reason = policy.recommend_route(
        task_type="chat", ers=0.5, sds=0.5, qps=1.0, host_stress=0.9, active_reflex_exists=False, ambiguity_margin=1.0
    )
    assert route == "defer_due_to_host_stress"
    assert allowed is False

def test_recommend_route_active_reflex(mock_memory):
    policy = SymbioticDelegationPolicy(memory_dir=str(mock_memory))
    route, allowed, reason = policy.recommend_route(
        task_type="chat", ers=0.0, sds=1.0, qps=1.0, host_stress=0.0, active_reflex_exists=True, ambiguity_margin=1.0
    )
    assert route == "local_reflex"

def test_recommend_route_ambiguity_observe(mock_memory):
    policy = SymbioticDelegationPolicy(memory_dir=str(mock_memory))
    route, allowed, reason = policy.recommend_route(
        task_type="chat", ers=0.5, sds=0.5, qps=0.1, host_stress=0.0, active_reflex_exists=False, ambiguity_margin=0.05
    )
    assert route == "observe_only"

def test_recommend_route_force_local(mock_memory, monkeypatch):
    monkeypatch.setenv("GREYS_FORCE_LOCAL_ONLY", "1")
    policy = SymbioticDelegationPolicy(memory_dir=str(mock_memory))
    
    # ERS < SDS significa que normalmente iría al LLM
    route, allowed, reason = policy.recommend_route(
        task_type="chat", ers=0.1, sds=0.9, qps=1.0, host_stress=0.0, active_reflex_exists=False, ambiguity_margin=1.0
    )
    assert route == "block_due_to_policy"
    assert allowed is False
    assert "FORCE_LOCAL_ONLY" in reason

def test_dry_run_persistence(mock_memory, monkeypatch):
    monkeypatch.setenv("GREYS_SYMBIOTIC_DELEGATION_DRY_RUN", "1")
    policy = SymbioticDelegationPolicy(memory_dir=str(mock_memory))
    
    assessment = policy.assess_task("sig123", "chat", 0.5, 0.0, 0.0)
    
    ledger = mock_memory / "symbiotic_delegation_ledger.jsonl"
    assert ledger.exists()
    
    data = json.loads(ledger.read_text().splitlines()[-1])
    assert data["task_signature"] == "sig123"
    assert "recommended_route" in data
