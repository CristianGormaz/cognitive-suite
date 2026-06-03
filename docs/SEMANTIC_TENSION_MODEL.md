# Modelo de Tensión Semántica (Greys-v3)

Este documento describe la implementación operativa del modelo de tolerancia y estrés aplicado a la cognición de Greys-v3.

## Conceptos Operativos

Basado en el modelo matemático de tolerancia y estrés, Greys-v3 utiliza las siguientes variables para regular su proactividad y respuesta:

1.  **Tensión Semántica ($\tau_{sem}$)**: Es el esfuerzo o fricción generada por un evento (error, timeout, rechazo, duda evolutiva). Aumenta cuando el sistema encuentra obstáculos o cuando el host está bajo estrés físico.
2.  **Capacidad del Sistema ($A_{sem}$)**: Es la habilidad actual del sistema para procesar una intención. Disminuye con el estrés del host y aumenta con la disponibilidad de respuestas seguras y validación IAFA positiva.
3.  **Esfuerzo Relativo / Ratio de Estrés ($\sigma_{sem}$)**: $\sigma = \tau / A$. Si la tensión supera la capacidad, el sistema entra en un estado de fatiga semántica.
4.  **Daño Acumulado ($d_t$)**: Representa la fatiga persistente causada por la repetición de eventos de alta tensión. Si una propuesta es rechazada repetidamente, acumula daño hasta que es suprimida (enfriamiento cognitivo).
5.  **Costo de Insistencia ($J_t$)**: La métrica final que decide si SparkEngine debe emitir una nueva duda evolutiva o esperar a que el sistema se recupere.

## El Ledger Semántico

Los eventos se registran en `assets/memory/semantic_tension_ledger.jsonl`. Este archivo es:
- **Append-only**: Solo se añaden nuevos registros.
- **Local**: No se comparte ni se sube a repositorios.
- **Estructurado**: Formato JSONL para fácil análisis y recuperación.

### Eventos Registrados
- `evolutionary_doubt`: Cuando SparkEngine emite una propuesta proactiva.
- `iafa_rejected`: Cuando una propuesta es bloqueada por las salvaguardas de IAFA.
- `timeout`: Fallos de comunicación con el LLM (Ollama).
- `error`: Fallos genéricos de ejecución o parseo.
- `outcome_update`: Registro de la reacción del usuario (aceptar, abortar, ignorar).

## Mecanismo de Supresión (Fatiga Cognitiva)

SparkEngine consulta el ledger antes de cada pulso. Si una firma de propuesta (ej. `document_analysis:reflection`) ha acumulado un daño superior al umbral configurado, la propuesta se **suprime silenciosamente**.

Esto evita:
- Spam de dudas evolutivas ignoradas.
- Insistencia en tareas que el host no puede procesar (ej. timeouts repetidos).
- Frustración del usuario por repetición de errores.

## Recuperación
El daño acumulado disminuye cuando el sistema logra ejecutar acciones con éxito o cuando el usuario acepta una propuesta, permitiendo que el sistema "aprenda" qué caminos son seguros y valorados.
