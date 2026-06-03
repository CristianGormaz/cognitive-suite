from __future__ import annotations

import hashlib
import json
import logging
import os
import time
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Set

from cognition.skill_candidate_review import SkillCandidateReview, SkillCandidateSummary
from core.dependency_review_ledger import DependencyReviewLedger

logger = logging.getLogger("SkillPromotionGate")

PROMOTION_LEDGER_VERSION = "skill-promotion.v1"
DEFAULT_PROMOTION_LEDGER_PATH = "assets/memory/skill_promotion_ledger.jsonl"

@dataclass(frozen=True)
class SkillPromotionAssessment:
    candidate_id: str
    capability_signature: str
    code_sha256: str
    current_status: str
    target_stage: str
    ast_safe: bool
    sandbox_safe: bool
    has_required_tests: bool
    dependency_status: Dict[str, bool]
    blocked_imports: List[str]
    blocked_calls: List[str]
    risk_level: str
    blockers: List[str]
    recommendation: str
    can_promote: bool
    dry_run_only: bool = True
    requires_human_approval: bool = True
    timestamp: float = field(default_factory=time.time)
    schema_version: str = PROMOTION_LEDGER_VERSION

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

class SkillPromotionGate:
    """
    Evalúa si un candidato en cuarentena cumple los criterios para ser promovido.
    Opera exclusivamente en modo DRY-RUN (simulación).
    """

    def __init__(
        self,
        reviewer: Optional[SkillCandidateReview] = None,
        ledger_path: str = DEFAULT_PROMOTION_LEDGER_PATH,
        dependency_ledger: Optional[DependencyReviewLedger] = None
    ):
        self.reviewer = reviewer or SkillCandidateReview()
        self.ledger_path = Path(ledger_path)
        self.dependency_ledger = dependency_ledger or DependencyReviewLedger()
        self._ensure_dir()

    def _ensure_dir(self):
        if not self.ledger_path.parent.exists():
            self.ledger_path.parent.mkdir(parents=True, exist_ok=True)

    def assess_candidate(self, candidate_id: str, target_stage: str = "experimental") -> SkillPromotionAssessment:
        """Realiza una evaluación completa de un candidato sin realizar cambios."""
        summaries = self.reviewer.list_candidates()
        summary = next((s for s in summaries if s.candidate_id == candidate_id), None)
        
        if not summary:
            raise FileNotFoundError(f"Candidate {candidate_id} not found in quarantine.")

        # 1. Criterios de Seguridad Estática
        blocked_imports = summary.dangerous_calls_detected
        critical_unsafe = {"eval", "exec", "subprocess"}
        found_critical = [c for c in blocked_imports if c in critical_unsafe]
        ast_safe = len(found_critical) == 0
        
        # 2. Estado de Revisión Humana
        current_status = summary.current_status
        human_approved = (current_status == "approved_for_future_promotion")
        
        # 3. Verificación de Dependencias (Heurística)
        dependencies = {}
        if "solve_integral" in candidate_id or summary.capability_signature == "math:solve_integral":
            try:
                import sympy
                dependencies["sympy"] = True
            except ImportError:
                dependencies["sympy"] = False
                
        if "pdf_reader" in candidate_id or summary.capability_signature in ["pdf", "file:pdf_reader"]:
            is_approved = self.dependency_ledger.is_dependency_approved("pypdf")
            dependencies["pypdf"] = is_approved

        # 4. Verificación de Tests (Heurística)
        test_filename = f"test_{candidate_id}"
        has_tests = (Path("tests") / test_filename).exists()
        
        # Exception for PDF reader which has a shared test file
        if not has_tests and "pdf_reader" in candidate_id:
            if Path("tests/test_pdf_reader_with_pypdf.py").exists():
                has_tests = True
        
        # 5. Identificar Bloqueadores
        blockers = []
        if not human_approved:
            blockers.append(f"human_review_status:{current_status}")
            
        if not ast_safe:
            blockers.append(f"critical_unsafe_calls:{found_critical}")
        
        # os/sys are blockers unless human approved for Medium Risk
        if ("os" in blocked_imports or "sys" in blocked_imports) and not human_approved:
            blockers.append(f"unsafe_calls:{blocked_imports}")

        if any(not status for status in dependencies.values()):
            missing = [dep for dep, status in dependencies.items() if not status]
            pending_reviews = {rev.dependency_name for rev in self.dependency_ledger.get_pending_reviews()}
            for m in missing:
                if m in pending_reviews:
                    blockers.append(f"dependency_review_pending:{m}")
                else:
                    blockers.append(f"dependency_missing_or_unapproved:{m}")
                    
        if not has_tests:
            blockers.append(f"missing_required_tests: {test_filename}")
            
        # Sandbox status
        sandbox_safe = current_status not in ["unsafe_rejected"]

        can_promote = len(blockers) == 0 and human_approved and sandbox_safe

        # Determinar Recomendación
        if can_promote:
            recommendation = "Candidato listo para promoción experimental."
        elif any("dependency_review_pending" in b for b in blockers):
            recommendation = "Aprobar dependency review pendiente antes de promover."
        elif "needs_dependency" in current_status or any("dependency_missing" in b for b in blockers):
            recommendation = "Resolver dependencias antes de intentar promoción."
        elif "unsafe" in current_status or not ast_safe:
            recommendation = "Candidato RECHAZADO por seguridad. Mantener en cuarentena."
        else:
            recommendation = "Completar revisión humana y añadir tests."

        # Risk level logic: at least Medium for PDF or file handling
        base_risk = "medium" if ("pdf" in candidate_id or "file" in summary.capability_signature) else "low"
        
        assessment = SkillPromotionAssessment(
            candidate_id=candidate_id,
            capability_signature=summary.capability_signature,
            code_sha256=summary.code_sha256,
            current_status=current_status,
            target_stage=target_stage,
            ast_safe=ast_safe,
            sandbox_safe=sandbox_safe,
            has_required_tests=has_tests,
            dependency_status=dependencies,
            blocked_imports=blocked_imports,
            blocked_calls=[], 
            risk_level="high" if not ast_safe else base_risk,
            blockers=blockers,
            recommendation=recommendation,
            can_promote=can_promote
        )
        
        self._log_assessment(assessment)
        return assessment

    def dry_run_promote(self, candidate_id: str, target_stage: str = "experimental") -> Dict[str, Any]:
        """Simula la promoción y devuelve el resultado de la evaluación."""
        assessment = self.assess_candidate(candidate_id, target_stage)
        return {
            "candidate_id": candidate_id,
            "can_promote": assessment.can_promote,
            "target_stage": target_stage,
            "blockers": assessment.blockers,
            "recommendation": assessment.recommendation,
            "dry_run": True,
            "status": "success" if assessment.can_promote else "blocked"
        }

    def list_promotable_candidates(self) -> List[str]:
        """Lista IDs de candidatos que cumplen criterios básicos (sin bloqueadores fatales)."""
        summaries = self.reviewer.list_candidates()
        promotable = []
        for s in summaries:
            # Una versión rápida que no loguea todo
            if s.current_status == "approved_for_future_promotion" and not s.dangerous_calls_detected:
                promotable.append(s.candidate_id)
        return promotable

    def _log_assessment(self, assessment: SkillPromotionAssessment):
        """Registra la evaluación en el ledger de promoción."""
        event = {
            "event_id": f"prom_{os.urandom(4).hex()}",
            "timestamp": assessment.timestamp,
            "candidate_id": assessment.candidate_id,
            "capability_signature": assessment.capability_signature,
            "code_sha256": assessment.code_sha256,
            "target_stage": assessment.target_stage,
            "can_promote": assessment.can_promote,
            "blockers": assessment.blockers,
            "recommendation": assessment.recommendation,
            "human_required": assessment.requires_human_approval,
            "schema_version": PROMOTION_LEDGER_VERSION
        }
        try:
            with open(self.ledger_path, "a", encoding="utf-8") as f:
                f.write(json.dumps(event) + "\n")
        except Exception as exc:
            logger.error(f"Error writing to promotion ledger: {exc}")
