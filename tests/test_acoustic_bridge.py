import asyncio
import sys
import unittest
from pathlib import Path


sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from core.iafa_auditor import IafaAuditor
from perception.acoustic_bridge import AcousticBridge, AcousticInputUnavailableError


async def inline_executor(function, *args):
    return function(*args)


class InMemoryAuditor(IafaAuditor):
    def __init__(self):
        super().__init__(log_path="unused.log", secret_key="test-secret")
        self.payloads = []

    async def append_payload(self, payload):
        self.payloads.append(payload)


class FakeRecognizerBackend:
    def __init__(self, phrases=None, error=None):
        self.phrases = list(phrases or [])
        self.error = error
        self.calls = 0

    def recognize_forever(self, stop_event, emit_text):
        self.calls += 1
        if self.error is not None:
            raise self.error
        for phrase in self.phrases:
            if stop_event.is_set():
                break
            emit_text(phrase)


class AcousticBridgeTests(unittest.TestCase):
    def test_listen_continuously_emits_to_callback_and_queue(self):
        async def run_case():
            queue = asyncio.Queue()
            recognized = []
            backend = FakeRecognizerBackend(phrases=["hola Greys", "inicia auditoria"])

            bridge = AcousticBridge(
                on_text_recognized_callback=recognized.append,
                recognized_text_queue=queue,
                recognizer_backend=backend,
                piper_binary="/bin/cat",
                executor_runner=inline_executor,
            )
            await bridge.listen_continuously()
            await asyncio.sleep(0)

            queued = [await queue.get(), await queue.get()]
            return recognized, queued, backend.calls, bridge.is_muted

        recognized, queued, backend_calls, is_muted = asyncio.run(run_case())

        self.assertEqual(backend_calls, 1)
        self.assertEqual(recognized, ["hola Greys", "inicia auditoria"])
        self.assertEqual(queued, ["hola Greys", "inicia auditoria"])
        self.assertFalse(is_muted)

    def test_microphone_unavailable_degrades_to_mute_and_audits(self):
        async def run_case():
            auditor = InMemoryAuditor()
            backend = FakeRecognizerBackend(error=AcousticInputUnavailableError("mic offline"))
            bridge = AcousticBridge(
                auditor=auditor,
                recognizer_backend=backend,
                piper_binary="/bin/cat",
                executor_runner=inline_executor,
            )

            await bridge.listen_continuously()
            speak_result = await bridge.speak("texto de prueba")
            return bridge, speak_result, auditor.payloads

        bridge, speak_result, entries = asyncio.run(run_case())

        self.assertTrue(bridge.is_muted)
        self.assertIn("mic offline", bridge.last_error or "")
        self.assertFalse(speak_result)
        self.assertEqual(entries[0]["record_type"], "acoustic_bridge_muted")
        self.assertEqual(entries[1]["record_type"], "acoustic_tts_skipped")

    def test_speak_failure_is_handled_and_audited(self):
        async def run_case():
            auditor = InMemoryAuditor()
            bridge = AcousticBridge(
                auditor=auditor,
                recognizer_backend=FakeRecognizerBackend(),
                piper_binary="/__missing__/piper",
                executor_runner=inline_executor,
            )

            result = await bridge.speak("hola")
            return result, bridge.last_error, auditor.payloads

        result, last_error, entries = asyncio.run(run_case())

        self.assertFalse(result)
        self.assertIn("Piper binary not found", last_error or "")
        self.assertEqual(len(entries), 1)
        self.assertEqual(entries[0]["record_type"], "acoustic_tts_error")


if __name__ == "__main__":
    unittest.main()
