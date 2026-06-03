# Inventario Conceptual de Greys-v2

Este documento cataloga los componentes, ideas e intenciones funcionales extraídas de la versión heredada Greys-v2. 

**AVISO DE SEGURIDAD**: Greys-v2 es una fuente arqueológica no confiable. El código fuente presenta corrupción, contratos rotos y deudas técnicas graves. **NUNCA** importar código directamente.

## Tabla de Inventario

| Componente Legacy | Nombre Conceptual | Tipo | Estado | Riesgo | Equivalencia v3 | Recomendación |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| `greys/skills/ConsultorTiempo.py` | Consultor de Tiempo | Skill | Rescatable conceptualmente | Bajo | Skill Experimental | Re-implementar como skill pura en v3 (solo texto). |
| `greys/cognition/hqs.py` | HQS (High Quality Sovereignty) | Cognición / Ética | Inconsistente | Crítico | EvolutionDialog / IAFA | Extraer principios éticos de soberanía, descartar código de "tensión". |
| `greys/cognition/attention_manager.py` | Attention Manager | Cognición | Conceptualmente útil | Medio | SparkEngine (Idle Probe) | Rescatar idea de "capacidad de atención" para regular el pulso de Spark. |
| `greys/cognition/tts_engine.py` | TTS Engine (Piper) | Voz | Rescatable conceptualmente | Medio | PiperProvider (Futuro) | Usar la idea de parámetros emocionales (R, V) para el habla futura. |
| `greys/cognition/anticipatory_nlu.py` | Anticipatory NLU | NLU | Rescatable conceptualmente | Bajo | LLMPlanner | Rescatar patrones de palabras clave para pre-clasificación rápida. |
| `greys/cognition/genesis_engine.py` | Genesis Engine v2 | Motor | Corrupto / Inseguro | Crítico | GenesisEngine v3 | Descartar código; rescatar idea de "genealogía evolutiva" para ledgers. |
| `greys/core/iafa_engine.py` | IAFA v2 | Núcleo | Contrato roto | Alto | IAFAEngine v3 | No mezclar; v3 tiene un modelo de variables más robusto. |
| `greys/interface/ui_bubbles.py` | Thought Bubbles | UI | Visualmente rescatable | Bajo | EvolutionDialog | Adaptar estética de "nodos orbitales" para la UI evolutiva futura. |
| `greys/cognition/purpose_engine.py` | Purpose Engine | Cognición | Rescatable conceptualmente | Medio | SemanticTensionLedger | Usar la estructura de "árbol de propósitos" como blueprint de memoria semántica. |
| `greys/memory/episodic_engine.py` | Episodic Engine | Memoria | Inconsistente | Alto | Ledgers (JSONL) | v3 usa JSONL para trazabilidad; rescatar solo tipos de eventos episódicos. |

## Resumen de Hallazgos

1.  **Intenciones de Voz**: v2 ya exploraba parámetros emocionales (Riesgo, Voluntad) en TTS.
2.  **Soberanía Cognitiva (HQS)**: v2 tenía una "Constitución" (`assets/constitution.json`) que definía límites éticos. Es vital rescatar este JSON conceptualmente.
3.  **Habilidad "ConsultorTiempo"**: Era la única skill funcional identificada. Su lógica era simple (singletons, execute).
4.  **Escalabilidad**: Se encontraron referencias a "Diseño para 10,000 agentes", una ambición de v2 que v3 debe heredar en su arquitectura asíncrona.
