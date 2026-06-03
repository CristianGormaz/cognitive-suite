from __future__ import annotations

import os
import time
import logging
from dataclasses import asdict, dataclass, field
from typing import Any, Dict, List, Optional

logger = logging.getLogger("MultidimensionalContext")

@dataclass(frozen=True)
class ContextDimension:
    name: str
    score: float # 0.0 to 1.0
    status: str # stable, volatile, stressed, blocked
    evidence_refs: List[str]
    risk_notes: Optional[str] = None
    schema_version: str = "context-dimension.v1"

@dataclass(frozen=True)
class MultidimensionalContextFrame:
    frame_id: str
    timestamp: float
    target_decision: str
    environment_context: ContextDimension
    flow_context: ContextDimension
    human_context: ContextDimension
    temporal_context: ContextDimension
    constraint_context: ContextDimension
    overall_context_score: float
    context_risk_level: str # low, medium, high, critical
    missing_context: List[str]
    recommended_decision: str # promote, maintain, block, refine
    requires_human_review: bool = True
    schema_version: str = "context-frame.v1"

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

class MultidimensionalContextEngine:
    """
    Motor encargado de generar marcos de contexto multidimensionales
    para evaluar decisiones arquitectónicas.
    """

    def __init__(self, stress_guard: Optional[Any] = None):
        self.stress_guard = stress_guard

    def build_context_frame(self, target: str, metadata: Optional[Dict[str, Any]] = None) -> MultidimensionalContextFrame:
        """Construye un frame completo analizando todas las dimensiones."""
        meta = metadata or {}
        
        env = self.evaluate_environment_context()
        flow = self.evaluate_flow_context(meta)
        human = self.evaluate_human_context(meta)
        temporal = self.evaluate_temporal_context(meta)
        constraint = self.evaluate_constraint_context(meta)
        
        score = self.calculate_overall_score(env, flow, human, temporal, constraint)
        
        risk = "low"
        if env.status == "stressed" or constraint.status == "blocked":
            risk = "critical"
        elif score < 0.5:
            risk = "high"
        elif score < 0.8:
            risk = "medium"

        decision = "maintain"
        if risk == "low" and score > 0.85:
            decision = "promote"
        elif risk == "critical":
            decision = "block"

        return MultidimensionalContextFrame(
            frame_id=f"ctx_{os.urandom(4).hex()}",
            timestamp=time.time(),
            target_decision=target,
            environment_context=env,
            flow_context=flow,
            human_context=human,
            temporal_context=temporal,
            constraint_context=constraint,
            overall_context_score=score,
            context_risk_level=risk,
            missing_context=meta.get("missing_context_signals", []),
            recommended_decision=decision
        )

    def evaluate_environment_context(self) -> ContextDimension:
        """Evalúa el estado del host físico."""
        score = 1.0
        status = "stable"
        refs = []
        
        if self.stress_guard and self.stress_guard.is_host_under_stress():
            score = 0.2
            status = "stressed"
            refs.append("stress_guard")
            
        return ContextDimension("environment", score, status, refs)

    def evaluate_flow_context(self, meta: Dict[str, Any]) -> ContextDimension:
        """Evalúa la dinámica de procesos."""
        # Heurística inicial simple
        score = 0.9
        status = "stable"
        if meta.get("high_flow_load"):
            score = 0.5
            status = "volatile"
            
        return ContextDimension("flow", score, status, [])

    def evaluate_human_context(self, meta: Dict[str, Any]) -> ContextDimension:
        """Evalúa la interacción humana."""
        score = 0.8
        status = "stable"
        if meta.get("requires_immediate_feedback"):
            score = 0.4
            status = "volatile"
            
        return ContextDimension("human", score, status, [])

    def evaluate_temporal_context(self, meta: Dict[str, Any]) -> ContextDimension:
        """Evalúa la validez temporal y tendencias."""
        score = 0.7
        status = "stable"
        if meta.get("stale_evidence"):
            score = 0.3
            status = "volatile"
            
        return ContextDimension("temporal", score, status, [])

    def evaluate_constraint_context(self, meta: Dict[str, Any]) -> ContextDimension:
        """Evalúa restricciones y políticas (IAFA, privacy)."""
        score = 1.0
        status = "stable"
        if meta.get("policy_violation"):
            score = 0.0
            status = "blocked"
            
        return ContextDimension("constraint", score, status, [])

    def calculate_overall_score(self, *dims: ContextDimension) -> float:
        if not dims: return 0.0
        # Media ponderada simple (podemos refinar después)
        return round(sum(d.score for d in dims) / len(dims), 2)
