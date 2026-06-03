import unittest
from core.experimental_risk_profile import ExperimentalRiskProfile

class TestPdfRiskProfile(unittest.TestCase):
    def test_pdf_reader_is_medium_risk(self):
        profile = ExperimentalRiskProfile.for_skill(
            "pdf_reader_basic", 
            is_allowlisted=True,
            human_review_status="approved_for_future_promotion",
            sandbox_safe=True
        )
        self.assertEqual(profile.risk_level, "medium")
        self.assertTrue(profile.reads_files)
        self.assertTrue(profile.handles_user_file)
        self.assertTrue(profile.requires_external_dependency)
        # R = 0.3 for medium risk
        self.assertEqual(profile.iafa_risk_adjustment["R"], 0.3)

if __name__ == "__main__":
    unittest.main()
