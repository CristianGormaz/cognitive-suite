from __future__ import annotations

import logging
import os
from dataclasses import asdict, dataclass
from typing import Any, Dict, Optional

logger = logging.getLogger("LocalNarrativeLayer")

@dataclass(frozen=True)
class NarrativeResponse:
    message_id: str
    source_signal: str
    narrative_type: str # info, warning, success, alert, meta
    user_facing_summary: str
    technical_summary: str
    recommended_next_step: str
    severity: str # low, medium, high, critical
    reassurance_level: str # informational, corrective, protective
    requires_human_review: bool = False
    should_interrupt_user: bool = False
    schema_version: str = "narrative-response.v1"

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

class LocalNarrativeLayer:
    """
    Capa encagada de traducir decisiones técnicas y señales intrusivas
    en lenguaje humano claro, seguro y no alarmista.
    """

    def __init__(self):
        self.templates = {
            "intrusive_signal": {
                "summary": "Detecté una señal intensa en el sistema, pero no se ejecutará automáticamente.",
                "technical": "Señal {signal} detectada y contenida bajo IntrusiveSignalPolicy.",
                "next": "Fue aislada para análisis. Puedes revisarla en el Morning Brief.",
                "reassurance": "protective"
            },
            "candidate_unsafe": {
                "summary": "Este candidato de habilidad contiene patrones no alineados con la seguridad.",
                "technical": "Código detectado con riesgo nivel 3 (eval/exec/subprocess).",
                "next": "Se conserva como muestra inmune para fortalecer mis defensas internas.",
                "reassurance": "protective"
            },
            "llm_timeout": {
                "summary": "El canal de razonamiento profundo mostró latencia o no respondió.",
                "technical": "LlmTimeoutError registrado en llm_health_ledger.",
                "next": "Puedo continuar operando en modo local para tus tareas básicas.",
                "reassurance": "corrective"
            },
            "host_stress_block": {
                "summary": "El host físico está bajo alta carga en este momento.",
                "technical": "SystemStressGuard activó bloqueo metabólico preventivo.",
                "next": "Se recomienda diferir tareas pesadas para proteger la integridad del hardware.",
                "reassurance": "protective"
            },
            "pdf_disabled_by_configuration": {
                "summary": "Lector PDF detectado pero desactivado por configuración global.",
                "technical": "GREYS_EXPERIMENTAL_SKILLS_ENABLED=0 bloqueó ruteo automático.",
                "next": "Habilita el modo experimental si deseas probar esta capacidad.",
                "reassurance": "informational"
            },
            "pdf_reader_not_allowlisted": {
                "summary": "El lector PDF existe, pero no está autorizado en tu lista de permisos.",
                "technical": "pdf_reader_basic ausente en GREYS_EXPERIMENTAL_SKILL_ALLOWLIST.",
                "next": "Agrega 'pdf_reader_basic' a la allowlist para activarlo.",
                "reassurance": "informational"
            },
            "dependency_approved": {
                "summary": "La dependencia está aprobada e instalada correctamente.",
                "technical": "Canonical state: approved_installed.",
                "next": "No se requiere acción adicional.",
                "reassurance": "informational"
            },
            "reflex_shadow_mode": {
                "summary": "El núcleo de reflejos propuso una acción en modo sombra.",
                "technical": "Sugerencia local observada y comparada con flujo real.",
                "next": "No se tomó control del flujo; sigo calibrando mi razonamiento local.",
                "reassurance": "informational"
            },
            "iafa_block": {
                "summary": "La acción fue bloqueada por falta de alineación o riesgo elevado.",
                "technical": "IAFA score {score} por debajo del umbral {threshold}.",
                "next": "La seguridad es prioritaria; intenta una solicitud más específica o segura.",
                "reassurance": "protective"
            }
        }

    def explain_signal(self, signal_type: str, context: Optional[Dict[str, Any]] = None) -> NarrativeResponse:
        """Genera una explicación estructurada para una señal."""
        temp = self.templates.get(signal_type, self._get_default_template())
        ctx = context or {}
        
        # Renderizar resúmenes con contexto si aplica
        tech = temp["technical"].format(**ctx) if "{" in temp["technical"] else temp["technical"]
        
        return NarrativeResponse(
            message_id=f"msg_{os.urandom(4).hex()}",
            source_signal=signal_type,
            narrative_type="alert" if temp["reassurance"] == "protective" else "info",
            user_facing_summary=temp["summary"],
            technical_summary=tech,
            recommended_next_step=temp["next"],
            severity=ctx.get("severity", "medium"),
            reassurance_level=temp["reassurance"]
        )

    def render_user_message(self, response: NarrativeResponse) -> str:
        """Formatea el mensaje para el usuario final."""
        msg = f"{response.user_facing_summary}\n"
        msg += f"Recomendación: {response.recommended_next_step}"
        return msg

    def render_technical_message(self, response: NarrativeResponse) -> str:
        """Formatea el mensaje técnico (ej. para logs o modo debug)."""
        return f"[LOG]: {response.technical_summary} | ID: {response.message_id} | Reassurance: {response.reassurance_level}"

    def _get_default_template(self) -> Dict[str, str]:
        return {
            "summary": "Se detectó un evento interno inusual.",
            "technical": "Evento técnico sin plantilla específica.",
            "next": "Monitorear registros para más detalles.",
            "reassurance": "informational"
        }
