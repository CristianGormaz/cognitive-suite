# Análisis de Génesis en Sandbox

Este documento describe el procedimiento de análisis proactivo de capacidades faltantes en Greys-v3 utilizando GenesisEngine y GenesisSandbox sin comprometer la integridad del sistema.

## Ciclo de Vida del Candidato

1.  **Detección**: SparkEngine identifica una capacidad faltante repetida (ej: `math:solve_integral`) a través del `IngestionFailureLedger`.
2.  **Propuesta**: Spark emite una `evolutionary_doubt` al usuario sugiriendo investigar esta capacidad.
3.  **Autorización**: El usuario selecciona "Autorizar análisis en sandbox" (acción `sandbox_code`).
4.  **Generación**: `GenesisAnalysis` solicita al LLM un candidato de código Python puro para resolver la tarea.
5.  **Validación AST**: Se verifica que el código tenga la estructura esperada (una única función `_generated_skill_impl(context)`).
6.  **Inspección Sandbox**: `GenesisSandbox` analiza el AST buscando:
    -   Imports prohibidos (`os`, `subprocess`, `socket`, etc.).
    -   Llamadas peligrosas (`eval`, `exec`, `open`).
    -   Acceso a atributos internos (`__class__`, `__dict__`).
7.  **Cuarentena**: El candidato (envuelto en un módulo seguro) se guarda en `assets/quarantine/genesis_candidates/` con un nombre basado en su hash.
8.  **Registro**: El resultado del análisis (errores, riesgos, recomendaciones) se guarda en el `SemanticTensionLedger`.

## Aislamiento de Ejecución

**REGLA CRÍTICA**: GenesisEngine **NO** instala habilidades automáticamente durante la fase de análisis.

-   Los candidatos se guardan fuera de `src/skills/`.
-   `DynamicSkillLoader` **NO** tiene visibilidad de la carpeta de cuarentena.
-   El sistema nunca carga ni ejecuta el código candidato en el flujo de producción.

## Caso Piloto: `math:solve_integral`

Como primera prueba, Greys analiza la capacidad de resolver integrales.
-   Si el LLM propone usar `sympy`, el análisis marcará que `sympy` no está instalado en el entorno actual.
-   Se recomienda una implementación básica o marcar la dependencia faltante antes de cualquier intento de promoción.

## Próximos Pasos (Revisión Humana)

Un candidato en cuarentena requiere una revisión manual del código antes de ser promovido a `src/skills/stable/` o `src/skills/experimental/`. La promoción activará finalmente la carga dinámica de la nueva habilidad.
