# Modelo de Fallos de Ingestión (Greys-v3)

Este documento describe la capa de persistencia especializada en registrar fallos de procesamiento y capacidades faltantes.

## Concepto

Mientras que el **Ledger Semántico** registra el "costo" (tensión, fatiga) de las interacciones, el **Ledger de Fallos de Ingestión** registra el "por qué" operativo del fallo. Esto permite que el sistema identifique patrones de necesidad técnica.

## El Ledger de Fallos

Ubicado en `assets/memory/ingestion_failure_ledger.jsonl`, este archivo registra eventos de forma estructurada sin comprometer la privacidad del usuario.

### Datos Registrados
- **Metadatos del Sobre**: Task ID, tipo de fuente (text/file), MIME type, tamaño del payload (bytes), SHA256.
- **Clasificación del Fallo**: `unsupported_action`, `unsupported_file_type`, `llm_timeout`, `llm_parse_error`, etc.
- **Capacidad Faltante**: Una firma combinada (ej: `intent:action`) que identifica qué habilidad no pudo ejecutarse.
- **Categoría Sugerida**: Sugerencia heurística de qué tipo de habilidad resolvería el fallo (ej: `lector_pdf`, `responder_texto`).

### Datos NO Registrados (Privacidad)
- **NO** se guarda el texto completo del usuario.
- **NO** se guardan contenidos de archivos.
- **NO** se guardan prompts enviados al LLM.
- **NO** se guardan rutas absolutas locales sensibles.

## Evolución Proactiva (SparkEngine)

SparkEngine consulta este ledger periódicamente. Si detecta que una **firma de capacidad faltante** se repite con frecuencia (ej: 3 o más veces), genera una **Propuesta de Evolución**.

1.  **Detección**: Spark identifica el patrón repetitivo.
2.  **Validación de Tensión**: Consulta el Ledger Semántico para asegurar que la propuesta no está suprimida por fatiga cognitiva previa.
3.  **Propuesta**: Emite una `evolutionary_doubt` al usuario sugiriendo el análisis de una nueva habilidad.
4.  **Decisión Humana**: El usuario decide si autoriza el análisis en el Sandbox de GenesisEngine.

## Relación con GenesisEngine

Este modelo actúa como el "sensor de necesidades" para GenesisEngine. No ejecuta código automáticamente, pero proporciona la evidencia necesaria para que el sistema proponga mejoras estructurales basadas en el uso real del host.
