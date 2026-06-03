## [2026-06-03] HITO: UNKNOWN FAILURE BACKFILL & LIVE CLASSIFICATION PROBE

Este hito introduce la capacidad de reconciliación histórica mediante "etiquetado epigenético", permitiendo al sistema interpretar la experiencia pasada con la inteligencia de la nueva taxonomía sin alterar la integridad de los registros originales.

### Avances Clave
- **Derivative Reconciliation**: Implementado `UnknownFailureReconciler` para inferir tipos de fallo específicos a partir de la deuda acumulada de `unknown_failure`.
- **Epigenetic Labeling**: Los hallazgos se guardan en un ledger derivado (`unknown_failure_reconciliation_ledger.jsonl`), actuando como una capa de significado sobre la memoria inmutable.
- **Historical vs Active Distinction**: El `MorningBrief` ahora separa claramente los fallos desconocidos históricos de cualquier posible brecha en la clasificación actual (Post-Taxonomía).
- **Live Classification Probe**: Confirmado mediante pruebas controladas que la etapa `process_envelope` ya no genera fallos genéricos ante errores de contrato o ruteo.
- **Privacy Hardening**: Asegurado que el proceso de reconciliación no extraiga ni persista contenido sensible del usuario, operando exclusivamente sobre firmas de error y metadatos de etapa.

### Nuevos Componentes
- `src/core/unknown_failure_reconciler.py`: Motor de inferencia para deuda histórica.
- `docs/UNKNOWN_FAILURE_RECONCILIATION.md`: Manifiesto sobre la gestión interpretativa de la memoria.
- `tests/test_unknown_failure_reconciler.py`: Validación de reglas de inferencia.
- `tests/test_unknown_reconciliation_privacy.py`: Verificación de anonimización en el ledger derivado.

### Validación de Calidad
- **Resultado de Tests**: 511 passed (100% éxito).
- **Integridad**: Verificado que los ledgers originales permanecen inalterados tras múltiples ejecuciones del Morning Brief.

## [2026-06-03] HITO: PROCESS ENVELOPE FAILURE CLASSIFICATION & CONTRACT HARDENING

Este hito erradica la opacidad de los fallos desconocidos en el orquestador principal, implementando una taxonomía de alta resolución y validación estricta de contratos estructurales.

### Avances Clave
- **Process Envelope Taxonomy**: Implementadas 9 nuevas categorías de fallo específicas para la etapa de sobre (Contrato, Task ID, Router Local, Planner, Dispatcher, Política, etc.).
- **Contract Hardening**: Creado `ProcessEnvelopeContract` para validar la integridad de los datos en cada sub-etapa del ciclo de vida de la tarea.
- **Structured Triage**: El `MainOrchestrator` ahora envuelve errores de sub-módulos en clasificaciones específicas antes de registrarlos, permitiendo una triada técnica inmediata.
- **Privacy Enforcement**: Asegurado que el ledger de fallos y los reportes de Morning Brief operen exclusivamente sobre metadatos estructurales, eliminando cualquier rastro de contenido de usuario en los logs técnicos.
- **LLM Configuration Awareness**: Añadida clasificación específica para `llm_disabled_error`, distinguiendo fallos técnicos de decisiones de configuración.

### Nuevos Componentes
- `src/core/process_envelope_contract.py`: Motor de validación de integridad estructural.
- `docs/PROCESS_ENVELOPE_FAILURE_CLASSIFICATION.md`: Documentación técnica de la nueva taxonomía.
- `tests/test_process_envelope_contract.py`: Validación de integridad de sobres y planes.
- `tests/test_process_envelope_failure_classifier.py`: Test de mapeo de excepciones a taxonomía.

### Validación de Calidad
- **Resultado de Tests**: 504 passed (100% éxito).
- **Reducción de Incertidumbre**: Verificado en pruebas manuales que errores de configuración y capacidad se desglosan correctamente en el Morning Brief.

## [2026-06-03] HITO: DREAM IDLE CONTINUITY & PROCESS ENVELOPE TRIAGE SPRINT

Este hito consolida la resiliencia del Modo Sueño ante la falta de evidencia y mejora el diagnóstico de fallos críticos en la etapa de sobre cognitivo.

### Avances Clave
- **Dream Idle Continuity**: Implementado `GREYS_DREAM_CONTINUE_ON_NO_NEW_EVIDENCE` para evitar el cierre prematuro de sesiones nocturnas cuando el LLM no tiene nuevos datos que procesar.
- **Idle Maintenance Mode**: Greys ahora realiza tareas analíticas ligeras (validación de cache, análisis de fallos `unknown`) durante los ciclos de espera.
- **Process Envelope Triage**: Refinado el `FailureClassifier` para desglosar fallos en la etapa `process_envelope` (Contratos, Rutas, Excepciones no manejadas), eliminando el ruido de "fallo desconocido".
- **Visual Deduplication (Reflexes)**: El `MorningBrief` ahora agrupa visualmente múltiples ocurrencias de reflejos generalizados (`status`, `identity`, `help`), reduciendo la redundancia en los reportes.
- **Parse Error Resilience**: Asegurada la clasificación de errores de parseo LLM como eventos específicos, evitando que inflen artificialmente las métricas de fallos desconocidos.

### Nuevos Componentes
- `tests/test_dream_continue_on_no_new_evidence.py`: Validación de continuidad sin evidencia.
- `tests/test_dream_idle_maintenance.py`: Verificación de tareas de mantenimiento.
- `tests/test_process_envelope_failure_classification.py`: Test de triada de fallos de etapa.
- `tests/test_morning_brief_dedup_generalized_reflexes.py`: Test de agrupación visual de candidatos.

### Validación de Calidad
- **Resultado de Tests**: 493 passed (100% éxito).
- **Consistencia**: Verificada la rotación de foco y ejecución de mantenimiento idle en sesiones simuladas sin LLM.

## [2026-06-03] HITO: DREAM FOCUS LOADER & MORNINGBRIEF RECONCILIATION SPRINT

Este hito perfecciona la orquestación del Modo Sueño y la claridad del Morning Brief, separando la experiencia inmediata de las métricas históricas y eliminando el ruido visual en los reportes técnicos.

### Avances Clave
- **Dream Focus Loader**: Implementada la carga automática del foco más reciente desde `assets/memory/dream_focus/`. Greys ahora "despierta" con un propósito técnico validado.
- **Session Reconciliation**: El `MorningBrief` ahora distingue entre la **Última Sesión** nocturna y el acumulado histórico, evitando la confusión de métricas de sesiones pasadas.
- **Visual Deduplication**: Implementada la agrupación visual de candidatos redundantes (`unknown_safe`, `dependency_debt_math`) en el Morning Brief, reduciendo el spam sin sacrificar la integridad de los ledgers.
- **Envelope Diagnosis**: Refinado el desglose de `unknown_failure`, identificando `process_envelope` como hotspot principal y sugiriendo sprints de clasificación específicos.
- **Focus ID Support**: Añadido soporte para `GREYS_DREAM_FOCUS_ID`, permitiendo forzar focos específicos para validaciones técnicas dirigidas.

### Nuevos Componentes
- `tests/test_dream_focus_loader.py`: Validación de precedencia y carga de archivos de foco.
- `tests/test_morning_brief_current_vs_historical_session.py`: Test de separación de sesiones en el reporte.
- `tests/test_morning_brief_dedup_unknown_safe.py`: Verificación de agrupación de señales de incertidumbre.
- `tests/test_morning_brief_dedup_reflex_promotions.py`: Verificación de agrupación de deuda de dependencias.

### Validación de Calidad
- **Resultado de Tests**: 487 passed (100% éxito).
- **Observabilidad**: Verificado en logs que el foco cargado coincide con el esperado (`dream_continuity_validation_v1`).

## [2026-06-03] HITO: DREAM CONTINUITY & EVOLUTION QUEUE HYGIENE SPRINT

Este hito mejora la robustez del Modo Sueño y la integridad de la memoria evolutiva, permitiendo sesiones nocturnas ininterrumpidas y eliminando la rumiación redundante.

### Avances Clave
- **Dream Continuity**: Implementado `GREYS_DREAM_CONTINUE_ON_SUPPRESS` para permitir que el Modo Sueño rote el foco cognitivo en lugar de terminar la sesión ante redundancia.
- **Rotación de Foco**: El sistema ahora alterna automáticamente entre 7 focos técnicos (quorum, unknown_failure, hygiene, etc.) para asegurar una exploración diversa.
- **Higiene de Memoria**: Corregido el bug de duplicación masiva en `EvolutionOptionQueue` mediante deduplicación por ID en el motor de carga.
- **Curaduría Inteligente**: El `EvolutionOptionCurator` ahora detecta y evita crear propuestas curadas redundantes para familias que ya tienen temas pendientes de revisión.
- **Desglose de unknown_failure**: El `MorningBrief` ahora desglosa los fallos desconocidos por etapa operativa (ej. `process_envelope`), mejorando la visibilidad de la deuda técnica.
- **Validación de Foco**: Implementado `DreamFocusValidator` para garantizar que las configuraciones de foco externas sean seguras y estén bien formadas.

### Nuevos Componentes
- `src/core/dream_focus_validator.py`: Validador de esquemas JSON para configuración de foco.
- `tests/test_dream_continue_on_suppress.py`: Validación de continuidad de sesión.
- `tests/test_dream_focus_rotation.py`: Verificación del algoritmo de rotación.
- `tests/test_evolution_queue_deduplication.py`: Test de integridad de la memoria operativa.

### Validación de Calidad
- **Resultado de Tests**: 480 passed (100% éxito).
- **Control de Rumia**: Verificada la reducción de duplicados en el Morning Brief, mostrando familias únicas y señales fusionadas.

## [2026-06-01] HITO: NIGHT EXPERIENCE MINING (V2)

Este hito transforma el Modo Sueño de una reflexión aislada a un sistema de aprendizaje operativo progresivo y sin redundancia.

### Avances Clave
- **Dream Recurrence Guard**: Implementación de `DreamQuestionLedger` y firmas semánticas. Greys ahora detecta si está preguntando lo mismo y evita redundancias.
- **Cognitive Depth Ladder**: El sistema ahora avanza por niveles de profundidad (0-5), desde la observación básica hasta la formulación de estrategias técnicas complejas.
- **Bandeja de Evolución Matinal**: Integración con `EvolutionOptionQueue`. Las reflexiones nocturnas generan opciones de micro-sprint priorizadas por beneficio, riesgo y daño acumulado.
- **Understood Score**: Heurística para determinar si el sistema ha comprendido una respuesta del LLM antes de escalar la profundidad del análisis.
- **Morning Brief Mejorado**: El resumen ejecutivo ahora informa sobre supresiones por redundancia y niveles de profundidad alcanzados.

### Nuevos Componentes
- `src/cognition/dream_question_ledger.py`: Memoria de interacciones cognitivas.
- `src/cognition/evolution_option_queue.py`: Gestión de propuestas evolutivas pendientes.
- `src/cognition/morning_brief.py`: Interfaz de salida resumida para el operador.

### Validación de Calidad
- **Resultado de Tests**: 181 passed (100% éxito).
- **Control de Repetición**: Validado que el sistema bloquea llamadas LLM redundantes cuando el límite de repetición se alcanza.

## [2026-06-01] HITO: IAFA EXPERIMENTAL RISK PROFILE

Este hito refuerza la seguridad inmunológica de Greys-v3 mediante la evaluación de riesgo en vivo de habilidades experimentales antes de su ejecución.

### Avances Clave
- **Perfil de Riesgo Dinámico**: Implementación de `ExperimentalRiskProfile` para analizar capacidades técnicas (red, archivos, dependencias) y estado de gobernanza de cada skill.
- **Ajuste Proactivo de IAFA**: Integración de perfiles de riesgo con el despachador, permitiendo ajustar dinámicamente las variables **R** (Riesgo), **I** (Inconsistencia) y **N** (Ruido) basándose en el peligro detectado.
- **Seguridad Gradual**: Clasificación de habilidades por niveles (Low, Medium, High, Critical), garantizando el bloqueo absoluto de componentes no autorizados o fallidos.
- **Trazabilidad de Riesgo**: Registro de evaluaciones de perfil en el Ledger de Tensión Semántica bajo el evento `experimental_iafa_evaluated`.
- **Casos Validados**: `consultor_tiempo_local` clasificado como **Low Risk**; bases sentadas para clasificar futuros lectores de documentos como **Medium Risk**.

### Nuevos Componentes
- `src/core/experimental_risk_profile.py`: Motor de clasificación de riesgo para skills.
- `docs/EXPERIMENTAL_IAFA_PROFILE.md`: Especificación de la matriz de riesgo y penalizaciones IAFA.

### Validación de Calidad
- **Resultado de Tests**: 165 passed (100% éxito).
- **Integridad**: Confirmación de que el núcleo estable permanece inmune a los riesgos experimentales mediante ruteo dinámico supervisado.

## [2026-06-01] HITO: RUNTIME EXPERIMENTAL CONTROLADO

Este hito consolida el ciclo de vida evolutivo de Greys-v3, permitiendo la re-implementación segura de capacidades legacy y la regulación proactiva mediante fatiga semántica.

### Avances Clave
- **Fatiga Semántica y Ledgers**: Implementación de `SemanticTensionLedger` y `IngestionFailureLedger`. Greys ahora "recuerda" fallos, timeouts y rechazos humanos para autorregular su proactividad.
- **Rescate Legacy**: Re-implementación nativa del `ConsultorTiempo` desde blueprints de v2 sin contaminación de código.
- **Promoción Segura**: Implementación de `SkillPromotionGate` (Dry-Run) y `SkillExperimentalPromoter`. El código pasa de cuarentena a experimental bajo supervisión humana rigurosa.
- **Activación Runtime**: Habilitación por allowlist de habilidades experimentales (`GREYS_EXPERIMENTAL_SKILLS_ENABLED`).
- **Observabilidad**: SparkEngine ahora reporta sus latidos y omisiones por estrés físico o fatiga cognitiva.
- **Versionado**: Inicialización de repositorio Git local y preservación de línea base estable.

### Nuevos Componentes
- `src/core/semantic_tension_ledger.py`: Persistencia de fatiga cognitiva ($\tau_{sem}$, $A_{sem}$, $d_t$).
- `src/core/ingestion_failure_ledger.py`: Registro estructurado de capacidades faltantes.
- `src/cognition/skill_promotion_gate.py`: Validación técnica para salida de cuarentena.
- `src/cognition/skill_experimental_promoter.py`: Movimiento físico seguro de archivos con backups.
- `src/skills/experimental/consultor_tiempo_local.py`: Primera habilidad promovida.

### Validación de Calidad
- **Resultado de Tests**: 161 passed (100% éxito).
- **Control de Estrés**: `SystemStressGuard` validado bloqueando inferencias ante carga basal alta.

### Riesgos Residuales
- **Latencia del Host**: El equipo local presenta picos de CPU que causan timeouts en Ollama; se requiere monitoreo constante de `SystemStressGuard`.
- **Dependencias Externas**: Capacidades como `math:solve_integral` están bloqueadas por falta de librerías (`sympy`).
- **Activación Manual**: Las habilidades experimentales requieren configuración manual de variables de entorno.

Este hito marca la transición de Greys-v3 de un sistema puramente reactivo a uno con capacidades de autorreflexión proactiva controlada.

### Componentes Integrados
- **SparkEngine**: Motor de reflexión interna que observa el estado de inactividad y genera dudas evolutivas basadas en señales de auditoría.
- **CognitiveOrchestrator (UI Bridge)**: Capa de mediación que conecta las dudas de SparkEngine con la interfaz de usuario de forma asíncrona.
- **EvolutionDialog**: Interfaz visual para la resolución de dudas evolutivas con aprobación humana obligatoria.

### Archivos Relevantes
- `src/cognition/spark_engine.py`: Lógica del pulso proactivo.
- `src/core/cognitive_loop.py`: Orquestación de la UI y el ciclo de fallback.
- `src/ui/evolution_dialog.py`: Componente visual de PySide6.
- `src/main.py`: Punto de entrada con soporte para flags de Spark.
- `tests/test_evolutionary_doubt_ui.py`: Pruebas de integración de la interfaz.

### Banderas de Activación
- `GREYS_SPARK_ENABLED=1`: Activa el pulso de SparkEngine.
- `GREYS_EVOLUTION_UI_ENABLED=1`: Habilita la apertura automática del diálogo ante dudas evolutivas.
- `GREYS_SPARK_INTERVAL=N`: Segundos entre pulsos (default: 300).

### Validación de Calidad
- **Resultado de Tests**: 97 passed (Suite completa).
- **Compilación**: 100% verificada en `src/` y `tests/`.

### Garantías de Seguridad (Mandatos)
1. **No Autoprogramación Proactiva**: `SparkEngine` NO ejecuta `GenesisEngine`. Solo propone.
2. **Aprobación Humana**: `EvolutionDialog` requiere un clic explícito del usuario para proceder con cualquier acción.
3. **Aislamiento de Errores**: Si la UI falla o es cerrada, Greys continúa su operación normal sin crashear.
4. **Respeto a la Inactividad**: El pulso proactivo solo se dispara si el sistema detecta inactividad (60s por defecto).

### Riesgos y Deuda Técnica Pendiente
- **Latencia del Auditor**: La lectura secuencial del log de auditoría puede degradar el rendimiento si el archivo crece excesivamente.
- **Validación del Planner**: El motor de reflexión depende de que el Planner entregue propuestas coherentes.
- **Persistencia de Decisiones**: Las dudas rechazadas no se guardan; SparkEngine podría volver a proponer la misma duda en el futuro.
- **Control de Versiones**: El proyecto no cuenta con inicialización de Git (este hito se preserva vía backup manual).
## [2026-06-02] HITO: INTENT REBALANCING V1 (UNKNOWN-SAFE HARDENING)

Este hito refuerza la integridad del clasificador local mediante la implementación de umbrales de ambigüedad y la expansión sistemática del dataset de ruido.

### Avances Clave
- **Margin-Based Scoring**: Implementado un mecanismo que invalida predicciones si la diferencia entre la mejor intención y la segunda opción es menor al 10%, favoreciendo la clasificación como `unknown_safe`.
- **Unknown-Safe Hardening**: Expandido el dataset sintético con ejemplos de pensamientos intrusivos, ruido y frases no accionables, mejorando el reconocimiento de los límites del sistema.
- **Healthy Thresholds**: Ajustada la confianza mínima a un nivel más cauto (40%) y calibrado el ruteo local para evitar "forzar" intenciones ante entradas ambiguas.
- **Confusion Matrix v1.1**: Las métricas de autoevaluación ahora incluyen la "Salud de unknown_safe" y alertas de sobreconfianza en el Morning Brief.
- **Deduplication Metrics**: El motor de soak test ahora detecta y reporta tasas de redundancia, facilitando la identificación de bucles de rumiación en la generalización.

### Nuevos Componentes
- `src/core/local_micro_classifier.py`: Mejoras de lógica de margen y hardening.
- `tests/fixtures/local_classifier/synthetic_intents.json`: Dataset rebalanceado.

### Validación de Calidad
- **Resultado de Tests**: 424+ passed.
- **Estabilidad**: Verificada una salud de `unknown_safe` cercana al 40% en pruebas de estrés local, indicando un equilibrio robusto entre autonomía y precaución.

## [2026-06-02] HITO: CLASSIFIER SHADOW SOAK EVALUATION

Este hito inicia la fase de observación prolongada para el clasificador local, permitiendo medir su estabilidad y seguridad ante el ruido real antes de cualquier promoción activa.

### Avances Clave
- **Shadow Soak Engine**: Implementado `ClassifierShadowSoakEvaluator` para monitorear métricas de salud a largo plazo, como la tasa de `unknown_safe` y la redundancia de firmas.
- **Stability Metrics**: El sistema ahora detecta si el clasificador está "sobreconfiado" (caída de `unknown_safe`) o si presenta desbalances significativos en el ruteo.
- **Soak Section in Brief**: El Morning Brief incluye ahora un resumen ejecutivo del soak test, con recomendaciones automáticas basadas en la consistencia de los datos (ej. "estabilidad aceptable", "fortalecer unknown_safe").
- **Deduplication Strategy**: Implementada lógica de agrupación visual para el reporte de candidatos, reduciendo el ruido en el resumen matutino sin alterar los ledgers de auditoría.

### Nuevos Componentes
- `src/core/classifier_shadow_soak.py`: Evaluador de estabilidad y calidad.
- `docs/CLASSIFIER_SHADOW_SOAK.md`: Manual de gobernanza del periodo de prueba.

### Validación de Calidad
- **Resultado de Tests**: 419+ passed.
- **Gobernanza**: Se mantiene bloqueada la promoción automática de cualquier candidato generado por el clasificador hasta completar el ciclo de soak test.

## [2026-06-02] HITO: QUORUM PROMOTION READINESS SPRINT (DRY-RUN)

Siguiendo el principio bioinspirado de "Quorum Sensing", este hito implementa la capa de madurez encargada de validar la masa crítica de evidencia antes de cualquier promoción de reflejos.

### Avances Clave
- **Quorum Readiness Engine**: Implementado `QuorumPromotionReadiness` para calcular el `Quorum Readiness Score` (QRS), integrando métricas de volumen de señales, unicidad, estabilidad temporal y riesgo.
- **Anti-False-Quorum Logic**: El sistema ahora detecta y penaliza activamente la rumiación y el falso consenso, asegurando que la evidencia provenga de fuentes diversas y no solo de repeticiones del mismo origen (ej. rumiación en Dream Mode).
- **Maturity States**: Definida una escala de madurez (`insufficient_evidence`, `observe_more`, `false_quorum_suspected`, `ready_for_human_review`) para guiar la supervisión del operador.
- **Dry-Run Governance**: Se garantiza por diseño que la promoción automática está bloqueada; el motor sólo informa y recomienda, manteniendo al humano como la autoridad final de activación.

### Nuevos Componentes
- `src/core/quorum_promotion_readiness.py`: Motor de evaluación de masa crítica.
- `docs/QUORUM_PROMOTION_READINESS.md`: Manual de gobernanza de madurez.

### Validación de Calidad
- **Resultado de Tests**: 469+ passed.
- **Protección**: Verificado el bloqueo de candidatos con riesgo elevado o falta de mecanismo de rollback.

## [2026-06-02] HITO: I/O REFACTORING SPRINT V1 (LOCAL LEDGER CACHE)

En respuesta a la auditoría arquitectónica que identificó los bloqueos de I/O por la proliferación de archivos JSONL, este hito introduce una capa de memoria intermedia para optimizar las lecturas frecuentes sin comprometer la persistencia y la seguridad.

### Avances Clave
- **LocalLedgerCache**: Implementada una caché en memoria (RAM) siguiendo el patrón *Read-Through*. La caché carga las lecturas recurrentes y solo invalida cuando detecta un cambio en el tamaño (`file_size`) o la modificación (`mtime`) del archivo en disco.
- **Privacy-By-Design**: La caché prohíbe estrictamente la lectura de archivos fuera del directorio de memoria (`assets/memory`), evitando accesos no autorizados a credenciales o código fuente.
- **Integración con Morning Brief**: El reporte matutino (uno de los procesos de mayor lectura) ahora utiliza la caché para extraer estados de inmunidad y journals, reportando sus propias métricas de eficiencia (*hits, misses e invalidaciones*).
- **Consistencia Asegurada**: Las escrituras permanecen *append-only* y se envían de forma directa y síncrona al disco, garantizando que un fallo crítico del sistema no corrompa el historial de auditoría.

### Nuevos Componentes
- `src/core/local_ledger_cache.py`: Intermediario de lectura para acelerar el acceso JSONL.
- `docs/LOCAL_LEDGER_CACHE.md`: Documento de arquitectura sobre la estrategia de aceleración de I/O.

### Validación de Calidad
- **Resultado de Tests**: 463+ passed.
- **Tolerancia a la Corrupción**: Se verificó la capacidad del caché para omitir elegantemente una línea JSONL malformada sin abortar la carga del historial.

## [2026-06-02] HITO: FAST-PATH BYPASS SPRINT (RUTA MIELINIZADA)

Resolviendo la deuda técnica de sobre-preprocesamiento ("Dendritic Overfiltering"), este hito implementa un circuito rápido determinístico para reflejos certificados, reduciendo drásticamente la latencia cognitiva.

### Avances Clave
- **FastPathReflexGate**: Implementada una compuerta de certificación que exige riesgo 0, aprobación humana, soporte de rollback y ausencia de efectos secundarios (red, archivos, LLM) para permitir la ruta mielinizada.
- **Short-Circuit Orquestador**: Modificado el `MainOrchestrator` para que, si un reflejo es aprobado por la compuerta rápida, se eluda la evaluación de la Política de Delegación Simbiótica, la evaluación en sombra del Micro-Clasificador y el cálculo de contexto multidimensional.
- **Observabilidad Consolidada**: Creado un ledger de impactos (`fast_path_reflex_ledger.jsonl`) y sumarios directos en el Morning Brief, proyectando los ahorros en milisegundos de tiempo de cálculo.

### Nuevos Componentes
- `src/core/fast_path_reflex_gate.py`: Validador determinístico de reflejos maduros.
- `docs/FAST_PATH_REFLEX_GATE.md`: Documento fundamental de la ruta mielinizada.

### Validación de Calidad
- **Resultado de Tests**: 455+ passed.
- **Seguridad**: Se comprobó que el clasificador en sombra ("unknown_safe" y candidatos generalizados) y las habilidades experimentales nunca califiquen para la ruta rápida, garantizando que el "freno de seguridad" siga activo donde más se necesita.

## [2026-06-02] HITO: SYMBIOTIC DELEGATION & EDGE STABILIZATION SPRINT

Basado en las reflexiones del Dream Mode con DeepSeek-R1:8B, este hito implementa la política matemática para evaluar cuándo delegar tareas al LLM frente a procesarlas localmente.

### Avances Clave
- **Symbiotic Delegation Policy**: Implementado `SymbioticDelegationPolicy` para calcular scores de ruteo basados en beneficios locales, latencia del LLM, y complejidad de la tarea.
- **Formulación Matemática (ERS, SDS, QPS)**: Definidos algoritmos claros para el `Edge Routing Score`, `Symbiotic Delegation Score` y `Quorum Promotion Score`, basando la delegación en la rentabilidad de ejecución.
- **Dry-Run Mode**: La política opera actualmente como un observador analítico, registrando la recomendación del ruteo óptimo en `symbiotic_delegation_ledger.jsonl` sin forzar la ejecución todavía, permitiendo medir impactos.
- **Integración con Morning Brief**: El reporte matinal ahora agrega la distribución de las decisiones hipotéticas de la política para su evaluación diaria.

### Nuevos Componentes
- `src/core/symbiotic_delegation_policy.py`: Motor determinístico de ruteo local/LLM.
- `docs/SYMBIOTIC_DELEGATION_POLICY.md`: Documento fundamental de las reglas de delegación.

### Validación de Calidad
- **Resultado de Tests**: 440+ passed.
- **Seguridad**: Se garantizó que la política no invalide los vetos del `ExternalChannelGate` y mantenga el aislamiento de ejecución requerido.

## [2026-06-02] HITO: BIO-INSPIRED COGNITIVE ARCHITECTURE SPRINT

Este hito formaliza la analogía biológica como principio de diseño para Greys-v3, estableciendo un catálogo de patrones que guían el desarrollo de la autonomía sin caer en copias literales.

### Avances Clave
- **Bio-Inspired Pattern Atlas**: Implementado un módulo de consulta (`BioInspiredPatternAtlas`) que mapea la arquitectura actual a patrones como `Dendritic Preprocessing`, `Quorum Sensing`, y `Basket Cell Inhibition`.
- **Anti-Pattern Identification**: Formalizados los riesgos de corromper la arquitectura biológica, definiendo anti-patrones como `immune_overblocking` o `fast_path_overconfidence`.
- **Morning Brief Integration**: El resumen matutino ahora reporta el patrón dominante y las alertas orgánicas críticas.
- **Architectural Guidance**: Se generó el documento fundacional `BIO_INSPIRED_COGNITIVE_ARCHITECTURE.md`, estableciendo el "hardware evolutivo" de Greys.

### Nuevos Componentes
- `src/core/bio_inspired_pattern_atlas.py`: Catálogo consultivo de patrones orgánicos.
- `docs/BIO_INSPIRED_COGNITIVE_ARCHITECTURE.md`: Documento fundacional.

### Validación de Calidad
- **Resultado de Tests**: 433+ passed.
- **Seguridad**: El Atlas opera estrictamente como herramienta conceptual; no ejecuta acciones ni altera el flujo del sistema.

## [2026-06-02] HITO: LOCAL CLASSIFIER MATURITY SPRINT

Este hito culmina la fase de maduración del clasificador local, transformándolo en un motor de generalización robusto, consciente de sus propios límites y preparado para el aprendizaje supervisado.

### Avances Clave
- **Advanced Maturity Metrics**: Implementada la medición de `Balanced Accuracy` y `Precision/Recall` para asegurar que todas las intenciones se generalicen con igual calidad.
- **Margin-Based Hardening**: Refinado el mecanismo de margen (0.12) y ambigüedad, forzando la clasificación como `unknown_safe` ante cualquier duda estadística significativa.
- **Resilient Memory Injection**: Refactorizado el orquestador para inyectar `memory_dir` en todos los componentes, permitiendo un aislamiento perfecto entre entornos de test y producción.
- **Soak Maturity Integration**: El reporte matutino ahora consolida métricas de estabilidad a largo plazo, detectando proactivamente sobreconfianza y desbalances en el dataset.
- **Matured Shadow Bridge**: Implementado un gate de madurez en el puente de candidatos, exigiendo un margen relativo del 20% para elevar una predicción a candidato shadow.
- **v1 Architecture Design**: Finalizado el documento de diseño para la v1 del clasificador, definiendo la persistencia de pesos y el bucle de aprendizaje basado en feedback humano.

### Nuevos Componentes
- `src/core/classifier_shadow_soak.py`: Motor de métricas de madurez.
- `docs/LOCAL_MICRO_CLASSIFIER_V1_DESIGN.md`: Roadmap para el aprendizaje persistente.

### Validación de Calidad
- **Resultado de Tests**: 430+ passed.
- **Equilibrio**: Verificada una salud de `unknown_safe` superior al 30% bajo variaciones naturales, garantizando la integridad del ruteo local.

## [2026-06-02] HITO: CLASSIFIER-TO-SHADOW REFLEX BRIDGE (GENERALIZED AWARENESS)

Este hito establece el puente entre la inferencia estadística del clasificador local y la memoria de patrones del sistema, permitiendo que Greys-v3 proponga autónomamente nuevos reflejos basados en la observación de lenguaje natural.

### Avances Clave
- **Generalized Awareness Bridge**: Implementado `ClassifierShadowBridge` para transformar predicciones de alta confianza (>= 80%) en candidatos de reflejo en sombra.
- **Resilient Candidate Capture**: El ruteo de candidatos ahora ocurre dentro de `_record_classifier_shadow`, garantizando que la experiencia se capture incluso si el pipeline real falla (ej. por bloqueos `FORCE_LOCAL_ONLY`).
- **Whitelisted Intents**: Definida una política estricta que solo permite generar candidatos para intenciones seguras (saludo, ayuda, estado, identidad).
- **Observe-Only Uncertainty**: Las predicciones de tipo `unknown_safe` se transforman automáticamente en señales de no-acción, permitiendo rastrear la incertidumbre sin riesgo de ejecución.
- **Deep Visibility**: El Morning Brief ahora lista los candidatos generados por el puente, permitiendo al operador supervisar cómo Greys está generalizando su entendimiento local.

### Nuevos Componentes
- `src/core/classifier_shadow_bridge.py`: Motor de mapeo y evaluación de candidatos.
- `assets/memory/classifier_shadow_candidates.jsonl`: Registro de propuestas de generalización.

### Validación de Calidad
- **Resultado de Tests**: 415+ passed.
- **Seguridad**: Todos los candidatos generados por el puente están bloqueados como `shadow_only=True`, requiriendo pasar por el ciclo completo de calibración y aprobación humana antes de activarse.

## [2026-06-02] HITO: LOCAL MICRO-CLASSIFIER CALIBRATION V1

Este hito eleva la precisión de la generalización local mediante la expansión del dataset sintético y la implementación de normalización lingüística avanzada sin dependencias.

### Avances Clave
- **Expanded Synthetic Dataset**: Integrado un conjunto más rico de variaciones para intenciones de sistema (saludo, ayuda, estado, identidad) en un fixture versionable.
- **Linguistic Normalization**: Implementada normalización manual de tildes (á->a, ñ->n) y limpieza profunda de puntuación, mejorando el reconocimiento de lenguaje natural informal.
- **Confusion Matrix Analysis**: Incorporada capacidad de autoevaluación contra el dataset sintético, reportando precisión por intención y pares de confusión en el Morning Brief.
- **Refined Thresholds**: Ajustados los umbrales de confianza (70% para predicción fuerte) para reducir falsos positivos y favorecer la clasificación segura como `unknown_safe`.
- **System-Wide Alignment**: Refactorizado el `MainOrchestrator` para inyectar `memory_dir` de forma consistente, permitiendo una trazabilidad y aislamiento de tests superior.

### Nuevos Componentes
- `tests/fixtures/local_classifier/synthetic_intents.json`: Dataset de validación.
- `src/core/local_micro_classifier.py`: Mejoras de normalización y métricas.

### Validación de Calidad
- **Resultado de Tests**: 408+ passed.
- **Precisión**: Verificado un 92% de precisión teórica sobre el set sintético calibrado.

## [2026-06-02] HITO: LOCAL MICRO-CLASSIFIER V0 (INTENT GENERALIZATION)

Este hito introduce la capacidad de generalizar el reconocimiento de intenciones locales más allá de las firmas exactas, utilizando un clasificador liviano basado en tokens que opera íntegramente en la librería estándar.

### Avances Clave
- **Micro-Classifier Engine**: Implementado un clasificador basado en "Bolsa de Palabras" (BoW) con pesos sintéticos para intenciones de sistema (saludo, ayuda, estado, identidad).
- **Resilient Shadow Mode**: Integrado el clasificador en modo sombra dentro del `MainOrchestrator`, capturando predicciones incluso si el pipeline real falla técnicamente.
- **Intent Mapping**: Refinado el bucle de acuerdo para mapear etiquetas granulares (ej. `greeting`) a familias de intención del sistema (ej. `chat`), mejorando la precisión de las métricas.
- **Privacy-Safe Data Collection**: Nuevo ledger `local_classifier_shadow_ledger.jsonl` que almacena firmas semánticas y resultados de acuerdo sin persistir contenido de usuario.
- **Generalization Proof**: El clasificador demostró en pruebas manuales que reconoce variaciones como "buenas" o "¿qué eres?" que las heurísticas de firma exacta ignoraban.

### Nuevos Componentes
- `src/core/local_micro_classifier.py`: Motor de inferencia estadística local.
- `assets/memory/local_classifier_shadow_ledger.jsonl`: Almacén de métricas de generalización.

### Validación de Calidad
- **Resultado de Tests**: 404+ passed.
- **Impacto**: Cero afectación al ruteo real; el clasificador no tiene permisos de ejecución (`should_execute=False`) en esta versión.

## [2026-06-02] HITO: ACTIVE REFLEX PILOT (CONTROLLED AUTONOMY)

Este hito valida el ciclo de vida completo de un reflejo local activo, desde su aprobación supervisada hasta su ejecución determinística y capacidad de reversión.

### Avances Clave
- **Pilot Selection**: Seleccionado `basic_greeting_reflex` (ID: `dist_b86936fd`) como el primer reflejo piloto oficial por su bajo riesgo y alta tasa de coincidencia (100%).
- **Active Execution**: Confirmado que, tras la aprobación manual, Greys resuelve el saludo localmente ignorando el motor LLM, incluso bajo `FORCE_LOCAL_ONLY=1`.
- **Rollback Validation**: Verificado el funcionamiento del comando `/reflex-disable`, devolviendo el sistema a su comportamiento base sin efectos secundarios.
- **Ledger Audit**: El `reflex_promotion_ledger.jsonl` registra ahora el historial completo del piloto, asegurando trazabilidad total de la autonomía ganada.

### Validación de Calidad
- **Resultado de Tests**: 394+ passed.
- **Integridad**: Validado que la activación de un reflejo no degrada la supervisión IAFA ni expone datos sensibles.

## [2026-06-02] HITO: SUPERVISED REFLEX PROMOTION GATE

Este hito introduce el mecanismo de gobernanza para activar reflejos locales de forma definitiva, permitiendo que Greys-v3 gane autonomía sobre tareas validadas y aprobadas por el humano.

### Avances Clave
- **Promotion Gate**: Implementado `ReflexPromotionGate` para validar que los reflejos candidatos cumplan con umbrales estrictos (Agreement >= 90%, Context Score >= 85%).
- **Supervised Activation**: El operador ahora puede aprobar reflejos manualmente mediante comandos CLI (`/reflex-approve`), activando el ruteo local determinístico para esos patrones.
- **Active Reflex Memory**: Nuevo ledger `reflex_promotion_ledger.jsonl` para rastrear aprobaciones, desactivaciones y rollbacks de reflejos.
- **Autonomous Local Execution**: El `LocalIntentRouter` ha sido habilitado para ejecutar reflejos aprobados en tiempo real, eliminando totalmente la latencia del LLM para casos conocidos.
- **Manual Calibration**: Probada la promoción del patrón `ping_reflex` (ID: `dist_ping`), confirmando que bypassa exitosamente el LLM tras la aprobación humana.

### Nuevos Componentes
- `src/core/reflex_promotion_gate.py`: Validador de criterios de promoción.
- `assets/memory/reflex_promotion_ledger.jsonl`: Historial de gobernanza de reflejos.
- Comandos CLI: `/reflex-candidates`, `/reflex-review`, `/reflex-approve`, `/reflex-disable`.

### Validación de Calidad
- **Resultado de Tests**: 389+ passed.
- **Seguridad Superior**: IAFA sigue evaluando toda acción propuesta por un reflejo activo antes de su despacho.

## [2026-06-02] HITO: MULTIDIMENSIONAL CONTEXT ARCHITECTURE

Este hito introduce el Marco de Contexto Arquitectónico, una capa de evaluación que asegura que las decisiones de autonomía se tomen considerando no solo la precisión técnica, sino la viabilidad del entorno y las restricciones del sistema.

### Avances Clave
- **Architectural Context Frame**: Implementado `MultidimensionalContextEngine` para evaluar decisiones bajo cinco dimensiones: Entorno, Flujos, Humano, Temporal y Reglas.
- **Context-Aware Promotion**: El `ReflexShadowEvaluator` ahora requiere un contexto estable (`low risk`) para recomendar la promoción de un reflejo de "sombra" a "activo".
- **Situational Decision Making**: Greys ahora detecta bloqueos contextuales (ej. host bajo estrés) y difiere evoluciones automáticas proactivamente.
- **Context Visibility**: El Morning Brief incluye un resumen del estado de cada dimensión y identifica la "Dimensión Crítica" que requiere atención.

### Nuevos Componentes
- `src/core/multidimensional_context.py`: Motor de evaluación de contexto.
- `docs/MULTIDIMENSIONAL_CONTEXT_ARCHITECTURE.md`: Documentación del principio del arquitecto.

### Validación de Calidad
- **Resultado de Tests**: 380+ passed.
- **Robustez**: Validado que el estrés del host o violaciones de política bloquean correctamente la promoción de candidatos, incluso con 100% de coincidencia técnica.

## [2026-06-02] HITO: LOCAL NARRATIVE LAYER (EXPRESSIVE AUTONOMY)

Este hito completa la Pieza B de la arquitectura local, permitiendo que Greys-v3 explique sus decisiones técnicas y señales de seguridad en lenguaje humano claro y no alarmista sin depender de modelos externos.

### Avances Clave
- **Local Narrative Engine**: Implementado `LocalNarrativeLayer` para traducir señales complejas (IAFA blocks, timeouts, estrés) en mensajes estructurados con resumen de usuario y justificación técnica.
- **Non-Alarmist Tone**: Definidas plantillas de respuesta que priorizan la calma y la proactividad (ej. traducir un timeout como "continuidad local" en lugar de "fallo crítico").
- **Integrated Response Flow**: El `ResponseManager` ahora delega las explicaciones de sistema a la capa narrativa, eliminando la duplicidad de cadenas fijas.
- **Enhanced Morning Brief**: La sección de señales intrusivas ahora utiliza narrativa enriquecida, mostrando claramente la acción tomada y el siguiente paso recomendado.
- **UI Composability**: Rediseñado el motor de renderizado para evitar duplicidad de prefijos y asegurar consistencia en la consola.

### Nuevos Componentes
- `src/core/local_narrative_layer.py`: Motor de plantillas y traducción.
- `docs/LOCAL_NARRATIVE_LAYER.md`: Manual de la capa narrativa.

### Validación de Calidad
- **Resultado de Tests**: 374+ passed.
- **Seguridad Narrativa**: Validado que no se exponen rutas absolutas ni prompts en las explicaciones generadas.

## [2026-06-02] HITO: INTRUSIVE SIGNAL PRINCIPLE (ALARM-TO-INSIGHT)

Este hito introduce una capa de razonamiento para manejar señales de alarma (fallos, código inseguro, estrés) no como basura o comandos, sino como eventos contenidos con alto valor de aprendizaje.

### Avances Clave
- **Intrusive Signal Policy**: Implementado `IntrusiveSignalPolicy` para clasificar señales intensas y traducirlas en insights operativos (ej. `llm_timeout` traducido como necesidad de fortalecer ruteo local).
- **Immune Training Samples**: El sistema ahora identifica el código inseguro como "muestras de entrenamiento" en lugar de simples fallos de ejecución.
- **Self-Regulation Principle**: El `SemanticDreamMiner` ahora detecta el principio `alarma_como_senal_no_como_orden`, reforzando la autorregulación local.
- **Alarm Translation**: El Morning Brief ahora incluye una sección de traducción de alertas, permitiendo al operador ver la justificación técnica detrás de cada bloqueo o cuarentena.

### Nuevos Componentes
- `src/core/intrusive_signal_policy.py`: Motor de clasificación y traducción de señales.
- `docs/INTRUSIVE_SIGNAL_PRINCIPLE.md`: Documentación del principio rector.

### Validación de Calidad
- **Resultado de Tests**: 365+ passed.
- **Seguridad**: Se mantiene el bloqueo de ejecución para toda señal clasificada como intrusiva hasta su validación humana.

## [2026-06-02] HITO: DUAL-PIECE LOCAL MIND ARCHITECTURE

Este hito formaliza la estructura cognitiva de Greys-v3 en dos capas complementarias: el Reflex Kernel (decisión y control) y la Narrative Layer (expresión y contexto), reforzando la autonomía local.

### Avances Clave
- **Architectural Formalization**: Definida la arquitectura de dos piezas en `docs/LOCAL_MIND_ARCHITECTURE.md`, separando la lógica no generativa de la capacidad expresiva.
- **Reflex Pattern Expansion**: Agregados patrones iniciales para intenciones comunes (saludo, ayuda, estado, identidad, PDF) en el ledger de destilación.
- **Improved Neural Layer (v0)**: Evolucionado `MinimalNeuralLayer` para soportar matching por categoría/acción y cálculo de confianza dinámica.
- **Refined Shadow Evaluation**: El `ReflexShadowEvaluator` ahora clasifica las sugerencias (`aligned`, `candidate_for_promotion`, `risky_divergence`), permitiendo una calibración más fina.
- **Calibration Boost**: La tasa de coincidencia en Modo Sombra aumentó del 25% al 62% tras la expansión de patrones básicos.

### Nuevos Componentes / Modificaciones
- `docs/LOCAL_MIND_ARCHITECTURE.md`: Manifiesto de la estructura dual.
- `src/core/minimal_neural_layer.py`: Mejoras en el motor de búsqueda de patrones.
- `src/core/reflex_shadow_evaluator.py`: Clasificación granular de sugerencias.

### Validación de Calidad
- **Resultado de Tests**: 359+ passed.
- **Seguridad**: Los reflejos siguen operando exclusivamente en modo sombra, sin afectar la ejecución real ni el cumplimiento IAFA.

## [2026-06-02] HITO: MINIMAL NEURAL LAYER SHADOW MODE

Este hito introduce la capacidad de observar y evaluar el núcleo de razonamiento local en paralelo al flujo real, permitiendo medir la confianza en los reflejos destilados antes de su activación.

### Avances Clave
- **Shadow Mode**: Activado mediante la bandera `GREYS_REFLEX_SHADOW_ENABLED=1`, permitiendo observación no intrusiva.
- **Reflex Evaluation**: Implementado `ReflexShadowEvaluator` para comparar sugerencias locales con las rutas reales tomadas por el sistema.
- **Agreement Metrics**: Cálculo automático de tasa de coincidencia y estimación de riesgo para cada reflejo observado.
- **Performance Summary**: Integración en el Morning Brief para mostrar estadísticas de desempeño de la Capa Neural Mínima.
- **Secure Persistence**: Nuevo ledger `reflex_shadow_ledger.jsonl` para recolectar datos de calibración sin exponer contenido de usuario.

### Nuevos Componentes
- `src/core/reflex_shadow_evaluator.py`: Motor de comparación y métricas.
- `assets/memory/reflex_shadow_ledger.jsonl`: Almacén de evaluaciones en sombra.

### Validación de Calidad
- **Resultado de Tests**: 350+ passed.
- **Impacto**: Cero afectación al flujo real de ejecución; las sugerencias en sombra no modifican el plan ni alteran el Dispatcher.

## [2026-06-02] HITO: DEEPSEEK EXPERIENCE DISTILLATION & MINIMAL NEURAL LAYER (V0)

Este hito establece el mecanismo para que Greys-v3 aprenda de DeepSeek de forma asíncrona, internalizando conocimientos técnicos en un núcleo de razonamiento local y determinístico.

### Avances Clave
- **Experience Distillation**: Implementado `DeepseekExperienceDistiller` para extraer patrones de decisión desde ledgers históricos, fallos de salud LLM y principios semánticos.
- **Minimal Neural Layer (v0)**: Creada una capa de razonamiento simbólico que funciona como memoria local de patrones ("Reflejos"), permitiendo decisiones instantáneas basadas en la experiencia acumulada.
- **Pattern Persistence**: Nuevo ledger `distilled_reasoning_ledger.jsonl` para almacenar patrones destilados sin incluir prompts pesados ni datos sensibles.
- **Morning Brief Integration**: El resumen matutino ahora presenta los nuevos patrones identificados para revisión humana, cerrando el bucle de aprendizaje supervisado.
- **Autonomous Reflexes**: Identificados reflejos iniciales como `avoid_llm_for_known_intents` y `quarantine_as_training_sample`.

### Nuevos Componentes
- `src/cognition/deepseek_experience_distiller.py`: Motor de destilación.
- `src/core/minimal_neural_layer.py`: Memoria local de patrones.
- `assets/memory/distilled_reasoning_ledger.jsonl`: Almacén persistente de experiencia.

### Validación de Calidad
- **Resultado de Tests**: 345+ passed.
- **Eficiencia**: Los patrones destilados eliminan la necesidad de consultas LLM recurrentes para situaciones ya diagnosticadas.
- **Seguridad**: Todas las propuestas de destilación requieren revisión humana antes de ser promovidas a heurísticas fijas.

## [2026-06-02] HITO: LOCAL INTENT ROUTER PARA REDUCIR DEPENDENCIA LLM

Este hito introduce una capa de decisión determinística que resuelve intenciones obvias y ruteos ya gobernados por políticas locales sin necesidad de consultar modelos externos.

### Avances Clave
- **Deterministic Routing**: Implementación de `LocalIntentRouter` para interceptar comandos básicos ("hola", "ayuda", "estado") y ruteos críticos de archivos.
- **LLM Bypass**: Al procesar archivos PDF autorizados, el sistema ahora rutea directamente a la skill experimental sin latencia de planificación LLM.
- **Stress-Aware Local Decisions**: Las decisiones locales ahora respetan el estado del host (Stress Guard), bloqueando tareas pesadas proactivamente.
- **Unified Pipeline Consistency**: Las decisiones locales se transforman en planes compatibles con el flujo IAFA/Dispatcher, manteniendo la integridad de la auditoría.
- **Resiliencia en modo Local-Only**: Validado que con `FORCE_LOCAL_ONLY=1`, Greys sigue siendo funcional para tareas gobernadas localmente.

### Nuevos Componentes
- `src/core/local_intent_router.py`: Motor de heurísticas y ruteo local.
- `src/core/response_manager.py`: Actualizado para soportar claves de mensaje determinísticas.
- `src/cognition/llm_planner.py`: Extendido `CognitiveExecutionPayload` para soportar metadatos locales.

### Validación de Calidad
- **Resultado de Tests**: 338+ passed.
- **Latencia**: Eliminación total del tiempo de inferencia para comandos de sistema e ingesta PDF autorizada.
- **Seguridad**: Se mantiene la supervisión IAFA sobre las habilidades dinámicas invocadas localmente.

## [2026-06-02] HITO: PDF INGESTION ROUTED THROUGH CONTROLLED RUNTIME

Este hito activa el flujo seguro de ingestión de archivos PDF en Greys-v3, permitiendo la detección y procesamiento controlado bajo autorización explícita.

### Avances Clave
- **Safe Routing**: `IngestionRouter` ahora detecta PDFs y valida límites de seguridad (5MB) antes de crear el sobre de tarea.
- **Controlled Runtime**: Implementación de estados `pdf_detected`, `pdf_reader_available_but_disabled` y `pdf_reader_not_allowlisted` para una comunicación clara con el usuario.
- **Dynamic Skill Integration**: `ActionDispatcher` y `MainOrchestrator` ahora permiten la ejecución de `pdf_reader_basic` como una habilidad experimental autorizada.
- **Privacy Enforcement**: Sanitización automática de rutas absolutas y redacción de metadatos sensibles (autor, título) por defecto.
- **External Gate Synergy**: Todas las llamadas derivadas del procesamiento PDF (si las hubiera en el futuro) están protegidas por el `ExternalChannelGate`.

### Nuevos Componentes / Modificaciones
- `src/cognition/ingestion_router.py`: Ruteo y validación de PDF.
- `src/main.py`: Bloqueo temprano y feedback de activación.
- `src/core/action_dispatcher.py`: Autorización de la acción `pdf_reader_basic`.

### Validación de Calidad
- **Resultado de Tests**: 325+ passed.
- **Privacidad**: Verificado que los logs y ledgers no contienen rutas absolutas ni contenido PDF extraído.
- **Seguridad**: Validado el bloqueo automático cuando `GREYS_EXPERIMENTAL_SKILLS_ENABLED=0`.

## [2026-06-02] HITO: UNIFIED EXTERNAL LLM CHANNEL GATING

Este hito centraliza el control de todas las llamadas a LLM externos bajo una única compuerta de seguridad, garantizando que ninguna petición ocurra sin validar el estado del sistema y la configuración de modo.

### Avances Clave
- **Unified Gate**: Creación de `ExternalChannelGate` para centralizar decisiones de Circuit Breaker, Stress Guard y flags de modo (`FORCE_LOCAL_ONLY`).
- **Isolation of Modes**: Dream Mode y tests ya no pueden disparar llamadas LLM accidentales si están configurados como local-only.
- **Standardized Errors**: Introducción de `LlmDisabledError` para diferenciar entre fallos técnicos y desactivación por diseño.

### Nuevos Componentes
- `src/core/external_channel_gate.py`: Controlador central de acceso LLM.
- `src/cognition/iafa_transceiver.py`: Integración con el Gate antes de cada request.

## [2026-06-02] HITO: CANONICAL STATE RECONCILIATION

Este hito resuelve las inconsistencias semánticas en los reportes del sistema, distinguiendo entre deuda histórica y actividad en tiempo real.

### Avances Clave
- **Canonical State Resolver**: Capa de abstracción que valida la evidencia física (instalación) y temporal (ledgers) antes de reportar el estado de un componente.
- **Temporal Failure Classification**: Los fallos ahora se etiquetan como `[ACTIVO]`, `[DEUDA RECIENTE]` o `[HISTÓRICO]`.
- **Dependency Reconcilitation**: pypdf ahora se reporta correctamente como `approved_installed` basándose en el último registro del ledger.

### Nuevos Componentes
- `src/core/canonical_state_resolver.py`: Motor de reconciliación de estado.
