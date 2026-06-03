from __future__ import annotations

import json
import logging
import os
import time
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional

from cognition.evolution_option_queue import EvolutionOption, EvolutionOptionQueue

logger = logging.getLogger("EvolutionOptionCurator")

CURATED_LEDGER_VERSION = "evolution-option-curated.v1"
DEFAULT_CURATED_LEDGER_PATH = "assets/memory/evolution_option_curated.jsonl"

@dataclass(frozen=True)
class CuratedEvolutionOption:
    curated_id: str
    timestamp: float
    title: str
    summary: str
    source_option_ids: List[str]
    merged_count: int
    family: str
    evidence_refs: List[str]
    best_suggested_micro_sprint: str
    priority_score: float
    expected_benefit: float
    estimated_risk: float
    recommended_next_action: str = "review"
    requires_human_approval: bool = True
    status: str = "pending_human_review"
    schema_version: str = CURATED_LEDGER_VERSION

    def to_json(self) -> str:
        return json.dumps(asdict(self), ensure_ascii=False)

class EvolutionOptionCurator:
    """
    Consolida opciones evolutivas similares en una única propuesta curada.
    """

    FAMILIES = {
        "timeout_performance": ["timeout", "llm", "latencia", "rendimiento", "performance", "ollama", "transport_error", "connection"],
        "planner_contract": ["planner", "contract", "parse_error", "malformed_json"],
        "dispatcher_actions": ["dispatcher", "unsupported_action"],
        "memory_ledgers": ["ledger", "write_error", "read_error", "memory"],
        "skill_errors": ["skill_error", "experimental_skill", "contract_error", "allowlist"],
        "system_stress": ["stress_block", "circuit_open", "cooldown"],
        "ingestion_files": ["mime type", "unsupported_file_type", "pdf", "pypdf", "reader", "document"],
        "math_integrals": ["math", "integral", "solve_integral", "matemática"],
        "testing_validation": ["tests", "validación", "testing", "pytest"],
        "unknown_failure": ["unknown_failure", "desconocido", "diagnóstico", "unknown", "fallo", "unexpected_exception"],
    }

    def __init__(
        self,
        queue: Optional[EvolutionOptionQueue] = None,
        curated_path: str = DEFAULT_CURATED_LEDGER_PATH
    ):
        self.queue = queue or EvolutionOptionQueue()
        self.curated_path = Path(curated_path)
        self._ensure_dir()

    def _ensure_dir(self):
        if not self.curated_path.parent.exists():
            self.curated_path.parent.mkdir(parents=True, exist_ok=True)

    def curate_and_save(self) -> List[CuratedEvolutionOption]:
        """Ejecuta el ciclo de curaduría y guarda los resultados."""
        pending = self.queue.list_pending()
        if not pending:
            return []

        clusters = self.cluster_similar_options(pending)
        curated_options = []
        
        # Cargar ya curados para evitar duplicar familias pendientes
        existing_curated = self.load_curated_pending()
        existing_families = {c.family for c in existing_curated}

        for family, options in clusters.items():
            if not options or family in existing_families:
                # Si ya hay un tema curado para esta familia, no crear otro.
                # Las nuevas opciones se quedarán en el queue hasta que el curado se resuelva
                # o podríamos fusionarlas en el futuro. Por ahora, evitamos rumiación.
                continue
            curated = self.merge_option_cluster(family, options)
            curated_options.append(curated)

        # Guardar en ledger curado
        self._save_curated(curated_options)
        
        # Marcar originales
        for curated in curated_options:
            for source_id in curated.source_option_ids:
                try:
                    self.queue.mark_status(source_id, "superseded_by_curated")
                except Exception as exc:
                    logger.error(f"Failed to mark source option {source_id} as superseded: {exc}")

        return sorted(curated_options, key=lambda x: x.priority_score, reverse=True)

    def cluster_similar_options(self, options: List[EvolutionOption]) -> Dict[str, List[EvolutionOption]]:
        """Agrupa opciones por heurísticas de keywords."""
        clusters = {family: [] for family in self.FAMILIES}
        clusters["other"] = []

        for opt in options:
            found_family = False
            text = (opt.title + " " + opt.summary).lower()
            
            for family, keywords in self.FAMILIES.items():
                if any(kw in text for kw in keywords):
                    clusters[family].append(opt)
                    found_family = True
                    break
            
            if not found_family:
                clusters["other"].append(opt)
        
        return clusters

    def merge_option_cluster(self, family: str, options: List[EvolutionOption]) -> CuratedEvolutionOption:
        """Fusiona un grupo de opciones en una única CuratedEvolutionOption."""
        if not options:
            raise ValueError("Cannot merge empty cluster")

        # Ordenar por prioridad para elegir la "mejor" base
        sorted_opts = sorted(options, key=lambda x: x.priority_score, reverse=True)
        best = sorted_opts[0]

        # Consolidar metadatos
        source_ids = [o.option_id for o in options]
        evidence = list(set(ref for o in options for ref in o.evidence_refs))
        
        # Título y resumen curados (mejor título de la familia o el mejor de la lista)
        title = best.title
        if len(options) > 1:
            if family == "timeout_performance":
                title = "Consolidación: Estabilizar y Optimizar Timeouts LLM"
            elif family == "planner_contract":
                title = "Consolidación: Robustecer Contratos del Planificador LLM"
            elif family == "dispatcher_actions":
                title = "Consolidación: Manejar Acciones No Soportadas del Dispatcher"
            elif family == "memory_ledgers":
                title = "Consolidación: Resolver Errores de Memoria (Ledgers)"
            elif family == "skill_errors":
                title = "Consolidación: Depurar y Estabilizar Habilidades"
            elif family == "system_stress":
                title = "Consolidación: Mejorar Manejo de Estrés del Sistema"
            elif family == "unknown_failure":
                title = "Consolidación: Diagnóstico y Manejo de Fallos Desconocidos"
            elif family == "math_integrals":
                title = "Consolidación: Resolución de Integrales y Capacidades Matemáticas"
            elif family == "ingestion_files":
                title = "Consolidación: Mejora de Procesamiento y Soporte de Archivos"
            elif family == "testing_validation":
                title = "Consolidación: Refuerzo de Suite de Tests y Validación"

        summary = f"Curaduría de {len(options)} propuesta(s). Resumen principal: {best.summary}"
        
        return CuratedEvolutionOption(
            curated_id=f"cur_{os.urandom(4).hex()}",
            timestamp=time.time(),
            title=title,
            summary=summary,
            source_option_ids=source_ids,
            merged_count=len(options),
            family=family,
            evidence_refs=evidence,
            best_suggested_micro_sprint=best.suggested_micro_sprint,
            priority_score=max(o.priority_score for o in options),
            expected_benefit=max(o.expected_benefit for o in options),
            estimated_risk=min(o.estimated_risk for o in options),
            status="pending_human_review"
        )

    def _save_curated(self, curated: List[CuratedEvolutionOption]):
        try:
            with open(self.curated_path, "a", encoding="utf-8") as f:
                for c in curated:
                    f.write(c.to_json() + "\n")
        except Exception as exc:
            logger.error(f"Error escribiendo en ledger curado: {exc}")

    def load_curated_pending(self) -> List[CuratedEvolutionOption]:
        """Carga opciones curadas pendientes, deduplicando por curated_id y familia."""
        curated = []
        if not self.curated_path.exists():
            return curated
        try:
            with open(self.curated_path, "r", encoding="utf-8") as f:
                for line in f:
                    if not line.strip(): continue
                    try:
                        data = json.loads(line)
                        curated.append(CuratedEvolutionOption(**data))
                    except Exception:
                        continue
        except Exception as exc:
            logger.error(f"Error leyendo ledger curado: {exc}")
        
        # Devolver solo el estado más reciente de cada ID, y filtrar por estado pendiente
        unique_by_id = {}
        for c in curated:
            unique_by_id[c.curated_id] = c
            
        pending = [c for c in unique_by_id.values() if c.status == "pending_human_review"]
        
        # Adicionalmente, si hay múltiples para la misma familia, preferir el más reciente/prioritario
        unique_by_family = {}
        for c in pending:
            # Si hay colisión de familia, nos quedamos con el de mayor prioridad
            if c.family not in unique_by_family or c.priority_score > unique_by_family[c.family].priority_score:
                unique_by_family[c.family] = c
        
        return sorted(unique_by_family.values(), key=lambda x: x.priority_score, reverse=True)
