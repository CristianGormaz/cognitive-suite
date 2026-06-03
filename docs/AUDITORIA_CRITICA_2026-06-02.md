# Auditoría Arquitectónica y Crítica Constructiva (2026-06-02)

## 1. Evaluación General

**Greys-v3** ha logrado una madurez conceptual impresionante. La transición de un simple wrapper de LLM a una **arquitectura cognitiva bioinspirada determinística** es un salto cualitativo sobresaliente. 

**Fortalezas Destacadas:**
*   **Seguridad By-Design:** El aislamiento del canal externo (`ExternalChannelGate`) y la estricta política de "Shadow Mode" garantizan cero ejecuciones accidentales.
*   **Test-Driven Architecture:** Mantener 440 tests pasando de forma consistente demuestra una disciplina de ingeniería de primer nivel.
*   **Resiliencia (Fallback):** La capacidad del sistema para degradar elegantemente a `local-only` y no colapsar ante el estrés del host o la caída del LLM es excelente.
*   **Trazabilidad Semántica:** El uso de `MorningBrief` y `DreamMode` para destilar experiencia en texto plano auditable es una implementación brillante del patrón de "Memoria de Biofilm".

---

## 2. Áreas de Crítica Constructiva (Riesgos y Cuellos de Botella)

Sin embargo, el crecimiento de los últimos sprints ha introducido deuda técnica y riesgos arquitectónicos que deben abordarse antes de buscar nuevas funcionalidades ("features").

### A. El Síndrome del "Shadow Purgatory" (Exceso de Freno)
El sistema ha construido múltiples motores de decisión avanzados (`LocalMicroClassifier`, `ReflexPromotionGate`, `SymbioticDelegationPolicy`), pero casi todos operan en **modo sombra** (Dry-Run, Observe-Only).
*   **El Riesgo:** El sistema es 100% seguro porque *no está tomando riesgos*. La "Basket Cell Inhibition" (freno inmunológico) está dominando sobre la ejecución.
*   **Crítica:** Faltan gatillos de auto-promoción. Si el `ClassifierShadowSoak` indica 90% de exactitud y 0% de duplicados en 100 ciclos, el sistema debería promover automáticamente a *Active Local*, en lugar de depender siempre de `/reflex-approve`. La autonomía supervisada está tendiendo a ser "dependencia supervisada".

### B. Sobrecarga Cognitiva en la "Ruta Rápida" (Dendritic Overfiltering) [~RESUELTO~]
La promesa del `LocalIntentRouter` y la `MinimalNeuralLayer` era crear una *Myelinated Fast Path* (ruta rápida de milisegundos). 
*   **El Riesgo:** Actualmente, para procesar un simple "Hola", el sistema evalúa: Contexto Multidimensional (5 dimensiones) + Estrés del Host + Micro-Clasificador + Puente de Sombra + Política de Delegación Simbiótica (ERS, SDS, QPS) + Compuerta Externa.
*   **Crítica:** El pre-procesamiento se está volviendo más pesado que la ejecución. Se requiere un **"Circuit Breaker Inverso"**: si una entrada hace "match" exacto con un reflejo mielinizado activo de riesgo 0 (como el saludo), debe saltarse la evaluación profunda de simbiósis y contexto.
*   **Actualización (2026-06-02):** Mitigado mediante la implementación de `FastPathReflexGate` que bypassea el sobre-análisis para reflejos de riesgo cero comprobado.

### C. El Techo de Cristal del "LocalMicroClassifier" (NLP en Stdlib)
Usar puramente diccionarios y conteo de tokens (Bag of Words) usando la librería estándar de Python fue una decisión brillante para el MVP de privacidad.
*   **El Riesgo:** Este enfoque no escala semánticamente. Ya se observan colisiones ("qué puedes hacer" vs "cómo está el sistema") que requieren "Hardening de Márgenes" artificiales. No entiende sinonimia, errores ortográficos complejos ni contexto de frase.
*   **Crítica:** El diseño de la v1 con "pesos persistidos" seguirá sufriendo las mismas limitaciones porque la arquitectura base de tokens es frágil.
*   **Recomendación:** Para la v2, evaluar incrustaciones (Embeddings) ultra-ligeras locales (ej. `fasttext` o modelos GGUF minúsculos de <50MB) que corran en CPU en milisegundos, manteniendo el principio local pero ganando verdadera semántica.

### D. Proliferación de Ledgers y Cuello de Botella I/O (Mycelial Noise) [~MITIGADO~]
El directorio `assets/memory/` contiene casi 20 archivos `.jsonl` diferentes.
*   **El Riesgo:** En cada ciclo de procesamiento, el sistema abre, lee `readlines()[-limit:]`, parsea JSON y cierra múltiples archivos (soak, classifier, tension, failures, delegation, etc.). En un entorno de producción de alta frecuencia, esto causará bloqueos de I/O masivos.
*   **Crítica:** La abstracción de la base de datos está rota. El uso de JSONL es excelente para humanos (auditoría), pero pésimo para el rendimiento.
*   **Recomendación:** Implementar un **Memory/Ledger Manager** que lea los JSONL a memoria (RAM) al iniciar `MainOrchestrator`, opere sobre estructuras de datos nativas (listas/dicts) y haga *flush* asíncrono o periódico al disco.
*   **Actualización (2026-06-02):** Mitigado parcialmente mediante la implementación de `LocalLedgerCache` con patrón Read-Through. Las escrituras siguen siendo sincrónicas (append-only) por seguridad, pero las lecturas repetidas ya están cacheadas.

### E. Rumiación Estancada en Dream Mode
Las opciones curadas (`Bandeja de Evolución Curada`) muestran duplicación masiva (ej. "Resolución de Integrales" aparece repetida 12 veces).
*   **El Riesgo:** El `SemanticDreamMiner` y el `EvolutionOptionQueue` no están agrupando semánticamente (deduplicando) de manera eficiente. El LLM nocturno gasta tokens llegando a las mismas conclusiones repetidas.
*   **Crítica:** Falta una política de decaimiento ("Decay") más agresiva para la tensión antigua y una consolidación estricta por "hash semántico" en la bandeja de curaduría.

---

## 3. Hoja de Ruta Sugerida (Próximos Sprints)

Antes de agregar nuevas capacidades (ej. más herramientas PDF o agentes), la arquitectura exige un periodo de consolidación:

1.  **I/O Refactoring Sprint:** Consolidar el acceso a los Ledgers usando una caché en RAM y flush asíncrono.
2.  **Fast-Path Bypass Sprint:** Asegurar que los `active_local_reflexes` ignoren la burocracia de delegación si su riesgo es cero.
3.  **Quorum Auto-Promotion Sprint:** Implementar que si QPS (Quorum Promotion Score) se mantiene en verde durante $X$ horas en el *Soak Test*, el candidato pase a activo sin intervención humana, desbloqueando el "Shadow Purgatory".
