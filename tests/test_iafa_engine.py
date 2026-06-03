import math
import sys
import unittest
from pathlib import Path


sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from core.iafa_core import IafaCore
from core.iafa_engine import IAFAEngine, IAFAInputError


class IAFAEngineTests(unittest.TestCase):
    def setUp(self):
        self.weights = {
            "O": 0.1,
            "M": 0.2,
            "P": 0.3,
            "V": 0.2,
            "K": 0.2,
            "R": -0.4,
            "I": -0.3,
            "N": -0.2,
            "A": 0.8,
        }
        self.context = {
            "O": 0.9,
            "M": 0.9,
            "P": 0.9,
            "V": 0.9,
            "K": 0.9,
            "R": 0.1,
            "I": 0.1,
            "N": 0.1,
            "A": 0.8,
        }

    def test_calculates_deterministic_score_with_breakdown(self):
        engine = IAFAEngine(self.weights, bias=0.1)

        breakdown = engine.score(self.context, ["test"], 0.5)

        self.assertEqual(breakdown.score, engine.calculate_iafa_score(self.context, ["test"], 0.5))
        self.assertGreaterEqual(breakdown.score, 0.0)
        self.assertLessEqual(breakdown.score, 1.0)
        self.assertEqual(breakdown.entropy, 0.0)
        self.assertEqual(breakdown.recent_intents_count, 1)
        self.assertEqual(breakdown.variables["A"], 0.8)

    def test_entropy_uses_intent_distribution(self):
        entropy = IAFAEngine.shannon_entropy(["a", "a", "b", "b"])

        self.assertTrue(math.isclose(entropy, 1.0))

    def test_evaluate_action_returns_decision_not_side_effects(self):
        engine = IAFAEngine(self.weights, bias=0.1)

        decision = engine.evaluate_action("process_document", self.context, ["test"], 0.5, threshold=0.6)

        self.assertTrue(decision.allowed)
        self.assertEqual(decision.action_name, "process_document")
        self.assertEqual(decision.reason, "score_meets_threshold")
        self.assertGreaterEqual(decision.score, decision.threshold)

    def test_rejects_non_finite_input(self):
        engine = IAFAEngine(self.weights)
        context = dict(self.context)
        context["A"] = float("nan")

        with self.assertRaises(IAFAInputError):
            engine.calculate_iafa_score(context, ["test"], 0.5)

    def test_legacy_core_name_still_works(self):
        engine = IafaCore(self.weights, bias=0.1)

        self.assertIsInstance(engine, IAFAEngine)
        self.assertGreater(engine.calculate_iafa_score(self.context, ["test"], 0.5), 0.0)


if __name__ == "__main__":
    unittest.main()
