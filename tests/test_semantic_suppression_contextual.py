import pytest
import time
from core.semantic_fatigue_policy import SemanticFatiguePolicy
from core.semantic_tension_ledger import SemanticTensionEvent

def test_critical_with_new_evidence_never_suppressed():
    policy = SemanticFatiguePolicy()
    
    events = [
        SemanticTensionEvent(
            event_id="e1", timestamp=time.time(), source="test", event_type="llm_circuit_open",
            task_id="t1", intent_category="test", proposed_action="act", proposal_signature="test:act",
            user_outcome="pending", damage_delta=10.0  # Massive damage
        )
    ]
    
    # Ordinarily this suppresses
    assert policy.evaluate(events, "test:act", threshold=2.0, has_new_evidence=False) is True
    
    # But with new evidence, it should NOT suppress
    assert policy.evaluate(events, "test:act", threshold=2.0, has_new_evidence=True) is False

def test_high_rejections_with_new_evidence():
    policy = SemanticFatiguePolicy()
    
    events = [
        SemanticTensionEvent(
            event_id="e1", timestamp=time.time(), source="test", event_type="llm_timeout",
            task_id="t1", intent_category="test", proposed_action="act", proposal_signature="test:act",
            user_outcome="rejected", damage_delta=0.5
        ) for _ in range(3)
    ]
    
    # 3 rejections = suppresses by default
    assert policy.evaluate(events, "test:act", threshold=2.0, has_new_evidence=False) is True
    
    # But with new evidence, total damage is 1.5, which is < threshold (2.0), so it should not suppress
    assert policy.evaluate(events, "test:act", threshold=2.0, has_new_evidence=True) is False
