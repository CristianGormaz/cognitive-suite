# Fast-Path Reflex Gate (Ruta Mielinizada)

La **Fast-Path Reflex Gate** actúa como el mecanismo de mielinización en la arquitectura cognitiva de Greys-v3. Permite que intenciones simples, determinísticas y previamente certificadas esquiven (bypass) las capas pesadas de evaluación cognitiva y delegación simbiótica.

## Propósito

Reducir drásticamente la latencia y la sobrecarga del orquestador principal (*Dendritic Overfiltering*) cuando se procesan comandos de bajo nivel (ej. "hola", "ayuda", "estado"). 

## Requisitos de Certificación

Para que una intención sea procesada a través de la ruta mielinizada, debe cumplir con **todos** los siguientes criterios:

1.  **Reflejo Activo**: Debe estar formalmente promovido a `active_local`.
2.  **Riesgo Cero**: El `risk_score` certificado en la Capa Neural Mínima debe ser exactamente `0.0`.
3.  **Libre de Efectos Secundarios**: No puede invocar al LLM, tocar el sistema de archivos, realizar peticiones de red, ni interactuar con herramientas experimentales (PDF, Sandbox, Genesis).
4.  **Aprobación Humana y Rollback**: Debe haber sido auditado y poseer una ruta de reversión segura.
5.  **Certeza Absoluta**: No se admiten clasificaciones ambiguas o generalizadas (`unknown_safe` o `generalized_xxx`).

## Flujo de Ejecución

1.  El `MainOrchestrator` recibe un sobre (Envelope) de tipo `text`.
2.  Antes de consultar el `ContextEngine`, el `MicroClassifier`, o la `SymbioticDelegationPolicy`, se interroga al `LocalIntentRouter` mediante `check_fast_path`.
3.  Si el input empareja exactamente con un patrón mielinizado, la `FastPathReflexGate` lo aprueba.
4.  El orquestador ejecuta la acción y devuelve el resultado, **ahorrando hasta 150ms** de procesamiento por comando, sin sacrificar la seguridad (IAFA no es necesario para riesgo 0).

## HITO: Ruta Mielinizada Operativa (2026-06-02)

-   `FastPathReflexGate` implementada y auditable en `fast_path_reflex_ledger.jsonl`.
-   Reflejos piloto (`basic_greeting_reflex`, `help_command_reflex`, `system_status_reflex`, `identity_query_reflex`) acelerados con éxito.
-   Integración métrica total en el `MorningBrief`.
