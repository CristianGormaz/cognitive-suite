import unittest
from core.experimental_risk_profile import ExperimentalRiskProfile

class TestExperimentalRiskProfile(unittest.TestCase):
    def test_risk_profile_low(self):
        # consultor_tiempo_local debe ser riesgo bajo
        profile = ExperimentalRiskProfile.for_skill(
            "consultor_tiempo_local", 
            is_allowlisted=True,
            human_review_status="approved_for_future_promotion",
            sandbox_safe=True
        )
        self.assertEqual(profile.risk_level, "low")
        self.assertEqual(profile.iafa_risk_adjustment["R"], 0.1)
        self.assertFalse(profile.uses_network)

    def test_risk_profile_medium(self):
        # pdf_reader debe ser riesgo medio
        profile = ExperimentalRiskProfile.for_skill(
            "pdf_reader", 
            is_allowlisted=True,
            human_review_status="approved_for_future_promotion",
            sandbox_safe=True
        )
        self.assertEqual(profile.risk_level, "medium")
        self.assertEqual(profile.iafa_risk_adjustment["R"], 0.3)
        self.assertTrue(profile.reads_files)

    def test_risk_profile_critical_untrusted(self):
        # Skill no permitida o no aprobada por humano
        profile = ExperimentalRiskProfile.for_skill(
            "any_skill",
            is_allowlisted=False,
            human_review_status="pending",
            sandbox_safe=False
        )
        self.assertEqual(profile.risk_level, "critical")
        self.assertEqual(profile.iafa_risk_adjustment["R"], 0.9)

if __name__ == "__main__":
    unittest.main()
