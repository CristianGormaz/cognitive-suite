import json
from unittest.mock import MagicMock
from cognition.morning_brief import MorningBrief
from core.classifier_shadow_bridge import LocalClassifierPrediction

def test_morning_brief_deduplicates_unknown_safe(tmp_path):
    brief_gen = MorningBrief(memory_dir=str(tmp_path))
    brief_gen.classifier_bridge = MagicMock()
    
    # Mock classifier bridge to return multiple unknown_safe candidates
    c1 = MagicMock()
    c1.predicted_intent = "unknown_safe"
    c1.proposed_reflex_name = "no_action_unknown_safe"
    c1.confidence = 0.5
    c1.candidate_id = "can1"
    c1.risk_score = 0.0
    
    c2 = MagicMock()
    c2.predicted_intent = "unknown_safe"
    c2.proposed_reflex_name = "no_action_unknown_safe"
    c2.confidence = 0.6
    c2.candidate_id = "can2"
    c2.risk_score = 0.0
    
    brief_gen.classifier_bridge.summarize_candidates.return_value = [c1, c2]
    
    brief = brief_gen.generate_brief()
    
    # Should only show no_action_unknown_safe once with "agrupadas"
    assert brief.count("no_action_unknown_safe") == 2 # Once in "Candidatos" and once in "Quorum"
    assert "2 ocurrencias agrupadas" in brief
    assert "(Agrupado)" in brief
