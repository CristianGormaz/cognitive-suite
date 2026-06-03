from __future__ import annotations

import json
import logging
import os
import time
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Set

from core.local_ledger_cache import LocalLedgerCache

logger = logging.getLogger("QuorumPromotionReadiness")

@dataclass(frozen=True)
class QuorumEvidence:
    source: str
    evidence_type: str
    candidate_id: str
    signal_count: int
    unique_signal_count: int
    duplicate_count: int
    confidence: float
    temporal_span_hours: float
    risk_score: float
    context_score: float
    human_approval_present: bool
    rollback_available: bool
    schema_version: str = "quorum-evidence.v1"

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

@dataclass(frozen=True)
class QuorumReadinessAssessment:
    candidate_id: str
    candidate_type: str
    evidence_score: float
    uniqueness_score: float
    temporal_stability_score: float
    agreement_score: float
    context_score: float
    risk_score: float
    duplication_penalty: float
    false_quorum_risk: float
    quorum_readiness_score: float
    readiness_state: str # insufficient_evidence, observe_more, false_quorum_suspected, ready_for_human_review
    recommended_action: str
    promotion_allowed: bool = False # Siempre False en este sprint
    requires_human_approval: bool = True
    reason_summary: str = ""
    timestamp: float = field(default_factory=time.time)
    schema_version: str = "quorum-readiness-assessment.v1"

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

class QuorumPromotionReadiness:
    """
    Evalúa la madurez de los candidatos de reflejo basándose en la masa crítica
    de evidencia (Quórum), detectando duplicados y rumiación.
    """

    def __init__(self, memory_dir: str = "assets/memory"):
        self.memory_dir = Path(memory_dir)
        self.ledger_path = self.memory_dir / "quorum_readiness_ledger.jsonl"
        self.cache = LocalLedgerCache(memory_dir=str(self.memory_dir))

    def assess_candidate(self, candidate_id: str, candidate_type: str, evidence_list: List[QuorumEvidence]) -> QuorumReadinessAssessment:
        """Calcula el score de readiness para un candidato."""
        
        # 1. Calcular Scores Base
        total_signals = sum(e.signal_count for e in evidence_list)
        total_unique = sum(e.unique_signal_count for e in evidence_list)
        
        # Evidencia Score: escala logarítmica para evitar que miles de ruidos inflen el quórum
        import math
        evidence_score = round(min(1.0, math.log10(total_signals + 1) / 2.0), 2) if total_signals > 0 else 0.0
        
        uniqueness_score = round(total_unique / total_signals, 2) if total_signals > 0 else 0.0
        
        # Estabilidad Temporal (max de las fuentes)
        temporal_stability = max([e.temporal_span_hours for e in evidence_list], default=0.0)
        temporal_score = round(min(1.0, temporal_stability / 48.0), 2) # Saturación a las 48h
        
        # Acuerdo y Contexto (promedio pesado)
        agreement_score = round(sum(e.confidence * e.signal_count for e in evidence_list) / total_signals, 2) if total_signals > 0 else 0.0
        context_score = round(sum(e.context_score * e.signal_count for e in evidence_list) / total_signals, 2) if total_signals > 0 else 0.0
        risk_score = max([e.risk_score for e in evidence_list], default=1.0)
        
        # 2. Penalización por Duplicados (Anti-False-Quorum)
        duplication_penalty = 0.0
        if uniqueness_score < 0.3:
            duplication_penalty = 0.4
        elif uniqueness_score < 0.6:
            duplication_penalty = 0.2
            
        # 3. Riesgo de Falso Quórum
        false_quorum_risk = 0.0
        # Si la mayoría de la evidencia viene de una sola fuente repetitiva (ej. Dream Mode)
        sources = [e.source for e in evidence_list]
        if len(set(sources)) == 1 and total_signals > 5:
            false_quorum_risk = 0.3
            
        # 4. Score Final de Readiness (QRS)
        qrs = round(
            (evidence_score * 0.2) + 
            (uniqueness_score * 0.2) + 
            (temporal_score * 0.2) + 
            (agreement_score * 0.2) + 
            (context_score * 0.2) - 
            duplication_penalty - 
            false_quorum_risk, 
            2
        )
        qrs = max(0.0, qrs)

        # 5. Determinación de Estado
        state = "insufficient_evidence"
        rec_action = "observe_more"
        reason = "Evidencia insuficiente acumulada."

        if false_quorum_risk > 0.2 or duplication_penalty > 0.3:
            state = "false_quorum_suspected"
            rec_action = "rebalance_evidence"
            reason = "Se sospecha falso quórum por alta redundancia o fuente única."
        elif qrs >= 0.7:
            state = "ready_for_human_review"
            rec_action = "submit_for_review"
            reason = "Quórum alcanzado con estabilidad temporal y diversidad."
        elif qrs >= 0.4:
            state = "observe_more"
            rec_action = "collect_more_data"
            reason = "Evidencia en crecimiento. Continuar observación."

        # Restricciones de Seguridad Hardcoded (v1)
        human_approved = any(e.human_approval_present for e in evidence_list)
        rollback_ok = all(e.rollback_available for e in evidence_list) if evidence_list else False
        
        if not rollback_ok:
            state = "insufficient_evidence"
            reason += " (Rollback no disponible)"
            
        if risk_score > 0.2:
            state = "observe_more"
            reason += f" (Riesgo {risk_score} elevado)"

        assessment = QuorumReadinessAssessment(
            candidate_id=candidate_id,
            candidate_type=candidate_type,
            evidence_score=evidence_score,
            uniqueness_score=uniqueness_score,
            temporal_stability_score=temporal_score,
            agreement_score=agreement_score,
            context_score=context_score,
            risk_score=risk_score,
            duplication_penalty=duplication_penalty,
            false_quorum_risk=false_quorum_risk,
            quorum_readiness_score=qrs,
            readiness_state=state,
            recommended_action=rec_action,
            promotion_allowed=False, # Bloqueado por diseño
            requires_human_approval=not human_approved,
            reason_summary=reason
        )

        self._persist_assessment(assessment)
        return assessment

    def _persist_assessment(self, assessment: QuorumReadinessAssessment):
        try:
            self.memory_dir.mkdir(parents=True, exist_ok=True)
            with open(self.ledger_path, "a", encoding="utf-8") as f:
                f.write(json.dumps(assessment.to_dict()) + "\n")
        except Exception as exc:
            logger.error(f"Error persistiendo assessment de quórum: {exc}")

    def summarize_readiness(self, limit: int = 50) -> List[QuorumReadinessAssessment]:
        """Carga assessments recientes para el MorningBrief."""
        assessments = []
        if not self.ledger_path.exists(): return assessments
        try:
            records = self.cache.get_records(str(self.ledger_path), limit=limit)
            for r in records:
                assessments.append(QuorumReadinessAssessment(**r))
        except Exception: pass
        return assessments
