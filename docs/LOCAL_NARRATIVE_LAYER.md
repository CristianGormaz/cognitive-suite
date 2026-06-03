# Local Narrative Layer

La **Capa Narrativa Local** de Greys-v3 es el componente de la Pieza B (Narrativa) encargado de la comunicación segura, clara y no generativa con el operador.

## Propósito

Asegurar que cada decisión técnica del sistema (bloqueos, fallos, estados de seguridad) se explique en lenguaje humano sin depender de un modelo de lenguaje (LLM). Esto reduce el riesgo de alucinaciones, disminuye la latencia de respuesta y evita generar estrés innecesario en el operador mediante un tono calmado y proactivo.

## Funcionamiento

La capa utiliza un motor de plantillas estructuradas (`src/core/local_narrative_layer.py`) que traduce las evaluaciones de la `IntrusiveSignalPolicy` y otros estados internos.

### Estructura de Respuesta
Cada mensaje generado contiene:
- **User Facing Summary**: Un resumen breve y claro de lo que sucedió.
- **Technical Summary**: Justificación técnica del evento (invisible por defecto en modo usuario).
- **Recommended Next Step**: Una instrucción clara sobre qué debe hacer el operador o qué hará el sistema.
- **Severity & Reassurance**: Clasificación del impacto y nivel de tranquilidad (informativo, correctivo o protectivo).

## Casos de Uso Principales

| Señal | Narrativa de Greys |
| :--- | :--- |
| **LLM Timeout** | El canal de razonamiento profundo mostró latencia. Puedo continuar en modo local. |
| **Host Stress** | El host físico está bajo alta carga. Recomiendo diferir tareas pesadas. |
| **Unsafe Code** | Este candidato contiene patrones inseguros. Se conserva como muestra inmune. |
| **PDF Disabled** | El lector PDF está desactivado por configuración global. Esto no es un error. |

## Integración en la Arquitectura

1.  **ResponseManager**: Consume la capa narrativa para responder a intenciones de sistema e ingesta de archivos.
2.  **MorningBrief**: Utiliza la capa para presentar la sección de "Traducción de Alertas" con mayor detalle técnico y humano.
3.  **Reflex Kernel**: Provee los datos y evaluaciones que la capa narrativa traduce.

## HITO: Capa Narrativa Operativa (2026-06-02)

-   Módulo `LocalNarrativeLayer` implementado y testeado.
-   Eliminada la dependencia de LLM para explicaciones de ruteo local y bloqueos de seguridad.
-   Integración completa en el flujo de respuesta interactiva y reportes diarios.
