from __future__ import annotations

import asyncio
import time
from dataclasses import asdict, dataclass
from typing import Any, Callable, Dict, Optional

from cognition.fallback_engine import FallbackOptions
from cognition.genesis_sandbox import GenesisSandbox
from core.action_dispatcher import DispatchResult
from core.iafa_auditor import IafaAuditor
from core.task_envelope import TaskEnvelope


COGNITIVE_LOOP_VERSION = "cognitive-loop.v1"

DialogFactory = Callable[[FallbackOptions], Any]


class CognitiveLoopError(ValueError):
    """Raised when the cognitive loop cannot safely continue."""


@dataclass(frozen=True)
class CognitiveLoopResult:
    selected_action: str
    status: str
    task_id: str
    details: Dict[str, Any]

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class CognitiveOrchestrator:
    """
    Nervous-system coordinator between backend fallback reasoning and Qt UI.

    The orchestrator awaits a PySide signal through an asyncio.Future, so qasync
    keeps the GUI loop alive without polling or blocking calls.
    """

    def __init__(
        self,
        fallback_engine: Any,
        auditor: Optional[IafaAuditor] = None,
        dispatcher: Optional[Any] = None,
        genesis_sandbox: Optional[GenesisSandbox] = None,
        dialog_factory: Optional[DialogFactory] = None,
    ) -> None:
        self.fallback_engine = fallback_engine
        self.auditor = auditor
        self.dispatcher = dispatcher
        self.genesis_sandbox = genesis_sandbox
        self.dialog_factory = dialog_factory or self._default_dialog_factory

    async def handle_fallback_cycle(
        self,
        dispatch_result: DispatchResult,
        envelope: TaskEnvelope,
    ) -> CognitiveLoopResult:
        self._validate_inputs(dispatch_result, envelope)

        fallback_options = await self.fallback_engine.generate_hypotheses(dispatch_result, envelope)
        dialog = self.dialog_factory(fallback_options)
        selected_action = await self._await_dialog_selection(dialog)
        result = await self._route_human_selection(selected_action, dispatch_result, envelope, fallback_options)
        return result

    async def handle_evolutionary_doubt(
        self,
        fallback_options: FallbackOptions,
    ) -> CognitiveLoopResult:
        """
        Specialized entry point for handling evolutionary doubt from SparkEngine.
        Does not generate hypotheses; uses provided ones and routes selection.
        """
        if not isinstance(fallback_options, FallbackOptions):
            raise CognitiveLoopError("fallback_options must be a FallbackOptions")

        dialog = self.dialog_factory(fallback_options)
        selected_action = await self._await_dialog_selection(dialog)
        
        # Fake dispatch result for routing compatibility
        fake_dispatch = DispatchResult(
            status="spark_reflection",
            ui_state="evolutionary_doubt",
            iafa_score=0.5,
            threshold=0.7,
            action="spark_reflection",
            task_id=fallback_options.task_id,
            details={"source": "spark_engine"}
        )
        # Fake envelope for routing compatibility
        fake_envelope = TaskEnvelope.from_text(
            text="SparkEngine proactive reflection",
            origin="spark_engine",
            declared_intent="evolutionary_reflection"
        )
        
        result = await self._route_human_selection(selected_action, fake_dispatch, fake_envelope, fallback_options)
        return result

    async def _await_dialog_selection(self, dialog: Any) -> str:
        loop = asyncio.get_running_loop()
        future: asyncio.Future[str] = loop.create_future()

        def complete(action_type: str) -> None:
            if not future.done():
                future.set_result(str(action_type))

        def complete_as_abort(*_: Any) -> None:
            if not future.done():
                future.set_result("abort")

        close_signal_names = ("destroyed", "rejected", "finished")

        try:
            dialog.actionSelected.connect(complete)
            for signal_name in close_signal_names:
                signal = getattr(dialog, signal_name, None)
                if signal is not None:
                    signal.connect(complete_as_abort)
            if hasattr(dialog, "show"):
                dialog.show()

            return await future
        finally:
            self._disconnect_signal(dialog, "actionSelected", complete)
            for signal_name in close_signal_names:
                self._disconnect_signal(dialog, signal_name, complete_as_abort)
            self._dispose_dialog(dialog)

    async def _route_human_selection(
        self,
        selected_action: str,
        dispatch_result: DispatchResult,
        envelope: TaskEnvelope,
        fallback_options: FallbackOptions,
    ) -> CognitiveLoopResult:
        match selected_action:
            case "abort":
                result = CognitiveLoopResult(
                    selected_action=selected_action,
                    status="aborted",
                    task_id=envelope.task_id,
                    details={"message": "Humano aborto tarea"},
                )
            case "ask_human":
                result = CognitiveLoopResult(
                    selected_action=selected_action,
                    status="human_channel_opening",
                    task_id=envelope.task_id,
                    details={"message": "Abriendo canal de audio/texto"},
                )
            case "sandbox_code":
                result = CognitiveLoopResult(
                    selected_action=selected_action,
                    status="genesis_sandbox_routing",
                    task_id=envelope.task_id,
                    details={
                        "message": "Enrutando hacia GenesisEngine/GenesisSandbox",
                        "sandbox_available": self.genesis_sandbox is not None,
                    },
                )
            case _:
                result = CognitiveLoopResult(
                    selected_action=selected_action,
                    status="unknown_selection_aborted",
                    task_id=envelope.task_id,
                    details={"message": "Seleccion desconocida; abortando por seguridad"},
                )

        await self._audit_human_selection(dispatch_result, envelope, fallback_options, result)
        return result

    async def _audit_human_selection(
        self,
        dispatch_result: DispatchResult,
        envelope: TaskEnvelope,
        fallback_options: FallbackOptions,
        result: CognitiveLoopResult,
    ) -> None:
        if not self.auditor:
            return

        payload = {
            "timestamp": time.time(),
            "record_type": "human_fallback_selection",
            "cognitive_loop_version": COGNITIVE_LOOP_VERSION,
            "task": envelope.to_audit_record_details(),
            "dispatch_result": dispatch_result.to_dict(),
            "fallback_options": fallback_options.to_dict(),
            "result": result.to_dict(),
        }
        loop = asyncio.get_running_loop()
        await loop.run_in_executor(None, self._write_audit_payload_sync, payload)

    def _write_audit_payload_sync(self, payload: Dict[str, Any]) -> None:
        log_entry = self.auditor.encode_payload(payload)
        self.auditor._write_to_disk_sync(log_entry)

    @staticmethod
    def _disconnect_signal(dialog: Any, signal_name: str, callback: Callable[..., None]) -> None:
        signal = getattr(dialog, signal_name, None)
        if signal is None:
            return

        try:
            signal.disconnect(callback)
        except (RuntimeError, TypeError):
            return

    @staticmethod
    def _dispose_dialog(dialog: Any) -> None:
        try:
            if hasattr(dialog, "hide"):
                dialog.hide()
            if hasattr(dialog, "deleteLater"):
                dialog.deleteLater()
        except RuntimeError:
            return

    @staticmethod
    def _default_dialog_factory(fallback_options: FallbackOptions) -> Any:
        from ui.evolution_dialog import EvolutionDialog

        return EvolutionDialog(fallback_options)

    @staticmethod
    def _validate_inputs(dispatch_result: DispatchResult, envelope: TaskEnvelope) -> None:
        if not isinstance(dispatch_result, DispatchResult):
            raise CognitiveLoopError("dispatch_result must be a DispatchResult")
        if not isinstance(envelope, TaskEnvelope):
            raise CognitiveLoopError("envelope must be a TaskEnvelope")
