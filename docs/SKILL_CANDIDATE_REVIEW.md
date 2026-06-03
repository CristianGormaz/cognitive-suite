# Revisión de Candidatos a Habilidades (Skill Candidate Review)

Este documento describe el proceso de revisión humana para los candidatos de código generados proactivamente por Greys-v3.

## Estados del Candidato

Los candidatos en cuarentena pueden transicionar a través de los siguientes estados:

1.  **`pending_review`**: Estado inicial. El código ha sido generado y validado en sandbox, pero no revisado por un humano.
2.  **`approved_for_future_promotion`**: El humano aprueba el código conceptualmente. Está listo para ser promovido a una skill real en el próximo ciclo de integración.
3.  **`rejected_by_human`**: El código no cumple con los requisitos o la intención es incorrecta.
4.  **`needs_dependency`**: El código es válido pero requiere librerías externas (ej: `sympy`) que no están instaladas en el host.
5.  **`unsafe_rejected`**: El código intentó realizar operaciones peligrosas que el humano detectó (o el sandbox marcó como riesgo crítico).
6.  **`needs_more_tests`**: La lógica parece correcta pero se requiere validación adicional en sandbox antes de aprobar.

## Procedimiento de Revisión

Actualmente, la revisión se realiza mediante comandos de consola internos:

-   **/candidates**: Lista todos los archivos en `assets/quarantine/genesis_candidates/`.
-   **/summarize <id>**: Muestra un resumen seguro (hash, estado y preview) del código.
-   **/review <id> <status> [reason]**: Registra la decisión humana y actualiza el ledger de revisión.

## Aislamiento y Seguridad

-   **Cuarentena**: Los archivos permanecen en `assets/quarantine/` y son invisibles para el `DynamicSkillLoader`.
-   **Sin Ejecución**: Marcar un candidato como "aprobado" **NO** lo instala ni lo ejecuta. La promoción a skill activa es un paso separado y explícito.
-   **Registro de Tensión**: Cada decisión de revisión se registra en el `SemanticTensionLedger` para que el sistema aprenda de la retroalimentación humana (ej: si el humano rechaza muchas habilidades matemáticas, SparkEngine bajará su proactividad en ese área).

## Caso Piloto: `math:solve_integral`

Si un candidato requiere `sympy`, debe marcarse como `needs_dependency`. Greys registrará esta necesidad técnica para proponer en el futuro la actualización del entorno de ejecución.
