import pytest
import os
from core.intrusive_signal_policy import IntrusiveSignalPolicy, IntrusiveSignalAssessment

def test_assess_candidate_unsafe():
    policy = IntrusiveSignalPolicy()
    res = policy.assess_signal("candidate_unsafe", "test", "unsafe_signature")
    
    assert res.signal_type == "unsafe_code_signal"
    assert res.should_execute is False
    assert res.should_quarantine is True
    assert res.should_preserve_as_training_sample is True
    assert res.recommended_action == "immune_training_sample"

def test_assess_llm_timeout():
    policy = IntrusiveSignalPolicy()
    res = policy.assess_signal("llm_timeout", "test", "timeout_signature")
    
    assert res.signal_type == "external_channel_limit"
    assert res.learning_value > 0.5
    assert "ruteo local" in res.recommended_translation

def test_noise_estimation():
    policy = IntrusiveSignalPolicy()
    # Sin metadata, ruido bajo
    low_noise = policy.assess_signal("llm_timeout", "test", "sig")
    assert low_noise.noise_score == 0.1
    
    # Con mucha repetición, ruido alto
    high_noise = policy.assess_signal("llm_timeout", "test", "sig", metadata={"repetition_count": 10})
    assert high_noise.noise_score == 0.8

def test_unknown_signal_default():
    policy = IntrusiveSignalPolicy()
    res = policy.assess_signal("mysterious_error", "test", "sig")
    assert res.signal_type == "unknown_intrusive_event"
    assert res.should_quarantine is True
    assert res.recommended_action == "contain_and_observe"
