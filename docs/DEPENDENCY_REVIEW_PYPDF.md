# Dependency Review: pypdf

## Contexto
Greys-v3 ha identificado la necesidad de procesar archivos PDF de manera controlada. El candidato experimental `candidate_pdf_reader_basic` ha sido desarrollado en el sandbox, pero declara la dependencia externa `pypdf`.

De acuerdo a la política de seguridad estricta del entorno, ninguna dependencia externa debe ser instalada dinámicamente ni añadida a `requirements.txt` sin una evaluación exhaustiva (Dependency Review).

## Evaluación del Candidato Actual
* **Implementación Actual:** Es un placeholder (`has_pypdf = False`). Atrapa el `ImportError` y devuelve de manera segura un dict con `"status": "missing_dependency"`.
* **Seguridad:** El candidato está en cuarentena y ha sido calificado como de riesgo Medio (Medium Risk). No intenta instalar paquetes en ejecución ni ejecutar comandos del sistema fuera de su alcance.
* **Estado de la Dependencia:** La ejecución local demostró que `pypdf`, `PyPDF2` y `fitz` **no están instaladas**.

## Criterios de Aprobación Futura
Para que `pypdf` sea aprobada e incorporada a `requirements.txt`, el micro-sprint correspondiente debe garantizar lo siguiente:

1. **Dependencia Fijada:** La versión de `pypdf` debe fijarse de forma estricta (ej. `pypdf==4.2.0`).
2. **Instalación Controlada:** Solo el humano puede modificar `requirements.txt`. El agente AI no debe ejecutar `pip install` por su cuenta en el entorno base.
3. **Tests Aislados:** Se requiere un suite de pruebas que opere sobre un *fixture PDF seguro*, verificando que las fallas de extracción son controladas.
4. **Límites Físicos y Semánticos:**
    * **Tamaño del Archivo:** Se debe descartar cualquier archivo que exceda 5MB (configurable).
    * **Extracción Truncada:** La extracción de texto debe detenerse al alcanzar un límite de tokens (ej. 30,000 caracteres) para proteger el Prompt Budget del LLM (`GREYS_LLM_MAX_PROMPT_CHARS`).
5. **No Almacenamiento en Crudo:** El texto completo de los PDFs no debe volcarse a memoria persistente o logs sin una directiva del usuario, para evitar fugas de información.
6. **Robustez ante Corrupción:** La habilidad debe manejar errores comunes como contraseñas, documentos dañados o *ParseErrors* retornando un `pdf_parse_error` limpio, sin romper el bloqueador de IAFA.
7. **Perfil IAFA:** El skill PDF Reader mantendrá su calificación **Medium Risk**.
8. **Rollback de Habilidades:** En caso de fallos repetitivos con la librería, el sistema debe ser capaz de desactivar dinámicamente la habilidad o recurrir al Local-Only Fallback sin comprometer otros flujos de ingestión.

## Estado Actual (2026-06-01)
* **pypdf:** Instalado (`6.12.2`) y fijado en `requirements.txt`.
* **Install Allowed:** `True` (ya ejecutado en .venv).
* **Review Status:** `approved_for_future_promotion`.
* **Candidato:** `candidate_pdf_reader_basic.py` actualizado con límites de seguridad (5MB, 30k chars).
* **Seguridad:** El sandbox continuará advirtiendo sobre el uso de `os`, pero el `SkillPromotionGate` permite la promoción a `experimental` tras la revisión humana exitosa.
