# Modo Sueño Cognitivo (Dream Mode)

Greys-v3 incluye un modo de reflexión diferida diseñado para analizar la experiencia operativa acumulada sin interferir con el host ni realizar cambios físicos.

## Propósito

El "Dream Mode" permite que Greys procese sus registros (ledgers) de forma profunda durante periodos de inactividad, identificando patrones que no son visibles en el flujo reactivo inmediato.

### Qué hace el Modo Sueño
- **Analiza Fallos**: Revisa el `IngestionFailureLedger` para encontrar capacidades que se necesitan con urgencia.
- **Evalúa la Tensión**: Identifica qué tipos de tareas generan más fatiga cognitiva mediante el `SemanticTensionLedger`.
- **Reflexiona con LLM**: Envía resúmenes estructurados al modelo de lenguaje para obtener recomendaciones técnicas.
- **Genera Dataset**: Persiste sus hallazgos en `assets/memory/dream_journal.jsonl`.

### Qué NO hace el Modo Sueño
- **No instala habilidades**: El motor `GenesisEngine` permanece inactivo.
- **No modifica el código**: No se realizan cambios en `src/` ni en `stable`.
- **No usa red**: El sistema mantiene su política de aislamiento local.
- **No entrena pesos**: No es un entrenamiento de redes neuronales, sino un aprendizaje operativo estructurado.

## Configuración y Seguridad

El modo sueño está protegido por múltiples capas de seguridad:

| Variable | Propósito | Default |
| :--- | :--- | :--- |
| `GREYS_DREAM_MODE_ENABLED` | Habilitación global del modo. | `0` |
| `GREYS_DREAM_MAX_CYCLES` | Límite máximo de reflexiones por sesión. | `5` |
| `GREYS_DREAM_SLEEP_SECONDS` | Tiempo de espera entre ciclos. | `60` |
| `GREYS_DREAM_STOP_ON_STRESS` | Detención automática si el host está bajo carga. | `1` |
| `GREYS_DREAM_NUM_PREDICT` | Límite de tokens para la reflexión LLM nocturna. | `512` |
| `GREYS_DREAM_MAX_LLM_FAILURES` | Timeouts LLM permitidos antes de desactivar LLM por el resto de la sesión. | `2` |
| `GREYS_DREAM_LOCAL_ONLY_ON_LLM_FAILURE` | Degradación automática a heurísticas locales tras fallo LLM. | `1` |
| `GREYS_DREAM_PREFLIGHT_OLLAMA` | Activa preflight liviano de Ollama antes del ciclo 1. | `0` |
| `GREYS_DREAM_PREFLIGHT_TIMEOUT` | Timeout del preflight liviano de Ollama. | `20` |

## Fallback local-only

Si Ollama no responde, Dream Mode registra `dream_llm_timeout` en el journal, añade tensión semántica moderada y marca la pregunta en `DreamQuestionLedger` como `local_only_after_timeout` o `defer_due_to_llm_timeout`. Si se alcanza `GREYS_DREAM_MAX_LLM_FAILURES`, el LLM queda desactivado por el resto de la sesión.

En local-only, el sistema no consulta el LLM. Resume `IngestionFailureLedger` y `SemanticTensionLedger`, detecta `top_missing_capabilities` y `top_tension_sources`, genera opciones en `EvolutionOptionQueue` mediante heurísticas locales y evita duplicados. Si no hay evidencia nueva, registra `no_new_evidence` y cierra la sesión sin dormir otro ciclo largo.

Comando nocturno recomendado:

```bash
GREYS_DREAM_MODE_ENABLED=1 \
GREYS_DREAM_MAX_CYCLES=5 \
GREYS_DREAM_SLEEP_SECONDS=300 \
GREYS_DREAM_MAX_REPETITIONS_PER_SIGNATURE=2 \
GREYS_DREAM_ENABLE_DEPTH_LADDER=1 \
GREYS_DREAM_LLM_ENABLED=1 \
GREYS_DREAM_NUM_PREDICT=128 \
GREYS_DREAM_MAX_LLM_FAILURES=2 \
GREYS_DREAM_LOCAL_ONLY_ON_LLM_FAILURE=1 \
GREYS_DREAM_PREFLIGHT_OLLAMA=1 \
GREYS_DREAM_PREFLIGHT_TIMEOUT=20 \
GREYS_DREAM_MAX_OPTIONS_PER_CYCLE=3 \
GREYS_DREAM_STOP_ON_STRESS=1 \
GREYS_PLANNER_FAST_MODE=1 \
GREYS_OLLAMA_NUM_PREDICT=128 \
GREYS_OLLAMA_FORMAT_JSON=1 \
GREYS_OLLAMA_TIMEOUT=90 \
GREYS_OLLAMA_KEEP_ALIVE=5m \
PYTHONPATH=src .venv/bin/python src/main.py --dream
```

## Uso

Para iniciar una sesión de sueño:
```bash
GREYS_DREAM_MODE_ENABLED=1 python src/main.py --dream
```

## Control de Continuidad y Foco (v3.2)

A partir de la versión 3.2, el Modo Sueño mejora su capacidad de ejecución larga mediante la gestión de ciclos sin evidencia.

### Configuración de Continuidad
- `GREYS_DREAM_CONTINUE_ON_SUPPRESS=1`: Si un ciclo se suprime por redundancia, el sistema rota el foco y continúa la sesión.
- `GREYS_DREAM_CONTINUE_ON_NO_NEW_EVIDENCE=1`: Si no hay evidencia nueva, rota el foco y ejecuta mantenimiento idle en lugar de cerrar la sesión.
- `GREYS_DREAM_SUPPRESS_SLEEP_SECONDS=5`: Tiempo de espera reducido tras una supresión.
- `GREYS_DREAM_NO_EVIDENCE_SLEEP_SECONDS=60`: Tiempo de espera tras un ciclo sin evidencia.

### Mantenimiento Idle
Cuando se habilita la continuidad sin evidencia, Greys realiza tareas analíticas ligeras:
- Validación de consistencia del cache de ledgers.
- Análisis proactivo de fallos `unknown_failure` desglosados.
- Registro de estado de salud modular.

### Carga de Foco Inicial (v3.1)
El sistema busca automáticamente el archivo de foco más reciente en `assets/memory/dream_focus/`.
- **Precedencia**: `GREYS_DREAM_FOCUS_ID` (Variable de entorno) > Archivo JSON más reciente > Fallback `auto`.
- **Validación**: Cada archivo es validado por `DreamFocusValidator` antes de ser cargado.

### Rotación de Foco
Si se detecta rumiación o falta de evidencia en un tema, el sistema alterna automáticamente entre:
- `quorum_readiness`: Evaluación de madurez de candidatos.
- `unknown_failure_classification`: Desglose de errores no clasificados.
- `evolution_queue_hygiene`: Limpieza y consolidación de la cola.
- `dream_deduplication`: Análisis de firmas redundantes.
- `fast_path_stability`: Verificación de ruteo rápido.
- `classifier_unknown_safe_health`: Monitoreo de incertidumbre segura.
- `ledger_cache_efficiency`: Optimización de memoria local.

## Trazabilidad

Los resultados se guardan en un diario cognitivo estructurado. El `MorningBrief` (v3.1+) ahora separa la **Última Sesión** de las **Estadísticas Históricas** y desglosa los fallos de la etapa `process_envelope` (v3.3) para una triada de errores de alta resolución.
