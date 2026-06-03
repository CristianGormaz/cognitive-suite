import pytest
import time
from core.semantic_fatigue_policy import SemanticFatiguePolicy
from core.semantic_tension_ledger import SemanticTensionEvent

def test_calculate_decayed_damage():
    policy = SemanticFatiguePolicy()
    policy.half_life_hours = 24.0
    
    now = time.time()
    # 24 hours ago
    timestamp = now - (24 * 3600)
    
    decayed = policy.calculate_decayed_damage(1.0, timestamp, now)
    assert 0.49 < decayed < 0.51  # Should be exactly 0.5

def test_decay_applies_to_evaluate():
    policy = SemanticFatiguePolicy()
    policy.half_life_hours = 24.0
    
    now = time.time()
    events = [
        SemanticTensionEvent(
            event_id="e1", timestamp=now - (24 * 3600), source="test", event_type="llm_timeout",
            task_id="t1", intent_category="test", proposed_action="act", proposal_signature="test:act",
            user_outcome="pending", damage_delta=3.0
        )
    ]
    
    # 3.0 damage, decayed by half life = 1.5. Threshold is 2.0.
    # So it should NOT suppress.
    assert policy.evaluate(events, "test:act", threshold=2.0) is False

def test_critical_events_decay_slower():
    policy = SemanticFatiguePolicy()
    policy.half_life_hours = 24.0
    
    now = time.time()
    events = [
        SemanticTensionEvent(
            event_id="e1", timestamp=now - (24 * 3600), source="test", event_type="llm_circuit_open",
            task_id="t1", intent_category="test", proposed_action="act", proposal_signature="test:act",
            user_outcome="pending", damage_delta=3.0
        )
    ]
    
    # 24 hours is 1/4 of critical half life (96 hours).
    # 3.0 * (0.5 ^ 0.25) = 3.0 * 0.84 = 2.52.
    # So it SHOULD suppress.
    assert policy.evaluate(events, "test:act", threshold=2.0) is True
