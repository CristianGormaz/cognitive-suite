# Clasificación de Fallos en Process Envelope

Greys-v3 implementa una taxonomía de alta resolución para la etapa `process_envelope`, eliminando la ambigüedad de los fallos desconocidos y permitiendo una triada técnica precisa.

## ¿Qué es Process Envelope?

Es la etapa del orquestador principal (`MainOrchestrator`) que gestiona el ciclo de vida de una tarea desde que es ingerida hasta que se despacha una respuesta o acción. Involucra:
1.  **Validación de Contrato**: Asegura que el sobre (`TaskEnvelope`) sea íntegro.
2.  **Ruteo Local**: Intento de resolución vía `LocalIntentRouter`.
3.  **Planificación**: Generación de un `CognitivePlan` (vía LLM o heurísticas).
4.  **Despacho**: Ejecución de la acción seleccionada vía `ActionDispatcher`.

## Nueva Taxonomía de Fallos

| Tipo de Fallo | Familia | Descripción | Acción Sugerida |
| :--- | :--- | :--- | :--- |
| `process_envelope_contract_error` | contract | Faltan campos requeridos en el sobre. | Inspeccionar cargadores. |
| `process_envelope_missing_task_id` | contract | El sobre no tiene un ID único rastreable. | Revisar ruteador de ingesta. |
| `process_envelope_invalid_envelope` | contract | El objeto recibido no es un `TaskEnvelope` válido. | Validar tipos en `main.py`. |
| `process_envelope_local_router_error` | router | Fallo lógico en el ruteador de intenciones local. | Debuggear `LocalIntentRouter`. |
| `process_envelope_planner_result_invalid` | planner | El plan generado no cumple con el contrato `CognitivePlan`. | Refinar prompts del Planner. |
| `process_envelope_dispatch_error` | dispatcher | Error durante la ejecución física de la acción. | Revisar `ActionDispatcher` y Skills. |
| `process_envelope_policy_block` | policy | Una política de seguridad bloqueó la ejecución. | Revisar `ExternalChannelGate`. |
| `process_envelope_parse_error` | parser | Error al procesar JSON o estructuras de datos. | Revisar lógica de parseo. |
| `process_envelope_unhandled_exception` | orchestrator | Error inesperado no capturado por bloques específicos. | Revisar logs del orquestador. |

## Privacidad y Trazabilidad

Para cumplir con el mandato de seguridad:
-   **No se guardan payloads**: El ledger de fallos solo almacena metadatos estructurales (IDs, tipos, etapas).
-   **Sin Stacktraces**: Se guarda un resumen técnico (`technical_summary`) truncado y seguro.
-   **Sin Datos de Usuario**: Los reportes del `MorningBrief` nunca exponen el contenido de los mensajes que fallaron.

## Cómo interpretar el Morning Brief

El bloque `[Desglose Process Envelope]` muestra la distribución de estos fallos en los últimos 100 eventos, permitiendo identificar si el sistema sufre por problemas de contrato (deuda técnica) o por bloqueos de política (seguridad endurecida).

Para eventos registrados antes de esta taxonomía, Greys utiliza un proceso de [Reconciliación Derivada](UNKNOWN_FAILURE_RECONCILIATION.md).
