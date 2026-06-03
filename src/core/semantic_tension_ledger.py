from __future__ import annotations

import json
import logging
import os
import time
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence

logger = logging.getLogger(__name__)

LEDGER_VERSION = "semantic-tension.v1"
DEFAULT_LEDGER_PATH = "assets/memory/semantic_tension_ledger.jsonl"

@dataclass(frozen=True)
class SemanticTensionEvent:
    event_id: str
    timestamp: float
    source: str
    event_type: str  # timeout, unsupported_action, llm_parse_error, evolutionary_doubt, action_executed, stress_limit
    task_id: str
    intent_category: str
    proposed_action: str
    proposal_signature: str  # e.g., "chat:respond"
    iafa_score: float = 0.0
    iafa_threshold: float = 0.7
    friction_R: float = 0.0
    friction_I: float = 0.0
    friction_N: float = 0.0
    host_under_stress: bool = False
    host_load_1m: float = 0.0
    available_memory_mb: int = 0
    user_outcome: str = "pending"  # pending, accepted, rejected, ignored, aborted
    tension_tau: float = 0.0
    capacity_A: float = 1.0
    stress_sigma: float = 0.0
    damage_delta: float = 0.0
    notes: str = ""
    schema_version: str = LEDGER_VERSION

    def to_json(self) -> str:
        return json.dumps(asdict(self))

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> SemanticTensionEvent:
        return cls(**data)

from core.semantic_fatigue_policy import SemanticFatiguePolicy

class SemanticTensionLedger:
    """
    Ledger local para registrar la tensión semántica y el daño acumulado.
    Basado en el modelo de tolerancia y estrés del sistema.
    """

    def __init__(self, ledger_path: Optional[str] = None):
        self.ledger_path = Path(ledger_path or DEFAULT_LEDGER_PATH)
        self.fatigue_policy = SemanticFatiguePolicy()
        self._ensure_dir()

    def _ensure_dir(self):
        if not self.ledger_path.parent.exists():
            self.ledger_path.parent.mkdir(parents=True, exist_ok=True)

    def append_event(self, event: SemanticTensionEvent):
        """Añade un evento al ledger de forma segura (append-only)."""
        try:
            with open(self.ledger_path, "a", encoding="utf-8") as f:
                f.write(event.to_json() + "\n")
        except Exception as exc:
            logger.error(f"Error escribiendo en el ledger semántico: {exc}")

    def load_recent(self, limit: int = 100) -> List[SemanticTensionEvent]:
        """Carga los eventos más recientes del ledger."""
        events = []
        if not self.ledger_path.exists():
            return events

        try:
            with open(self.ledger_path, "r", encoding="utf-8") as f:
                # Leemos todas las líneas y procesamos las últimas N
                lines = f.readlines()
                for line in lines[-limit:]:
                    line = line.strip()
                    if not line:
                        continue
                    try:
                        data = json.loads(line)
                        events.append(SemanticTensionEvent.from_dict(data))
                    except (json.JSONDecodeError, TypeError) as exc:
                        logger.warning(f"Línea corrupta en ledger semántico saltada: {exc}")
        except Exception as exc:
            logger.error(f"Error leyendo el ledger semántico: {exc}")
        
        return events

    def get_damage_score(self, proposal_signature: str, window_seconds: int = 86400) -> float:
        """Calcula el daño acumulado considerando decaimiento temporal."""
        events = self.load_recent(limit=500)
        cutoff = time.time() - window_seconds
        
        relevant_events = [
            e for e in events 
            if e.proposal_signature == proposal_signature and e.timestamp > cutoff
        ]
        
        now = time.time()
        return sum(self.fatigue_policy.calculate_decayed_damage(e.damage_delta, e.timestamp, now) for e in relevant_events)

    def should_suppress_proposal(self, proposal_signature: str, threshold: float = 2.0, has_new_evidence: bool = False) -> bool:
        """Determina si una propuesta debe ser suprimida usando SemanticFatiguePolicy."""
        events = self.load_recent(limit=500)
        return self.fatigue_policy.evaluate(events, proposal_signature, threshold, has_new_evidence)

    def mark_user_outcome(self, task_id: str, outcome: str):
        """Actualiza el resultado del usuario para un evento existente (vía nuevo evento de corrección)."""
        # En un ledger append-only puro, añadiríamos un evento de tipo 'outcome_update'
        # Pero para simplicidad heurística, buscaremos el evento original y emitiremos uno nuevo
        # que compense o actualice la tensión.
        events = self.load_recent(limit=50)
        original = next((e for e in reversed(events) if e.task_id == task_id), None)
        
        if not original:
            logger.warning(f"No se encontró el evento original para task_id {task_id}")
            return

        # Creamos el evento de actualización de resultado
        update_event = SemanticTensionEvent(
            event_id=f"upd_{os.urandom(4).hex()}",
            timestamp=time.time(),
            source="orchestrator",
            event_type="outcome_update",
            task_id=task_id,
            intent_category=original.intent_category,
            proposed_action=original.proposed_action,
            proposal_signature=original.proposal_signature,
            user_outcome=outcome,
            damage_delta=self.compute_damage_delta_for_outcome(outcome, original)
        )
        self.append_event(update_event)

    @staticmethod
    def compute_tensions(
        event_type: str, 
        host_under_stress: bool = False,
        iafa_friction: Optional[Dict[str, float]] = None,
        user_outcome: str = "pending"
    ) -> float:
        """Calcula la tensión semántica tau."""
        tau = 0.1  # Base
        if event_type == "timeout": tau += 0.5
        if event_type == "llm_parse_error": tau += 0.3
        if event_type == "unsupported_action": tau += 0.2
        if host_under_stress: tau += 0.4
        
        if iafa_friction:
            # Sumamos fricciones si son significativas
            tau += (iafa_friction.get("R", 0.0) * 0.2)
            tau += (iafa_friction.get("I", 0.0) * 0.2)
            tau += (iafa_friction.get("N", 0.0) * 0.1)
            
        return round(tau, 3)

    @staticmethod
    def compute_capacity(
        host_under_stress: bool = False,
        iafa_score: float = 0.5,
        has_response: bool = False
    ) -> float:
        """Calcula la capacidad A del sistema."""
        a = 0.5  # Base
        if not host_under_stress: a += 0.3
        if iafa_score > 0.8: a += 0.2
        if has_response: a += 0.1
        return round(min(1.0, a), 3)

    @staticmethod
    def compute_damage_delta_for_outcome(outcome: str, original: Optional[SemanticTensionEvent] = None) -> float:
        """Calcula el delta de daño d_t según el resultado."""
        if outcome == "rejected": return 0.5
        if outcome == "ignored": return 0.2
        if outcome == "aborted": return 0.3
        if outcome == "accepted": return -0.3  # Recuperación
        return 0.0
