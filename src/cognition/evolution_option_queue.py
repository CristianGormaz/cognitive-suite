from __future__ import annotations

import json
import logging
import os
import time
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional

logger = logging.getLogger("EvolutionOptionQueue")

OPTION_LEDGER_VERSION = "evolution-option.v1"
DEFAULT_OPTION_QUEUE_PATH = "assets/memory/evolution_option_queue.jsonl"

@dataclass(frozen=True)
class EvolutionOption:
    option_id: str
    timestamp: float
    title: str
    summary: str
    source: str = "dream_mode"
    evidence_refs: List[str] = field(default_factory=list)
    related_ledgers: List[str] = field(default_factory=list)
    tension_tau: float = 0.0
    capacity_A: float = 1.0
    stress_sigma: float = 0.0
    damage_score: float = 0.0
    expected_benefit: float = 0.5
    estimated_risk: float = 0.1
    priority_score: float = 0.0
    suggested_micro_sprint: str = ""
    requires_human_approval: bool = True
    status: str = "pending_human_review" # pending_human_review, approved, rejected, deferred, in_progress, completed
    schema_version: str = OPTION_LEDGER_VERSION

    def to_json(self) -> str:
        return json.dumps(asdict(self), ensure_ascii=False)

class EvolutionOptionQueue:
    """
    Cola de opciones evolutivas generadas por el sistema.
    Permite priorizar y gestionar propuestas técnicas basadas en la experiencia.
    """

    def __init__(self, queue_path: str = DEFAULT_OPTION_QUEUE_PATH):
        self.queue_path = Path(queue_path)
        self._ensure_dir()

    def _ensure_dir(self):
        if not self.queue_path.parent.exists():
            self.queue_path.parent.mkdir(parents=True, exist_ok=True)

    def append_option(self, option: EvolutionOption):
        """Añade una opción a la cola."""
        try:
            with open(self.queue_path, "a", encoding="utf-8") as f:
                f.write(option.to_json() + "\n")
        except Exception as exc:
            logger.error(f"Error escribiendo en la cola de evolución: {exc}")

    def load_all(self) -> List[EvolutionOption]:
        """Carga todas las opciones de la cola, deduplicando por option_id (mantiene la más reciente)."""
        options_dict: Dict[str, EvolutionOption] = {}
        if not self.queue_path.exists():
            return []
        try:
            with open(self.queue_path, "r", encoding="utf-8") as f:
                for line in f:
                    if not line.strip(): continue
                    try:
                        data = json.loads(line)
                        opt = EvolutionOption(**data)
                        options_dict[opt.option_id] = opt
                    except Exception:
                        continue
        except Exception as exc:
            logger.error(f"Error leyendo la cola de evolución: {exc}")
        
        # Devolver ordenadas por timestamp para consistencia histórica si fuera necesario,
        # pero para list_pending usaremos priority_score.
        return list(options_dict.values())

    def list_pending(self) -> List[EvolutionOption]:
        """Devuelve las opciones pendientes de revisión humana, ordenadas por prioridad."""
        options = self.load_all()
        pending = [o for o in options if o.status == "pending_human_review"]
        # Ordenar por prioridad descendente
        return sorted(pending, key=lambda x: x.priority_score, reverse=True)

    def mark_status(self, option_id: str, new_status: str, reason: Optional[str] = None):
        """Marca una opción con un nuevo estado (genera un nuevo evento en el ledger)."""
        options = self.load_all()
        original = next((o for o in reversed(options) if o.option_id == option_id), None)
        if not original:
            raise ValueError(f"Option ID {option_id} not found")

        updated = EvolutionOption(
            **{**asdict(original), "status": new_status, "timestamp": time.time()}
        )
        self.append_option(updated)

    @staticmethod
    def calculate_priority(benefit: float, risk: float, damage: float, capacity: float) -> float:
        """
        Ranking heurístico basado en el modelo de tensión.
        priority_score = beneficio_estimado - riesgo_estimado - daño_acumulado + capacidad_actual
        """
        score = benefit - risk - damage + capacity
        return round(score, 3)
