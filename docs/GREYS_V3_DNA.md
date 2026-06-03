# ADN Operativo de Greys-v3

## ¿Qué es Greys-v3?
Greys-v3 es un sistema de arquitectura cognitiva avanzada diseñado como un asistente local. Opera de forma autónoma bajo un modelo estricto de gobernanza denominado **IAFA** (Internal Agent Functional Analysis) y cuenta con capacidades de síntesis de código supervisado.

## ¿Qué puede hacer actualmente?
- **Recibir y clasificar información:** A través de `IngestionRouter` procesa texto y archivos (ej. .docx), encapsulándolos en un `TaskEnvelope` inmutable con hash SHA-256.
- **Escuchar comandos de voz:** Utilizando `AcousticBridge` (con Vosk y Piper).
- **Razonar intenciones y planificar:** Usa `LLMPlanner` conectado a modelos locales (ej. Ollama/deepseek-r1:8b) para clasificar intenciones y estimar niveles de fricción.
- **Evaluar la seguridad de las acciones:** A través de `IAFAEngine`, un gatekeeper matemático determinista que aprueba o deniega acciones basándose en variables de fricción y penalizaciones (éxito y red herring).
- **Mantener un registro inmutable:** `IafaAuditor` firma criptográficamente cada decisión tomada mediante HMAC-SHA256, creando un log de auditoría *append-only*.
- **Generar y validar habilidades (Habilidades Asistidas):** Mediante `GenesisEngine`, el sistema puede sintetizar código Python para nuevas habilidades, que luego son validadas estructuralmente mediante AST en el `GenesisSandbox` antes de ser instaladas.
- **Gestionar contingencias:** Si una acción falla o no es segura, el `FallbackEngine` y el `CognitiveOrchestrator` intervienen, presentando opciones al humano a través de una UI (`EvolutionDialog` en PySide6).

## ¿Qué NO puede hacer todavía?
- **Actuar de forma proactiva o autónoma sin estímulo:** El sistema actual es puramente reactivo. No tiene iniciativa propia ni un ciclo continuo que observe el estado inactivo (*idle*) para generar dudas evolutivas, reflexionar sobre errores recientes o automejorarse en segundo plano.

## Motores Existentes
1. **IAFAEngine:** Motor de gobernanza y puntuación de seguridad.
2. **LLMPlanner:** Motor de planificación y extracción de intenciones asistido por LLM.
3. **ActionDispatcher:** Encargado de ejecutar las habilidades aprobadas.
4. **FallbackEngine:** Motor lógico de contingencias.
5. **GenesisEngine:** Sintetizador seguro de código Python.
6. **IafaAuditor:** Motor criptográfico de registro de memoria.

## Flujo de una Entrada (Usuario -> IAFA)
1. **Entrada:** El usuario habla (AcousticBridge) o envía texto/archivo.
2. **Ingestión:** `IngestionRouter` lo convierte en un `TaskEnvelope` inmutable.
3. **Planificación:** `LLMPlanner` lee el sobre, determina la intención y estima las variables de fricción IAFA (R, I, N).
4. **Validación:** `IAFAEngine` procesa la intención, las variables de fricción y el historial reciente para emitir un fallo (Allow/Deny).
5. **Auditoría:** La decisión se registra y firma en `IafaAuditor`.
6. **Ejecución/Contingencia:** Si IAFA lo permite, `ActionDispatcher` ejecuta la habilidad (usando `DynamicSkillLoader`). Si lo deniega o falla, `CognitiveOrchestrator` abre un diálogo de *fallback*.

## Autoprogramación Asistida
Greys-v3 **no se autoprograma sin control**.
- Se requiere una intención no resuelta o un fallback explícito para activar el proceso.
- `GenesisEngine` le pide al LLM generar *exactamente una* función síncrona en Python.
- El código generado nunca se ejecuta en el proceso principal directamente durante la síntesis.
- Pasa por el `GenesisSandbox`, que valida el AST (rechazando importaciones peligrosas, acceso a disco/red, etc.).
- Requiere confirmación/autorización antes de considerarse una habilidad estable.

## Límites de Seguridad
- **Sandbox AST:** Impide código malicioso.
- **IAFA Gatekeeper:** Bloquea acciones con alta fricción (Riesgo, Interferencia, Negación) o por penalizaciones de entropía (red herring).
- **TaskEnvelope:** Evita que el contenido procesado (*payload_preview*) sea interpretado como instrucciones (Prompt Injection local mitigado por el prompt del planner).
- **Firma HMAC-SHA256:** Evita manipulación de la memoria del sistema.

## Dependencia de Ollama / deepseek-r1:8b
El LLM local actúa como el "lóbulo frontal" para:
- Clasificar intenciones de texto libre.
- Extraer fricciones IAFA sugeridas desde el texto.
- Escribir código Python en el `GenesisEngine`.
*El LLM no ejecuta código ni toma la decisión final de seguridad (lo hace IAFA).*

## Partes Reactivas vs. Proactivas
**Todo** el sistema confirmado en la auditoría es reactivo. Falta integrar un motor de "pulso" (`SparkEngine`) para habilitar proactividad segura.

## Comandos Seguros para Pruebas
Para una prueba puramente reactiva:
`python src/main.py --text "Inicia diagnóstico interno"` (O el equivalente implementado para inyectar texto al orquestador).

## Respuesta Esperada a "¿Qué puedes hacer?"
Si el usuario hace esta pregunta, Greys debe basar su respuesta en su arquitectura real y capacidades comprobadas (`DynamicSkillLoader`), y mencionar que posee motores de razonamiento supervisado y seguridad matemática (IAFA), pero que su proactividad depende de la integración final de sus sistemas de reflexión.
