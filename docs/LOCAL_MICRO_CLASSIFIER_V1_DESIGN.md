# Diseño del Micro-Clasificador Local v1

Este documento establece el diseño de la versión **v1** del clasificador local de Greys-v3, que introducirá la persistencia de pesos y un aprendizaje supervisado basado en la validación humana de los reflejos.

## Objetivos de v1

1.  **Persistencia de Pesos**: Mover el conocimiento del código estático a un archivo JSON de pesos refinados (`local_classifier_weights.v1.json`).
2.  **Aprendizaje Supervisado**: Ajustar los pesos de los tokens basándose en las aprobaciones y rechazos del `ReflexPromotionGate`.
3.  **Generalización Fluida**: Superar la limitación de coincidencias exactas mediante un modelo de scoring ponderado por importancia global de tokens (similar a TF-IDF liviano).
4.  **Aislamiento de Privacidad**: Garantizar que el proceso de ajuste de pesos no almacene frases reales de usuario, solo estadísticas de tokens anonimizadas.

## Estructura de Datos (Pesos)

```json
{
  "version": "1.0",
  "last_updated": 1780435200.0,
  "intents": {
    "greeting": {
      "hola": 0.85,
      "buenas": 0.42,
      "tokens": {
        "hola": 12.5,
        "buen": 5.2
      }
    }
  },
  "global_tokens": {
    "sistema": 0.1,
    "ayuda": 0.9
  }
}
```

## Ciclo de Aprendizaje v1

1.  **Inferencia (Tiempo Real)**: Usa pesos persistidos para predecir.
2.  **Shadow Evaluation**: Compara con el pipeline real.
3.  **Human Feedback**: El operador usa `/reflex-approve` o `/reflex-disable`.
4.  **Weight Adjustment (Asíncrono)**:
    -   Si se aprueba: Se incrementa el peso de los tokens del input para esa intención.
    -   Si se revierte: Se penalizan los tokens responsables de la predicción errónea.
5.  **Audit**: Los cambios en los pesos se registran en un log de evolución neural.

## Criterios de Transición (v0 -> v1)

Para pasar a la implementación de v1, se deben cumplir los siguientes hitos en el periodo de Soak Test:
-   **Precisión Sintética**: >= 92%.
-   **Balanced Accuracy**: >= 85%.
-   **Salud unknown_safe**: >= 20% (evidencia de cautela).
-   **Falsos Positivos Críticos**: 0 (en al menos 50 ciclos).
-   **Aprobación del Operador**: Revisión técnica del documento de diseño.

## Seguridad y Rollback

-   **Safe Defaults**: Si el archivo de pesos se corrompe o pierde, el sistema vuelve al dataset sintético integrado.
-   **Manual Override**: El operador podrá resetear los pesos a su estado inicial mediante `/reflex-reset-weights`.
-   **No Red**: El entrenamiento y ajuste ocurren 100% localmente.
