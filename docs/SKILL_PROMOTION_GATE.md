# Compuerta de Promoción de Habilidades (Skill Promotion Gate)

Este documento describe la capa de seguridad y validación técnica que decide si un candidato en cuarentena puede ser promovido a una categoría operativa (`experimental` o `stable`).

## Criterios de Promoción

Para que un candidato sea promovible (`can_promote = True`), debe cumplir los siguientes requisitos:

1.  **Aprobación Humana**: El estado del candidato debe ser `approved_for_future_promotion`.
2.  **Seguridad AST**: No debe contener llamadas peligrosas no autorizadas (`os`, `subprocess`, etc.) detectadas por el análisis estático inicial.
3.  **Seguridad en Sandbox**: Debe haber pasado la validación de `GenesisSandbox`.
4.  **Dependencias Resueltas**: Todas las librerías requeridas deben estar instaladas y confirmadas en el host.
5.  **Tests Requeridos**: Debe contar con una suite de tests unitarios que validen su comportamiento (actualmente en fase de implementación heurística).

## Modo Dry-Run (Simulación)

Toda evaluación de promoción se realiza inicialmente en modo **Dry-Run**. Esto significa que el sistema evalúa y reporta los bloqueadores sin realizar cambios físicos:
- NO mueve archivos de `assets/quarantine/` a `src/skills/`.
- NO modifica `requirements.txt`.
- NO carga la habilidad en el `DynamicSkillLoader`.

## Comandos de Consola

-   **/promotion**: Lista todos los candidatos y su viabilidad de promoción (✅/❌).
-   **/promotion <candidate_id>**: Muestra el assessment detallado, incluyendo la lista de bloqueadores.
-   **/promotion-dry-run <candidate_id> <stage>**: Simula el proceso de promoción para un destino específico.

## Ledger de Promoción

Los resultados de las evaluaciones se registran en `assets/memory/skill_promotion_ledger.jsonl`. Este registro permite auditar por qué se rechazó o aceptó una habilidad y ayuda al sistema a refinar sus propuestas futuras.

## Relación con SparkEngine

SparkEngine utiliza la información de la compuerta para saber qué habilidades están "cerca" de ser operativas y motivar al usuario a resolver los bloqueadores pendientes (ej: instalar una dependencia o realizar una revisión final).
