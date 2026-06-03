from __future__ import annotations

import json
import logging
import os
import time
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)

DEPENDENCY_LEDGER_VERSION = "dependency-review.v1"
DEFAULT_DEPENDENCY_LEDGER_PATH = "assets/memory/dependency_review_ledger.jsonl"

@dataclass(frozen=True)
class DependencyReviewEvent:
    event_id: str
    timestamp: float
    dependency_name: str
    purpose: str
    candidate_id: str
    risk_level: str
    required_by: str
    installed_status: str
    approved_status: str
    review_status: str
    notes_summary: str
    requires_human_approval: bool = True
    install_allowed: bool = False
    schema_version: str = DEPENDENCY_LEDGER_VERSION

    def to_json(self) -> str:
        return json.dumps(asdict(self))

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> DependencyReviewEvent:
        return cls(**data)

class DependencyReviewLedger:
    """
    Ledger para gestionar el ciclo de vida de las dependencias requeridas por skills experimentales.
    Asegura que ninguna librería se instale sin revisión explícita humana.
    """

    def __init__(self, ledger_path: Optional[str] = None):
        self.ledger_path = Path(ledger_path or DEFAULT_DEPENDENCY_LEDGER_PATH)
        self._ensure_dir()

    def _ensure_dir(self):
        if not self.ledger_path.parent.exists():
            self.ledger_path.parent.mkdir(parents=True, exist_ok=True)

    def append_review(self, event: DependencyReviewEvent):
        """Añade una revisión de dependencia al ledger."""
        try:
            with open(self.ledger_path, "a", encoding="utf-8") as f:
                f.write(event.to_json() + "\n")
        except Exception as exc:
            logger.error(f"Error escribiendo en ledger de dependencias: {exc}")

    def load_all(self) -> List[DependencyReviewEvent]:
        """Carga todas las revisiones del ledger."""
        events = []
        if not self.ledger_path.exists():
            return events

        try:
            with open(self.ledger_path, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if not line: continue
                    try:
                        data = json.loads(line)
                        events.append(DependencyReviewEvent.from_dict(data))
                    except Exception:
                        continue
        except Exception as exc:
            logger.error(f"Error leyendo ledger de dependencias: {exc}")
        return events

    def get_pending_reviews(self) -> List[DependencyReviewEvent]:
        """Obtiene las dependencias que están pendientes de revisión humana."""
        events = self.load_all()
        # Retornar la última versión de cada dependencia
        latest: Dict[str, DependencyReviewEvent] = {}
        for e in events:
            latest[e.dependency_name] = e
            
        pending = [e for e in latest.values() if e.review_status == "pending_human_review"]
        return sorted(pending, key=lambda x: x.timestamp, reverse=True)

    def get_approved_dependencies(self) -> List[DependencyReviewEvent]:
        """Obtiene las dependencias que ya han sido aprobadas."""
        events = self.load_all()
        latest: Dict[str, DependencyReviewEvent] = {}
        for e in events:
            latest[e.dependency_name] = e
            
        approved = [e for e in latest.values() if e.approved_status == "approved"]
        return sorted(approved, key=lambda x: x.timestamp, reverse=True)

    def is_dependency_approved(self, dependency_name: str) -> bool:
        """Verifica si una dependencia tiene permiso explícito para ser instalada/usada."""
        events = self.load_all()
        for e in reversed(events):
            if e.dependency_name == dependency_name:
                return e.install_allowed and e.approved_status == "approved"
        return False
