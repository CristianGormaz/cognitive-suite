# Semantic Dream Miner (v1)

## Propósito
El `SemanticDreamMiner` es el componente encargado de la **evolución intelectual** de Greys-v3. Mientras que el aprendizaje técnico se enfoca en resolver fallos de código o dependencias, el aprendizaje semántico busca extraer **principios, interpretaciones y dimensiones de contexto** a partir de la experiencia operacional.

## Filosofía
A diferencia del entrenamiento tradicional de redes neuronales, el entrenamiento semántico de Greys:
1.  No modifica los pesos de un modelo de lenguaje.
2.  No altera el código fuente de forma autónoma.
3.  Genera un **dataset de sabiduría operativa** que el sistema utiliza para mejorar su autocrítica y su alineación de seguridad.

## Conceptos Clave

### 1. Principios Semánticos
Un principio es una regla abstracta derivada de la evidencia.
*   **Ejemplo:** `error_como_muestra_inmune`.
*   **Origen:** Múltiples detecciones de código peligroso en el sandbox.
*   **Interpretación:** El sistema entiende que el riesgo no es solo algo que evitar, sino una señal que codifica patrones de ataque que deben ser retenidos para fortalecer el sistema inmune.

### 2. Dimensiones de Contexto
Categorías de alto nivel sobre las cuales el sistema reflexiona durante el `Dream Mode`.
*   **Defensa:** Relacionado con bloqueos, ISS y cuarentena.
*   **Resiliencia:** Relacionado con fallos externos (LLM) y degradación local.
*   **Privacidad:** Relacionado con la sanitización de rutas y metadatos.

## Implementación Técnica
*   **Módulo:** `src/cognition/semantic_dream_miner.py`
*   **Ledger:** `assets/memory/semantic_principle_ledger.jsonl`
*   **Frecuencia:** Se ejecuta al finalizar cada sesión de Dream Mode.
*   **Anti-Rumiación:** El sistema utiliza puntuaciones de novedad (`novelty_score`) para evitar repetir los mismos principios si no existe evidencia significativamente nueva.

## Reglas de Seguridad
*   **Aislamiento:** El minero semántico solo procesa metadatos y resúmenes técnicos. Nunca tiene acceso a contenido de usuario crudo ni a prompts completos.
*   **Human-in-the-loop:** Todos los principios detectados se presentan en el `MorningBrief` para revisión humana. Un principio puede ser aprobado, rechazado o marcado como "sobreinterpretación".
