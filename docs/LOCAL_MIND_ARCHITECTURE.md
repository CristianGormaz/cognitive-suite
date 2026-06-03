# Arquitectura de la Mente Local: Greys-v3

Greys-v3 opera bajo una arquitectura de **Mente Local de Dos Piezas**, separando el razonamiento operativo y de seguridad de la capacidad narrativa y expresiva.

## Estructura Dual

### 1. Reflex Kernel (Pieza A: Decisión y Control)
Es el núcleo no generativo encargado de la lógica, el ruteo, la clasificación de riesgo y la seguridad. Su función es determinar **QUÉ** debe hacerse y **SI** es seguro hacerlo.

**Componentes Clave:**
- **LocalIntentRouter**: Interceptor determinístico de intenciones conocidas.
- **MinimalNeuralLayer**: Memoria de patrones destilados (Reflejos) para decisiones basadas en experiencia.
- **ReflexShadowEvaluator**: Motor de calibración y métricas en modo sombra.
- **ReflexPromotionGate**: Compuerta de gobernanza para la activación supervisada de reflejos.
- **BioInspiredPatternAtlas**: Catálogo conceptual de patrones orgánicos (Dendritas, Mielina, Quórum) que guían la evolución del sistema.
- **IntrusiveSignalPolicy**: Clasificador y traductor de alarmas crudas en insights operativos.
- **IAFA Engine**: Validador de Integridad, Autonomía, Fricción y Alineación.
- **ImmuneQuarantinePolicy**: Gobernanza de código experimental y aislamiento.
- **CanonicalStateResolver**: Resolutor de la verdad vigente del sistema.
- **SymbioticDelegationPolicy**: Política que calcula ERS y SDS para recomendar rutas (local vs LLM).
- **FastPathReflexGate**: Compuerta de mielinización que permite a reflejos certificados de riesgo 0 evadir la sobrecarga cognitiva.
- **ExternalChannelGate**: Guardián del acceso al canal externo (LLM) con poder de veto sobre la política de delegación.

**Propiedades:**
- **Determinístico**: Resultados consistentes y predecibles.
- **Baja Latencia**: Ejecución en milisegundos.
- **Cero Alucinación**: No genera contenido nuevo, solo mapea a estados conocidos.

---

### 2. Narrative Layer (Pieza B: Expresión y Contexto)
Es la capa encargada de traducir las decisiones del Reflex Kernel a un lenguaje comprensible para el humano. Su función es determinar **CÓMO** explicar lo sucedido.

**Componentes Clave:**
- **LocalNarrativeLayer**: Motor de traducción y plantillas para señales técnicas y alertas.
- **ResponseManager**: Gestor de plantillas y respuestas locales fijas.
- **MorningBrief**: Generador de resúmenes ejecutivos de aprendizaje.
- **SemanticDreamMiner**: Extractor de sabiduría operativa (principios).
- **LLM (Opcional)**: DeepSeek-r1:8b, consultado solo bajo permiso explícito del Gate para análisis profundos o redacción compleja.

**Propiedades:**
- **Informativo**: Provee contexto y justificación técnica.
- **Configurable**: Permite diferentes niveles de expresividad según el modo (interactivo, sueño, etc.).

## Flujo de Pensamiento Local

1.  **Ingestión**: El archivo o texto entra al sistema.
2.  **Mapeo de Reflejos**: El `LocalIntentRouter` y la `MinimalNeuralLayer` buscan coincidencias locales.
3.  **Evaluación de Riesgo**: Si se propone una acción, IAFA valida el riesgo físico y lógico.
4.  **Decisión Determinística**: Si el Reflex Kernel tiene alta confianza, se toma la ruta local.
5.  **Explicación Narrativa**: El `ResponseManager` o la lógica local construye la respuesta final.

Esta arquitectura garantiza que Greys-v3 mantenga su integridad operativa incluso cuando el canal externo (LLM) está degradado o desactivado, reservando la potencia de los modelos generativos para la síntesis de experiencia de alto nivel.
