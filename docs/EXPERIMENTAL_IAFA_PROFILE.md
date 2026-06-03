# Perfil de Riesgo IAFA para Habilidades Experimentales

Greys-v3 utiliza una capa de evaluación de riesgo específica para las habilidades que se encuentran en fase experimental. Este perfil permite ajustar dinámicamente los umbrales de seguridad de IAFA basándose en el peligro técnico real de cada componente.

## Filosofía de Riesgo

El objetivo es permitir la innovación (skills nuevas) manteniendo una postura defensiva extrema. Mientras que una skill **Stable** tiene parámetros de fricción fijos, una skill **Experimental** es sometida a un análisis de riesgo antes de cada invocación.

## Factores de Evaluación

El `ExperimentalRiskProfile` analiza las siguientes dimensiones:

1.  **Aislamiento**: ¿Usa red? ¿Lee archivos locales? ¿Escribe en disco?
2.  **Gobernanza**: ¿Está en la allowlist? ¿Ha sido aprobada por un humano?
3.  **Calidad**: ¿Tiene tests unitarios asociados? ¿Pasó la validación del Sandbox?

## Niveles de Riesgo y Ajustes IAFA

Basándose en los factores anteriores, se asigna un nivel de riesgo que impacta directamente en las variables **R** (Riesgo), **I** (Inconsistencia) y **N** (Ruido) de IAFA:

| Riesgo | Descripción | Ajuste R/I/N (Típico) | Acción Resultante |
| :--- | :--- | :--- | :--- |
| **Low** | Local, sin red, aprobado, con tests. | 0.1 / 0.1 / 0.1 | Ejecución permitida (si IAFA global OK). |
| **Medium** | Maneja archivos, requiere dependencias. | 0.3 / 0.4 / 0.2 | IAFA más estricto; puede requerir confirmación. |
| **High** | Usa red o subprocesos, sin tests completos. | 0.6 / 0.7 / 0.4 | Bloqueo probable; requiere supervisión. |
| **Critical** | No allowlisted o falla sandbox. | 0.9 / 0.9 / 0.8 | **BLOQUEO ABSOLUTO**. |

## Ejemplo: Consultor de Tiempo Local

Actualmente clasificado como **Low Risk**:
-   **Motivo**: Python puro, librería estándar, sin red, aprobado por humano, validado por tests.
-   **Resultado**: Invocación fluida en runtime experimental.

## Trazabilidad

Cada evaluación de riesgo se registra en el `SemanticTensionLedger` bajo el evento `experimental_iafa_evaluated`. Esto permite auditar por qué una habilidad fue permitida o bloqueada en un momento específico de la sesión.
