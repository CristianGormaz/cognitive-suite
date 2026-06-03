from __future__ import annotations

import math
import time
from dataclasses import asdict, dataclass
from typing import Any, Dict, Mapping, Optional, Protocol, Sequence

from cognition.llm_planner import CognitivePlan
from core.iafa_auditor import IafaAuditor
from core.iafa_engine import IAFAEngine


DISPATCHER_VERSION = "action-dispatcher.v1"
PlanEnvelope = CognitivePlan


class ActionDispatcherError(ValueError):
    """Raised when an action plan cannot be dispatched."""


class MemoryWriter(Protocol):
    async def store_semantic(self, target_path: str, payload: Mapping[str, Any]) -> Dict[str, Any]:
        """Store semantic-memory payload and return a receipt."""


class InMemoryMemoryWriter:
    """
    Mock memory writer for the first execution boundary.

    It records semantic writes in memory so the dispatcher can be tested without
    creating storage side effects before the real memory subsystem exists.
    """

    def __init__(self) -> None:
        self.records: list[Dict[str, Any]] = []

    async def store_semantic(self, target_path: str, payload: Mapping[str, Any]) -> Dict[str, Any]:
        receipt = {
            "writer": self.__class__.__name__,
            "target_path": target_path,
            "record_index": len(self.records),
            "payload": dict(payload),
        }
        self.records.append(receipt)
        return {
            "writer": receipt["writer"],
            "target_path": receipt["target_path"],
            "record_index": receipt["record_index"],
        }


@dataclass(frozen=True)
class DispatchResult:
    status: str
    ui_state: str
    iafa_score: float
    threshold: float
    action: str
    task_id: str
    details: Dict[str, Any]

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class ActionDispatcher:
    """
    Motor boundary for validated cognitive plans.

    The dispatcher mixes LLM-estimated friction (R, I, N) with internal system
    purpose/criterion variables, asks IAFA for authorization, and only then
    routes execution payloads to action handlers.
    """

    def __init__(
        self,
        iafa_engine: IAFAEngine,
        auditor: Optional[IafaAuditor] = None,
        memory_writer: Optional[MemoryWriter] = None,
        threshold: float = 0.7,
        internal_context: Optional[Mapping[str, float]] = None,
        current_hz: float = 0.5,
    ) -> None:
        self.iafa_engine = iafa_engine
        self.auditor = auditor
        self.memory_writer = memory_writer or InMemoryMemoryWriter()
        self.threshold = _require_probability(threshold, "threshold")
        self.internal_context = self._normalize_internal_context(internal_context)
        self.current_hz = _require_non_negative_float(current_hz, "current_hz")

    async def dispatch(
        self,
        plan: PlanEnvelope,
        recent_intents: Optional[Sequence[str]] = None,
    ) -> DispatchResult:
        if not isinstance(plan, CognitivePlan):
            raise ActionDispatcherError("ActionDispatcher requires a CognitivePlan")

        context = self.build_iafa_context(plan)
        intents = list(recent_intents or [plan.decision.intent_category, plan.decision.proposed_action])
        iafa_score = self.iafa_engine.calculate_iafa_score(context, intents, self.current_hz)
        action = plan.decision.proposed_action

        if iafa_score < self.threshold:
            result = self._fallback_result(
                plan,
                iafa_score,
                "blocked_fallback",
                "evolutionary_doubt",
                {
                    "reason": "iafa_score_below_threshold",
                    "iafa_context": context,
                    "recent_intents": intents,
                },
            )
            await self._audit_blocked(plan, result)
            return result

        if action == "store_in_semantic_memory":
            receipt = await self._store_in_semantic_memory(plan)
            result = DispatchResult(
                status="executed",
                ui_state="action_executed",
                iafa_score=iafa_score,
                threshold=self.threshold,
                action=action,
                task_id=plan.task_id,
                details={
                    "receipt": receipt,
                    "iafa_context": context,
                },
            )
            await self._audit_executed(plan, result)
            return result

        if action == "respond":
            result = DispatchResult(
                status="executed",
                ui_state="action_executed",
                iafa_score=iafa_score,
                threshold=self.threshold,
                action=action,
                task_id=plan.task_id,
                details={
                    "iafa_context": context,
                    "message": "Response pending execution by orchestrator",
                },
            )
            await self._audit_executed(plan, result)
            return result

        # --- SOPORTE PARA ACCIONES DINÁMICAS (Habilidades) ---
        # Heurística: Si la acción tiene un prefijo de skill o si deseamos permitir 
        # ruteo dinámico, devolvemos 'executed'. Para evitar romper tests antiguos, 
        # por ahora solo permitiremos 'consultor_tiempo_local' explícitamente o
        # cualquier acción si el entorno lo habilita (vía auditor/context).
        
        allowed_dynamic = [
            "consultor_tiempo_local",
            "pdf_reader",
            "pdf_reader_basic",
            "docx_reader"
        ]
        
        if action in allowed_dynamic:
            result = DispatchResult(
                status="executed",
                ui_state="action_executed",
                iafa_score=iafa_score,
                threshold=self.threshold,
                action=action,
                task_id=plan.task_id,
                details={
                    "iafa_context": context,
                    "dynamic_routing": True,
                },
            )
            await self._audit_executed(plan, result)
            return result

        result = self._fallback_result(
            plan,
            iafa_score,
            "unsupported_fallback",
            "evolutionary_doubt",
            {
                "reason": "unsupported_action",
                "iafa_context": context,
                "supported_actions": ["store_in_semantic_memory", "respond"] + allowed_dynamic,
            },
        )
        await self._audit_blocked(plan, result, record_type="iafa_execution_unsupported")
        return result

    def build_iafa_context(self, plan: PlanEnvelope) -> Dict[str, float]:
        if not isinstance(plan, CognitivePlan):
            raise ActionDispatcherError("build_iafa_context requires a CognitivePlan")

        context = dict(self.internal_context)
        context.update(plan.to_iafa_context_overlay())
        return context

    async def _store_in_semantic_memory(self, plan: PlanEnvelope) -> Dict[str, Any]:
        payload = plan.decision.execution_payload
        return await self.memory_writer.store_semantic(
            payload.target_path,
            {
                "task_id": plan.task_id,
                "intent_category": plan.decision.intent_category,
                "proposed_action": plan.decision.proposed_action,
                "extracted_tags": list(payload.extracted_tags),
                "planner_version": plan.planner_version,
                "raw_response_sha256": plan.raw_response_sha256,
            },
        )

    def _fallback_result(
        self,
        plan: PlanEnvelope,
        iafa_score: float,
        status: str,
        ui_state: str,
        details: Dict[str, Any],
    ) -> DispatchResult:
        return DispatchResult(
            status=status,
            ui_state=ui_state,
            iafa_score=iafa_score,
            threshold=self.threshold,
            action=plan.decision.proposed_action,
            task_id=plan.task_id,
            details={
                "fallback": "duda",
                **details,
            },
        )

    async def _audit_blocked(
        self,
        plan: PlanEnvelope,
        result: DispatchResult,
        record_type: str = "iafa_execution_blocked",
    ) -> None:
        if not self.auditor:
            return

        await self.auditor.append_payload(
            {
                "timestamp": time.time(),
                "record_type": record_type,
                "dispatcher_version": DISPATCHER_VERSION,
                "task_id": plan.task_id,
                "plan": plan.to_dict(),
                "result": result.to_dict(),
            }
        )

    async def _audit_executed(self, plan: PlanEnvelope, result: DispatchResult) -> None:
        if not self.auditor:
            return

        await self.auditor.append_payload(
            {
                "timestamp": time.time(),
                "record_type": "iafa_execution_approved",
                "dispatcher_version": DISPATCHER_VERSION,
                "task_id": plan.task_id,
                "plan": plan.to_dict(),
                "result": result.to_dict(),
            }
        )

    @staticmethod
    def _normalize_internal_context(internal_context: Optional[Mapping[str, float]]) -> Dict[str, float]:
        defaults = {
            "O": 0.8,
            "M": 0.8,
            "P": 0.9,
            "V": 0.8,
            "K": 0.9,
            "A": 0.7,
        }
        if internal_context:
            defaults.update({key: _require_probability(value, f"internal_context.{key}") for key, value in internal_context.items()})
        return defaults


def _require_probability(value: Any, label: str) -> float:
    try:
        numeric_value = float(value)
    except (TypeError, ValueError) as exc:
        raise ActionDispatcherError(f"{label} must be numeric") from exc

    if not math.isfinite(numeric_value) or not 0.0 <= numeric_value <= 1.0:
        raise ActionDispatcherError(f"{label} must be between 0.0 and 1.0")
    return numeric_value


def _require_non_negative_float(value: Any, label: str) -> float:
    try:
        numeric_value = float(value)
    except (TypeError, ValueError) as exc:
        raise ActionDispatcherError(f"{label} must be numeric") from exc

    if not math.isfinite(numeric_value) or numeric_value < 0.0:
        raise ActionDispatcherError(f"{label} must be finite and non-negative")
    return numeric_value
