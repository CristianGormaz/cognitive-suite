from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

logger = logging.getLogger("ExperimentalRiskProfile")

@dataclass(frozen=True)
class ExperimentalRiskProfile:
    """
    Perfil de riesgo para habilidades experimentales en Greys-v3.
    Permite ajustar los parámetros IAFA basados en el nivel de peligro técnico.
    """
    skill_name: str
    stage: str = "experimental"
    uses_network: bool = False
    reads_files: bool = False
    writes_files: bool = False
    requires_external_dependency: bool = False
    handles_user_file: bool = False
    handles_sensitive_data: bool = False
    is_allowlisted: bool = False
    has_tests: bool = False
    sandbox_safe: bool = False
    human_review_status: str = "pending"
    risk_level: str = "high"  # low, medium, high, critical
    iafa_risk_adjustment: Dict[str, float] = field(default_factory=lambda: {"R": 0.0, "I": 0.0, "N": 0.0})

    @classmethod
    def for_skill(
        cls, 
        skill_name: str, 
        is_allowlisted: bool = False,
        human_review_status: str = "pending",
        has_tests: bool = False,
        sandbox_safe: bool = False
    ) -> ExperimentalRiskProfile:
        """
        Genera un perfil de riesgo basado en heurísticas para la skill dada.
        """
        # Valores por defecto
        uses_network = False
        reads_files = False
        writes_files = False
        requires_external_dependency = False
        handles_user_file = False
        handles_sensitive_data = False
        
        # Heurísticas basadas en nombre (v0)
        if "consultor_tiempo_local" in skill_name:
            risk_level = "low"
        elif "pdf_reader" in skill_name or "docx_reader" in skill_name:
            reads_files = True
            handles_user_file = True
            requires_external_dependency = True
            risk_level = "medium"
        else:
            risk_level = "high"

        # Ajustes de riesgo basados en auditoría
        if not is_allowlisted:
            risk_level = "critical"
        elif not sandbox_safe:
            risk_level = "critical"
        elif human_review_status != "approved_for_future_promotion":
            risk_level = max(risk_level, "medium")

        # Cálculo de ajuste IAFA
        adjustment = {"R": 0.0, "I": 0.0, "N": 0.0}
        if risk_level == "low":
            adjustment = {"R": 0.1, "I": 0.1, "N": 0.1}
        elif risk_level == "medium":
            adjustment = {"R": 0.3, "I": 0.4, "N": 0.2}
        elif risk_level == "high":
            adjustment = {"R": 0.6, "I": 0.7, "N": 0.4}
        elif risk_level == "critical":
            adjustment = {"R": 0.9, "I": 0.9, "N": 0.8}

        return cls(
            skill_name=skill_name,
            uses_network=uses_network,
            reads_files=reads_files,
            writes_files=writes_files,
            requires_external_dependency=requires_external_dependency,
            handles_user_file=handles_user_file,
            handles_sensitive_data=handles_sensitive_data,
            is_allowlisted=is_allowlisted,
            has_tests=has_tests,
            sandbox_safe=sandbox_safe,
            human_review_status=human_review_status,
            risk_level=risk_level,
            iafa_risk_adjustment=adjustment
        )

    def to_dict(self) -> Dict[str, Any]:
        from dataclasses import asdict
        return asdict(self)
