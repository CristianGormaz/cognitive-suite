from __future__ import annotations

import json
import logging
import os
import time
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional

logger = logging.getLogger("FastPathReflexGate")

@dataclass(frozen=True)
class FastPathAssessment:
    event_id: str
    timestamp: float
    pattern_id: str
    input_signature: str
    reflex_name: str
    active_local: bool
    risk_score: float
    human_approved: bool
    rollback_available: bool
    uses_llm: bool
    uses_files: bool
    uses_network: bool
    uses_dynamic_skill_loader: bool
    uses_genesis: bool
    fast_path_allowed: bool
    block_reason: Optional[str]
    duration_ms: float
    schema_version: str = "fast-path-assessment.v1"

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

class FastPathReflexGate:
    """
    Certificador de la "Ruta Mielinizada" (Fast-Path).
    Asegura que solo los reflejos locales con riesgo 0, aprobados y libres
    de efectos secundarios complejos (red, archivos, LLM) puedan evitar el flujo
    pesado de evaluación simbiótica y context frame.
    """

    def __init__(self, memory_dir: str = "assets/memory"):
        self.memory_dir = Path(memory_dir)
        self.ledger_path = self.memory_dir / "fast_path_reflex_ledger.jsonl"
        # Reflejos certificados explícitamente para fast-path v1
        self.certified_reflexes = {
            "basic_greeting_reflex",
            "help_command_reflex",
            "system_status_reflex",
            "identity_query_reflex"
        }

    def assess_reflex(
        self,
        pattern_id: str,
        reflex_name: str,
        input_signature: str,
        active_local: bool,
        risk_score: float,
        human_approved: bool,
        rollback_available: bool,
        uses_llm: bool = False,
        uses_files: bool = False,
        uses_network: bool = False,
        uses_dynamic_skill_loader: bool = False,
        uses_genesis: bool = False,
        start_time_ms: float = 0.0
    ) -> FastPathAssessment:
        """Evalúa si un reflejo cumple con los requisitos estrictos del Fast-Path."""
        
        allowed, reason = self.is_certified_fast_path(
            reflex_name=reflex_name,
            active_local=active_local,
            risk_score=risk_score,
            human_approved=human_approved,
            rollback_available=rollback_available,
            uses_llm=uses_llm,
            uses_files=uses_files,
            uses_network=uses_network,
            uses_dynamic_skill_loader=uses_dynamic_skill_loader,
            uses_genesis=uses_genesis
        )
        
        duration = (time.time() * 1000.0) - start_time_ms if start_time_ms > 0 else 0.0

        assessment = FastPathAssessment(
            event_id=f"fp_{os.urandom(4).hex()}",
            timestamp=time.time(),
            pattern_id=pattern_id,
            input_signature=input_signature[:30], # Firma segura acortada
            reflex_name=reflex_name,
            active_local=active_local,
            risk_score=risk_score,
            human_approved=human_approved,
            rollback_available=rollback_available,
            uses_llm=uses_llm,
            uses_files=uses_files,
            uses_network=uses_network,
            uses_dynamic_skill_loader=uses_dynamic_skill_loader,
            uses_genesis=uses_genesis,
            fast_path_allowed=allowed,
            block_reason=reason,
            duration_ms=round(duration, 2)
        )

        self._persist_assessment(assessment)
        return assessment

    def is_certified_fast_path(
        self,
        reflex_name: str,
        active_local: bool,
        risk_score: float,
        human_approved: bool,
        rollback_available: bool,
        uses_llm: bool,
        uses_files: bool,
        uses_network: bool,
        uses_dynamic_skill_loader: bool,
        uses_genesis: bool
    ) -> tuple[bool, Optional[str]]:
        
        if self.deny_if_ambiguous(reflex_name):
            return False, "is_ambiguous_or_generalized"
            
        if self.deny_if_experimental(reflex_name):
            return False, "is_experimental_skill"
            
        if reflex_name not in self.certified_reflexes:
            return False, "not_certified_for_fast_path"
            
        if not active_local:
            return False, "not_active_local"
            
        if risk_score > 0.0:
            return False, "risk_score_above_zero"
            
        if not human_approved:
            return False, "not_human_approved"
            
        if not rollback_available:
            return False, "no_rollback_available"
            
        if self.deny_if_side_effectful(uses_llm, uses_files, uses_network, uses_dynamic_skill_loader, uses_genesis):
            return False, "has_prohibited_side_effects"
            
        if self.deny_if_experimental(reflex_name):
            return False, "is_experimental_skill"
            
        if self.deny_if_ambiguous(reflex_name):
            return False, "is_ambiguous_or_generalized"

        return True, None

    def deny_if_ambiguous(self, reflex_name: str) -> bool:
        """Filtra predicciones generalizadas del clasificador u otras ambigüedades."""
        if reflex_name.startswith("generalized_") or "unknown_safe" in reflex_name:
            return True
        return False

    def deny_if_experimental(self, reflex_name: str) -> bool:
        """Filtra cualquier intento de saltar la seguridad en habilidades experimentales."""
        # En v1, no permitimos nada fuera del core reflex pack
        return False

    def deny_if_side_effectful(self, uses_llm: bool, uses_files: bool, uses_network: bool, uses_dynamic_skill_loader: bool, uses_genesis: bool) -> bool:
        """Deniega fast-path si hay efectos secundarios pesados o externos."""
        return uses_llm or uses_files or uses_network or uses_dynamic_skill_loader or uses_genesis

    def explain_decision(self, assessment: FastPathAssessment) -> str:
        if assessment.fast_path_allowed:
            return f"Fast-Path permitido para '{assessment.reflex_name}' (0 riesgos, certificado)."
        return f"Fast-Path denegado para '{assessment.reflex_name}'. Razón: {assessment.block_reason}."

    def _persist_assessment(self, assessment: FastPathAssessment):
        try:
            self.memory_dir.mkdir(parents=True, exist_ok=True)
            with open(self.ledger_path, "a", encoding="utf-8") as f:
                f.write(json.dumps(assessment.to_dict()) + "\n")
        except Exception as exc:
            logger.error(f"Failed to persist fast-path assessment: {exc}")

    def summarize_metrics(self) -> Dict[str, Any]:
        """Agrega métricas para el MorningBrief."""
        hits = 0
        blocks = 0
        durations = []
        reflex_usage = {}
        
        if not self.ledger_path.exists():
            return {}
            
        try:
            with open(self.ledger_path, "r", encoding="utf-8") as f:
                for line in f:
                    if not line.strip(): continue
                    data = json.loads(line)
                    if data.get("fast_path_allowed"):
                        hits += 1
                        durations.append(data.get("duration_ms", 0.0))
                        r_name = data.get("reflex_name", "unknown")
                        reflex_usage[r_name] = reflex_usage.get(r_name, 0) + 1
                    else:
                        blocks += 1
                        
            avg_duration = sum(durations) / len(durations) if durations else 0.0
            
            return {
                "fast_path_hits": hits,
                "blocks": blocks,
                "average_duration_ms": round(avg_duration, 2),
                "estimated_savings_ms": hits * 150, # asumiendo que el flow normal toma ~150ms
                "reflex_usage": reflex_usage
            }
        except Exception:
            return {}
