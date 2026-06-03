import pytest
import time
from unittest.mock import patch
from core.semantic_fatigue_policy import SemanticFatiguePolicy
from core.semantic_tension_ledger import SemanticTensionEvent

def test_semantic_fatigue_policy_critical_families():
    policy = SemanticFatiguePolicy()
    assert "llm_circuit_open" in policy.CRITICAL_FAMILIES
    assert "host_stress_block" in policy.CRITICAL_FAMILIES
    assert "planner_contract_error" in policy.CRITICAL_FAMILIES

def test_semantic_fatigue_policy_moderate_families():
    policy = SemanticFatiguePolicy()
    assert "llm_timeout" in policy.MODERATE_FAMILIES
    assert "llm_malformed_json" in policy.MODERATE_FAMILIES

def test_rejections_increase_fatigue():
    policy = SemanticFatiguePolicy()
    
    events = [
        SemanticTensionEvent(
            event_id="e1", timestamp=time.time(), source="test", event_type="timeout",
            task_id="t1", intent_category="test", proposed_action="act", proposal_signature="test:act",
            user_outcome="rejected", damage_delta=0.5
        ),
        SemanticTensionEvent(
            event_id="e2", timestamp=time.time(), source="test", event_type="timeout",
            task_id="t2", intent_category="test", proposed_action="act", proposal_signature="test:act",
            user_outcome="rejected", damage_delta=0.5
        )
    ]
    
    # Should not suppress yet, rejections = 2, total damage = 1.0, threshold = 2.0
    assert policy.evaluate(events, "test:act", threshold=2.0) is False
    
    events.append(
        SemanticTensionEvent(
            event_id="e3", timestamp=time.time(), source="test", event_type="timeout",
            task_id="t3", intent_category="test", proposed_action="act", proposal_signature="test:act",
            user_outcome="rejected", damage_delta=0.5
        )
    )
    # Should suppress now, rejections = 3, threshold reached or just by rule 2
    assert policy.evaluate(events, "test:act", threshold=2.0) is True

def test_success_reduces_fatigue():
    policy = SemanticFatiguePolicy()
    
    events = [
        SemanticTensionEvent(
            event_id="e1", timestamp=time.time(), source="test", event_type="timeout",
            task_id="t1", intent_category="test", proposed_action="act", proposal_signature="test:act",
            user_outcome="rejected", damage_delta=2.5
        ),
        SemanticTensionEvent(
            event_id="e2", timestamp=time.time(), source="test", event_type="curated_option_completed",
            task_id="t2", intent_category="test", proposed_action="act", proposal_signature="test:act",
            user_outcome="accepted", damage_delta=0.0
        )
    ]
    
    # Normally 2.5 damage would suppress at threshold 2.0, but success reduces it by 1.0 (2 successes: curated + accepted)
    # Actually curated_option_completed adds 0.5 reduction. user_outcome=accepted adds 0.5 reduction. Total 1.0. Total damage = 1.5.
    assert policy.evaluate(events, "test:act", threshold=2.0) is False
