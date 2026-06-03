import asyncio
import json
import sys
import unittest
from pathlib import Path


sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from cognition.iafa_transceiver import IafaTransceiver
from core.task_envelope import TaskEnvelope


class CapturingTransceiver(IafaTransceiver):
    def __init__(self):
        super().__init__(host="http://test.local")
        self.last_endpoint = None
        self.last_payload = None

    async def _safe_request(self, endpoint, payload, **kwargs):
        self.last_endpoint = endpoint
        self.last_payload = payload
        return {"response": '{"status": "ok"}'}


class IafaTransceiverTests(unittest.TestCase):
    def test_build_prompt_uses_llm_safe_task_envelope(self):
        envelope = TaskEnvelope.from_text(
            "contenido largo",
            declared_intent="summarize",
            created_at="2026-05-31T12:00:00Z",
        )
        transceiver = IafaTransceiver()

        prompt = transceiver.build_prompt(
            envelope,
            operator_instruction="resume",
            max_payload_chars=9,
        )
        prompt_payload = json.loads(prompt)

        self.assertEqual(prompt_payload["task_envelope"]["task_id"], envelope.task_id)
        self.assertEqual(prompt_payload["task_envelope"]["payload_trust"], "untrusted")
        self.assertFalse(prompt_payload["task_envelope"]["payload_is_instruction"])
        self.assertEqual(prompt_payload["task_envelope"]["untrusted_payload_preview"], "contenido")
        self.assertTrue(prompt_payload["task_envelope"]["preview_truncated"])
        self.assertEqual(prompt_payload["operator_instruction"], "resume")

    def test_query_llm_sends_envelope_prompt_to_ollama(self):
        envelope = TaskEnvelope.from_text("hola", created_at="2026-05-31T12:00:00Z")
        transceiver = CapturingTransceiver()

        response = asyncio.run(transceiver.query_llm(envelope, system_prompt="sistema", json_format=True))

        self.assertEqual(response, '{"status": "ok"}')
        self.assertEqual(transceiver.last_endpoint, "/api/generate")
        self.assertEqual(transceiver.last_payload["model"], "deepseek-r1:8b")
        self.assertEqual(transceiver.last_payload["system"], "sistema")
        self.assertEqual(transceiver.last_payload["format"], "json")
        prompt_payload = json.loads(transceiver.last_payload["prompt"])
        self.assertEqual(prompt_payload["task_envelope"]["task_id"], envelope.task_id)

    def test_rejects_plain_text_prompt(self):
        with self.assertRaises(TypeError):
            IafaTransceiver().build_prompt("hola")


if __name__ == "__main__":
    unittest.main()
