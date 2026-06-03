import os
import json
import unittest
import tempfile
import time
from core.ingestion_failure_ledger import IngestionFailureLedger, IngestionFailureEvent

class TestIngestionFailureLedger(unittest.TestCase):
    def setUp(self):
        self.test_dir = tempfile.TemporaryDirectory()
        self.ledger_path = os.path.join(self.test_dir.name, "failure_ledger.jsonl")
        self.ledger = IngestionFailureLedger(ledger_path=self.ledger_path)

    def tearDown(self):
        self.test_dir.cleanup()

    def test_append_and_load(self):
        event = IngestionFailureEvent(
            event_id="f1", timestamp=time.time(), source="test", task_id="t1",
            source_type="text", payload_mime_type="text/plain", payload_size_bytes=10,
            payload_sha256="sha", declared_intent=None, detected_intent="chat",
            proposed_action="respond", failure_type="unsupported_action",
            failure_stage="dispatch", error_type="ActionError", error_summary="fail",
            supported_actions=["respond"], missing_capability_signature="chat:respond",
            suggested_skill_category="responder_texto"
        )
        self.ledger.append_failure(event)
        
        loaded = self.ledger.load_recent(limit=1)
        self.assertEqual(len(loaded), 1)
        self.assertEqual(loaded[0].event_id, "f1")

    def test_top_missing_capabilities(self):
        # Registramos 3 fallos de la misma capacidad
        for i in range(3):
            event = IngestionFailureEvent(
                event_id=f"f_{i}", timestamp=time.time(), source="test", task_id=f"t_{i}",
                source_type="text", payload_mime_type="text/plain", payload_size_bytes=10,
                payload_sha256="sha", declared_intent=None, detected_intent="pdf_read",
                proposed_action="extract", failure_type="unsupported_action",
                failure_stage="dispatch", error_type="ActionError", error_summary="fail",
                supported_actions=[], missing_capability_signature="pdf_read:extract",
                suggested_skill_category="lector_pdf"
            )
            self.ledger.append_failure(event)
            
        top = self.ledger.get_top_missing_capabilities()
        self.assertEqual(top[0], ("pdf_read:extract", 3))
        self.assertTrue(self.ledger.should_propose_skill("pdf_read:extract", min_count=3))

    def test_classify_failure(self):
        self.assertEqual(self.ledger.classify_failure(RuntimeError("Ollama no respondió")), "llm_timeout")
        self.assertEqual(self.ledger.classify_failure(ValueError("unsupported_action")), "dispatcher_unsupported_action")

if __name__ == "__main__":
    unittest.main()
