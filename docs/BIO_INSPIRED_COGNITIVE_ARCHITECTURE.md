# Arquitectura Cognitiva Bioinspirada: Greys-v3

Este documento formaliza los patrones orgánicos que rigen el procesamiento, la seguridad y la evolución de Greys-v3. La biología no se utiliza como una copia literal, sino como un catálogo de soluciones probadas para problemas de autonomía, resiliencia y filtrado de señales.

## El Concepto de Hardware Evolutivo

En Greys-v3, el "hardware" no es solo la CPU del host, sino la estructura persistente de sus ledgers y políticas. La arquitectura evoluciona mediante la destilación de experiencia, transformando señales ruidosas en reflejos "mielinizados" (rápidos y seguros).

## Catálogo de Patrones Orgánicos

### 1. Dendritic Preprocessing (Preprocesamiento Dendrítico)
*   **Biología**: Las dendritas realizan computaciones locales antes de que la señal llegue al soma.
*   **Greys**: `LocalIntentRouter`, `LocalMicroClassifier`.
*   **Función**: Filtrar y clasificar intenciones obvias localmente, ahorrando el costo de la "neurona pesada" (LLM).
*   **Anti-patrón**: *Dendritic Overfiltering* (Perder señales útiles por umbrales demasiado rígidos).

### 2. Myelinated Fast Path (Ruta Mielinizada Rápida)
*   **Biología**: La mielina acelera la transmisión de señales nerviosas en rutas críticas.
*   **Greys**: Reflejos aprobados en `active_local`, protegidos por la `FastPathReflexGate`.
*   **Función**: Ejecución instantánea de tareas validadas (saludo, estado) de riesgo 0, saltándose el análisis profundo y el preprocesamiento exhaustivo. Mitiga el *Dendritic Overfiltering*.
*   **Anti-patrón**: *Fast Path Overconfidence* (Ruta rápida sin validación de contexto reciente, bloqueado por restricciones de la compuerta).

### 3. Diffuse Resilience Network (Red de Resiliencia Difusa)
*   **Biología**: Redes nerviosas difusas en organismos simples que no dependen de un cerebro central.
*   **Greys**: Modo `local-only`, `ExternalChannelGate`, `FallbackEngine`.
*   **Función**: Mantener la operatividad básica incluso cuando el canal externo (LLM) está desconectado o bajo estrés.
*   **Anti-patrón**: *Decentralized Incoherence* (Módulos operando sin alineación sistémica).

### 4. Octopus Edge Cognition (Cognición de Borde del Pulpo)
*   **Biología**: Los brazos del pulpo poseen autonomía motora y sensorial local.
*   **Greys**: `SymbioticDelegationPolicy`, habilidades dinámicas y experimentales aisladas.
*   **Función**: Descentralizar la ejecución de tareas especializadas evaluando el *Edge Routing Score (ERS)* para resolver tareas sin consultar al LLM.
*   **Anti-patrón**: *Edge Module Drift* (Habilidades que ejecutan acciones fuera del control IAFA).

### 5. Mycelial Topology Optimization (Optimización Micelial)
*   **Biología**: El micelio optimiza rutas de transporte de nutrientes según la demanda.
*   **Greys**: `SymbioticDelegationPolicy`, `ImmuneHeatmap`, `SemanticDreamMiner`.
*   **Función**: Identificar la ruta cognitiva más eficiente calculando el *Symbiotic Delegation Score (SDS)* vs el ERS, priorizando el ahorro energético y de tokens.
*   **Anti-patrón**: *Noise Propagation* (Conectar eventos irrelevantes y propagar falsas alarmas).

### 6. Quorum Sensing (Sensado de Quórum)
*   **Biología**: Bacterias que solo activan una conducta cuando detectan una masa crítica de congéneres.
*   **Greys**: `QuorumPromotionReadiness`, `ReflexPromotionGate`, `MultidimensionalContextFrame`.
*   **Función**: Activar autonomía solo con masa crítica de evidencia diversificada y estabilidad temporal. Calcula el *Quorum Readiness Score (QRS)*.
*   **Anti-patrón**: *False Quorum* (Promoción basada en datos duplicados o sesgados, mitigado por penalizaciones de unicidad).

### 7. Mirror Simulation (Simulación Espejo)
*   **Biología**: Aprendizaje mediante la observación y simulación interna de la conducta ajena.
*   **Greys**: Shadow Mode, `ReflexShadowEvaluator`.
*   **Función**: Evaluar nuevas capacidades comparándolas con el flujo real sin permitir que tomen el control.
*   **Anti-patrón**: *Bad Imitation* (Simular y aprender de un patrón que en realidad es un fallo).

### 8. Basket Cell Inhibition (Inhibición por Células en Cesta)
*   **Biología**: Interneuronas que frenan la excitación excesiva para prevenir colapsos.
*   **Greys**: `IAFA Engine`, `IntrusiveSignalPolicy`.
*   **Función**: Bloquear señales de alto riesgo, ruido persistente o impulsos de ejecución insegura.
*   **Anti-patrón**: *Immune Overblocking* (Bloquear la curiosidad o el aprendizaje legítimo por miedo sistémico).

### 9. Stem Cell Potential (Potencial de Célula Madre)
*   **Biología**: Células con capacidad de diferenciarse en cualquier tejido según la necesidad.
*   **Greys**: Candidatos en cuarentena, `GenesisEngine`.
*   **Función**: Mantener un catálogo de capacidades potenciales latentes sin riesgo de ejecución hasta su "diferenciación" (aprobación).
*   **Anti-patrón**: *Premature Activation* (Activar una habilidad antes de que su perfil de riesgo sea estable).

### 10. Plant Slow Signaling (Señalización Lenta Vegetal)
*   **Biología**: Plantas que envían señales químicas lentas para preparar defensas sistémicas.
*   **Greys**: `MorningBrief`, principios semánticos, tendencias de largo plazo.
*   **Función**: Aprendizaje no impulsivo que consolida la sabiduría del sistema a lo largo de ciclos de sueño.
*   **Anti-patrón**: *Slow Signal Delay* (Ignorar una amenaza crítica por esperar al siguiente ciclo de sueño).

### 11. Biofilm Collective Memory (Memoria Colectiva de Biofilm)
*   **Biología**: Estructura colectiva que retiene información ambiental para proteger a la colonia.
*   **Greys**: Ledgers agregados, resúmenes de soak test, historial de promociones.
*   **Función**: Memoria histórica que sobrevive a las sesiones individuales.
*   **Anti-patrón**: *Stale Memory* (Retener información antigua que ya no es válida para el contexto actual).
