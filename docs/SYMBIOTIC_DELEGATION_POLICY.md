# Symbiotic Delegation Policy

La **Symbiotic Delegation Policy** (Política de Delegación Simbiótica) es el mecanismo determinístico que decide cuándo Greys-v3 debe resolver una tarea localmente ("Edge Cognition") y cuándo debe delegarla al núcleo LLM central.

## Principio Simbiótico

DeepSeek (o cualquier modelo LLM configurado) no es el cerebro de Greys; es una **herramienta cognitiva externa** de alto costo y alta latencia. Greys es el orquestador local. La política asegura que el LLM solo se invoque cuando el beneficio de su capacidad analítica supere el costo de red, el riesgo de alucinación y el estrés del sistema host.

## Métricas de Evaluación

Para cada tarea, la política calcula tres puntajes (scores):

### 1. Edge Routing Score (ERS)
Mide el beneficio neto de resolver la tarea localmente.
`ERS = Beneficio Local (Privacidad, Cero Tokens, Baja Latencia) - Costo Central (Latencia LLM, Estrés del Host)`

### 2. Symbiotic Delegation Score (SDS)
Mide el beneficio neto de invocar al LLM.
`SDS = Beneficio de Delegación (Complejidad de la Tarea, Necesidad Diagnóstica) - Costo de Delegación (Estrés del Host, Latencia de Red)`

### 3. Quorum Promotion Score (QPS)
Mide la confianza estadística para tomar una decisión en casos ambiguos.
`QPS = Evidencia * Margen de Ambigüedad`

## Árbol de Decisión Determinístico

El enrutamiento se determina evaluando las métricas en orden de prioridad:

1.  **Bloqueo por Estrés Crítico**: Si `host_stress >= 0.8`, la ruta recomendada es `defer_due_to_host_stress` (posponer).
2.  **Ruta Rápida Mielinizada**: Si existe un reflejo activo (Active Reflex) para la tarea, la ruta es `local_reflex`.
3.  **Protección contra Ambigüedad**: Si la entrada es altamente ambigua (bajo margen de confianza) y el QPS es bajo, la ruta es `observe_only`.
4.  **Delegación Simbiótica**: Si `SDS > ERS` y el uso del LLM está permitido, la ruta es `llm_delegate`.
5.  **Procesamiento de Borde**: Si `ERS >= SDS`, la ruta preferida es `local_fast_path`.
6.  **Bloqueo de Política**: Si `FORCE_LOCAL_ONLY` está activo pero la ruta local no es viable, la ruta es `block_due_to_policy`.

## Interacción con ExternalChannelGate

La `SymbioticDelegationPolicy` actúa como el **estratega** que recomienda la mejor ruta económica y lógica. Sin embargo, el `ExternalChannelGate` actúa como el **Guardián de Hardware**. 
Si la política recomienda `llm_delegate`, el `ExternalChannelGate` aún tiene el **poder de veto absoluto** si detecta que el circuito (Circuit Breaker) está abierto o si el modo de degradación estricta (`local_only`) está forzado por variables de entorno.

## HITO: Delegación Simbiótica (Dry-Run) (2026-06-02)

-   Módulo `SymbioticDelegationPolicy` implementado.
-   Evaluación en vivo de las métricas ERS, SDS y QPS.
-   Operando en modo de observación (Dry-Run) para validar el comportamiento antes de enlazar la ejecución real.
