from __future__ import annotations

import json
import logging
import os
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional

logger = logging.getLogger("ClassifierShadowSoak")

@dataclass(frozen=True)
class ClassifierSoakSummary:
    total_candidates: int
    candidates_by_intent: Dict[str, int]
    average_confidence: float
    unknown_safe_rate: float
    duplicate_rate: float
    false_positive_estimate: float
    promotion_readiness: str # always "observe_more" for now
    weak_intents: List[str]
    risky_candidates: int
    recommended_action: str
    schema_version: str = "classifier-soak-summary.v1"

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

class ClassifierShadowSoakEvaluator:
    """
    Evalúa la estabilidad y calidad de los candidatos generados por el clasificador
    durante un periodo de observación prolongado (Soak Test).
    v1.2: Métricas de madurez y detección de ambigüedad.
    """

    def __init__(self, memory_dir: str = "assets/memory"):
        self.memory_dir = Path(memory_dir)
        self.ledger_path = self.memory_dir / "classifier_shadow_candidates.jsonl"

    def summarize_performance(self, limit: int = 500) -> ClassifierSoakSummary:
        """Genera un resumen profundo del desempeño en el soak test."""
        candidates = self._load_candidates(limit)
        total = len(candidates)
        
        if total == 0:
            return self._empty_summary()

        by_intent = {}
        confidences = []
        unknown_safe_count = 0
        signatures = {}
        risky_count = 0
        ambiguous_count = 0
        overconfident_count = 0

        for c in candidates:
            intent = c.get("predicted_intent", "unknown")
            by_intent[intent] = by_intent.get(intent, 0) + 1
            
            conf = c.get("confidence", 0.0)
            confidences.append(conf)
            
            if intent == "unknown_safe":
                unknown_safe_count += 1
                if "Margen" in c.get("reason_summary", ""):
                    ambiguous_count += 1
            
            sig = c.get("input_signature", "unknown")
            signatures[sig] = signatures.get(sig, 0) + 1
            
            if c.get("risk_score", 0.0) > 0.4:
                risky_count += 1
                
            if "[OVERCONFIDENCE]" in c.get("reason_summary", ""):
                overconfident_count += 1

        # Métricas de Madurez
        avg_conf = round(sum(confidences) / total, 2)
        us_rate = round(unknown_safe_count / total, 2)
        
        dupes = sum(1 for count in signatures.values() if count > 1)
        dupe_rate = round(dupes / len(signatures), 2) if signatures else 0.0
        
        overconf_rate = round(overconfident_count / total, 2)
        ambiguous_rate = round(ambiguous_count / total, 2)

        weak = [intent for intent, count in by_intent.items() if count < (total * 0.05)]
        
        # El sistema de madurez v1.2 proactivamente pide más observación
        rec = "keep_observing"
        if us_rate < 0.15: rec = "strengthen_unknown_safe"
        elif overconf_rate > 0.10: rec = "calibrate_margins"
        elif total > 100 and avg_conf > 0.85: rec = "ready_for_v1_design"

        return ClassifierSoakSummary(
            total_candidates=total,
            candidates_by_intent=by_intent,
            average_confidence=avg_conf,
            unknown_safe_rate=us_rate,
            duplicate_rate=dupe_rate,
            false_positive_estimate=round(risky_count / total, 2),
            promotion_readiness="observe_more", # Bloqueado por diseño en este sprint
            weak_intents=weak,
            risky_candidates=risky_count,
            recommended_action=rec
        )

    def _load_candidates(self, limit: int) -> List[Dict[str, Any]]:
        if not self.ledger_path.exists():
            return []
        try:
            with open(self.ledger_path, "r", encoding="utf-8") as f:
                lines = f.readlines()
                return [json.loads(l) for l in lines[-limit:] if l.strip()]
        except Exception:
            return []

    def _empty_summary(self) -> ClassifierSoakSummary:
        return ClassifierSoakSummary(
            total_candidates=0,
            candidates_by_intent={},
            average_confidence=0.0,
            unknown_safe_rate=0.0,
            duplicate_rate=0.0,
            false_positive_estimate=0.0,
            promotion_readiness="no_data",
            weak_intents=[],
            risky_candidates=0,
            recommended_action="start_observation"
        )
