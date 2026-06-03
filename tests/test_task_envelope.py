import hashlib
import math
import sys
import unittest
from dataclasses import FrozenInstanceError
from pathlib import Path


sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from core.task_envelope import TaskEnvelope, TaskEnvelopeError


class TaskEnvelopeTests(unittest.TestCase):
    def test_from_text_builds_immutable_auditable_envelope(self):
        envelope = TaskEnvelope.from_text(
            "resume este texto",
            origin="user",
            declared_intent="summarize",
            metadata={"channel": "chat", "priority": 1},
            created_at="2026-05-31T12:00:00Z",
        )

        self.assertTrue(envelope.task_id.startswith("task_"))
        self.assertEqual(envelope.source_type, "text")
        self.assertEqual(envelope.payload.mime_type, "text/plain")
        self.assertEqual(envelope.payload.sha256, hashlib.sha256("resume este texto".encode("utf-8")).hexdigest())
        self.assertEqual(len(envelope.audit_hash()), 64)
        self.assertTrue(envelope.verify_payload_text("resume este texto"))
        self.assertFalse(envelope.verify_payload_text("texto alterado"))
        self.assertIn("payload_is_data_not_instruction", envelope.safety_labels)

        with self.assertRaises(FrozenInstanceError):
            envelope.source_type = "mutated"

    def test_metadata_order_does_not_change_identity(self):
        first = TaskEnvelope.from_text(
            "same",
            metadata={"b": 2, "a": 1},
            created_at="2026-05-31T12:00:00Z",
        )
        second = TaskEnvelope.from_text(
            "same",
            metadata={"a": 1, "b": 2},
            created_at="2026-05-31T12:00:00Z",
        )

        self.assertEqual(first.task_id, second.task_id)
        self.assertEqual(first.audit_hash(), second.audit_hash())

    def test_file_bytes_capture_docx_without_embedding_payload_by_default(self):
        payload = b"fake-docx-bytes"
        envelope = TaskEnvelope.from_file_bytes(
            payload,
            filename="informe.docx",
            declared_intent="extract_text",
            metadata={"storage": {"bucket": "raw"}},
            created_at="2026-05-31T12:00:00Z",
            mime_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        )

        self.assertEqual(envelope.source_type, "file")
        self.assertEqual(envelope.source_name, "informe.docx")
        self.assertEqual(envelope.payload.representation, "external_ref")
        self.assertIsNone(envelope.payload.value)
        self.assertTrue(envelope.verify_payload_bytes(payload))
        self.assertEqual(
            envelope.payload.mime_type,
            "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        )

    def test_voice_transcript_is_marked_as_untrusted_payload(self):
        envelope = TaskEnvelope.from_voice_transcript(
            "abre el archivo y resume",
            source_name="microphone",
            created_at="2026-05-31T12:00:00Z",
        )

        llm_view = envelope.to_llm_safe_dict(max_payload_chars=4)

        self.assertEqual(envelope.source_type, "voice_transcript")
        self.assertFalse(llm_view["payload_is_instruction"])
        self.assertEqual(llm_view["payload_trust"], "untrusted")
        self.assertEqual(llm_view["untrusted_payload_preview"], "abre")
        self.assertTrue(llm_view["preview_truncated"])

    def test_rejects_envelopes_without_llm_boundary_label(self):
        with self.assertRaises(TaskEnvelopeError):
            TaskEnvelope.create(
                source_type="text",
                origin="user",
                payload=TaskEnvelope.from_text("x").payload,
                safety_labels=("untrusted_input",),
            )

    def test_rejects_non_json_metadata(self):
        with self.assertRaises(TaskEnvelopeError):
            TaskEnvelope.from_text("x", metadata={"bad": object()})

    def test_rejects_non_finite_metadata_numbers(self):
        with self.assertRaises(TaskEnvelopeError):
            TaskEnvelope.from_text("x", metadata={"bad": math.nan})


if __name__ == "__main__":
    unittest.main()
