# Quorum Promotion Readiness (Madurez por Quórum)

La capa de **Quorum Promotion Readiness** es el mecanismo de Greys-v3 encargado de evaluar si un candidato (reflejo, patrón o propuesta) ha acumulado una masa crítica de evidencia estable, diversa y segura para ser promovido a la fase activa.

## Principio de Quórum
Inspirado en el *Quorum Sensing* biológico, Greys no toma decisiones de evolución basadas en una sola señal. La promoción requiere un consenso emergente entre múltiples fuentes de evidencia (Sombra, Clasificador, Reflexiones del Dream Mode, Auditoría IAFA).

## Métricas de Readiness (QRS)
El `Quorum Readiness Score` (QRS) se calcula integrando:
1.  **Masa de Evidencia**: Volumen total de señales detectadas (escala logarítmica).
2.  **Unicidad (Anti-False-Quorum)**: Penalización severa si la evidencia es redundante o proviene de una sola fuente repetitiva (evita la rumiación).
3.  **Estabilidad Temporal**: Exige que la evidencia se haya mantenido consistente durante al menos 48 horas.
4.  **Acuerdo y Contexto**: Validación de que el patrón coincide con las decisiones reales del sistema y con el marco de contexto actual.
5.  **Riesgo y Seguridad**: Bloqueo automático si el riesgo es superior a 0.2 o si no hay un mecanismo de rollback disponible.

## Estados de Madurez
-   **Insufficient Evidence**: Pocas señales o falta de requisitos técnicos (ej. sin rollback).
-   **Observe More**: Evidencia en crecimiento pero aún no consolidada temporalmente.
-   **False Quorum Suspected**: Alerta crítica de que el consenso es artificial (ej. muchas señales idénticas de la misma fuente).
-   **Ready for Human Review**: El sistema recomienda formalmente la revisión humana para promoción.

## Protección contra Falso Quórum
Greys detecta activamente el "Falso Quórum" mediante:
-   **Análisis de Diversidad**: Si el 90% de la evidencia viene de una sola fuente (ej. solo Dream Mode), el riesgo de falso quórum aumenta y el score disminuye.
-   **Detección de Rumiación**: Identificación de firmas idénticas que se repiten sin aportar valor diagnóstico nuevo.

## HITO: Evaluación de Quórum (Dry-Run) (2026-06-02)
-   Motor `QuorumPromotionReadiness` operativo.
-   Ledger de madurez implementado en `quorum_readiness_ledger.jsonl`.
-   Gobernanza bloqueada en modo observación: Greys calcula la madurez pero **nunca auto-promueve** en esta fase.
