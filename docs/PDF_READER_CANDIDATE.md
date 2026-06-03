# Candidato: Lector PDF Experimental

Este documento describe la capacidad experimental de lectura de archivos PDF en Greys-v3, actualmente en fase de candidato en cuarentena.

## Clasificación de Riesgo

El lector PDF está clasificado como **Medium Risk** debido a las siguientes razones:
- **Manejo de Datos del Usuario**: Procesa archivos externos suministrados por el operador.
- **Acceso a Sistema de Archivos**: Requiere lectura de archivos locales.
- **Dependencias Externas**: Requiere la librería `pypdf` para la extracción de texto.

## Estado Actual (Cuarentena)

- **Candidato**: `candidate_pdf_reader_basic.py`
- **Ubicación**: `assets/quarantine/genesis_candidates/`
- **Activación**: **DESACTIVADO**. El código ha sido validado por el Sandbox pero no está instalado en `src/skills/`.

## Ciclo de Ingestión y Fallos

1.  **Detección**: Al intentar procesar un archivo `.pdf`, el `IngestionRouter` detecta el formato pero bloquea el procesamiento directo.
2.  **Registro de Fallo**: Se crea un evento en `IngestionFailureLedger` con la firma `file:pdf_reader`.
3.  **Tensión**: Se registra el costo cognitivo en el `SemanticTensionLedger`.
4.  **Propuesta Proactiva**: Tras 3 fallos detectados, `SparkEngine` propone al usuario realizar el análisis en sandbox para esta capacidad.

## Validación en Sandbox

El candidato ha sido sometido a un análisis AST estricto:
- **Habilitación de Bloques**: Se han habilitado los nodos `Try` y `Raise` en el `GenesisSandbox` para permitir una detección robusta de dependencias.
- **Allowlist**: `pypdf` y `__future__` han sido añadidos a la lista de importaciones permitidas para este candidato.

## Estado de Evolución (Post Dependency Review)
* **Dependencia:** `pypdf==6.12.2` instalada y fijada.
* **Candidato:** Revisado y aprobado para promoción futura.
* **Seguridad:** Validado como **Medium Risk**.

## HITO: PDF Reader promovido a experimental físico (2026-06-01)
* **Estado:** El código ha sido copiado de cuarentena a `src/skills/experimental/pdf_reader_basic.py`.
* **Seguridad:** Mantiene límites de 5MB y 30,000 caracteres.
* **Aislamiento:** El archivo original en cuarentena se conserva como evidencia.
* **Runtime:** **INACTIVO**. No se carga en el `DynamicSkillLoader` todavía.

## HITO: Privacy Hardening del PDF Reader (2026-06-01)
* **Privacidad:** Implementado `PrivacySanitizer`.
* **Rutas:** Las rutas absolutas ya no se exponen en logs ni respuestas; se usa `file_ref` (hash + nombre).
* **Metadata:** `author` y `title` están desactivados por defecto (redacted). Controlable vía `GREYS_PDF_INCLUDE_METADATA=1`.
* **Errores:** Los mensajes de error son sanitizados para ocultar la estructura del sistema de archivos local (`/home/[REDACTED]`).
* **Estado Inmune:** El ISS ha bajado, permitiendo la reclasificación a **Nivel 2 (Validación)**.
## HITO: PDF Reader runtime controlado por allowlist (2026-06-01)
* **Activación:** Requiere `GREYS_EXPERIMENTAL_SKILLS_ENABLED=1` y la entrada `pdf_reader_basic` en la allowlist.
* **Seguridad:** IAFA Medium Risk. Privacy strict por defecto (rutas ocultas).
* **Limitaciones:** Aún no integrado con `IngestionRouter` de forma automática; invocación manual para validación.

## HITO: PDF Ingestion routed through controlled runtime (2026-06-02)
*   **Integración**: El `IngestionRouter` ahora detecta automáticamente archivos `.pdf` y los enruta al flujo cognitivo.
*   **Seguridad**: Validado límite de 5MB en el punto de entrada (Router).
*   **Gobernanza**: Si el modo experimental está desactivado o la skill `pdf_reader_basic` no está en allowlist, el sistema devuelve un estado informativo (`pdf_reader_available_but_disabled`) sin ejecutar código.
*   **Privacidad**: Sanitización de rutas y metadatos activa por defecto.
*   **Acción**: La acción autorizada es `pdf_reader_basic`.

## Siguiente Paso
1. Prueba con PDF fixture más realista y de mayor tamaño (sin exceder 5MB).
2. SemanticDreamMiner con LLM opcional controlado para analizar fallos de parseo.
3. Hardening de heurísticas locales para detección de intenciones PDF sin LLM.
