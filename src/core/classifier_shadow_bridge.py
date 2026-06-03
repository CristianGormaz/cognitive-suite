from __future__ import annotations

import json
import logging
import os
import time
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional

from core.local_micro_classifier import LocalClassifierPrediction

logger = logging.getLogger("ClassifierShadowBridge")

@dataclass(frozen=True)
class ClassifierShadowCandidate:
    candidate_id: str
    timestamp: float
    source_prediction_id: str
    predicted_intent: str
    confidence: float
    input_signature: str
    proposed_reflex_name: str
    proposed_action: str
    target_module: str
    risk_score: float
    should_execute: bool = False # Siempre False en Shadow Mode
    shadow_only: bool = True # Siempre True en esta fase
    requires_human_review: bool = True
    reason_summary: str = ""
    schema_version: str = "classifier-shadow-candidate.v1"

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

class ClassifierShadowBridge:
    """
    Puente entre las predicciones del Micro-Clasificador y la MinimalNeuralLayer.
    Convierte predicciones de alta confianza en candidatos de reflejo en sombra.
    """

    def __init__(self, memory_dir: str = "assets/memory"):
        self.memory_dir = Path(memory_dir)
        self.ledger_path = self.memory_dir / "classifier_shadow_candidates.jsonl"
        self.intent_whitelist = ["greeting", "help", "status", "identity"]

    def build_candidate_from_prediction(self, prediction: LocalClassifierPrediction) -> Optional[ClassifierShadowCandidate]:
        """Evalúa si una predicción merece ser un candidato de reflejo en sombra."""
        
        if not self.should_create_shadow_candidate(prediction):
            return None

        intent = prediction.predicted_intent
        
        # Mapeo de intención a nombre de reflejo propuesto
        reflex_map = {
            "greeting": ("generalized_greeting_reflex", "respond"),
            "help": ("generalized_help_reflex", "respond"),
            "status": ("generalized_status_reflex", "respond"),
            "identity": ("generalized_identity_reflex", "respond"),
        }
        
        reflex_name, action = reflex_map.get(intent, (f"shadow_{intent}_reflex", "respond"))
        
        # Tratamiento especial para unknown_safe (no debe promoverse, solo observarse)
        if intent == "unknown_safe":
            reflex_name = "no_action_unknown_safe"
            action = "observe_only"

        risk = self.estimate_candidate_risk(intent)

        candidate = ClassifierShadowCandidate(
            candidate_id=f"cand_{os.urandom(4).hex()}",
            timestamp=time.time(),
            source_prediction_id=prediction.input_signature, # Usamos signature como ID de fuente por ahora
            predicted_intent=intent,
            confidence=prediction.confidence,
            input_signature=prediction.input_signature,
            proposed_reflex_name=reflex_name,
            proposed_action=action,
            target_module="LocalIntentRouter",
            risk_score=risk,
            reason_summary=prediction.reason_summary
        )
        
        self.persist_shadow_candidate(candidate)
        return candidate

    def should_create_shadow_candidate(self, prediction: LocalClassifierPrediction) -> bool:
        """Aplica filtros estrictos de madurez para candidatos shadow."""
        intent = prediction.predicted_intent
        
        # 1. Caso especial: unknown_safe siempre se registra como observe_only
        if intent == "unknown_safe":
            return True

        # 2. Whitelist de intenciones seguras
        if intent not in self.intent_whitelist:
            return False

        # 3. Confianza mínima alta (80%)
        if prediction.confidence < 0.80:
            return False
            
        # 4. Margen de seguridad (Extraído del reason_summary si es posible o asumiendo v1.2)
        # Para v1.2, el clasificador ya filtra por margen < 0.12 como unknown_safe.
        # Aquí pedimos un margen aún mayor (0.20) para calificar como CANDIDATO SHADOW fuerte.
        try:
            # Heurística para extraer margen del resumen: "Score X, Margin Y"
            parts = prediction.reason_summary.split("Margin")
            if len(parts) > 1:
                margin = float(parts[1].split()[0])
                if margin < 0.20:
                    return False
        except Exception:
            # Si no podemos parsear, somos conservadores
            return False
            
        return True

    def estimate_candidate_risk(self, intent: str) -> float:
        """Estima el riesgo de automatizar una intención específica."""
        # Las intenciones básicas tienen riesgo mínimo (0.05 - 0.1)
        # unknown_safe se considera sin riesgo de ejecución porque no ejecuta nada.
        risk_map = {
            "greeting": 0.05,
            "help": 0.1,
            "status": 0.1,
            "identity": 0.1,
            "unknown_safe": 0.0
        }
        return risk_map.get(intent, 0.5)

    def persist_shadow_candidate(self, candidate: ClassifierShadowCandidate):
        """Guarda el candidato en el ledger persistente."""
        try:
            self.memory_dir.mkdir(parents=True, exist_ok=True)
            with open(self.ledger_path, "a", encoding="utf-8") as f:
                f.write(json.dumps(candidate.to_dict()) + "\n")
        except Exception as exc:
            logger.error(f"Error persistiendo candidato shadow: {exc}")

    def summarize_candidates(self, limit: int = 50) -> List[ClassifierShadowCandidate]:
        """Carga candidatos recientes para reportes."""
        candidates = []
        if not self.ledger_path.exists(): return candidates
        try:
            with open(self.ledger_path, "r", encoding="utf-8") as f:
                lines = f.readlines()
                for line in lines[-limit:]:
                    if line.strip():
                        candidates.append(ClassifierShadowCandidate(**json.loads(line)))
        except Exception: pass
        return candidates
