import os
import json
import unittest
import tempfile
import time
from cognition.dream_question_ledger import DreamQuestionLedger, DreamQuestionEntry

class TestDreamQuestionLedger(unittest.TestCase):
    def setUp(self):
        self.test_dir = tempfile.TemporaryDirectory()
        self.ledger_path = os.path.join(self.test_dir.name, "questions.jsonl")
        self.ledger = DreamQuestionLedger(ledger_path=self.ledger_path)

    def tearDown(self):
        self.test_dir.cleanup()

    def test_append_and_load(self):
        entry = DreamQuestionEntry(
            question_id="q1", timestamp=time.time(), cycle=1, topic="pdf",
            question_text_hash="h1", context_hash="c1", evidence_refs=["e1"],
            semantic_signature="sig1", depth_level=0, question_type="observation"
        )
        self.ledger.append_entry(entry)
        
        loaded = self.ledger.load_all()
        self.assertEqual(len(loaded), 1)
        self.assertEqual(loaded[0].semantic_signature, "sig1")

    def test_semantic_signature_consistency(self):
        sig1 = self.ledger.generate_semantic_signature("PDF", "obs", "ctx1")
        sig2 = self.ledger.generate_semantic_signature("pdf", "OBS", "ctx1")
        self.assertEqual(sig1, sig2)

    def test_calculate_understood_score(self):
        # JSON válido + keywords
        ans = '{"summary": "test", "micro-sprint": "build"}'
        score = self.ledger.calculate_understood_score(ans)
        self.assertGreaterEqual(score, 0.8)
        
        # Basura
        self.assertLess(self.ledger.calculate_understood_score("no se"), 0.7)

if __name__ == "__main__":
    unittest.main()
