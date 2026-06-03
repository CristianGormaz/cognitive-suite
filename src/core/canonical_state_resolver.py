from __future__ import annotations

import json
import os
import time
import importlib.util
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional, Set

@dataclass(frozen=True)
class EntityState:
    entity_id: str
    canonical_status: str # approved_installed, active, historical_debt, disabled_by_config, etc.
    raw_status: str
    timestamp: float
    metadata: Dict[str, Any]

class CanonicalStateResolver:
    """
    Resuelve el estado canónico de los componentes del sistema reconciliando
    los ledgers históricos con la realidad actual del runtime.
    """

    def __init__(
        self,
        memory_dir: str = "assets/memory",
        skills_dir: str = "src/skills"
    ):
        self.memory_dir = Path(memory_dir)
        self.skills_dir = Path(skills_dir)

    def resolve_dependency_state(self, dependency_name: str) -> EntityState:
        """
        Determina si una dependencia está realmente instalada y aprobada.
        """
        # 1. Verificar presencia física
        is_installed = importlib.util.find_spec(dependency_name) is not None
        
        # 2. Verificar aprobación en ledger (tomamos el último estado)
        ledger_path = self.memory_dir / "dependency_review_ledger.jsonl"
        last_status = "unknown"
        last_ts = 0.0
        
        if ledger_path.exists():
            try:
                with open(ledger_path, "r", encoding="utf-8") as f:
                    for line in f:
                        if not line.strip(): continue
                        entry = json.loads(line)
                        if entry.get("dependency_name") == dependency_name:
                            last_status = entry.get("review_status", "pending")
                            last_ts = entry.get("timestamp", 0.0)
            except Exception: pass

        # 3. Reconciliación
        canonical = "unauthorized"
        # Si está instalado y el ÚLTIMO estado es aprobado, entonces está OK.
        if is_installed and last_status in ["approved_for_installation", "installed_approved"]:
            canonical = "approved_installed"
        elif is_installed and last_status == "pending_human_review":
            canonical = "installed_pending_review"
        elif not is_installed and last_status == "pending_human_review":
            canonical = "pending_review"
        elif not is_installed and last_status in ["approved_for_installation", "installed_approved"]:
            canonical = "approved_but_missing_physically"
            
        return EntityState(
            entity_id=dependency_name,
            canonical_status=canonical,
            raw_status=last_status,
            timestamp=last_ts,
            metadata={"is_installed_physically": is_installed}
        )

    def resolve_skill_state(self, skill_name: str) -> EntityState:
        """
        Resuelve si una skill experimental está disponible y autorizada.
        """
        # 1. Verificar existencia física (experimental)
        exp_path = self.skills_dir / "experimental" / f"skill_{skill_name}.py"
        exists = exp_path.exists()
        
        # 2. Verificar configuración
        is_enabled = os.getenv("GREYS_EXPERIMENTAL_SKILLS_ENABLED") == "1"
        allowlist = {s.strip() for s in os.getenv("GREYS_EXPERIMENTAL_SKILL_ALLOWLIST", "").split(",") if s.strip()}
        is_allowlisted = skill_name in allowlist
        
        # 3. Reconciliación
        if not exists:
            canonical = "not_found"
        elif not is_enabled:
            canonical = "disabled_by_global_config"
        elif not is_allowlisted:
            canonical = "disabled_by_allowlist"
        else:
            canonical = "active_experimental"
            
        return EntityState(
            entity_id=skill_name,
            canonical_status=canonical,
            raw_status="exists" if exists else "missing",
            timestamp=time.time(),
            metadata={
                "exists": exists,
                "is_enabled": is_enabled,
                "is_allowlisted": is_allowlisted,
                "path": str(exp_path) if exists else None
            }
        )

    def resolve_runtime_gate_state(self, gate_name: str) -> EntityState:
        """
        Resuelve el estado de un gate de runtime (p.ej. allowlist_mode).
        """
        # En esta arquitectura, el gate depende de GREYS_EXPERIMENTAL_SKILLS_ENABLED
        is_enabled = os.getenv("GREYS_EXPERIMENTAL_SKILLS_ENABLED") == "1"
        
        if not is_enabled:
            canonical = "disabled_by_design"
        else:
            canonical = "active_protection"
            
        return EntityState(
            entity_id=gate_name,
            canonical_status=canonical,
            raw_status="off" if not is_enabled else "on",
            timestamp=time.time(),
            metadata={"is_enabled": is_enabled}
        )

    def resolve_failure_family_state(self, failure_family: str, recent_hours: int = 24) -> EntityState:
        """
        Distingue entre fallos activos y deuda histórica reciente, 
        incluyendo llm_health_ledger si corresponde.
        """
        ledger_paths = [
            self.memory_dir / "ingestion_failure_ledger.jsonl",
            self.memory_dir / "llm_health_ledger.jsonl"
        ]
        
        now = time.time()
        cutoff = now - (recent_hours * 3600)
        very_recent_cutoff = now - 3600 # 1 hora para "activo"
        
        hist_count = 0
        recent_count = 0
        active_count = 0
        last_ts = 0.0
        
        for ledger_path in ledger_paths:
            if not ledger_path.exists(): continue
            try:
                with open(ledger_path, "r", encoding="utf-8") as f:
                    for line in f:
                        if not line.strip(): continue
                        entry = json.loads(line)
                        # ingestion_failure_ledger usa failure_type
                        # llm_health_ledger usa error_type o status
                        f_type = entry.get("failure_type") or entry.get("error_type") or entry.get("status")
                        
                        if f_type == failure_family:
                            ts = entry.get("timestamp", 0.0)
                            hist_count += 1
                            if ts > cutoff:
                                recent_count += 1
                            if ts > very_recent_cutoff:
                                active_count += 1
                            if ts > last_ts:
                                last_ts = ts
            except Exception: pass

        # 3. Reconciliación
        if active_count > 0:
            canonical = "active_failure"
        elif recent_count > 0:
            canonical = "recent_debt"
        elif hist_count > 0:
            canonical = "historical_debt"
        else:
            canonical = "inactive"
            
        return EntityState(
            entity_id=failure_family,
            canonical_status=canonical,
            raw_status=f"count:{hist_count}",
            timestamp=last_ts,
            metadata={
                "hist_count": hist_count,
                "recent_count": recent_count,
                "active_count": active_count
            }
        )

    def resolve_current_system_state(self) -> Dict[str, Any]:
        """Resumen profundo del estado actual."""
        return {
            "pypdf": self.resolve_dependency_state("pypdf").canonical_status,
            "pdf_capability": self.resolve_skill_state("pdf_reader_basic").canonical_status,
            "allowlist_gate": self.resolve_runtime_gate_state("allowlist_flow").canonical_status,
            "llm_health": self.resolve_failure_family_state("llm_timeout").canonical_status,
            "host_stress": self.resolve_failure_family_state("host_stress_block").canonical_status
        }

    def get_system_summary(self) -> Dict[str, Any]:
        """Mantiene compatibilidad con la versión previa."""
        return self.resolve_current_system_state()
