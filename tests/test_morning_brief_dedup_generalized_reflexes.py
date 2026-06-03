import pytest
from unittest.mock import MagicMock
from cognition.morning_brief import MorningBrief

def test_morning_brief_deduplicates_generalized_reflexes(tmp_path):
    brief_gen = MorningBrief(memory_dir=str(tmp_path))
    brief_gen.classifier_bridge = MagicMock()
    
    # Mock multiple status and identity candidates
    c1 = MagicMock()
    c1.proposed_reflex_name = "generalized_status_reflex"
    c1.predicted_intent = "status"
    c1.confidence = 0.9
    c1.candidate_id = "can1"
    c1.risk_score = 0.0
    
    c2 = MagicMock()
    c2.proposed_reflex_name = "generalized_status_reflex"
    c2.predicted_intent = "status"
    c2.confidence = 0.8
    c2.candidate_id = "can2"
    c2.risk_score = 0.0
    
    c3 = MagicMock()
    c3.proposed_reflex_name = "generalized_identity_reflex"
    c3.predicted_intent = "identity"
    c3.confidence = 1.0
    c3.candidate_id = "can3"
    c3.risk_score = 0.0
    
    brief_gen.classifier_bridge.summarize_candidates.return_value = [c1, c2, c3]
    
    brief = brief_gen.generate_brief()
    
    # Should show status once with "2 ocurrencias agrupadas"
    assert brief.count("generalized_status_reflex") == 2 # Once in Candidates, once in Quorum
    assert "2 ocurrencias agrupadas" in brief
    assert "generalized_identity_reflex" in brief
