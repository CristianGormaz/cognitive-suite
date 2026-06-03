import pytest
from unittest.mock import MagicMock
from core.local_intent_router import LocalIntentRouter
from core.task_envelope import TaskEnvelope
from core.fast_path_reflex_gate import FastPathReflexGate, FastPathAssessment

def test_fast_path_local_intent_router():
    minimal = MagicMock()
    # Mock pattern to return a certified reflex
    minimal.match_pattern.return_value = {
        "pattern_id": "p1",
        "pattern_name": "basic_greeting_reflex",
        "decision_category": "chat",
        "recommended_action": "respond",
        "match_confidence": 1.0,
        "risk_score": 0.0,
        "human_approved": True,
        "rollback_available": True,
        "uses_llm": False,
        "uses_files": False,
        "uses_network": False,
        "uses_dynamic_skill_loader": False,
        "uses_genesis": False
    }
    
    promotion = MagicMock()
    promotion.get_active_reflexes.return_value = ["p1"]
    
    gate = MagicMock()
    # Ensure it returns True for fast-path
    gate.assess_reflex.return_value = FastPathAssessment(
        event_id="e1", timestamp=1.0, pattern_id="p1", input_signature="hola",
        reflex_name="basic_greeting_reflex", active_local=True, risk_score=0.0,
        human_approved=True, rollback_available=True, uses_llm=False, uses_files=False,
        uses_network=False, uses_dynamic_skill_loader=False, uses_genesis=False,
        fast_path_allowed=True, block_reason=None, duration_ms=1.0
    )
    
    router = LocalIntentRouter(
        minimal_neural_layer=minimal,
        promotion_gate=promotion,
        fast_path_gate=gate
    )
    
    envelope = TaskEnvelope.from_text("hola")
    decision = router.check_fast_path(envelope)
    
    assert decision is not None
    assert decision.matched is True
    assert decision.reason == "fast_path_basic_greeting_reflex"
    assert decision.bypass_llm is True
    assert decision.requires_iafa is False

def test_fast_path_returns_none_if_blocked():
    minimal = MagicMock()
    minimal.match_pattern.return_value = {"pattern_id": "p1", "pattern_name": "basic_greeting_reflex"}
    promotion = MagicMock()
    promotion.get_active_reflexes.return_value = ["p1"]
    
    gate = MagicMock()
    # Returns False
    gate.assess_reflex.return_value = FastPathAssessment(
        event_id="e1", timestamp=1.0, pattern_id="p1", input_signature="hola",
        reflex_name="basic_greeting_reflex", active_local=True, risk_score=0.0,
        human_approved=True, rollback_available=True, uses_llm=False, uses_files=False,
        uses_network=False, uses_dynamic_skill_loader=False, uses_genesis=False,
        fast_path_allowed=False, block_reason="some_reason", duration_ms=1.0
    )
    
    router = LocalIntentRouter(minimal_neural_layer=minimal, promotion_gate=promotion, fast_path_gate=gate)
    decision = router.check_fast_path(TaskEnvelope.from_text("hola"))
    
    assert decision is None
