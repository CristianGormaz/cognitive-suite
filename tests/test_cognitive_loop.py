import asyncio
import sys
import tempfile
import threading
import unittest
from pathlib import Path


sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from cognition.fallback_engine import FallbackHypothesis, FallbackOptions
from core.action_dispatcher import DispatchResult
from core.cognitive_loop import CognitiveLoopError, CognitiveOrchestrator
from core.iafa_auditor import IafaAuditor
from core.task_envelope import TaskEnvelope


class FakeSignal:
    def __init__(self):
        self.callbacks = []

    def connect(self, callback):
        self.callbacks.append(callback)

    def disconnect(self, callback):
        if callback not in self.callbacks:
            raise RuntimeError("callback is not connected")
        self.callbacks.remove(callback)

    def emit(self, *args):
        for callback in list(self.callbacks):
            callback(*args)


class FakeDialog:
    def __init__(self, fallback_options, emitted_signal="actionSelected", action_type="abort"):
        self.fallback_options = fallback_options
        self.emitted_signal = emitted_signal
        self.action_type = action_type
        self.actionSelected = FakeSignal()
        self.destroyed = FakeSignal()
        self.rejected = FakeSignal()
        self.finished = FakeSignal()
        self.shown = False
        self.hidden = False
        self.deleted = False

    def show(self):
        self.shown = True
        loop = asyncio.get_running_loop()
        if self.emitted_signal == "actionSelected":
            loop.call_soon(self.actionSelected.emit, self.action_type)
        elif self.emitted_signal == "destroyed":
            loop.call_soon(self.destroyed.emit, self)
        elif self.emitted_signal == "rejected":
            loop.call_soon(self.rejected.emit)
        elif self.emitted_signal == "finished":
            loop.call_soon(self.finished.emit, 0)

    def hide(self):
        self.hidden = True

    def deleteLater(self):
        self.deleted = True


class FakeDialogFactory:
    def __init__(self, emitted_signal="actionSelected", action_type="abort"):
        self.emitted_signal = emitted_signal
        self.action_type = action_type
        self.dialogs = []

    def __call__(self, fallback_options):
        dialog = FakeDialog(fallback_options, self.emitted_signal, self.action_type)
        self.dialogs.append(dialog)
        return dialog


class FakeFallbackEngine:
    def __init__(self, options):
        self.options = options
        self.calls = []

    async def generate_hypotheses(self, dispatch_result, envelope):
        self.calls.append((dispatch_result, envelope))
        return self.options


class ThreadRecordingAuditor(IafaAuditor):
    def __init__(self, log_path, secret_key="test-secret"):
        super().__init__(log_path, secret_key)
        self.write_thread_ids = []

    def _write_to_disk_sync(self, log_entry):
        self.write_thread_ids.append(threading.get_ident())
        super()._write_to_disk_sync(log_entry)


def make_dispatch_result():
    return DispatchResult(
        status="blocked_fallback",
        ui_state="evolutionary_doubt",
        iafa_score=0.31,
        threshold=0.7,
        action="store_in_semantic_memory",
        task_id="task_loop",
        details={"fallback": "duda", "reason": "iafa_score_below_threshold"},
    )


def make_options(task_id="task_loop"):
    return FallbackOptions(
        task_id=task_id,
        source_status="blocked_fallback",
        ui_state="evolutionary_doubt",
        hypotheses=(
            FallbackHypothesis(
                id="opt_1",
                action_type="ask_human",
                label="Pedir aclaracion",
                description="Solicitar mas contexto al usuario.",
            ),
            FallbackHypothesis(
                id="opt_2",
                action_type="sandbox_code",
                label="Generar script seguro",
                description="Preparar codigo aislado para auditoria AST.",
            ),
            FallbackHypothesis(
                id="opt_3",
                action_type="abort",
                label="Descartar tarea",
                description="Cerrar el flujo sin cambios persistentes.",
            ),
        ),
    )


class CognitiveOrchestratorTests(unittest.TestCase):
    def setUp(self):
        self.dispatch_result = make_dispatch_result()
        self.envelope = TaskEnvelope.from_text(
            "entrada bloqueada",
            declared_intent="document_analysis",
            created_at="2026-05-31T12:00:00Z",
        )
        self.options = make_options(self.envelope.task_id)

    def test_abort_selection_waits_on_signal_cleans_dialog_and_audits(self):
        async def run_case():
            with tempfile.TemporaryDirectory() as temp_dir:
                auditor = ThreadRecordingAuditor(str(Path(temp_dir) / "audit.log"))
                fallback_engine = FakeFallbackEngine(self.options)
                dialog_factory = FakeDialogFactory(action_type="abort")
                orchestrator = CognitiveOrchestrator(
                    fallback_engine=fallback_engine,
                    auditor=auditor,
                    dialog_factory=dialog_factory,
                )
                loop_thread_id = threading.get_ident()

                result = await orchestrator.handle_fallback_cycle(self.dispatch_result, self.envelope)
                entries = list(auditor.iter_verified_entries())

                return result, entries, fallback_engine, dialog_factory.dialogs[0], auditor, loop_thread_id

        result, entries, fallback_engine, dialog, auditor, loop_thread_id = asyncio.run(run_case())

        self.assertEqual(result.selected_action, "abort")
        self.assertEqual(result.status, "aborted")
        self.assertEqual(result.details["message"], "Humano aborto tarea")
        self.assertEqual(fallback_engine.calls, [(self.dispatch_result, self.envelope)])
        self.assertTrue(dialog.shown)
        self.assertTrue(dialog.hidden)
        self.assertTrue(dialog.deleted)
        self.assertEqual(dialog.actionSelected.callbacks, [])
        self.assertEqual(dialog.destroyed.callbacks, [])
        self.assertEqual(dialog.rejected.callbacks, [])
        self.assertEqual(dialog.finished.callbacks, [])

        self.assertEqual(len(entries), 1)
        payload = entries[0]["payload"]
        self.assertEqual(payload["record_type"], "human_fallback_selection")
        self.assertEqual(payload["result"]["status"], "aborted")
        self.assertEqual(payload["result"]["selected_action"], "abort")
        self.assertEqual(payload["task"]["task_id"], self.envelope.task_id)
        self.assertTrue(auditor.write_thread_ids)
        self.assertNotEqual(auditor.write_thread_ids[0], loop_thread_id)

    def test_ask_human_selection_returns_channel_opening_result(self):
        async def run_case():
            orchestrator = CognitiveOrchestrator(
                fallback_engine=FakeFallbackEngine(self.options),
                dialog_factory=FakeDialogFactory(action_type="ask_human"),
            )
            return await orchestrator.handle_fallback_cycle(self.dispatch_result, self.envelope)

        result = asyncio.run(run_case())

        self.assertEqual(result.selected_action, "ask_human")
        self.assertEqual(result.status, "human_channel_opening")
        self.assertEqual(result.details["message"], "Abriendo canal de audio/texto")

    def test_sandbox_code_selection_simulates_genesis_sandbox_routing(self):
        async def run_case():
            orchestrator = CognitiveOrchestrator(
                fallback_engine=FakeFallbackEngine(self.options),
                genesis_sandbox=object(),
                dialog_factory=FakeDialogFactory(action_type="sandbox_code"),
            )
            return await orchestrator.handle_fallback_cycle(self.dispatch_result, self.envelope)

        result = asyncio.run(run_case())

        self.assertEqual(result.selected_action, "sandbox_code")
        self.assertEqual(result.status, "genesis_sandbox_routing")
        self.assertTrue(result.details["sandbox_available"])

    def test_dialog_destroyed_before_selection_resolves_as_abort(self):
        async def run_case():
            dialog_factory = FakeDialogFactory(emitted_signal="destroyed")
            orchestrator = CognitiveOrchestrator(
                fallback_engine=FakeFallbackEngine(self.options),
                dialog_factory=dialog_factory,
            )
            result = await orchestrator.handle_fallback_cycle(self.dispatch_result, self.envelope)
            return result, dialog_factory.dialogs[0]

        result, dialog = asyncio.run(run_case())

        self.assertEqual(result.selected_action, "abort")
        self.assertEqual(result.status, "aborted")
        self.assertTrue(dialog.deleted)
        self.assertEqual(dialog.destroyed.callbacks, [])

    def test_rejected_signal_before_selection_resolves_as_abort(self):
        async def run_case():
            orchestrator = CognitiveOrchestrator(
                fallback_engine=FakeFallbackEngine(self.options),
                dialog_factory=FakeDialogFactory(emitted_signal="rejected"),
            )
            return await orchestrator.handle_fallback_cycle(self.dispatch_result, self.envelope)

        result = asyncio.run(run_case())

        self.assertEqual(result.selected_action, "abort")
        self.assertEqual(result.status, "aborted")

    def test_rejects_invalid_inputs_before_generating_options(self):
        fallback_engine = FakeFallbackEngine(self.options)
        orchestrator = CognitiveOrchestrator(fallback_engine=fallback_engine)

        with self.assertRaises(CognitiveLoopError):
            asyncio.run(orchestrator.handle_fallback_cycle({"bad": "result"}, self.envelope))

        self.assertEqual(fallback_engine.calls, [])


if __name__ == "__main__":
    unittest.main()
