from __future__ import annotations

import json
import logging
import time
from dataclasses import asdict, dataclass, field
from typing import Any, Dict, List, Optional
from core.task_envelope import TaskEnvelope

logger = logging.getLogger("ProcessEnvelopeContract")

@dataclass(frozen=True)
class ProcessEnvelopeContractResult:
    valid: bool
    missing_fields: List[str] = field(default_factory=list)
    invalid_fields: List[str] = field(default_factory=list)
    task_id_present: bool = False
    task_type: str = "unknown"
    route_hint: str = "unknown"
    safe_summary: str = ""
    schema_version: str = "process-envelope-contract.v1"

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

class ProcessEnvelopeContract:
    """
    Valida la integridad estructural de los datos durante el ciclo process_envelope.
    Previene ruidos de tipo 'unknown' capturando inconsistencias de contrato.
    """

    def validate_envelope(self, envelope: Any) -> ProcessEnvelopeContractResult:
        if not isinstance(envelope, TaskEnvelope):
            return ProcessEnvelopeContractResult(valid=False, invalid_fields=["envelope_type"], safe_summary="Input is not a TaskEnvelope")
        
        missing = []
        if not envelope.task_id: missing.append("task_id")
        if not envelope.payload: missing.append("payload")
        if not envelope.origin: missing.append("origin")
        
        valid = len(missing) == 0
        return ProcessEnvelopeContractResult(
            valid=valid,
            missing_fields=missing,
            task_id_present=bool(envelope.task_id),
            task_type=envelope.source_type,
            safe_summary="Envelope structural validation" if valid else f"Missing fields: {', '.join(missing)}"
        )

    def validate_plan_result(self, plan: Any) -> ProcessEnvelopeContractResult:
        # Asumiendo CognitivePlan del LLMPlanner
        missing = []
        if not hasattr(plan, "task_id") or not plan.task_id: missing.append("task_id")
        if not hasattr(plan, "decision") or not plan.decision: missing.append("decision")
        
        if not missing and hasattr(plan, "decision"):
            d = plan.decision
            if not hasattr(d, "intent_category") or not d.intent_category: missing.append("intent_category")
            if not hasattr(d, "proposed_action") or not d.proposed_action: missing.append("proposed_action")

        valid = len(missing) == 0
        return ProcessEnvelopeContractResult(
            valid=valid,
            missing_fields=missing,
            task_id_present=hasattr(plan, "task_id") and bool(plan.task_id),
            route_hint=getattr(plan.decision, "proposed_action", "unknown") if not missing else "unknown",
            safe_summary="Planner result structural validation" if valid else f"Missing plan fields: {', '.join(missing)}"
        )

    def validate_dispatch_result(self, result: Any) -> ProcessEnvelopeContractResult:
        # Asumiendo DispatchResult del ActionDispatcher
        missing = []
        if not hasattr(result, "task_id") or not result.task_id: missing.append("task_id")
        if not hasattr(result, "status") or not result.status: missing.append("status")
        if not hasattr(result, "action") or not result.action: missing.append("action")

        valid = len(missing) == 0
        return ProcessEnvelopeContractResult(
            valid=valid,
            missing_fields=missing,
            task_id_present=hasattr(result, "task_id") and bool(result.task_id),
            route_hint=getattr(result, "action", "unknown") if not missing else "unknown",
            safe_summary="Dispatcher result structural validation" if valid else f"Missing dispatch fields: {', '.join(missing)}"
        )

    def summarize_contract_failure(self, res: ProcessEnvelopeContractResult) -> str:
        if res.valid: return "Contract OK"
        msg = []
        if res.missing_fields: msg.append(f"Missing: {res.missing_fields}")
        if res.invalid_fields: msg.append(f"Invalid: {res.invalid_fields}")
        return "; ".join(msg)
