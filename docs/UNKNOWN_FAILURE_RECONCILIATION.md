# Reconciliación de Deuda Unknown (Epigenética de Memoria)

Greys-v3 implementa un mecanismo de reconciliación derivada para gestionar los fallos acumulados antes de la estandarización de la taxonomía técnica.

## Concepto: Etiqueta Epigenética

A diferencia de un proceso de compactación o reescritura, la reconciliación funciona como una **capa interpretativa** sobre los ledgers originales.
-   **Inmutabilidad**: Los registros originales en `ingestion_failure_ledger.jsonl` permanecen intactos para auditoría forense.
-   **Derivación**: El sistema infiere el tipo de fallo real basándose en metadatos estructurales (`error_type`, `failure_stage`, `error_summary`).
-   **Contexto**: Esta interpretación se guarda en un ledger derivado (`unknown_failure_reconciliation_ledger.jsonl`).

## Diferencia entre Deuda y Falla Activa

| Estado | Definición | Interpretación en Morning Brief |
| :--- | :--- | :--- |
| **Historical Debt** | Fallos ocurridos antes del commit `10bbb68` (v3.3). | Se muestran como deuda a monitorear, no como bloqueos actuales. |
| **Post-Taxonomy Unknown** | Fallos `unknown_failure` registrados después de la taxonomía. | **ALERTA**: Indica una brecha en la clasificación que requiere atención inmediata. |
| **Reclassified Debt** | Eventos antiguos con inferencia de alta confianza. | Permite entender qué estaba fallando realmente en el pasado. |

## Trazabilidad y Privacidad

El ledger de reconciliación cumple con los mandatos de seguridad más estrictos:
-   **No Payloads**: Solo se referencian IDs de eventos originales.
-   **No PII**: No se extraen textos de usuario ni prompts durante la inferencia.
-   **Idempotencia**: `MorningBrief` utiliza el ledger derivado para evitar cálculos redundantes, asegurando un reporte rápido y consistente.

## Cómo leer el Morning Brief

En la sección `[Reconciliación de Deuda Unknown]`:
-   Si **Unknown Post-Taxonomía** es `0 [OK]`, significa que el sistema está clasificando correctamente toda la experiencia actual.
-   Si hay **Inferencias derivadas**, estas te darán una pista clara de qué habilidades faltaban o qué contratos se rompían antes de la mejora v3.3.
