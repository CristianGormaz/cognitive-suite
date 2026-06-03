import asyncio
import json
import sys
import tempfile
import unittest
from pathlib import Path


sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from core.iafa_auditor import IafaAuditError, IafaAuditRecord, IafaAuditor
from core.iafa_engine import IAFAEngine
from core.iafa_gatekeeper import IafaGatekeeper
from core.task_envelope import TaskEnvelope


class IafaAuditorTests(unittest.TestCase):
    def test_encode_decode_and_verify_entry(self):
        auditor = IafaAuditor(secret_key="test-secret")
        record = IafaAuditRecord(
            timestamp=1.0,
            action="process_document",
            score=0.75,
            threshold=0.7,
            allowed=True,
            details={"reason": "score_meets_threshold"},
        )

        line = auditor.encode_entry(record)
        entry = auditor.decode_entry(line)

        self.assertTrue(auditor.verify_entry(entry))
        self.assertEqual(entry["payload"]["action"], "process_document")

    def test_rejects_tampered_entry(self):
        auditor = IafaAuditor(secret_key="test-secret")
        record = IafaAuditRecord(
            timestamp=1.0,
            action="process_document",
            score=0.75,
            threshold=0.7,
            allowed=True,
        )
        entry = json.loads(auditor.encode_entry(record))
        entry["payload"]["score"] = 0.1

        with self.assertRaises(IafaAuditError):
            auditor.decode_entry(json.dumps(entry))

    def test_gatekeeper_logs_decision_without_engine_io(self):
        weights = {"P": 0.3, "V": 0.2, "A": 0.8}
        context = {"P": 0.9, "V": 0.9, "A": 0.8}

        with tempfile.TemporaryDirectory() as temp_dir:
            log_path = Path(temp_dir) / "iafa.log"
            auditor = IafaAuditor(str(log_path), secret_key="test-secret")
            gatekeeper = IafaGatekeeper(IAFAEngine(weights, bias=0.1), auditor)

            allowed = asyncio.run(
                gatekeeper.authorize_action(
                    "process_document",
                    context,
                    ["document"],
                    0.5,
                    threshold=0.6,
                )
            )

            self.assertTrue(allowed)
            entries = list(auditor.iter_verified_entries())
            self.assertEqual(len(entries), 1)
            self.assertEqual(entries[0]["payload"]["action"], "process_document")
            self.assertTrue(entries[0]["payload"]["allowed"])

    def test_gatekeeper_accepts_legacy_secret_key_argument(self):
        gatekeeper = IafaGatekeeper(IAFAEngine({"A": 0.8}), "legacy-secret")

        self.assertIsInstance(gatekeeper.auditor, IafaAuditor)

    def test_logs_task_envelope_event(self):
        envelope = TaskEnvelope.from_text(
            "texto no confiable",
            declared_intent="summarize",
            created_at="2026-05-31T12:00:00Z",
        )

        with tempfile.TemporaryDirectory() as temp_dir:
            log_path = Path(temp_dir) / "iafa.log"
            auditor = IafaAuditor(str(log_path), secret_key="test-secret")

            asyncio.run(
                auditor.log_task_envelope(
                    envelope,
                    event_name="task_envelope.created",
                    details={"stage": "ingestion"},
                    timestamp=1.0,
                )
            )

            entries = list(auditor.iter_verified_entries())

        self.assertEqual(len(entries), 1)
        payload = entries[0]["payload"]
        self.assertEqual(payload["record_type"], "task_envelope")
        self.assertEqual(payload["event"], "task_envelope.created")
        self.assertEqual(payload["task"]["task_id"], envelope.task_id)
        self.assertEqual(payload["task"]["audit_hash"], envelope.audit_hash())
        self.assertEqual(payload["details"]["stage"], "ingestion")

    def test_rejects_non_json_audit_payloads(self):
        auditor = IafaAuditor(secret_key="test-secret")

        with self.assertRaises(IafaAuditError):
            auditor.encode_payload({"record_type": "bad", "value": float("nan")})


if __name__ == "__main__":
    unittest.main()
