from __future__ import annotations

import json
import logging
import os
import time
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional

logger = logging.getLogger("SymbioticDelegationPolicy")

@dataclass(frozen=True)
class DelegationAssessment:
    assessment_id: str
    timestamp: float
    task_signature: str
    task_type: str
    edge_routing_score: float
    symbiotic_delegation_score: float
    quorum_promotion_score: float
    recommended_route: str
    llm_allowed: bool
    local_resolution_preferred: bool
    defer_recommended: bool
    block_reason: Optional[str]
    risk_level: str
    evidence_refs: List[str]
    requires_human_review: bool
    schema_version: str = "symbiotic-delegation.v1"

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

class SymbioticDelegationPolicy:
    """
    Política determinística para decidir cuándo resolver localmente y cuándo delegar al LLM.
    Basado en los principios bioinspirados del Symbiotic Delegation & Edge Stabilization Sprint.
    Actualmente opera solo en modo DRY RUN (no altera ejecución real).
    """

    def __init__(self, memory_dir: str = "assets/memory"):
        self.memory_dir = Path(memory_dir)
        self.ledger_path = self.memory_dir / "symbiotic_delegation_ledger.jsonl"
        self.dry_run_enabled = os.getenv("GREYS_SYMBIOTIC_DELEGATION_DRY_RUN", "0") == "1"

    def assess_task(
        self,
        task_signature: str,
        task_type: str,
        complexity_score: float,
        host_stress: float,
        llm_latency_risk: float,
        active_reflex_exists: bool = False,
        ambiguity_margin: float = 1.0,
        evidence_score: float = 0.5,
        risk_level: str = "low"
    ) -> DelegationAssessment:
        """Evalúa una tarea y recomienda una ruta basada en ERS, SDS y QPS."""
        
        ers = self.calculate_edge_routing_score(
            complexity_score=complexity_score,
            host_stress=host_stress,
            llm_latency_risk=llm_latency_risk
        )
        
        sds = self.calculate_symbiotic_delegation_score(
            complexity_score=complexity_score,
            host_stress=host_stress,
            llm_latency_risk=llm_latency_risk
        )
        
        qps = self.calculate_quorum_promotion_score(
            evidence_score=evidence_score,
            ambiguity_margin=ambiguity_margin
        )
        
        route, llm_allowed, block_reason = self.recommend_route(
            task_type=task_type,
            ers=ers,
            sds=sds,
            qps=qps,
            host_stress=host_stress,
            active_reflex_exists=active_reflex_exists,
            ambiguity_margin=ambiguity_margin
        )

        assessment = DelegationAssessment(
            assessment_id=f"del_{os.urandom(4).hex()}",
            timestamp=time.time(),
            task_signature=task_signature[:30], # Acortar para seguridad
            task_type=task_type,
            edge_routing_score=ers,
            symbiotic_delegation_score=sds,
            quorum_promotion_score=qps,
            recommended_route=route,
            llm_allowed=llm_allowed,
            local_resolution_preferred=ers > sds,
            defer_recommended=route == "defer_due_to_host_stress",
            block_reason=block_reason,
            risk_level=risk_level,
            evidence_refs=[],
            requires_human_review=False
        )

        if self.dry_run_enabled:
            self._persist_assessment(assessment)
            
        return assessment

    def calculate_edge_routing_score(self, complexity_score: float, host_stress: float, llm_latency_risk: float) -> float:
        """ERS = local_benefit - central_cost"""
        # Beneficios de resolver local: más rápido, no gasta tokens, 100% privado
        local_benefit = 1.0 - complexity_score
        
        # Costo de usar el núcleo central (LLM): alto si hay latencia o el host está estresado
        central_cost = llm_latency_risk + (host_stress * 0.5)
        
        return round(local_benefit - central_cost, 2)

    def calculate_symbiotic_delegation_score(self, complexity_score: float, host_stress: float, llm_latency_risk: float) -> float:
        """SDS = delegation_benefit - delegation_cost"""
        # Beneficio de delegar: resolver cosas complejas o novedosas
        delegation_benefit = complexity_score
        
        # Costo de delegar: lentitud, riesgo de no responder, estrés
        delegation_cost = llm_latency_risk + host_stress
        
        return round(delegation_benefit - delegation_cost, 2)

    def calculate_quorum_promotion_score(self, evidence_score: float, ambiguity_margin: float) -> float:
        """QPS simplificado. Para decisiones de promoción o confianza estructural."""
        return round(evidence_score * ambiguity_margin, 2)

    def recommend_route(self, task_type: str, ers: float, sds: float, qps: float, host_stress: float, active_reflex_exists: bool, ambiguity_margin: float) -> tuple[str, bool, Optional[str]]:
        """Aplica reglas determinísticas para decidir la ruta (Dry Run)."""
        force_local = os.getenv("GREYS_FORCE_LOCAL_ONLY") == "1"
        llm_allowed = not force_local

        if force_local:
            llm_allowed = False
        
        if host_stress >= 0.8:
            return "defer_due_to_host_stress", False, "Host stress critical"
            
        if active_reflex_exists:
            return "local_reflex", llm_allowed, None
            
        if ambiguity_margin < 0.15 and qps < 0.4:
            return "observe_only", llm_allowed, "High ambiguity, low QPS"
            
        if sds > ers and llm_allowed:
            return "llm_delegate", True, None
            
        if ers >= sds:
            return "local_fast_path", llm_allowed, None
            
        if force_local:
            return "block_due_to_policy", False, "FORCE_LOCAL_ONLY active but local fast path not preferred"

        return "observe_only", llm_allowed, "No clear route recommended"

    def _persist_assessment(self, assessment: DelegationAssessment):
        try:
            self.memory_dir.mkdir(parents=True, exist_ok=True)
            with open(self.ledger_path, "a", encoding="utf-8") as f:
                f.write(json.dumps(assessment.to_dict()) + "\n")
        except Exception as exc:
            logger.error(f"Failed to persist delegation assessment: {exc}")

    def summarize_recent(self, limit: int = 100) -> List[DelegationAssessment]:
        assessments = []
        if not self.ledger_path.exists(): return assessments
        try:
            with open(self.ledger_path, "r", encoding="utf-8") as f:
                lines = f.readlines()
                for line in lines[-limit:]:
                    if line.strip():
                        assessments.append(DelegationAssessment(**json.loads(line)))
        except Exception: pass
        return assessments
