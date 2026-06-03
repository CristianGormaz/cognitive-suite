from __future__ import annotations

import json
import logging
import os
import time
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional

logger = logging.getLogger("ImmuneQuarantinePolicy")

IMMUNE_POLICY_VERSION = "immune-policy.v1"

@dataclass(frozen=True)
class ImmuneQuarantineAssessment:
    item_id: str
    item_type: str  # candidate, experimental_skill, ledger_entry, dependency
    source_path: Optional[str]
    risk_score: float  # 0.0 to 1.0
    uncertainty_score: float  # 0.0 to 1.0
    accumulated_damage: float  # Historical damage
    entropy_score: float  # Disorder/corruption
    maintenance_cost: float
    potential_value: float
    traceability_score: float
    isolation_capacity: float
    immune_learning_value: float
    healthy_separation_index: float
    recommended_quarantine_level: int  # 1, 2, 3
    recommended_action: str
    delete_recommended: bool = False
    requires_human_approval: bool = True
    reason_summary: str = ""
    evidence_refs: List[str] = field(default_factory=list)
    schema_version: str = IMMUNE_POLICY_VERSION

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    def to_json(self) -> str:
        return json.dumps(self.to_dict(), ensure_ascii=False)

class ImmuneQuarantinePolicy:
    """
    Motor de evaluación inmunológica para Greys-v3 (Corte Sano).
    Calcula el Índice de Separación Sana (ISS) para decidir niveles de aislamiento.
    """

    def __init__(self):
        # Umbrales para niveles de cuarentena
        self.threshold_level_1 = 0.5  # Observación
        self.threshold_level_2 = 1.0  # Validación
        self.threshold_level_3 = 2.5  # Inmunológica
        
    def calculate_iss(self, 
        risk: float, uncertainty: float, damage: float, entropy: float, cost: float,
        value: float, traceability: float, isolation: float
    ) -> float:
        """
        ISS = (R + U + D + H + C) - (V + T + A)
        """
        positive_factors = risk + uncertainty + damage + entropy + cost
        negative_factors = value + traceability + isolation
        return round(positive_factors - negative_factors, 3)

    def classify_quarantine_level(self, iss: float) -> int:
        if iss >= self.threshold_level_3:
            return 3
        if iss >= self.threshold_level_2:
            return 2
        if iss >= self.threshold_level_1:
            return 1
        return 0 # Conservar/Saludable

    def assess_item(self, item_id: str, item_type: str, metadata: Dict[str, Any]) -> ImmuneQuarantineAssessment:
        """
        Evalúa un elemento basado en sus metadatos y aplica reglas heurísticas.
        """
        # Valores base
        r = metadata.get("risk", 0.1)
        u = metadata.get("uncertainty", 0.1)
        d = metadata.get("damage", 0.0)
        h = metadata.get("entropy", 0.1)
        c = metadata.get("cost", 0.1)
        
        v = metadata.get("value", 0.5)
        t = metadata.get("traceability", 0.8)
        a = metadata.get("isolation", 0.9)
        
        learning_value = metadata.get("learning_value", 0.1)
        source_path = metadata.get("source_path")
        evidence = metadata.get("evidence", [])
        reason = ""

        # Reglas Inmunes
        if item_type == "candidate":
            u += 0.8 # Los candidatos son inherentemente inciertos
            reason += " Candidato en fase de propuesta."

        if "unsafe" in item_id.lower() or metadata.get("contains_dangerous_calls"):
            r += 2.0
            u += 0.5
            h += 1.0
            a -= 0.6 # Es más difícil de aislar si es inherentemente peligroso
            learning_value += 0.8
            reason += " Contiene llamadas peligrosas (eval/exec/subprocess)."
            
        if item_type == "experimental_skill" and not metadata.get("in_runtime"):
            u += 0.6
            reason += " Skill experimental inactiva en runtime."
            
        if metadata.get("handles_user_file") or "pdf" in item_id.lower():
            r += 1.0
            u += 0.8
            a -= 0.4
            reason += " Maneja archivos de usuario (riesgo de ingestión)."

        if metadata.get("is_legacy"):
            h += 1.2
            c += 0.6
            v -= 0.4
            reason += " Código legacy con alta entropía y bajo valor relativo."

        if metadata.get("metadata_leak_risk"):
            if metadata.get("metadata_redacted"):
                r += 0.2
                reason += " Riesgo de fuga de metadatos mitigado (privacidad endurecida)."
            else:
                r += 1.2
                u += 0.5
                reason += " Riesgo de fuga de metadatos/privacidad detectado."

        if metadata.get("is_corrupt") or metadata.get("parse_error"):
            h += 1.2
            u += 0.8
            v -= 0.4
            reason += " Elemento corrupto o con errores de parseo recurrentes."

        iss = self.calculate_iss(r, u, d, h, c, v, t, a)
        level = self.classify_quarantine_level(iss)
        
        action = self.recommend_action(level, learning_value, metadata)

        return ImmuneQuarantineAssessment(
            item_id=item_id,
            item_type=item_type,
            source_path=source_path,
            risk_score=r,
            uncertainty_score=u,
            accumulated_damage=d,
            entropy_score=h,
            maintenance_cost=c,
            potential_value=v,
            traceability_score=t,
            isolation_capacity=a,
            immune_learning_value=learning_value,
            healthy_separation_index=iss,
            recommended_quarantine_level=level,
            recommended_action=action,
            delete_recommended=False, # Nunca borrar automáticamente
            requires_human_approval=True,
            reason_summary=reason.strip(),
            evidence_refs=evidence
        )

    def recommend_action(self, level: int, learning_value: float, metadata: Dict[str, Any]) -> str:
        if metadata.get("metadata_leak_risk") and not metadata.get("metadata_redacted"):
            return "needs_privacy_review"
            
        if level == 3:
            if learning_value >= 0.5:
                return "preserve_as_immune_training_sample"
            return "strict_isolation_block"
        if level == 2:
            return "validation_quarantine"
        if level == 1:
            return "observation_quarantine"
        return "monitor_health"
