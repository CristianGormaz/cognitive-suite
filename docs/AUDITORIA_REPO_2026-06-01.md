# Auditoria de Repositorio: Greys-v3

Fecha: 2026-06-01

## Resumen Ejecutivo

`greys-v3` no es un producto cerrado ni una libreria empaquetada. Es un runtime local de arquitectura cognitiva experimental centrado en:

1. gobernanza determinista (`IAFAEngine`);
2. ingestión segura de entradas (`TaskEnvelope` + `IngestionRouter`);
3. planificación asistida por LLM local (`LLMPlanner` + Ollama);
4. ejecución limitada y auditable (`ActionDispatcher`, `IafaAuditor`);
5. evolución controlada de habilidades (`GenesisSandbox`, cuarentena, revisión humana, promoción experimental);
6. memoria operativa en ledgers (`assets/memory/*.jsonl`);
7. reflexión diferida (`DreamMode`) y priorización operativa (`MorningBrief`);
8. proactividad acotada (`SparkEngine`) con aprobación humana obligatoria.

La idea central de Greys-v3 no es "ser un chatbot". La idea es construir un asistente local que pueda operar, fallar, registrar evidencia, autorregularse y proponer evolución sin saltarse una capa de soberanía técnica.

## Que Es Realmente Greys-v3

La forma más fiel de describirlo es:

- un **kernel cognitivo local** con gating IAFA;
- un **sistema de memoria operacional** basado en JSONL append-only;
- un **pipeline de skill lifecycle** con sandbox, cuarentena y promoción;
- un **bucle de aprendizaje diferido** sobre fallos y fatiga;
- una **superficie de UI/CLI experimental**, no completamente desacoplada.

No es todavía:

- una plataforma multiusuario;
- un paquete Python listo para distribuir;
- un CLI headless robusto;
- un sistema de plugins estable;
- un repositorio con fronteras limpias entre core, runtime state y experimentos.

## Mapa del Sistema

### Flujo reactivo principal

1. `src/main.py` crea el grafo principal.
2. `IngestionRouter` transforma texto/archivos en `TaskEnvelope`.
3. `LLMPlanner` clasifica intención y propone acción.
4. `ActionDispatcher` mezcla fricción estimada con contexto IAFA y decide si ejecutar o caer a fallback.
5. `CognitiveOrchestrator` abre el loop humano para dudas/fallbacks.
6. `GenesisAnalysis` y `GenesisSandbox` permiten analizar capacidades faltantes sin instalarlas.
7. Si una skill experimental existe y está permitida, `DynamicSkillLoader` intenta cargarla.

### Flujo de memoria y evolución

- `SemanticTensionLedger`: fatiga, daño, supresión.
- `IngestionFailureLedger`: fallos y capacidades faltantes.
- `DependencyReviewLedger`: dependencias externas con aprobación humana.
- `DreamMode`: minería nocturna de esos ledgers.
- `EvolutionOptionQueue` y `EvolutionOptionCurator`: backlog técnico derivado de evidencia.
- `MorningBrief`: resumen ejecutivo para operador humano.
- `SparkEngine`: propone evolución desde inactividad o recurrencia de fallos.

## Estado Operativo Observado

### Inventario

- Código fuente en `src/`: ~9k LOC.
- Suite de tests: `249` tests recolectados.
- Dependencias declaradas: `aiohttp`, `python-docx`, `PySide6`, `qasync`, `pypdf`.
- Estado runtime persistente en `assets/memory/`.
- Candidatos en cuarentena en `assets/quarantine/genesis_candidates/`.
- Logs de sueño en `logs/`.

### Evidencia runtime actual

El `Morning Brief` real del repositorio indica:

- 19 ciclos de sueño registrados;
- profundidad cognitiva alcanzada: 5;
- dominancia de `llm_timeout` y `unknown_failure`;
- dependencia `pypdf` aprobada e instalada;
- backlog curado orientado a:
  - estabilizar timeouts del LLM;
  - diagnosticar fallos desconocidos;
  - resolver capacidad matemática faltante.

Esto muestra que Greys-v3 ya se está usando como sistema de observación y priorización técnica, no solo como spike de arquitectura.

## Proposito y Proyeccion del Proyecto

### Proposito actual

El propósito real de Greys-v3 es probar un modelo de asistente local con cuatro propiedades:

1. **seguridad por defecto**;
2. **capacidad de evolucionar sin auto-instalarse**;
3. **memoria operacional auditable**;
4. **proactividad regulada por evidencia y fatiga**.

### Proyeccion implícita

La trayectoria del repo sugiere esta evolución:

1. texto local estable;
2. ingestión documental controlada;
3. skill runtime experimental con allowlist;
4. sueño + morning brief + curación;
5. skill proposals basadas en evidencia real;
6. expansión progresiva de capacidades bajo gates humanos y técnicos.

La pieza más madura conceptualmente hoy no es la voz ni la UI. Es la combinación:

- ledgers;
- IAFA;
- DreamMode;
- pipeline de cuarentena/promoción;
- manejo local de fallos del LLM.

## Hallazgos Relevantes Para Extraer a un Repo Nuevo

### Lo más valioso para preservar

1. **Modelo de TaskEnvelope y auditoría**
   - Es la base de trazabilidad y seguridad semántica.

2. **Ledgers como frontera de memoria**
   - El proyecto ya piensa en operaciones observables y en aprendizaje por evidencia.

3. **Skill lifecycle**
   - Candidato -> sandbox -> revisión -> dependency review -> promoción.

4. **DreamMode + MorningBrief**
   - Es la parte más distintiva del proyecto porque convierte fallos operativos en backlog técnico.

5. **IAFA como gate local**
   - Le da identidad al sistema y evita que el LLM sea autoridad final.

### Lo que no conviene arrastrar tal cual

1. `src/main.py` como punto central monolítico.
2. El acoplamiento entre CLI, Qt, runtime y comandos internos.
3. El estado runtime mezclado en el mismo repo de código.
4. La documentación que ya quedó parcialmente desfasada.
5. Las skills experimentales con contratos aún inconsistentes.

## Riesgos y Deuda Tecnica Detectada

### 1. Contrato roto entre promoción y runtime de skills

El loader espera archivos `skill_<intent>.py` con entrypoint `async`, pero la promoción física copia archivos sin ese prefijo y la skill experimental real `consultor_tiempo_local.py` expone un `def`, no `async def`.

Impacto:

- una skill puede aparecer como "promovida" pero no ser ejecutable por el loader;
- el pipeline candidato -> experimental -> runtime no está cerrado de extremo a extremo.

### 2. Lookup inconsistente del estado de revisión

El runtime consulta el estado de revisión usando `<accion>.py`, mientras la cuarentena trabaja con `candidate_<nombre>.py`.

Impacto:

- el perfil de riesgo puede evaluarse con estado equivocado;
- se pierde trazabilidad entre skill activa y su expediente de revisión.

### 3. CLI no desacoplada de Qt

Incluso comandos no visuales (`--morning-brief`, `--dream`, `--compact-ledgers`) inicializan `QApplication`.

Impacto:

- fallo en entornos headless si no se fuerza `QT_QPA_PLATFORM=offscreen`;
- difícil automatizar operación batch o CI.

### 4. Spark en modo práctico más agresivo que la narrativa

En `run_app`, si Spark está habilitado, el `idle_probe` es siempre `True`.

Impacto:

- el comportamiento real no coincide con la narrativa de inactividad detectada;
- riesgo de proactividad fuera de una señal real de idle.

### 5. Documentación de estado ya quedó atrás del código

`docs/CURRENT_STATE.md` habla de 181 tests y del PDF como "siguiente paso", pero hoy el repo ya tiene 249 tests recolectados y `pypdf` está pinneado.

Impacto:

- cualquier repo nuevo que copie docs sin depuración heredará contexto engañoso.

### 6. Suposiciones locales no empaquetadas

- no hay `README`;
- no hay `pyproject.toml`;
- no hay pipeline de CI visible;
- la ejecución depende de rutas relativas y variables de entorno.

Impacto:

- alto costo de transferencia a otro entorno;
- onboarding débil para terceros o para un futuro repo público.

## Estado de Pruebas

Observado durante la auditoría:

- `env PYTHONPATH=. .venv/bin/pytest --collect-only -q` recolecta `249` tests.
- `pytest -q` directo falla en este entorno porque una prueba importa módulos desde `assets...` y depende de `PYTHONPATH=.`.
- `src/main.py --morning-brief` falla en headless sin `QT_QPA_PLATFORM=offscreen`.

Lectura práctica:

- la base tiene mucha cobertura;
- la operatividad sigue siendo de entorno local, no empaquetada.

## Que Separaria En Un Nuevo Repositorio

### Opcion A: extraer el núcleo cognitivo

Crear un repo tipo `greys-core` con:

- `TaskEnvelope`
- `IAFAEngine`
- `IafaAuditor`
- `IngestionRouter`
- `LLMPlanner`
- `ActionDispatcher`
- `SemanticTensionLedger`
- `IngestionFailureLedger`

Usarlo si el objetivo es preservar el "motor" del sistema.

### Opcion B: extraer el sistema de evolución

Crear un repo tipo `greys-evolution` con:

- `GenesisSandbox`
- `GenesisAnalysis`
- `SkillCandidateReview`
- `SkillPromotionGate`
- `SkillExperimentalPromoter`
- `DependencyReviewLedger`
- `DreamMode`
- `MorningBrief`
- `EvolutionOptionQueue`
- `EvolutionOptionCurator`

Usarlo si el objetivo es profundizar la tesis de auto-mejora controlada.

### Opcion C: extraer un vertical de ingestión documental

Crear un repo tipo `greys-doc-ingestion` con:

- `DocumentProcessor`
- `IngestionRouter`
- candidato/skill PDF ya estabilizado
- límites de tamaño/truncado
- dependency review simplificado

Usarlo si el nuevo repo quiere convertirse en una pieza utilitaria, más fácil de operar y demostrar.

## Recomendacion

Si el nuevo repositorio debe ser legible, defendible y operable pronto, no intentaría mover Greys-v3 completo como primera extracción.

La frontera más razonable hoy es:

1. **core + ledgers**, o
2. **evolution pipeline + dream/morning**.

Eso conserva la identidad del proyecto sin arrastrar toda la superficie experimental de UI, voz y runtime acoplado.

## Que No Deberia Ir a un Repo Nuevo

- `assets/memory/*`
- `assets/quarantine/*`
- `logs/*`
- `backups/*`
- `.venv/`
- cualquier secreto/flag local

Ese material sirve como evidencia arqueológica y operativa, pero no como base de un repo limpio.

## Conclusión

Greys-v3 ya tiene una tesis fuerte:

> un asistente local con memoria operativa, gates de seguridad, evolución por evidencia y mejora controlada por humano.

Lo más importante para el repo nuevo no es copiar archivos. Es preservar esa tesis y elegir una frontera técnica coherente.

Si se arrastra todo, se hereda también el acoplamiento. Si se extrae un núcleo claro, el proyecto gana legibilidad, mantenibilidad y una narrativa mucho más fuerte.
