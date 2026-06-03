from __future__ import annotations

import hashlib
import json
import logging
import os
import time
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional

logger = logging.getLogger("DreamQuestionLedger")

QUESTION_LEDGER_VERSION = "dream-question.v1"
DEFAULT_QUESTION_LEDGER_PATH = "assets/memory/dream_question_ledger.jsonl"

@dataclass(frozen=True)
class DreamQuestionEntry:
    question_id: str
    timestamp: float
    cycle: int
    topic: str
    question_text_hash: str
    context_hash: str
    evidence_refs: List[str]
    semantic_signature: str
    depth_level: int
    question_type: str  # observation, grouping, cause, strategy, validation, decision
    answer_summary: Optional[str] = None
    answer_hash: Optional[str] = None
    understood_score: float = 0.0
    repetition_count: int = 1
    next_action: str = "pending" # repeat_once, escalate_depth, create_evolution_option, suppress, local_only_after_timeout, defer_due_to_llm_timeout
    schema_version: str = QUESTION_LEDGER_VERSION

    def to_json(self) -> str:
        return json.dumps(asdict(self), ensure_ascii=False)

class DreamQuestionLedger:
    """
    Ledger local para memorizar las preguntas realizadas durante el modo sueño.
    Permite evitar la redundancia y escalar la profundidad cognitiva.
    """

    def __init__(self, ledger_path: str = DEFAULT_QUESTION_LEDGER_PATH):
        self.ledger_path = Path(ledger_path)
        self._ensure_dir()

    def _ensure_dir(self):
        if not self.ledger_path.parent.exists():
            self.ledger_path.parent.mkdir(parents=True, exist_ok=True)

    def append_entry(self, entry: DreamQuestionEntry):
        """Guarda una nueva entrada en el ledger."""
        try:
            with open(self.ledger_path, "a", encoding="utf-8") as f:
                f.write(entry.to_json() + "\n")
        except Exception as exc:
            logger.error(f"Error escribiendo en ledger de preguntas: {exc}")

    def load_all(self) -> List[DreamQuestionEntry]:
        """Carga todas las preguntas registradas."""
        entries = []
        if not self.ledger_path.exists():
            return entries
        try:
            with open(self.ledger_path, "r", encoding="utf-8") as f:
                for line in f:
                    if not line.strip(): continue
                    try:
                        data = json.loads(line)
                        entries.append(DreamQuestionEntry(**data))
                    except Exception:
                        continue
        except Exception as exc:
            logger.error(f"Error leyendo ledger de preguntas: {exc}")
        return entries

    def get_last_by_signature(self, signature: str) -> Optional[DreamQuestionEntry]:
        """Obtiene la última vez que se preguntó algo con esa firma semántica."""
        all_entries = self.load_all()
        for entry in reversed(all_entries):
            if entry.semantic_signature == signature:
                return entry
        return None

    def get_max_depth_for_topic(self, topic: str) -> int:
        """Determina cuál es el nivel más profundo alcanzado para un tema."""
        all_entries = self.load_all()
        depths = [e.depth_level for e in all_entries if e.topic == topic and e.understood_score >= 0.7]
        return max(depths) if depths else -1

    @staticmethod
    def generate_semantic_signature(topic: str, q_type: str, context_summary: str) -> str:
        """
        Crea una firma única para detectar repeticiones conceptuales.
        """
        raw = f"{topic.lower()}|{q_type.lower()}|{context_summary.lower()}"
        return hashlib.sha256(raw.encode()).hexdigest()[:16]

    @staticmethod
    def calculate_understood_score(answer: str) -> float:
        """
        Heurística simple para determinar si el sistema entendió la respuesta.
        En v0, buscamos estructura JSON válida y palabras clave de cierre.
        """
        score = 0.5 # Base
        if not answer: return 0.0
        
        # Si parece JSON
        if answer.strip().startswith("{") and answer.strip().endswith("}"):
            score += 0.3
            
        # Si contiene palabras de "conclusión" o "plan"
        keywords = ["micro-sprint", "recomendación", "patrón identificado", "acción", "estrategia"]
        if any(w in answer.lower() for w in keywords):
            score += 0.2
            
        return min(1.0, score)
