import json
from unittest.mock import MagicMock
from cognition.morning_brief import MorningBrief

def test_morning_brief_deduplicates_reflex_promotions(tmp_path):
    brief_gen = MorningBrief(memory_dir=str(tmp_path))
    brief_gen.promotion_gate = MagicMock()
    brief_gen.neural_layer = MagicMock()
    
    # Mock neural layer patterns
    p1 = {"pattern_id": "p1", "pattern_name": "math_debt"}
    p2 = {"pattern_id": "p2", "pattern_name": "math_debt"}
    brief_gen.neural_layer.patterns = [p1, p2]
    
    # Mock promotion gate
    brief_gen.promotion_gate.get_active_reflexes.return_value = []
    
    # Mock assess_pattern_for_promotion and shadow stats
    assessment = MagicMock()
    assessment.promotion_allowed = False
    assessment.reason_summary = "Blocked"
    assessment.context_score = 0.8
    assessment.risk_score = 0.1
    brief_gen.promotion_gate.assess_pattern_for_promotion.return_value = assessment
    brief_gen.promotion_gate._get_pattern_shadow_stats.return_value = {"agreement_rate": 0.5}
    
    brief = brief_gen.generate_brief()
    
    # Should only show math_debt once with "agrupadas"
    assert brief.count("math_debt") == 1
    assert "2 señales agrupadas" in brief
