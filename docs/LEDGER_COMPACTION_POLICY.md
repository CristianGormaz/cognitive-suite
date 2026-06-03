# Política de Compactación y Higiene de Ledgers (v1)

## Contexto
Greys-v3 utiliza archivos `.jsonl` (JSON Lines) en `assets/memory/` para persistir su memoria de largo plazo. Estos archivos crecen de forma incremental (append-only). Con el tiempo, el volumen de eventos puede ralentizar la lectura secuencial y aumentar el ruido cognitivo.

## Definiciones
* **Ledger Crudo:** El archivo original con todos los eventos en orden cronológico.
* **Resumen Compacto:** Un archivo JSON con estadísticas agregadas y metadatos críticos extraídos de un periodo archivado.
* **Archivo de Memoria (Archive):** El lugar donde se mueven los eventos crudos antiguos para su preservación fuera del flujo caliente.

## Política de Conservación
1. **Flujo Caliente (Recent):** Se mantendrán los últimos **200 eventos** (por defecto) de cada ledger en el archivo principal.
2. **Archivado (Archive):** Los eventos que excedan el límite de conservación se moverán a `assets/memory/archive/YYYYMMDD/`. Estos archivos son inmutables.
3. **Compactación (Compact):** Se generará un resumen agregado en `assets/memory/compact/` por cada ciclo de archivado.
4. **Privacidad:** Los resúmenes compactos **no deben contener**:
    * prompts completos;
    * contenido de archivos de usuario;
    * respuestas íntegras del LLM;
    * stacktraces detallados (solo tipo de error y resumen).
5. **Trazabilidad:** Se deben conservar los `event_id` y `task_id` (o sus hashes) para poder rastrear señales en el archivo si fuera necesario.

## Integración con MorningBrief
El `MorningBrief` debe ser capaz de:
* Leer los eventos recientes del ledger crudo.
* Incorporar las estadísticas de los resúmenes compactos para dar contexto histórico (ej. "En los últimos 30 días hubo X timeouts").
* No cargar gigabytes de datos históricos de forma síncrona.

## Higiene Técnica
* Las líneas corruptas en los archivos `.jsonl` deben ser detectadas y movidas a un log de errores de ledger, no descartadas silenciosamente.
* La compactación debe soportar un modo `dry-run` para previsualizar el ahorro de espacio.
* Se requiere confirmación explícita (`GREYS_LEDGER_COMPACTION_CONFIRM=1`) para realizar cambios físicos.

## Seguridad y Git
* La carpeta `assets/memory/` (incluyendo `archive/` y `compact/`) debe permanecer ignorada por Git.
* Ningún dato de usuario debe filtrarse a los metadatos compactos.
