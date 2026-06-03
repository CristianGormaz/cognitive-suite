from __future__ import annotations

import os
import time
import logging
from dataclasses import asdict, dataclass, field
from typing import Any, Dict, List, Optional

logger = logging.getLogger("IntrusiveSignalPolicy")

@dataclass(frozen=True)
class IntrusiveSignalAssessment:
    signal_id: str
    timestamp: float
    signal_type: str
    source_module: str
    trigger_signature: str
    perceived_threat: str
    evidence_strength: float
    urgency_score: float
    noise_score: float
    protective_value: float
    execution_risk: float
    learning_value: float
    recommended_containment: str
    recommended_translation: str
    recommended_action: str
    should_execute: bool
    should_quarantine: bool
    should_preserve_as_training_sample: bool
    requires_human_review: bool
    reason_summary: str
    schema_version: str = "intrusive-signal-assessment.v1"

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

class IntrusiveSignalPolicy:
    """
    Política para clasificar y evaluar señales intrusivas (alarmas, fallos, código inseguro).
    Transforma alertas crudas en insights operativos mediante contención y traducción.
    """

    def __init__(self):
        self.rules = {
            "candidate_unsafe": {
                "signal_type": "unsafe_code_signal",
                "perceived_threat": "high_integrity_risk",
                "urgency_score": 0.8,
                "protective_value": 0.95,
                "learning_value": 1.0,
                "recommended_containment": "level_3_quarantine",
                "recommended_translation": "No es una habilidad fallida, es una muestra útil para refinar defensas.",
                "recommended_action": "immune_training_sample",
                "should_execute": False,
                "should_quarantine": True,
                "preserve_as_training_sample": True
            },
            "llm_timeout": {
                "signal_type": "external_channel_limit",
                "perceived_threat": "operational_latency",
                "urgency_score": 0.5,
                "protective_value": 0.3,
                "learning_value": 0.7,
                "recommended_containment": "health_ledger",
                "recommended_translation": "El canal externo es inestable; priorizar ruteo local determinístico.",
                "recommended_action": "strengthen_local_routing",
                "should_execute": False,
                "should_quarantine": False,
                "preserve_as_training_sample": False
            },
            "host_stress_block": {
                "signal_type": "metabolic_limit_signal",
                "perceived_threat": "hardware_exhaustion",
                "urgency_score": 0.9,
                "protective_value": 0.9,
                "learning_value": 0.4,
                "recommended_containment": "stress_ledger",
                "recommended_translation": "Límite físico alcanzado; reducir carga o diferir tareas pesadas.",
                "recommended_action": "reduce_load_or_defer",
                "should_execute": False,
                "should_quarantine": False,
                "preserve_as_training_sample": False
            },
            "shadow_risky_divergence": {
                "signal_type": "reflex_miscalibration",
                "perceived_threat": "logic_divergence",
                "urgency_score": 0.3,
                "protective_value": 0.2,
                "learning_value": 0.9,
                "recommended_containment": "shadow_ledger",
                "recommended_translation": "El núcleo de reflejos aún no está alineado con el pipeline real.",
                "recommended_action": "keep_shadow_mode",
                "should_execute": False,
                "should_quarantine": False,
                "preserve_as_training_sample": False
            }
        }

    def assess_signal(self, signal_type: str, source: str, signature: str, metadata: Optional[Dict[str, Any]] = None) -> IntrusiveSignalAssessment:
        """Realiza una evaluación completa de una señal basada en reglas predefinidas."""
        rule = self.rules.get(signal_type, self._get_default_rule())
        
        # Calcular ruido (heurística simple)
        noise = self.estimate_noise(signal_type, metadata)
        
        return IntrusiveSignalAssessment(
            signal_id=f"sig_{os.urandom(4).hex()}",
            timestamp=time.time(),
            signal_type=rule["signal_type"],
            source_module=source,
            trigger_signature=signature,
            perceived_threat=rule["perceived_threat"],
            evidence_strength=metadata.get("evidence_strength", 1.0) if metadata else 1.0,
            urgency_score=rule["urgency_score"],
            noise_score=noise,
            protective_value=rule["protective_value"],
            execution_risk=metadata.get("risk_score", 0.5) if metadata else 0.5,
            learning_value=rule["learning_value"],
            recommended_containment=rule["recommended_containment"],
            recommended_translation=rule["recommended_translation"],
            recommended_action=rule["recommended_action"],
            should_execute=rule["should_execute"],
            should_quarantine=rule["should_quarantine"],
            should_preserve_as_training_sample=rule.get("preserve_as_training_sample", False),
            requires_human_review=True,
            reason_summary=f"Evaluación de señal {signal_type}: {rule['recommended_translation']}"
        )

    def estimate_noise(self, signal_type: str, metadata: Optional[Dict[str, Any]]) -> float:
        """Estima qué tan 'ruidosa' o redundante es la señal."""
        if not metadata: return 0.1
        # Si es un error repetido muchas veces en corto tiempo, el ruido sube
        if metadata.get("repetition_count", 0) > 5:
            return 0.8
        return 0.1

    def _get_default_rule(self) -> Dict[str, Any]:
        return {
            "signal_type": "unknown_intrusive_event",
            "perceived_threat": "unknown",
            "urgency_score": 0.5,
            "protective_value": 0.5,
            "learning_value": 0.5,
            "recommended_containment": "default_quarantine",
            "recommended_translation": "Señal desconocida detectada; requiere análisis manual.",
            "recommended_action": "contain_and_observe",
            "should_execute": False,
            "should_quarantine": True
        }
