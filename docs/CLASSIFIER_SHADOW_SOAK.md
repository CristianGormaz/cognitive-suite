# Classifier Shadow Soak Test

El **Shadow Soak Test** (Evaluación Prolongada en Sombra) de Greys-v3 es una fase de validación crítica para el `LocalMicroClassifier`. Su objetivo es medir la estabilidad, consistencia y seguridad del clasificador durante múltiples interacciones reales antes de permitir cualquier tipo de ejecución activa.

## Filosofía del Soak Test

A diferencia de una prueba unitaria estática, el soak test observa el comportamiento del clasificador bajo el ruido y la variabilidad del lenguaje natural en tiempo real. 

### Principio de Salud: unknown_safe
Un clasificador saludable debe reconocer sus propios límites. Si la tasa de `unknown_safe` es cero, se considera un signo de sobreconfianza (overfitting al dataset sintético). El soak test monitorea que esta tasa se mantenga en niveles razonables, garantizando que el sistema prefiera la duda segura ante entradas ambiguas.

## Métricas de Estabilidad

El `ClassifierShadowSoakEvaluator` calcula las siguientes métricas:

-   **Salud unknown_safe**: Porcentaje de entradas clasificadas como desconocidas. Una caída drástica indica riesgo de falsos positivos.
-   **Tasa de Duplicados**: Mide qué tan redundante es el ruteo. Una tasa alta sugiere que el sistema está atrapado en un patrón que ya debería haber sido promovido o silenciado.
-   **Confianza Promedio**: Estabilidad del score de confianza a lo largo del tiempo.
-   **Alerta de Sobreconfianza**: Se dispara si la precisión teórica es alta pero el margen de decisión es estrecho, indicando posible inestabilidad ante variaciones menores.

## Gobernanza de Madurez (v1.2)

Durante el periodo de madurez, el `ClassifierShadowSoakEvaluator` integra los resultados de la matriz de confusión con el comportamiento en tiempo real:
-   **Promotion Readiness**: Bloqueado en `observe_more`.
-   **Recomendaciones**: El sistema sugiere proactivamente cuándo ampliar el dataset de ruido o rebalancear ejemplos sintéticos.

## HITO: Evaluación Prolongada Activa (2026-06-02)

-   Módulo `ClassifierShadowSoakEvaluator` operativo.
-   Métricas de estabilidad integradas en el Morning Brief.
-   Establecida la línea base de observación para la generalización de intenciones.
