from __future__ import annotations

import os
import logging
from dataclasses import dataclass, field
from typing import Any, Dict, Optional, Mapping

from core.task_envelope import TaskEnvelope
from core.fast_path_reflex_gate import FastPathReflexGate

logger = logging.getLogger("LocalIntentRouter")

@dataclass(frozen=True)
class LocalIntentDecision:
    matched: bool
    intent_category: str = "unknown"
    proposed_action: str = "none"
    reason: str = "no_match"
    confidence: float = 0.0
    execution_payload: Dict[str, Any] = field(default_factory=dict)
    requires_iafa: bool = False
    bypass_llm: bool = False
    schema_version: str = "local-intent-decision.v1"

    def to_dict(self) -> Dict[str, Any]:
        from dataclasses import asdict
        return asdict(self)

class LocalIntentRouter:
    """
    Resuelve intenciones obvias, críticas o gobernadas por políticas locales
    sin necesidad de consultar al LLM.
    """

    def __init__(
        self, 
        stress_guard: Optional[Any] = None,
        minimal_neural_layer: Optional[Any] = None,
        promotion_gate: Optional[Any] = None,
        fast_path_gate: Optional[FastPathReflexGate] = None
    ):
        self.stress_guard = stress_guard
        self.minimal_neural_layer = minimal_neural_layer
        self.promotion_gate = promotion_gate
        self.fast_path_gate = fast_path_gate
        self.basic_keywords = {
            "hola": ("chat", "respond", "saludo"),
            "ayuda": ("chat", "respond", "help"),
            "help": ("chat", "respond", "help"),
            "estado": ("chat", "respond", "status"),
            "status": ("chat", "respond", "status"),
            "quien eres": ("chat", "respond", "identity"),
            "quién eres": ("chat", "respond", "identity"),
            "vitals": ("chat", "respond", "status"),
            "comandos": ("chat", "respond", "help"),
        }

    def check_fast_path(self, envelope: TaskEnvelope, start_time_ms: float = 0.0) -> Optional[LocalIntentDecision]:
        """Verifica si la entrada califica para la ruta mielinizada rápida (Fast-Path)."""
        if not self.fast_path_gate or not self.minimal_neural_layer or not self.promotion_gate:
            return None
            
        if envelope.source_type != "text":
            return None # PDFs y archivos no usan fast-path
            
        # Comprobar coincidencia de patrón en la capa neural
        input_sig = envelope.payload.value[:100] if envelope.payload.value else ""
        context = {"trigger_signature": input_sig, "intent_category": envelope.declared_intent}
        
        pattern = self.minimal_neural_layer.match_pattern(context)
        if not pattern:
            return None
            
        pid = pattern.get("pattern_id")
        p_name = pattern.get("pattern_name", "")
        active_ids = self.promotion_gate.get_active_reflexes()
        is_active = pid in active_ids
        
        # Safe Reflex Pack v1 defaults
        is_safe_pack = p_name in {
            "basic_greeting_reflex", "help_command_reflex", 
            "system_status_reflex", "identity_query_reflex"
        }
        human_approved = pattern.get("human_approved", is_safe_pack)
        rollback_available = pattern.get("rollback_available", is_safe_pack)
        
        # Consultar la compuerta Fast-Path
        assessment = self.fast_path_gate.assess_reflex(
            pattern_id=pid,
            reflex_name=p_name,
            input_signature=input_sig,
            active_local=is_active,
            risk_score=pattern.get("risk_score", 1.0),
            human_approved=human_approved,
            rollback_available=rollback_available,
            uses_llm=pattern.get("uses_llm", False),
            uses_files=pattern.get("uses_files", False),
            uses_network=pattern.get("uses_network", False),
            uses_dynamic_skill_loader=pattern.get("uses_dynamic_skill_loader", False),
            uses_genesis=pattern.get("uses_genesis", False),
            start_time_ms=start_time_ms
        )
        
        if assessment.fast_path_allowed:
            logger.info("Fast-path triggered for reflex: %s", assessment.reflex_name)
            return LocalIntentDecision(
                matched=True,
                intent_category=pattern.get("decision_category", "unknown"),
                proposed_action=pattern.get("recommended_action", "respond"),
                reason=f"fast_path_{assessment.reflex_name}",
                confidence=pattern.get("match_confidence", 1.0),
                bypass_llm=True,
                requires_iafa=False, # Fast-path certifica riesgo 0
                execution_payload={
                    "target_path": envelope.metadata.get("ingestion", {}).get("source_path") or "n/a"
                }
            )
            
        return None

    def route_envelope(self, envelope: TaskEnvelope) -> LocalIntentDecision:
        """
        Punto de entrada principal para decidir si un sobre puede procesarse localmente.
        """
        # 1. Prioridad: Reflejos Aprendidos y Aprobados (NUEVO)
        if self.minimal_neural_layer and self.promotion_gate:
            input_sig = envelope.payload.value[:100] if envelope.source_type == "text" else envelope.payload.mime_type
            context = {"trigger_signature": input_sig, "intent_category": envelope.declared_intent}
            
            pattern = self.minimal_neural_layer.match_pattern(context)
            if pattern:
                pid = pattern.get("pattern_id")
                active_ids = self.promotion_gate.get_active_reflexes()
                
                if pid in active_ids:
                    logger.info("Using approved active reflex: %s", pattern.get("pattern_name"))
                    return LocalIntentDecision(
                        matched=True,
                        intent_category=pattern.get("decision_category", "unknown"),
                        proposed_action=pattern.get("recommended_action", "respond"),
                        reason=f"active_reflex_{pattern.get('pattern_name')}",
                        confidence=pattern.get("match_confidence", 1.0),
                        bypass_llm=True,
                        requires_iafa=pattern.get("risk_score", 1.0) > 0.1,
                        execution_payload={
                            "target_path": envelope.metadata.get("ingestion", {}).get("source_path") or "n/a"
                        }
                    )

        # 2. Prioridad: Archivos (PDF)
        if envelope.payload.mime_type == "application/pdf":
            return self.route_pdf(envelope)

        # 3. Prioridad: Texto / Chat básico (Keywords fijas)
        if envelope.source_type in ["text", "voice_transcript"]:
            text = (envelope.payload.value or "").lower().strip()
            return self.route_text(text)

        return LocalIntentDecision(False, reason="unsupported_source_type")

    def route_text(self, text: str) -> LocalIntentDecision:
        """Mapea texto a intenciones locales."""
        # Limpiar texto para búsqueda básica
        clean = text
        for char in "¿?!!¡,.":
            clean = clean.replace(char, "")
        clean = clean.strip()

        # Búsqueda exacta
        if clean in self.basic_keywords:
            cat, act, reason = self.basic_keywords[clean]
            return LocalIntentDecision(
                matched=True,
                intent_category=cat,
                proposed_action=act,
                reason=reason,
                confidence=1.0,
                bypass_llm=True
            )

        # Búsqueda por palabras clave (si es muy corto o contiene palabras clave únicas)
        for kw, (cat, act, reason) in self.basic_keywords.items():
            if kw in clean and len(clean) < 30: # Heurística: no matchear si es un párrafo largo
                return LocalIntentDecision(
                    matched=True,
                    intent_category=cat,
                    proposed_action=act,
                    reason=f"keyword_{reason}",
                    confidence=0.9,
                    bypass_llm=True
                )

        return LocalIntentDecision(False, reason="no_keyword_match")

    def route_pdf(self, envelope: TaskEnvelope) -> LocalIntentDecision:
        """Determina el flujo determinístico para PDFs."""
        if self.stress_guard and self.stress_guard.is_host_under_stress():
             return LocalIntentDecision(
                matched=True,
                intent_category="pdf_ingestion",
                proposed_action="respond",
                reason="pdf_reader_blocked_by_stress",
                confidence=1.0,
                bypass_llm=True,
                execution_payload={"message_key": "host_under_stress"}
            )

        is_experimental = os.getenv("GREYS_EXPERIMENTAL_SKILLS_ENABLED") == "1"
        allowlist = {s.strip() for s in os.getenv("GREYS_EXPERIMENTAL_SKILL_ALLOWLIST", "").split(",") if s.strip()}
        
        if not is_experimental:
            return LocalIntentDecision(
                matched=True,
                intent_category="pdf_ingestion",
                proposed_action="respond",
                reason="pdf_reader_available_but_disabled",
                confidence=1.0,
                bypass_llm=True,
                execution_payload={"message_key": "pdf_reader_available_but_disabled"}
            )

        if "pdf_reader_basic" not in allowlist:
            return LocalIntentDecision(
                matched=True,
                intent_category="pdf_ingestion",
                proposed_action="respond",
                reason="pdf_reader_not_allowlisted",
                confidence=1.0,
                bypass_llm=True,
                execution_payload={"message_key": "pdf_reader_not_allowlisted"}
            )

        # Si está autorizado, ruteamos a la skill experimental sin preguntar al LLM
        return LocalIntentDecision(
            matched=True,
            intent_category="pdf_analysis",
            proposed_action="pdf_reader_basic",
            reason="deterministic_pdf_routing",
            confidence=1.0,
            bypass_llm=True,
            requires_iafa=True,
            execution_payload={
                "target_path": envelope.metadata.get("ingestion", {}).get("source_path") or "unknown"
            }
        )
