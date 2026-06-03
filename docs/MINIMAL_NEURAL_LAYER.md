# Minimal Neural Layer

La **Capa Neural Mínima** es el kernel de razonamiento local de Greys-v3. Su función es actuar como un puente entre el razonamiento profundo (LLM) y la ejecución determinística (Dispatcher).

## Propósito

A medida que el sistema interactúa con el usuario y el entorno, acumula "experiencia técnica". La Capa Neural Mínima almacena esta experiencia en forma de **Reflejos Operativos**, permitiendo que Greys responda a situaciones conocidas sin el costo cognitivo (latencia y recursos) de una inferencia completa.

## Arquitectura (v0)

En su versión inicial, la capa funciona bajo un modelo **simbólico de coincidencia de patrones**:

-   **Entrada**: Un contexto de ejecución (intent, fallos, estado de host).
-   **Memoria**: Un almacén de patrones destilados (`distilled_reasoning_ledger.jsonl`).
-   **Match**: Si la firma del contexto coincide con un patrón destilado, se activa un reflejo.
-   **Salida**: Una recomendación de acción o una explicación del bloqueo.

## Shadow Mode (Modo Sombra)

Implementado el **2026-06-02**, el Modo Sombra permite evaluar la eficacia de los reflejos destilados sin que estos afecten el flujo real de ejecución.

-   **Observación**: El sistema observa cada entrada y consulta a la Capa Neural Mínima.
-   **Evaluación**: El `ReflexShadowEvaluator` compara la sugerencia de la capa neural con la decisión final del pipeline real.
-   **Métricas**: Se calcula la tasa de coincidencia (`agreement_rate`), confianza y riesgo estimado.
-   **Ledger**: Las evaluaciones se guardan en `reflex_shadow_ledger.jsonl` para su análisis posterior.

Este modo es fundamental para calibrar el núcleo de razonamiento local antes de otorgarle autonomía de ejecución.

## Integración con Marco de Contexto Arquitectónico

A partir del **2026-06-02**, los reflejos observados en Modo Sombra ya no se evalúan únicamente por su tasa de coincidencia (`agreement_rate`). Ahora se validan mediante un **Frame de Contexto Multidimensional**:

-   **Validación de Promoción**: Un reflejo solo se marca como `candidate_for_promotion` si, además de tener alta coincidencia y confianza, el contexto global es estable (bajo estrés, sin violaciones de política).
-   **Bloqueo Contextual**: Si el entorno está bajo estrés (`stressed`) o las restricciones están bloqueadas (`blocked`), la promoción se difiere automáticamente hasta que la dimensión crítica se estabilice.

Esta capa asegura que la autonomía ganada por la Capa Neural Mínima sea siempre **situacionalmente correcta**.

## Promoción a Decisión Local Activa

Desde el **2026-06-02**, Greys-v3 permite la **Promoción Supervisada** de reflejos. 

-   **Gate de Promoción**: El `ReflexPromotionGate` valida que un patrón tenga una tasa de coincidencia >= 90% y un contexto estable.
-   **Aprobación Humana**: El operador puede usar el comando `/reflex-approve <pattern_id>` para activar un reflejo candidato.
-   **Ruteo Autónomo**: Una vez aprobado, el `LocalIntentRouter` ejecutará el reflejo automáticamente, eliminando la latencia de planificación LLM para ese caso específico.

## Diferencia con LLM

| Característica | DeepSeek-r1:8b | Minimal Neural Layer (v0) |
| :--- | :--- | :--- |
| **Ubicación** | Externa/Local (Host pesado) | Local (Trunk de Greys) |
| **Latencia** | Alta (segundos) | Casi Instantánea (ms) |
| **Razonamiento** | Generativo y flexible | Determinístico y basado en reglas |
| **Estado** | Sin memoria persistente (stateless) | Memoria histórica acumulada |

## Integración con IAFA

Los reflejos sugeridos por la Capa Neural Mínima pasan por la validación IAFA. Un reflejo que promueva una acción de alto riesgo será bloqueado o requerirá supervisión humana, asegurando que la autonomía ganada no comprometa la integridad del sistema.

## HITO: Context Frame & Shadow Mode Operativo (2026-06-02)

-   Activado mediante `GREYS_REFLEX_SHADOW_ENABLED=1`.
-   Implementado `MultidimensionalContextEngine` para validación situada.
-   Métricas visibles en el Morning Brief.
-   Cero impacto en la latencia o ejecución real.
