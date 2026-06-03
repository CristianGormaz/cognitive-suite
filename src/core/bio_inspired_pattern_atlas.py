from __future__ import annotations

import logging
import os
from dataclasses import asdict, dataclass, field
from typing import Any, Dict, List, Optional

logger = logging.getLogger("BioPatternAtlas")

@dataclass(frozen=True)
class BioInspiredPattern:
    pattern_id: str
    biological_source: str
    greys_equivalent: str
    target_modules: List[str]
    core_function: str
    useful_when: str
    danger_when: str
    anti_pattern: str
    metrics: List[str]
    recommended_status: str = "active_observation"
    requires_human_review: bool = True
    schema_version: str = "bio-pattern.v1"

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

class BioInspiredPatternAtlas:
    """
    Catálogo de patrones de diseño bioinspirados aplicados a la arquitectura de Greys-v3.
    Provee una capa conceptual para evaluar la salud orgánica del sistema.
    """

    def __init__(self):
        self.patterns = self._initialize_atlas()

    def _initialize_atlas(self) -> Dict[str, BioInspiredPattern]:
        raw_data = [
            {
                "pattern_id": "dendritic_preprocessing",
                "biological_source": "Dendritas (micro-procesamiento local)",
                "greys_equivalent": "LocalIntentRouter, LocalMicroClassifier",
                "target_modules": ["LocalIntentRouter", "LocalMicroClassifier"],
                "core_function": "Filtrar y clasificar intenciones simples sin llamar al núcleo pesado.",
                "useful_when": "Baja latencia requerida para comandos comunes.",
                "danger_when": "Los filtros bloquean señales que necesitan análisis profundo.",
                "anti_pattern": "dendritic_overfiltering",
                "metrics": ["bypass_llm_rate", "unknown_safe_rate"]
            },
            {
                "pattern_id": "basket_cell_inhibition",
                "biological_source": "Células en cesta (interneuronas inhibidoras)",
                "greys_equivalent": "IAFA Engine, IntrusiveSignalPolicy",
                "target_modules": ["IAFAEngine", "IntrusiveSignalPolicy", "ImmuneQuarantinePolicy"],
                "core_function": "Frenar impulsos de alto riesgo o ruido sistémico.",
                "useful_when": "Incertidumbre elevada o amenaza detectada.",
                "danger_when": "La inhibición impide la exploración y el aprendizaje.",
                "anti_pattern": "immune_overblocking",
                "metrics": ["iafa_block_rate", "quarantine_count"]
            },
            {
                "pattern_id": "quorum_sensing",
                "biological_source": "Quórum bacteriano (conducta colectiva)",
                "greys_equivalent": "PromotionGate, MultidimensionalContextFrame",
                "target_modules": ["ReflexPromotionGate", "MultidimensionalContextEngine"],
                "core_function": "Activar autonomía solo con masa crítica de evidencia y estabilidad.",
                "useful_when": "Promoción de reflejos o activación de habilidades.",
                "danger_when": "Falsa sensación de consenso por datos sesgados.",
                "anti_pattern": "false_quorum",
                "metrics": ["agreement_rate", "context_score"]
            },
            {
                "pattern_id": "stem_cell_potential",
                "biological_source": "Células madre (potencial no diferenciado)",
                "greys_equivalent": "Candidatos en cuarentena, GenesisEngine",
                "target_modules": ["ImmuneQuarantinePolicy", "GenesisEngine"],
                "core_function": "Mantener capacidades latentes sin ejecución hasta validación.",
                "useful_when": "Descubrimiento de nuevas habilidades o código inseguro.",
                "danger_when": "Activación prematura antes de entender el perfil de riesgo.",
                "anti_pattern": "premature_differentiation",
                "metrics": ["candidate_count", "quarantine_duration"]
            },
            {
                "pattern_id": "myelinated_fast_path",
                "biological_source": "Vaina de mielina (transmisión acelerada)",
                "greys_equivalent": "Reflejos activos (active_local)",
                "target_modules": ["LocalIntentRouter", "ReflexPromotionGate"],
                "core_function": "Rutas rápidas para procesos validados y de bajo riesgo.",
                "useful_when": "Tareas repetitivas de alta confianza.",
                "danger_when": "Sobreconfianza en la ruta rápida ignorando cambios de entorno.",
                "anti_pattern": "fast_path_overconfidence",
                "metrics": ["active_reflex_usage", "rollback_count"]
            }
        ]
        return {p["pattern_id"]: BioInspiredPattern(**p) for p in raw_data}

    def list_patterns(self) -> List[BioInspiredPattern]:
        return list(self.patterns.values())

    def get_pattern(self, pattern_id: str) -> Optional[BioInspiredPattern]:
        return self.patterns.get(pattern_id)

    def summarize_risks(self) -> List[Dict[str, str]]:
        """Identifica los anti-patrones más críticos a vigilar."""
        return [
            {
                "pattern": p.pattern_id,
                "danger": p.danger_when,
                "anti_pattern": p.anti_pattern
            }
            for p in self.patterns.values()
        ]
