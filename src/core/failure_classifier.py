from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Any, Dict, Optional

logger = logging.getLogger(__name__)

CLASSIFIER_VERSION = "failure-classifier.v1"

@dataclass(frozen=True)
class FailureClassification:
    failure_type: str
    failure_stage: str
    error_type: str
    error_family: str
    severity: str  # low, medium, high, critical
    retryable: bool
    user_visible_summary: str
    technical_summary: str
    suggested_next_action: str
    confidence: float
    schema_version: str = CLASSIFIER_VERSION

    def to_dict(self) -> Dict[str, Any]:
        return {
            "failure_type": self.failure_type,
            "failure_stage": self.failure_stage,
            "error_type": self.error_type,
            "error_family": self.error_family,
            "severity": self.severity,
            "retryable": self.retryable,
            "user_visible_summary": self.user_visible_summary,
            "technical_summary": self.technical_summary,
            "suggested_next_action": self.suggested_next_action,
            "confidence": self.confidence,
            "schema_version": self.schema_version,
        }

class FailureClassifier:
    """
    Clasificador estructurado de fallos para Greys-v3.
    Reduce la cantidad de errores 'unknown' proveyendo taxonomía específica.
    """

    @staticmethod
    def classify_exception(exc: Exception, context: Optional[Dict[str, Any]] = None) -> FailureClassification:
        context = context or {}
        err_str = str(exc).lower()
        err_type = exc.__class__.__name__
        stage = context.get("stage", "unknown_stage")

        # 1. Triage específico por ETAPA (Prioridad alta para diagnóstico)
        if stage == "process_envelope":
            # Contract Family in process_envelope
            if "missing" in err_str and "field" in err_str:
                return FailureClassification("process_envelope_contract_error", stage, err_type, "contract", "high", False, "Fallo de contrato estructural.", err_str, "inspect_contract_definitions", 0.8)
            if "task_id" in err_str and ("missing" in err_str or "none" in err_str):
                return FailureClassification("process_envelope_missing_task_id", stage, err_type, "contract", "critical", False, "Task ID ausente en el sobre.", err_str, "inspect_ingestion_router_output", 0.9)
            if "invalid" in err_str and "envelope" in err_str:
                return FailureClassification("process_envelope_invalid_envelope", stage, err_type, "contract", "high", False, "Sobre de tarea inválido.", err_str, "inspect_envelope_schema", 0.8)
            
            # Sub-module specific errors in process_envelope
            if "router" in err_str or "route" in err_str:
                return FailureClassification("process_envelope_local_router_error", stage, err_type, "router", "high", False, "Error en ruteador local.", err_str, "inspect_local_intent_router", 0.7)
            if "planner" in err_str or "plan" in err_str or "contract" in err_str:
                return FailureClassification("process_envelope_planner_result_invalid", stage, err_type, "planner", "high", False, "Resultado del planificador inválido.", err_str, "inspect_planner_output", 0.7)
            if "dispatch" in err_str or "execute" in err_str:
                return FailureClassification("process_envelope_dispatch_error", stage, err_type, "dispatcher", "high", False, "Error en el despacho de acción.", err_str, "inspect_action_dispatcher", 0.7)
            if "policy" in err_str or "blocked" in err_str or "denied" in err_str:
                return FailureClassification("process_envelope_policy_block", stage, err_type, "policy", "medium", False, "Acción bloqueada por política.", err_str, "review_system_policies", 0.8)
            if "parse" in err_str or "json" in err_str:
                return FailureClassification("process_envelope_parse_error", stage, err_type, "parser", "medium", False, "Error de parseo en proceso de sobre.", err_str, "inspect_parser_logic", 0.7)
            
            if "unhandled" in err_str or "unexpected" in err_str:
                return FailureClassification("process_envelope_unhandled_exception", stage, err_type, "orchestrator", "critical", False, "Excepción no manejada en sobre cognitivo.", err_str, "inspect_main_orchestrator_logs", 0.6)
            
            # Si contiene keywords de LLM, dejamos que pase al bloque de LLM general
            llm_keywords = {"timeout", "ollama", "json", "parse", "connection", "circuit", "empty response"}
            if any(k in err_str for k in llm_keywords):
                pass 
            else:
                # Si no es nada obvio ni de LLM, lo marcamos como unknown en esta etapa
                return FailureClassification("unknown_failure_process_envelope", stage, err_type, "unknown", "medium", False, "Fallo desconocido en etapa de sobre.", err_str[:200], "inspect_failure_context", 0.4)

        # 2. LLM Family (Taxonomy from IafaTransceiver micro-sprint)
        if "llm_timeout" in err_str or "timeout" in err_str or "ollama no respondió" in err_str:
            return FailureClassification("llm_timeout", stage, err_type, "llm", "high", True, "El motor LLM tardó demasiado.", err_str, "retry_or_fallback", 0.9)
        if "llm_connection_error" in err_str or "connection" in err_str:
            return FailureClassification("llm_transport_error", stage, err_type, "llm", "high", True, "Fallo de red con el LLM.", err_str, "check_ollama_service", 0.9)
        if "llm_malformed_json" in err_str or "json" in err_str or "parse" in err_str:
            return FailureClassification("llm_malformed_json", stage, err_type, "llm", "medium", True, "El LLM devolvió un formato inválido.", err_str, "retry_with_strict_prompt", 0.9)
        if "llm_empty_response" in err_str or "empty response" in err_str:
            return FailureClassification("llm_empty_response", stage, err_type, "llm", "medium", True, "El LLM devolvió respuesta vacía.", err_str, "retry", 0.9)
        if "llm_host_stressed" in err_str or "stress" in err_str or "estrés" in err_str:
            return FailureClassification("host_stress_block", stage, err_type, "system", "high", False, "Sistema bajo mucho estrés.", err_str, "wait_for_cooldown", 0.9)
        if "llm_circuit_open" in err_str or "circuit" in err_str:
            return FailureClassification("llm_circuit_open", stage, err_type, "llm", "critical", False, "El circuito LLM está abierto por fallos.", err_str, "wait_for_cooldown", 0.9)
        if "llm_disabled" in err_str or "force_local_only" in err_str:
            return FailureClassification("llm_disabled_error", stage, err_type, "llm", "low", False, "El acceso al LLM está desactivado por configuración.", err_str, "check_system_configuration", 0.9)

        # Dispatcher / Action Family
        if "unsupported_action" in err_str or "action not supported" in err_str:
            return FailureClassification("dispatcher_unsupported_action", stage, err_type, "dispatcher", "medium", False, "Acción no soportada.", err_str, "propose_skill_creation", 0.8)
        
        # Ingestion Family
        if "mime type" in err_str or "tipo de archivo" in err_str:
            return FailureClassification("ingestion_unsupported_file_type", stage, err_type, "ingestion", "low", False, "Archivo no soportado.", err_str, "propose_reader_skill", 0.9)
        
        # Planner / Contract Family
        if "plan" in err_type.lower() or "contract" in err_str:
            return FailureClassification("planner_contract_error", stage, err_type, "planner", "medium", False, "El planificador no generó un contrato válido.", err_str, "refine_planner_prompt", 0.8)

        # Ledger Family
        if "ledger" in err_str and ("write" in err_str or "save" in err_str):
            return FailureClassification("ledger_write_error", stage, err_type, "memory", "high", False, "Error al guardar memoria.", err_str, "inspect_disk_permissions", 0.8)
        if "ledger" in err_str and ("read" in err_str or "load" in err_str):
            return FailureClassification("ledger_read_error", stage, err_type, "memory", "high", False, "Error al leer memoria.", err_str, "inspect_ledger_corruption", 0.8)

        # Skill Family
        if "skill" in err_type.lower() or "skill" in err_str:
            if "experimental" in err_str or "allowlist" in err_str:
                return FailureClassification("experimental_skill_error", stage, err_type, "skill", "medium", False, "Error en habilidad experimental.", err_str, "review_experimental_skill", 0.8)
            return FailureClassification("skill_contract_error", stage, err_type, "skill", "medium", False, "Error en ejecución de habilidad.", err_str, "debug_skill_code", 0.7)

        # Fallback (The True Unknown)
        return FailureClassification(
            failure_type="unknown_failure",
            failure_stage=stage,
            error_type=err_type,
            error_family="unknown",
            severity="medium",
            retryable=False,
            user_visible_summary="Ocurrió un error inesperado.",
            technical_summary=err_str[:200],  # No stacktrace, truncated.
            suggested_next_action="inspect_failure_context",
            confidence=0.1
        )
