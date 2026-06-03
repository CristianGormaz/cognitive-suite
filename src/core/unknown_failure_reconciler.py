from __future__ import annotations

import json
import logging
import time
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional

logger = logging.getLogger("UnknownFailureReconciler")

RECONCILIATION_LEDGER_VERSION = "unknown-reconciliation.v1"
TAXONOMY_TIMESTAMP = 1780495971.0

@dataclass(frozen=True)
class UnknownFailureReclassification:
    event_id: str
    timestamp: float
    original_event_ref: str
    original_failure_type: str
    original_stage: str
    inferred_failure_type: str
    confidence: float
    historical_debt: bool
    post_taxonomy_event: bool
    safe_reason: str
    evidence_fields_used: List[str] = field(default_factory=list)
    schema_version: str = RECONCILIATION_LEDGER_VERSION

    def to_json(self) -> str:
        return json.dumps(asdict(self))

class UnknownFailureReconciler:
    """
    Reclasifica eventos unknown_failure de forma derivada.
    Permite limpiar el reporte sin alterar la evidencia original.
    """

    def __init__(self, taxonomy_timestamp: float, reconciliation_path: str = "assets/memory/unknown_failure_reconciliation_ledger.jsonl"):
        self.taxonomy_timestamp = taxonomy_timestamp
        self.reconciliation_path = Path(reconciliation_path)
        self._ensure_dir()

    def _ensure_dir(self):
        if not self.reconciliation_path.parent.exists():
            self.reconciliation_path.parent.mkdir(parents=True, exist_ok=True)

    def reconcile_event(self, event: Dict[str, Any]) -> Optional[UnknownFailureReclassification]:
        if event.get("failure_type") != "unknown_failure":
            return None
        
        orig_id = event.get("event_id", "unknown")
        timestamp = event.get("timestamp", 0.0)
        stage = event.get("failure_stage", "unknown_stage")
        err_type = event.get("error_type", "UnknownError")
        err_summary = event.get("error_summary", "").lower()
        
        historical = timestamp < self.taxonomy_timestamp
        post_taxonomy = not historical
        
        inferred_type = "legacy_unknown_unclassified"
        confidence = 0.1
        evidence = []
        
        # Lógica de inferencia
        if stage == "process_envelope":
            if "task_id" in err_summary and "missing" in err_summary:
                inferred_type = "process_envelope_missing_task_id"
                confidence = 0.9
                evidence = ["err_summary", "stage"]
            elif any(k in err_summary for k in ["contract", "missing field", "missing payload", "payload", "invalid envelope", "invalid field", "field"]):
                inferred_type = "process_envelope_contract_error"
                confidence = 0.8
                evidence = ["err_summary", "stage"]
            elif "router" in err_summary or "route" in err_summary:
                inferred_type = "process_envelope_local_router_error"
                confidence = 0.7
                evidence = ["err_summary", "stage"]
            elif "planner" in err_summary or "plan" in err_summary:
                inferred_type = "process_envelope_planner_result_invalid"
                confidence = 0.7
                evidence = ["err_summary", "stage"]
            elif "coroutine" in err_summary and "iterable" in err_summary:
                inferred_type = "process_envelope_unhandled_exception"
                confidence = 0.9
                evidence = ["err_summary", "stage"]
                # Nota: Esto parece ser un bug de async missing await.
            elif "gate" in err_summary or "blocked" in err_summary:
                inferred_type = "process_envelope_policy_block"
                confidence = 0.8
                evidence = ["err_summary", "stage"]
            else:
                inferred_type = "unknown_failure_process_envelope"
                confidence = 0.4
                evidence = ["stage"]
        
        # Otros escenarios comunes antes de la taxonomía
        if inferred_type == "legacy_unknown_unclassified":
            if "ollama" in err_summary or "timeout" in err_summary:
                inferred_type = "llm_timeout"
                confidence = 0.8
                evidence = ["err_summary"]
            elif "json" in err_summary or "parse" in err_summary:
                inferred_type = "llm_malformed_json"
                confidence = 0.8
                evidence = ["err_summary"]

        reclass = UnknownFailureReclassification(
            event_id=f"reco_{orig_id}",
            timestamp=time.time(),
            original_event_ref=orig_id,
            original_failure_type="unknown_failure",
            original_stage=stage,
            inferred_failure_type=inferred_type,
            confidence=confidence,
            historical_debt=historical,
            post_taxonomy_event=post_taxonomy,
            safe_reason=f"Derivative inference from legacy {err_type}",
            evidence_fields_used=evidence
        )
        
        self.write_reconciliation_event(reclass)
        return reclass

    def write_reconciliation_event(self, reclass: UnknownFailureReclassification):
        try:
            with open(self.reconciliation_path, "a", encoding="utf-8") as f:
                f.write(reclass.to_json() + "\n")
        except Exception as exc:
            logger.error(f"Error escribiendo en ledger de reconciliación: {exc}")

    def load_all_reclassifications(self) -> Dict[str, UnknownFailureReclassification]:
        """Carga todas las reclasificaciones por ID de evento original."""
        results = {}
        if not self.reconciliation_path.exists():
            return results
        
        try:
            with open(self.reconciliation_path, "r", encoding="utf-8") as f:
                for line in f:
                    if not line.strip(): continue
                    try:
                        data = json.loads(line)
                        reco = UnknownFailureReclassification(**data)
                        results[reco.original_event_ref] = reco
                    except Exception:
                        continue
        except Exception as exc:
            logger.error(f"Error leyendo ledger de reconciliación: {exc}")
        return results
