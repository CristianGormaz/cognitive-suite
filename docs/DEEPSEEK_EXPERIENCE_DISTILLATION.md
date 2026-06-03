# DeepSeek Experience Distillation

Este documento describe la capa de destilación de experiencia de Greys-v3, diseñada para internalizar el conocimiento técnico generado por DeepSeek-r1:8b y convertirlo en capacidades locales y autónomas.

## Filosofía de Aprendizaje

Greys-v3 no depende de los modelos de lenguaje (LLM) para su operación básica. En su lugar, utiliza a DeepSeek como un **Consultor Maestro** asíncrono. El proceso de destilación permite:

1.  **Reducir Latencia**: Convertir decisiones complejas del LLM en heurísticas locales instantáneas.
2.  **Aumentar Autonomía**: Operar en modo `local-only` con un núcleo de razonamiento enriquecido por la experiencia previa.
3.  **Seguridad Determinística**: Validar patrones de código inseguro basándose en análisis históricos del LLM.

## Proceso de Destilación

El módulo `DeepseekExperienceDistiller` analiza los ledgers del sistema para extraer patrones:

-   **Dream Journal**: Extrae observaciones sobre fallos de capacidad (ej. falta de dependencias matemáticas).
-   **Semantic Principles**: Convierte principios abstractos (ej. `cuarentena_como_aprendizaje`) en reglas operativas.
-   **LLM Health**: Detecta inestabilidades en el canal externo para proponer el bypass local proactivo.

## Minimal Neural Layer (v0)

La "Capa Neural Mínima" actúa como una memoria de corto y mediano plazo para estos patrones destilados (Reflejos).

-   **Symbolic Pattern Match**: En la v0, utiliza firmas semánticas y coincidencias de contexto.
-   **Reflejos Operativos**: Si una firma coincide (ej. intento de resolver una integral sin dependencias), la capa sugiere una acción inmediata (ej. bloqueo con explicación) sin consultar al LLM.

## Estados de Patrones

Cada patrón destilado pasa por un ciclo de vida:

1.  **Identificado**: Detectado en ledgers.
2.  **Requiere Revisión**: Presentado en el Morning Brief para validación humana.
3.  **Heurística Local**: Una vez validado, puede integrarse en el `LocalIntentRouter` o políticas de seguridad.

## Próximos Pasos

-   **Micro-Clasificador Local**: Entrenar un modelo de pesos ligero (p.ej. Scikit-learn o una red mínima) cuando el dataset de patrones sea suficiente.
-   **Reflejos Activos**: Permitir que `LocalIntentRouter` consulte la `MinimalNeuralLayer` en tiempo real para todas las peticiones.
