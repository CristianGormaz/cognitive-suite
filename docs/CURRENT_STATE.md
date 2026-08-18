# Estado histórico reportado: Greys-v3 — junio de 2026

> **Contexto histórico**
>
> Este documento conserva el estado que el proyecto reportaba en el snapshot público saneado de junio de 2026. No describe la implementación privada actual ni debe interpretarse como una afirmación vigente sobre capacidades presentes.

## Capacidades reportadas en el snapshot
- **Ingesta Segura y Multimodal**: Procesa texto y archivos (`--file`) de tipo `docx`, `txt`, `md` y ahora `pdf` (experimental).
- **Autonomía Local Validada**: Completado con éxito el piloto de activación de reflejos (`Active Reflex Pilot`), demostrando ruteo activo, bypass de LLM y capacidad de rollback.
- **Quorum de Promoción (Dry-Run)**: El motor `QuorumPromotionReadiness` evalúa la madurez de los candidatos basándose en masa crítica de evidencia, detectando riesgos de "falso quórum" y rumiación antes de cualquier activación.
- **Ruta Mielinizada (Fast-Path Bypass)**: La `FastPathReflexGate` asegura que reflejos locales de riesgo 0 (ej. saludos) se ejecuten en milisegundos.
- **Dream Continuity & Hygiene (v3.2)**: El Modo Sueño ahora soporta sesiones largas ininterrumpidas mediante `GREYS_DREAM_CONTINUE_ON_NO_NEW_EVIDENCE`. Implementado mantenimiento analítico (Idle Mode).
- **Process Envelope Hardening (v3.3)**: Implementada taxonomía de alta resolución para fallos en el sobre cognitivo y validación de contratos estructurales, eliminando la ambigüedad de los fallos desconocidos.
- **Reconciliación de Deuda Técnica (v3.4)**: Implementada capa de "etiquetado epigenético" para reclasificar fallos históricos de forma derivada, permitiendo distinguir deuda antigua de problemas activos.
- **Ruteo Local Determinístico**: El `LocalIntentRouter` intercepta comandos comunes y activa reflejos aprobados usando el fast-path.
- **Generalización de Intenciones (v1.2)**: El `LocalMicroClassifier` es ahora un motor maduro que utiliza `Balanced Accuracy` y un mecanismo de margen endurecido (0.12) para un ruteo local de alta integridad.

- **Arquitectura Bioinspirada**: El sistema evalúa su salud estructural contra patrones orgánicos (Dendritas, Mielina, Quórum) para prevenir anti-patrones y guiar su evolución.
- **Delegación Simbiótica (Dry-Run)**: La `SymbioticDelegationPolicy` calcula scores determinísticos (ERS, SDS, QPS) para evaluar si una tarea debe resolverse localmente o delegarse al LLM, operando actualmente en modo de observación.
- **Aceleración de Memoria**: El `LocalLedgerCache` implementa un patrón Read-Through en RAM para reducir la latencia de lectura de I/O en los registros auditables.
- **Marco de Madurez y Soak**: El sistema evalúa continuamente la estabilidad del núcleo local, detectando sobreconfianza y manteniendo una salud de `unknown_safe` superior al 30%.
- **Puente de Conciencia Generalizada**: El `ClassifierShadowBridge` transforma predicciones en candidatos shadow.
- **Camino a v1**: Finalizado el diseño para la persistencia de pesos y aprendizaje supervisado.
- **Marco de Contexto Multidimensional**: El `MultidimensionalContextEngine` asegura que toda decisión autónoma sea situada y segura.
- **Destilación de Experiencia DeepSeek**: Convierte análisis profundos del LLM en patrones locales (Reflejos).
- **Capa Neural Mínima (v0)**: Memoria local de patrones destilados que permite tomar decisiones basadas en la experiencia histórica sin consultar al LLM en tiempo real.
- **Minería de Principios (SemanticDreamMiner)**: Extrae sabiduría operativa a partir de la experiencia técnica acumulada.
- **Mapas de Calor Calibrados (ImmuneHeatmap)**: Identifica hotspots operativos distinguiendo entre deuda histórica y amenazas recientes.
- **Gestión de Fatiga y Tensión**: Calcula el desgaste modular y suprime rumiación redundante.
- **External Gate Synergy**: Todas las llamadas derivadas del procesamiento están protegidas por el `ExternalChannelGate`.

## Restricciones críticas reportadas en ese momento
- **NO promover a stable automáticamente**: La carpeta `src/skills/stable/` permanece inmutable.
- **NO usar red externa sin bypass**: Las heurísticas locales y la Capa Neural Mínima son el primer punto de decisión.

## Validación reportada en ese momento
Para asegurar la integridad de la línea base se registró:
```bash
export PYTHONPATH=src
.venv/bin/python -m pytest -q
```
Resultado reportado en ese momento: **511 tests passed** (100% éxito).

Este resultado se conserva como dato histórico del snapshot y no constituye una medición actual de la implementación privada vigente.

## Siguientes pasos registrados en ese momento
**A) Entrenamiento Real de Micro-Clasificador**: Implementar un modelo de pesos ligero para la Capa Neural Mínima.
**B) Expansión de LocalIntentRouter**: Usar los patrones destilados para automatizar respuestas complejas sin LLM.
**C) Prueba con PDF Fixture Realista**: Validar la extracción con documentos de mayor complejidad.
