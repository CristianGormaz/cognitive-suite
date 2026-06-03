from __future__ import annotations

import json
import logging
import os
import time
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional
from core.failure_classifier import FailureClassifier


logger = logging.getLogger(__name__)

INGESTION_LEDGER_VERSION = "ingestion-failure.v1"
DEFAULT_INGESTION_LEDGER_PATH = "assets/memory/ingestion_failure_ledger.jsonl"

@dataclass(frozen=True)
class IngestionFailureEvent:
    event_id: str
    timestamp: float
    source: str
    task_id: str
    source_type: str
    payload_mime_type: str
    payload_size_bytes: int
    payload_sha256: str
    declared_intent: Optional[str]
    detected_intent: Optional[str]
    proposed_action: Optional[str]
    failure_type: str  # unsupported_action, unsupported_file_type, llm_timeout, etc.
    failure_stage: str
    error_type: str
    error_summary: str
    supported_actions: List[str]
    missing_capability_signature: str  # e.g., "action:analyze_pdf"
    suggested_skill_category: str
    semantic_tension_event_id: Optional[str] = None
    host_under_stress: bool = False
    iafa_score: float = 0.0
    schema_version: str = INGESTION_LEDGER_VERSION

    def to_json(self) -> str:
        return json.dumps(asdict(self))

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> IngestionFailureEvent:
        return cls(**data)

class IngestionFailureLedger:
    """
    Ledger local para registrar fallos de ingestión y capacidades faltantes.
    Permite identificar patrones de necesidad para la evolución del sistema.
    """

    def __init__(self, ledger_path: Optional[str] = None):
        self.ledger_path = Path(ledger_path or DEFAULT_INGESTION_LEDGER_PATH)
        self._ensure_dir()

    def _ensure_dir(self):
        if not self.ledger_path.parent.exists():
            self.ledger_path.parent.mkdir(parents=True, exist_ok=True)

    def append_failure(self, event: IngestionFailureEvent):
        """Añade un fallo al ledger de forma segura."""
        try:
            with open(self.ledger_path, "a", encoding="utf-8") as f:
                f.write(event.to_json() + "\n")
        except Exception as exc:
            logger.error(f"Error escribiendo en ledger de fallos: {exc}")

    def load_recent(self, limit: int = 100) -> List[IngestionFailureEvent]:
        """Carga los fallos más recientes."""
        events = []
        if not self.ledger_path.exists():
            return events

        try:
            with open(self.ledger_path, "r", encoding="utf-8") as f:
                lines = f.readlines()
                for line in lines[-limit:]:
                    line = line.strip()
                    if not line: continue
                    try:
                        data = json.loads(line)
                        events.append(IngestionFailureEvent.from_dict(data))
                    except Exception:
                        continue
        except Exception as exc:
            logger.error(f"Error leyendo ledger de fallos: {exc}")
        return events

    def get_top_missing_capabilities(self, limit: int = 10) -> List[tuple[str, int]]:
        """Devuelve las capacidades faltantes más frecuentes."""
        events = self.load_recent(limit=500)
        counts: Dict[str, int] = {}
        for e in events:
            sig = e.missing_capability_signature
            if sig and sig != "unknown:unknown":
                counts[sig] = counts.get(sig, 0) + 1
        
        sorted_counts = sorted(counts.items(), key=lambda x: x[1], reverse=True)
        return sorted_counts[:limit]

    def should_propose_skill(self, missing_capability_signature: str, min_count: int = 3) -> bool:
        """Determina si una capacidad debería proponerse como nueva skill."""
        counts = dict(self.get_top_missing_capabilities())
        return counts.get(missing_capability_signature, 0) >= min_count

    @staticmethod
    def classify_failure(error: Exception, context: Dict[str, Any] = None) -> str:
        """Clasifica heurísticamente el tipo de fallo usando FailureClassifier."""
        classification = FailureClassifier.classify_exception(error, context)
        return classification.failure_type


    @staticmethod
    def suggest_category(intent: str, action: str, mime_type: str) -> str:
        """Sugiere una categoría de habilidad basada en el fallo."""
        if "pdf" in mime_type: return "lector_pdf"
        if "word" in mime_type or "docx" in mime_type: return "lector_docx"
        if action == "respond": return "responder_texto"
        if "audio" in mime_type: return "ingestion_audio"
        if "image" in mime_type: return "ingestion_image"
        return "unknown"
