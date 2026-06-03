# Ciclo de Minería de Experiencia (Experience Mining Loop)

Greys-v3 implementa un ciclo de vida evolutivo basado en el aprendizaje operativo continuo. Este proceso transforma los fallos y tensiones diarias en propuestas técnicas estructuradas para el operador humano.

## El Flujo Evolutivo

1.  **Operación Diaria**: El sistema registra éxitos, fallos y tensiones en sus ledgers (`IngestionFailureLedger`, `SemanticTensionLedger`).
2.  **Night Experience Mining (Dream Mode)**: Durante la noche (o en periodos de inactividad programada), Greys analiza estos registros.
    -   Utiliza el LLM (DeepSeek) para identificar patrones y recomendar micro-sprints.
    -   Genera opciones evolutivas basadas en evidencia técnica real.
3.  **Priorización**: Las opciones se guardan en la `EvolutionOptionQueue`, donde se priorizan según el beneficio esperado, el riesgo técnico y el daño acumulado en esa área.
4.  **Morning Brief**: Al iniciar la jornada, el sistema presenta un resumen ejecutivo de lo aprendido y una lista de opciones para evolucionar.
5.  **Decisión Humana**: El operador revisa y aprueba las opciones. La aprobación **NO** ejecuta cambios inmediatos, sino que autoriza al sistema a proponer esos micro-sprints durante el ciclo proactivo (Spark).

## Control de Repetición y Profundidad Cognitiva

Para evitar la redundancia y optimizar el uso del LLM, el Modo Sueño implementa dos mecanismos avanzados:

### 1. Dream Recurrence Guard
Utiliza el `DreamQuestionLedger` para memorizar qué preguntas se han realizado. Cada pregunta genera una **Firma Semántica** (hash del tema, tipo de pregunta y contexto).
-   **Límite de Repetición**: Si una firma se repite más de N veces (`GREYS_DREAM_MAX_REPETITIONS_PER_SIGNATURE`), el sistema suspende la consulta al LLM.
-   **Continuidad y Rotación (v3.1)**: Si se habilita `GREYS_DREAM_CONTINUE_ON_SUPPRESS`, el sistema no cierra la sesión ante una supresión; en su lugar, rota el foco hacia un nuevo tema (ej. quorum, hygiene, fast-path) para maximizar el aprendizaje nocturno sin rumiación.
-   **Entendimiento**: Se calcula un `understood_score` heurístico. Si es alto, el tema se marca como "comprendido" y se procede a generar opciones evolutivas o escalar la profundidad.

### 2. Cognitive Depth Ladder (Escalera de Profundidad)
El sistema avanza a través de 6 niveles de análisis progresivo:
-   **Nivel 0 (Observación)**: ¿Qué falló exactamente?
-   **Nivel 1 (Agrupación)**: ¿Qué patrones de fallo se repiten?
-   **Nivel 2 (Causa)**: ¿Cuál es la causa raíz probable?
-   **Nivel 3 (Estrategia)**: ¿Qué micro-sprint conviene para mitigar esto?
-   **Nivel 4 (Validación)**: ¿Qué pruebas confirmarían que la solución es segura?
-   **Nivel 5 (Decisión)**: ¿Cuáles son las opciones finales para el humano?

Greys solo sube de nivel si la respuesta anterior fue "entendida" y hay suficiente evidencia acumulada.

## Ventajas del Modelo

-   **Reducción de Alucinaciones**: Las propuestas se basan en datos reales de los ledgers, no en especulación del modelo.
-   **Gobernanza Estricta**: Ninguna "idea" nocturna se convierte en código sin supervisión humana explícita.
-   **Dataset Operativo**: El `Dream Journal` y la `Option Queue` crean un dataset histórico de la evolución del sistema en su propio host.
-   **Eficiencia de Recursos**: Evita preguntar lo mismo una y otra vez, ahorrando CPU y latencia.

## Seguridad y Aislamiento

Toda la minería de experiencia se realiza en un entorno de **solo lectura** para los ledgers operativos y **solo escritura** para el journal y la cola de opciones. Nunca se invoca a `GenesisEngine` ni se modifica el sistema de archivos de `src/` durante el sueño.
