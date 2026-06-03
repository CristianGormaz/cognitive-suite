# Ingestión de Archivos Reales Controlados

Este documento describe las pruebas realizadas para validar la capacidad de Greys-v3 de ingerir y procesar archivos de forma segura.

## Capacidades de Ingestión Actuales

1.  **Texto Plano (`.txt`, `.md`, `.json`, etc.)**: Soportado nativamente. El sistema extrae el contenido UTF-8 y lo procesa como una intención de usuario estándar.
2.  **Microsoft Word (`.docx`)**: Estructura implementada en `DocumentProcessor`, pero requiere la librería `python-docx` en el host para operar.
3.  **PDF (`.pdf`)**: Estructura detectada por el router pero bloqueada inicialmente.
    - **Candidato**: Se ha generado `candidate_pdf_reader_basic.py` en cuarentena tras detectar fallos repetidos en la ingesta de archivos PDF.
    - **Riesgo**: Clasificado como **Medium Risk** por el `ExperimentalRiskProfile` debido al manejo de archivos de usuario y requerimiento de dependencias externas.
    - **Dependencias**: Requiere la instalación de `pypdf` en el host local.
4.  **Tipos no soportados**: Cualquier extensión desconocida es bloqueada por el `IngestionRouter` lanzando un error controlado.

## Fixtures de Prueba

Se han creado archivos controlados en `tests/fixtures/ingestion/`:
- `sample.txt`: Texto simple para validar éxito.
- `sample.unsupported`: Extensión ficticia para validar registro de fallos.

## Registro de Fallos y Tensión

- **Metadatos**: El sistema registra el SHA256 y el tamaño del archivo, permitiendo identificar archivos repetidos sin guardar su contenido.
- **Detección de Necesidades**: Los fallos por tipo de archivo no soportado se agrupan en el `IngestionFailureLedger`.
- **Evolución**: SparkEngine puede proponer la creación de un `pdf_reader` o `docx_reader` tras detectar fallos repetidos en estos formatos.

## Seguridad y Privacidad

- **No Persistencia de Contenido**: El contenido de los archivos **NO** se guarda en los ledgers de memoria. Solo se mantiene en el `TaskEnvelope` volátil durante el ciclo cognitivo.
- **Aislamiento**: El código generado por Genesis para nuevos procesadores se mantiene en cuarentena.

## CLI

Se ha añadido soporte experimental para archivos en la CLI:
```bash
python src/main.py --file path/to/file.txt
```
