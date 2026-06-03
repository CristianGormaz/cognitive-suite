# Local Ledger Cache

La `LocalLedgerCache` (Caché de Ledgers Locales) es un mecanismo de almacenamiento en RAM diseñado para reducir la latencia de entrada/salida (I/O) en Greys-v3 mediante el acceso directo a los registros persistentes más consultados.

## Motivación (I/O Refactoring)
Antes de su implementación, los módulos analíticos (como `MorningBrief` o `ClassifierShadowSoakEvaluator`) debían abrir, leer, parsear y cerrar múltiples archivos `.jsonl` en disco durante cada evaluación. Con el aumento en la complejidad arquitectónica, este enfoque de lectura sincrónica amenazaba con convertirse en un cuello de botella grave.

## Patrón Arquitectónico: Read-Through
La caché utiliza el patrón **Read-Through**. 
La fuente única y verdadera de información sigue siendo el archivo físico `.jsonl` en disco. Todas las escrituras (*appends*) se realizan directamente al sistema de archivos para garantizar la inmutabilidad y seguridad auditada de los ledgers. 

El módulo de caché actúa únicamente como un intermediario de **aceleración de lectura**:
1.  Si el archivo solicitado ya fue cargado, la caché verifica de inmediato si el tamaño (`file_size`) o la fecha de modificación (`mtime`) del sistema de archivos han cambiado.
2.  Si son idénticos, se devuelve el objeto serializado directamente desde RAM (Cache Hit).
3.  Si han cambiado, o si es la primera lectura, la caché abre el archivo, parsea cada línea de JSON de forma segura, actualiza su registro interno y luego devuelve los datos (Cache Miss).

## Medidas de Privacidad y Seguridad
1.  **Strict Path Enforcement**: El `LocalLedgerCache` solo acepta leer rutas que se encuentren estrictamente bajo el directorio `memory_dir` (generalmente `assets/memory`). Intenta acceder a rutas foráneas o credenciales será bloqueado y reportado.
2.  **Volatilidad Total**: Las instancias en caché viven únicamente durante el tiempo de ejecución del proceso. No existen "archivos temporales" de caché ni serializaciones persistidas.
3.  **Tolerancia a la Corrupción**: Si una línea específica del registro `.jsonl` está corrompida y produce un `JSONDecodeError`, la caché aísla el error, omite esa línea y carga el resto del historial intacto.

## Visibilidad
Las métricas del rendimiento de caché (Archivos monitoreados, Hits, Misses e Invalidaciones) se informan directamente en la sección **Memoria Local / Ledger Cache** del `MorningBrief`.

## HITO: Aceleración de Lecturas (I/O Sprint v1) (2026-06-02)
-   `LocalLedgerCache` operativo e integrado en el `MorningBrief`.
-   Escrituras aseguradas de manera directa y persistente (append-only).
-   Trazabilidad completa con *Privacy-By-Design*.
