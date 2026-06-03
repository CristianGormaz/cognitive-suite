# Classifier Shadow Reflex Bridge

El **Puente de Clasificación a Reflejo en Sombra** es el componente de Greys-v3 encargado de conectar la generalización estadística del `LocalMicroClassifier` con la memoria de patrones de la `MinimalNeuralLayer`.

## Propósito

Permitir que el sistema proponga nuevos reflejos locales basados en variaciones del lenguaje natural observadas en tiempo real. Este puente transforma predicciones de alta confianza en **Candidatos Shadow**, permitiendo que sean evaluados por el mismo pipeline de gobernanza que los reflejos destilados manualmente.

## Funcionamiento

Cuando el clasificador local predice una intención, el puente aplica **Filtros de Madurez**:

1.  **Evaluación de Elegibilidad**: Verifica si la intención está en la whitelist de seguridad.
2.  **Mapeo de Reflejo**: Traduce la intención en una propuesta formal.
3.  **Confianza Alta (>= 80%)**: Solo se consideran predicciones con alta probabilidad estadística.
4.  **Margen de Seguridad (>= 20%)**: El puente exige que la mejor intención esté claramente separada de la segunda opción (margen de confianza relativo).
5.  **Generación de Candidato**: Crea un objeto `ClassifierShadowCandidate` marcado como `shadow_only`.

## Tratamiento de la Incertidumbre (unknown_safe)

Si el clasificador predice `unknown_safe`, el puente genera un candidato de tipo `OBSERVE_ONLY`. Estos candidatos sirven para rastrear patrones de entrada que no coinciden con ninguna categoría conocida, pero nunca son elegibles para promoción activa, garantizando que la autonomía no se extienda a zonas de incertidumbre.

## Integración en la Arquitectura Dual

-   **Reflex Kernel**: El puente alimenta a la `MinimalNeuralLayer` con nuevas posibilidades de ruteo local.
-   **Shadow Evaluator**: Estos candidatos son comparados contra las decisiones reales del sistema para medir su precisión en condiciones de "fuego real".
-   **Morning Brief**: El operador recibe un reporte de los candidatos generados, permitiendo una supervisión informada de la expansión del núcleo local.

## HITO: Puente de Generalización Operativo (2026-06-02)

-   Módulo `ClassifierShadowBridge` implementado.
-   Flujo resiliente capaz de capturar candidatos incluso ante fallos del pipeline real.
-   Visibilidad completa de la expansión local en el Morning Brief.
