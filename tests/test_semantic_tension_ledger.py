import os
import json
import unittest
import tempfile
import time
from core.semantic_tension_ledger import SemanticTensionLedger, SemanticTensionEvent

class TestSemanticTensionLedger(unittest.TestCase):
    def setUp(self):
        self.test_dir = tempfile.TemporaryDirectory()
        self.ledger_path = os.path.join(self.test_dir.name, "ledger.jsonl")
        self.ledger = SemanticTensionLedger(ledger_path=self.ledger_path)

    def tearDown(self):
        self.test_dir.cleanup()

    def test_append_and_load(self):
        event = SemanticTensionEvent(
            event_id="ev1", timestamp=time.time(), source="test", event_type="timeout",
            task_id="t1", intent_category="cat", proposed_action="act",
            proposal_signature="cat:act", damage_delta=0.5
        )
        self.ledger.append_event(event)
        
        loaded = self.ledger.load_recent(limit=1)
        self.assertEqual(len(loaded), 1)
        self.assertEqual(loaded[0].event_id, "ev1")
        self.assertEqual(loaded[0].damage_delta, 0.5)

    def test_corrupt_line_handling(self):
        with open(self.ledger_path, "a") as f:
            f.write("invalid json\n")
        
        event = SemanticTensionEvent(
            event_id="ev2", timestamp=time.time(), source="test", event_type="error",
            task_id="t2", intent_category="cat", proposed_action="act",
            proposal_signature="cat:act"
        )
        self.ledger.append_event(event)
        
        loaded = self.ledger.load_recent(limit=10)
        self.assertEqual(len(loaded), 1)
        self.assertEqual(loaded[0].event_id, "ev2")

    def test_damage_accumulation_and_suppression(self):
        sig = "annoying:intent"
        # Agregamos varios eventos de daño
        for i in range(5):
            event = SemanticTensionEvent(
                event_id=f"ev_{i}", timestamp=time.time(), source="test", 
                event_type="rejected", task_id=f"t_{i}", 
                intent_category="annoying", proposed_action="intent",
                proposal_signature=sig, damage_delta=0.5
            )
            self.ledger.append_event(event)
        
        score = self.ledger.get_damage_score(sig)
        self.assertAlmostEqual(score, 2.5, places=5)
        self.assertTrue(self.ledger.should_suppress_proposal(sig, threshold=2.0))
        self.assertFalse(self.ledger.should_suppress_proposal("other:sig"))

    def test_mark_user_outcome(self):
        task_id = "task_to_mark"
        event = SemanticTensionEvent(
            event_id="ev_orig", timestamp=time.time(), source="test", 
            event_type="evolutionary_doubt", task_id=task_id, 
            intent_category="cat", proposed_action="act",
            proposal_signature="cat:act"
        )
        self.ledger.append_event(event)
        
        self.ledger.mark_user_outcome(task_id, "rejected")
        
        loaded = self.ledger.load_recent(limit=10)
        self.assertEqual(len(loaded), 2)
        self.assertEqual(loaded[1].event_type, "outcome_update")
        self.assertEqual(loaded[1].user_outcome, "rejected")
        self.assertEqual(loaded[1].damage_delta, 0.5)

if __name__ == "__main__":
    unittest.main()
