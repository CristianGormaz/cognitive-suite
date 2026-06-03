from __future__ import annotations

import hashlib
import json
import logging
import os
import shutil
import time
from dataclasses import asdict
from pathlib import Path
from typing import Any, Dict, List, Optional

from cognition.skill_promotion_gate import SkillPromotionGate, SkillPromotionAssessment

logger = logging.getLogger("SkillExperimentalPromoter")

EXPERIMENTAL_DIR = "src/skills/experimental"
BACKUP_DIR = "assets/backups/experimental_skills"

class SkillExperimentalPromoter:
    """
    Gestiona la promoción física de candidatos de cuarentena a la categoría experimental.
    Implementa backups y validación de compuerta antes de cualquier movimiento.
    """

    def __init__(
        self,
        gate: Optional[SkillPromotionGate] = None,
        experimental_dir: str = EXPERIMENTAL_DIR,
        backup_dir: str = BACKUP_DIR
    ):
        self.gate = gate or SkillPromotionGate()
        self.experimental_path = Path(experimental_dir)
        self.backup_path = Path(backup_dir)
        self._ensure_dirs()

    def _ensure_dirs(self):
        self.experimental_path.mkdir(parents=True, exist_ok=True)
        self.backup_path.mkdir(parents=True, exist_ok=True)

    async def promote_to_experimental(self, candidate_id: str) -> Dict[str, Any]:
        """
        Evalúa y promueve un candidato a la carpeta experimental.
        Copia el archivo, no lo mueve de cuarentena.
        """
        # 1. Evaluar a través de la compuerta
        assessment = self.gate.assess_candidate(candidate_id, target_stage="experimental")
        
        if not assessment.can_promote:
            logger.warning(f"Promotion blocked for {candidate_id}: {assessment.blockers}")
            return {
                "status": "blocked",
                "candidate_id": candidate_id,
                "blockers": assessment.blockers,
                "recommendation": assessment.recommendation
            }

        # 2. Preparar destino y backup
        # El nombre final en experimental debe llevar el prefijo 'skill_' para el cargador dinámico
        clean_name = candidate_id.replace("candidate_", "")
        if not clean_name.startswith("skill_"):
            clean_name = f"skill_{clean_name}"
            
        dest_path = self.experimental_path / clean_name
        
        rollback_info = None
        if dest_path.exists():
            rollback_info = self._create_backup(dest_path)

        # 3. Realizar la copia
        source_path = self.gate.reviewer.quarantine_path / candidate_id
        try:
            shutil.copy2(source_path, dest_path)
            
            # 4. Registrar en el ledger
            self._log_promotion_event(assessment, dest_path, rollback_info)
            
            return {
                "status": "success",
                "candidate_id": candidate_id,
                "target_path": str(dest_path),
                "rollback_available": rollback_info is not None,
                "message": "Candidato promovido a experimental exitosamente. (Inactivo en runtime)"
            }
        except Exception as exc:
            logger.error(f"Failed to copy candidate {candidate_id} to experimental: {exc}")
            if rollback_info:
                self._rollback(dest_path, rollback_info)
            raise RuntimeError(f"Error físico durante la promoción: {exc}")

    def _create_backup(self, path: Path) -> Optional[str]:
        """Crea un backup del archivo existente antes de sobrescribir."""
        timestamp = int(time.time())
        backup_filename = f"{path.name}.{timestamp}.bak"
        backup_dest = self.backup_path / backup_filename
        try:
            shutil.copy2(path, backup_dest)
            return str(backup_dest)
        except Exception as exc:
            logger.error(f"Failed to create backup for {path}: {exc}")
            return None

    def _rollback(self, dest_path: Path, backup_path_str: str):
        """Restaura un backup en caso de fallo."""
        try:
            shutil.copy2(backup_path_str, dest_path)
            logger.info(f"Rollback successful for {dest_path}")
        except Exception as exc:
            logger.error(f"ROLLBACK FAILED for {dest_path}: {exc}")

    def _log_promotion_event(self, assessment: SkillPromotionAssessment, dest: Path, backup: Optional[str]):
        """Registra el evento físico en el ledger de promoción."""
        event = {
            "event_id": f"phys_prom_{os.urandom(4).hex()}",
            "timestamp": time.time(),
            "candidate_id": assessment.candidate_id,
            "code_sha256": assessment.code_sha256,
            "target_path": str(dest),
            "backup_path": backup,
            "action": "physical_promotion",
            "stage": "experimental",
            "schema_version": "skill-promotion-physical.v1"
        }
        try:
            with open(self.gate.ledger_path, "a", encoding="utf-8") as f:
                f.write(json.dumps(event) + "\n")
        except Exception as exc:
            logger.error(f"Error logging physical promotion: {exc}")
