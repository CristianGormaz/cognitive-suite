# Local Micro-Classifier

El **Micro-Clasificador Local** de Greys-v3 es un motor de generalización de intenciones diseñado para operar de forma 100% local, privada y determinística.

## Propósito

A diferencia del `LocalIntentRouter`, que utiliza coincidencias exactas (Reflejos), el Micro-Clasificador utiliza técnicas de procesamiento de lenguaje natural livianas para reconocer variaciones en el lenguaje del usuario. Esto permite que Greys comprenda intenciones básicas sin depender de un modelo de lenguaje externo (LLM), reduciendo la latencia y la dependencia de red.

## Arquitectura (v1.2 - Maduro)

En la versión **v1.2 (Madurez)**, el clasificador consolida su lógica de generalización local:

-   **Balanced Accuracy**: Nueva métrica que promedia el desempeño en todas las intenciones, evitando que una categoría dominante (ej. greeting) esconda debilidades en otras.
-   **Margin Calibration**: El umbral de margen se ajustó a **0.12**, balanceando la precisión técnica con la necesidad de cautela.
-   **Ambiguity Penalty**: Se introdujeron penalizaciones para inputs cortos (1 token) o con alta dispersión semántica, forzando la clasificación segura como `unknown_safe`.
-   **Explanation v1.2**: Las explicaciones de predicción ahora incluyen el margen detectado y alertas de sobreconfianza.

## Métricas de Madurez

El sistema monitorea la salud del "Kernel Inmune" mediante tres pilares:
1.  **Exactitud Balanceada**: Calidad de la generalización en todo el espectro de intenciones.
2.  **Salud unknown_safe**: Capacidad del sistema para detectar el límite de su conocimiento (Tasa ideal: 20% - 40%).
3.  **Stability Soak**: Consistencia de las predicciones bajo ruido real durante múltiples ciclos.

## HITO: Madurez del Clasificador v1.2 (2026-06-02)

-   Motor de métricas avanzadas (Balanced Accuracy, Precision/Recall) operativo.
-   Dataset sintético balanceado y expandido con categorías de ruido.
-   Establecida la línea base para el diseño de la v1 con pesos persistidos.

## Shadow Mode (Modo Sombra)

Implementado el **2026-06-02**, el clasificador opera estrictamente en Modo Sombra:

1.  **Observación**: Analiza cada entrada de texto en paralelo al flujo real.
2.  **Calibración**: Compara su predicción con la decisión final del sistema (Router o Planner).
3.  **Registro**: Las evaluaciones se guardan en `local_classifier_shadow_ledger.jsonl`.
4.  **No Ejecución**: v1 **nunca** toma el control del flujo real; su objetivo es validar la precisión antes de su activación.

## Intenciones Soportadas (v1)

| Intención | Ejemplos de Generalización |
| :--- | :--- |
| **Greeting** | "buenas", "hey greys", "saludos" |
| **Help** | "qué puedes hacer", "muéstrame ayuda", "comandos" |
| **Status** | "estás operativo", "cómo va el sistema", "salud" |
| **Identity** | "¿qué eres?", "dime quién eres", "identidad" |

## Seguridad y Privacidad

-   **Local Only**: No realiza peticiones a red ni requiere GPUs.
-   **Privacidad**: No almacena el texto completo del usuario en el ledger de sombra, solo firmas semánticas y resultados de clasificación.
-   **Sin Dependencias**: Implementado íntegramente con la librería estándar de Python.

## HITO: Calibración v1 Completada (2026-06-02)

-   Precisión en dataset sintético superior al 90%.
-   Implementada normalización de tildes y caracteres especiales.
-   Visibilidad de pares de confusión en el Morning Brief.
