from __future__ import annotations

import os
import time
import logging
import json
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional

logger = logging.getLogger("ReflexPromotionGate")

@dataclass(frozen=True)
class ReflexPromotionAssessment:
    pattern_id: str
    pattern_name: str
    agreement_rate: float
    context_score: float
    risk_score: float
    constraint_status: str # stable, blocked
    missing_context: List[str]
    promotion_allowed: bool
    requires_human_approval: bool
    recommended_target: str
    rollback_available: bool = True
    reason_summary: str = ""
    evidence_refs: List[str] = field(default_factory=list)
    schema_version: str = "reflex-promotion-assessment.v1"

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

class ReflexPromotionGate:
    """
    Gobernanza para la promoción de reflejos desde Shadow Mode a Active Local Decision.
    Valida criterios técnicos, contextuales y de seguridad.
    """

    def __init__(self, memory_dir: str = "assets/memory"):
        self.memory_dir = Path(memory_dir)
        self.promotion_ledger_path = self.memory_dir / "reflex_promotion_ledger.jsonl"
        self.shadow_ledger_path = self.memory_dir / "reflex_shadow_ledger.jsonl"
        self.distilled_ledger_path = self.memory_dir / "distilled_reasoning_ledger.jsonl"

    def assess_pattern_for_promotion(self, pattern_id: str, context_frame: Any) -> ReflexPromotionAssessment:
        """Realiza una evaluación completa para determinar si un patrón puede promoverse."""
        # 1. Obtener métricas de sombra
        stats = self._get_pattern_shadow_stats(pattern_id)
        
        # 2. Obtener metadatos del patrón
        pattern_data = self._get_pattern_metadata(pattern_id)
        if not pattern_data:
            return self._generate_failure_assessment(pattern_id, "pattern_not_found")

        # 3. Aplicar umbrales
        agreement_threshold = 0.90
        context_threshold = 0.85
        risk_max = 0.20
        
        agreement_ok = stats["agreement_rate"] >= agreement_threshold
        context_ok = context_frame.overall_context_score >= context_threshold
        risk_ok = pattern_data.get("risk_score", 1.0) <= risk_max
        constraints_ok = context_frame.constraint_context.status == "stable"
        
        allowed = all([agreement_ok, context_ok, risk_ok, constraints_ok])
        
        reasons = []
        if not agreement_ok: reasons.append(f"Agreement rate ({stats['agreement_rate']}) below {agreement_threshold}")
        if not context_ok: reasons.append(f"Context score ({context_frame.overall_context_score}) below {context_threshold}")
        if not risk_ok: reasons.append(f"Pattern risk ({pattern_data.get('risk_score')}) exceeds {risk_max}")
        if not constraints_ok: reasons.append(f"Constraints status is {context_frame.constraint_context.status}")

        return ReflexPromotionAssessment(
            pattern_id=pattern_id,
            pattern_name=pattern_data.get("pattern_name", "unknown"),
            agreement_rate=stats["agreement_rate"],
            context_score=context_frame.overall_context_score,
            risk_score=pattern_data.get("risk_score", 1.0),
            constraint_status=context_frame.constraint_context.status,
            missing_context=context_frame.missing_context,
            promotion_allowed=allowed,
            requires_human_approval=True,
            recommended_target=pattern_data.get("target_module", "LocalIntentRouter"),
            reason_summary="; ".join(reasons) if not allowed else "Criterios de promoción cumplidos."
        )

    def approve_promotion(self, pattern_id: str, reason: str) -> bool:
        """Registra la aprobación humana de un reflejo."""
        # En una versión real, esto validaría que el patrón sea elegible.
        # Por ahora, simplemente registramos el evento de activación.
        record = {
            "event_id": f"prom_{os.urandom(4).hex()}",
            "timestamp": time.time(),
            "pattern_id": pattern_id,
            "human_approved": True,
            "activation_status": "active_local",
            "reason_summary": reason,
            "schema_version": "reflex-promotion-record.v1"
        }
        return self._persist_promotion_record(record)

    def disable_reflex(self, pattern_id: str, reason: str) -> bool:
        """Desactiva o revierte un reflejo activo."""
        record = {
            "event_id": f"rev_{os.urandom(4).hex()}",
            "timestamp": time.time(),
            "pattern_id": pattern_id,
            "human_approved": True,
            "activation_status": "disabled",
            "reason_summary": reason,
            "schema_version": "reflex-promotion-record.v1"
        }
        return self._persist_promotion_record(record)

    def get_active_reflexes(self) -> List[str]:
        """Devuelve los IDs de los reflejos que están actualmente aprobados y activos."""
        active = {}
        if not self.promotion_ledger_path.exists(): return []
        
        try:
            with open(self.promotion_ledger_path, "r", encoding="utf-8") as f:
                for line in f:
                    if not line.strip(): continue
                    data = json.loads(line)
                    pid = data.get("pattern_id")
                    status = data.get("activation_status")
                    active[pid] = status
        except Exception: pass
        
        return [pid for pid, status in active.items() if status == "active_local"]

    def _get_pattern_shadow_stats(self, pattern_id: str) -> Dict[str, Any]:
        """Calcula estadísticas de sombra para un patrón específico."""
        total = 0
        agreements = 0
        if not self.shadow_ledger_path.exists():
            return {"agreement_rate": 0.0}
            
        try:
            with open(self.shadow_ledger_path, "r", encoding="utf-8") as f:
                for line in f:
                    if not line.strip(): continue
                    data = json.loads(line)
                    if data.get("matched_pattern_id") == pattern_id:
                        total += 1
                        if data.get("agreement_with_real_route"): agreements += 1
        except Exception: pass
        
        return {"agreement_rate": round(agreements / total, 2) if total > 0 else 0.0}

    def _get_pattern_metadata(self, pattern_id: str) -> Optional[Dict[str, Any]]:
        """Busca el patrón en el ledger de destilación."""
        if not self.distilled_ledger_path.exists(): return None
        try:
            with open(self.distilled_ledger_path, "r", encoding="utf-8") as f:
                for line in f:
                    if not line.strip(): continue
                    data = json.loads(line)
                    if data.get("pattern_id") == pattern_id:
                        return data
        except Exception: pass
        return None

    def _persist_promotion_record(self, record: Dict[str, Any]) -> bool:
        try:
            self.memory_dir.mkdir(parents=True, exist_ok=True)
            with open(self.promotion_ledger_path, "a", encoding="utf-8") as f:
                f.write(json.dumps(record) + "\n")
            return True
        except Exception as exc:
            logger.error(f"Error persistiendo registro de promoción: {exc}")
            return False

    def _generate_failure_assessment(self, pattern_id: str, reason: str) -> ReflexPromotionAssessment:
        return ReflexPromotionAssessment(
            pattern_id=pattern_id, pattern_name="unknown", agreement_rate=0.0,
            context_score=0.0, risk_score=1.0, constraint_status="unknown",
            missing_context=[], promotion_allowed=False, requires_human_approval=True,
            recommended_target="none", reason_summary=reason
        )
