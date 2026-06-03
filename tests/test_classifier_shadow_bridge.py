import pytest
import os
import json
from pathlib import Path
from core.classifier_shadow_bridge import ClassifierShadowBridge
from core.local_micro_classifier import LocalClassifierPrediction

@pytest.fixture
def mock_memory(tmp_path):
    return tmp_path

def test_bridge_creates_candidate_on_high_confidence(mock_memory):
    bridge = ClassifierShadowBridge(memory_dir=str(mock_memory))
    
    # Predicción fuerte
    pred = LocalClassifierPrediction(
        input_signature="buenas",
        predicted_intent="greeting",
        confidence=0.9,
        matched_features=["buenas"]
    )
    
    candidate = bridge.build_candidate_from_prediction(pred)
    
    assert candidate is not None
    assert candidate.proposed_reflex_name == "generalized_greeting_reflex"
    assert candidate.shadow_only is True
    assert candidate.should_execute is False

def test_bridge_skips_low_confidence(mock_memory):
    bridge = ClassifierShadowBridge(memory_dir=str(mock_memory))
    
    # Predicción débil
    pred = LocalClassifierPrediction(
        input_signature="ayuda",
        predicted_intent="help",
        confidence=0.5,
        matched_features=["ayuda"]
    )
    
    candidate = bridge.build_candidate_from_prediction(pred)
    assert candidate is None

def test_bridge_handles_unknown_safe(mock_memory):
    bridge = ClassifierShadowBridge(memory_dir=str(mock_memory))
    
    # unknown_safe se permite como candidato de observación (independiente de confianza)
    pred = LocalClassifierPrediction(
        input_signature="manzana",
        predicted_intent="unknown_safe",
        confidence=0.0,
        matched_features=[]
    )
    
    candidate = bridge.build_candidate_from_prediction(pred)
    assert candidate is not None
    assert candidate.proposed_reflex_name == "no_action_unknown_safe"
    assert candidate.proposed_action == "observe_only"

def test_bridge_persistence(mock_memory):
    bridge = ClassifierShadowBridge(memory_dir=str(mock_memory))
    pred = LocalClassifierPrediction("hola", "greeting", 1.0, ["hola"])
    bridge.build_candidate_from_prediction(pred)
    
    candidates = bridge.summarize_candidates()
    assert len(candidates) == 1
    assert candidates[0].predicted_intent == "greeting"
