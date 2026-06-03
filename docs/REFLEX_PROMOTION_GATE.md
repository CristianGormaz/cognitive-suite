# Supervised Reflex Promotion Gate

Greys-v3 utiliza una **Compuerta de Promoción Supervisada** para gestionar la transición de reflejos locales desde una fase de observación (Shadow Mode) a una fase de ejecución activa.

## Criterios de Promoción

Para que un reflejo sea elegible para su activación, debe cumplir con los siguientes umbrales técnicos y contextuales:

1.  **Agreement Rate (>= 90%)**: El reflejo debe haber coincidido con la decisión del pipeline real en al menos el 90% de las observaciones.
2.  **Context Score (>= 85%)**: El marco de contexto arquitectónico debe ser estable.
3.  **Quorum Readiness (QRS >= 0.70)**: Masa crítica de evidencia diversificada, libre de sospecha de falso quórum (calculado por `QuorumPromotionReadiness`).
4.  **Risk Score (<= 0.20)**: El riesgo estimado debe ser bajo.
5.  **Aprobación Humana**: Ningún reflejo se activa sin el consentimiento explícito del operador.

## Comandos de Gestión

El operador puede gestionar los reflejos mediante los siguientes comandos en la consola:

-   `/reflex-candidates`: Lista los patrones destilados y su elegibilidad actual.
-   `/reflex-review <pattern_id>`: Muestra un análisis detallado del porqué un patrón es o no elegible.
-   `/reflex-approve <pattern_id> [reason]`: Registra la aprobación humana y activa el ruteo local para ese patrón.
-   `/reflex-disable <pattern_id> [reason]`: Desactiva un reflejo previamente aprobado (Rollback).

## Ciclo de Vida del Reflejo

1.  **Destilado**: Identificado por el `DeepseekExperienceDistiller`.
2.  **Shadow**: Evaluado en sombra por el `ReflexShadowEvaluator`.
3.  **Candidate**: Elegible según criterios del `ReflexPromotionGate`.
4.  **Active Local**: Aprobado por el humano y ejecutado por el `LocalIntentRouter`.
5.  **Disabled/Rolled Back**: Desactivado por seguridad o cambio de contexto.

## Seguridad e Integridad

-   **IAFA Superior**: Incluso si un reflejo está activo, la acción propuesta pasa por el motor IAFA para validar la seguridad en tiempo de ejecución.
-   **Trazabilidad**: Todas las promociones y desactivaciones se registran en el `reflex_promotion_ledger.jsonl`.
-   **No LLM**: La gestión de la compuerta es 100% local y determinística.
