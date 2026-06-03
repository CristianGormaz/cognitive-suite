from __future__ import annotations

import json
import logging
import os
import time
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional

logger = logging.getLogger("ReflexShadowEvaluator")

from core.multidimensional_context import MultidimensionalContextEngine

@dataclass(frozen=True)
class ReflexShadowEvaluation:
    event_id: str
    timestamp: float
    input_signature: str
    real_route: str
    suggested_reflex: Optional[str]
    matched_pattern_id: Optional[str]
    confidence: float
    agreement_with_real_route: bool
    usefulness_estimate: float
    risk_estimate: float
    recommendation: str
    classification: str = "unknown" # aligned, redundant, missing_pattern, unsafe_suggestion, low_confidence, candidate_for_promotion
    context_frame_id: Optional[str] = None
    requires_human_review: bool = True
    schema_version: str = "reflex-shadow-evaluation.v2"

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

class ReflexShadowEvaluator:
    """
    Evalúa el desempeño de la MinimalNeuralLayer en modo sombra.
    Compara las sugerencias de reflejos con las rutas tomadas por el pipeline real.
    """

    def __init__(self, memory_dir: str = "assets/memory", stress_guard: Optional[Any] = None):
        self.memory_dir = Path(memory_dir)
        self.ledger_path = self.memory_dir / "reflex_shadow_ledger.jsonl"
        self.context_engine = MultidimensionalContextEngine(stress_guard=stress_guard)

    def evaluate(
        self, 
        input_signature: str, 
        real_route: str, 
        minimal_layer_suggestion: Optional[Dict[str, Any]],
        metadata: Optional[Dict[str, Any]] = None
    ) -> ReflexShadowEvaluation:
        """Compara una sugerencia de la capa neural con la realidad y el contexto."""
        
        suggested_action = None
        pattern_id = None
        confidence = 0.0
        agreement = False
        classification = "missing_pattern"
        
        if minimal_layer_suggestion:
            suggested_action = minimal_layer_suggestion.get("recommended_action")
            pattern_id = minimal_layer_suggestion.get("pattern_id")
            confidence = minimal_layer_suggestion.get("match_confidence", 0.0)
            
            # Comparación de ruteo
            if suggested_action == real_route:
                agreement = True
                classification = "aligned"
            else:
                classification = "misaligned"

        # 1. Evaluación Contextual Multidimensional
        ctx_frame = self.context_engine.build_context_frame(
            target=f"reflex_{pattern_id}" if pattern_id else "missing_pattern",
            metadata=metadata
        )

        # 2. Estimaciones
        usefulness = 1.0 if agreement else 0.0
        risk = minimal_layer_suggestion.get("risk_score", 0.1) if minimal_layer_suggestion else 0.0
        
        if not agreement and suggested_action:
            if confidence > 0.7:
                classification = "risky_divergence"
                risk = min(1.0, risk + 0.4)
            else:
                classification = "low_confidence_noise"

        recommendation = "monitor"
        # Regla del Arquitecto: Promoción requiere coincidencia + confianza + contexto estable
        if agreement and confidence > 0.8 and risk < 0.1 and ctx_frame.recommended_decision == "promote":
            classification = "candidate_for_promotion"
            recommendation = "promote_to_local_router"
        elif agreement:
            classification = "redundant_but_safe"
            if ctx_frame.context_risk_level != "low":
                recommendation = f"wait_for_context_{ctx_frame.context_risk_level}"

        eval_result = ReflexShadowEvaluation(
            event_id=f"shd_{os.urandom(4).hex()}",
            timestamp=time.time(),
            input_signature=input_signature,
            real_route=real_route,
            suggested_reflex=suggested_action,
            matched_pattern_id=pattern_id,
            confidence=confidence,
            agreement_with_real_route=agreement,
            usefulness_estimate=usefulness,
            risk_estimate=risk,
            recommendation=recommendation,
            classification=classification,
            context_frame_id=ctx_frame.frame_id
        )
        
        self.persist_evaluation(eval_result)
        return eval_result

    def persist_evaluation(self, evaluation: ReflexShadowEvaluation):
        """Guarda la evaluación en el ledger."""
        try:
            self.memory_dir.mkdir(parents=True, exist_ok=True)
            with open(self.ledger_path, "a", encoding="utf-8") as f:
                f.write(json.dumps(evaluation.to_dict()) + "\n")
        except Exception as exc:
            logger.error(f"Error persistiendo evaluación en sombra: {exc}")

    def summarize_performance(self, limit: int = 100) -> Dict[str, Any]:
        """Calcula métricas de desempeño desde el ledger."""
        stats = {
            "total_evaluations": 0,
            "agreement_rate": 0.0,
            "high_confidence_rate": 0.0,
            "risky_suggestions_count": 0,
            "unique_patterns_observed": 0,
            "classifications": {}
        }

        if not self.ledger_path.exists():
            return stats

        try:
            agreements = 0
            high_conf = 0
            patterns = set()
            
            with open(self.ledger_path, "r", encoding="utf-8") as f:
                lines = f.readlines()
                for line in lines[-limit:]:
                    if not line.strip(): continue
                    data = json.loads(line)
                    stats["total_evaluations"] += 1
                    if data.get("agreement_with_real_route"): agreements += 1
                    if data.get("confidence", 0.0) > 0.8: high_conf += 1
                    if data.get("risk_estimate", 0.0) > 0.5: stats["risky_suggestions_count"] += 1
                    
                    cls = data.get("classification", "unknown")
                    stats["classifications"][cls] = stats["classifications"].get(cls, 0) + 1
                    
                    pid = data.get("matched_pattern_id")
                    if pid: patterns.add(pid)
            
            total = stats["total_evaluations"]
            if total > 0:
                stats["agreement_rate"] = round(agreements / total, 2)
                stats["high_confidence_rate"] = round(high_conf / total, 2)
            stats["unique_patterns_observed"] = len(patterns)
            
        except Exception: pass

        return stats
