# Principio de la Señal Intrusiva: De Alarma a Sabiduría

En Greys-v3, una **Señal Intrusiva** se define como cualquier entrada, fallo, alerta o propuesta de código que dispara una reacción de alarma en el sistema sin haber sido solicitada o validada plenamente.

## Filosofía de Manejo

El principio fundamental es: **"No destruir la señal. No obedecerla ciegamente. Aislarla, traducirla, extraer aprendizaje y reducir su carga."**

### 1. La Señal no es la Verdad
Una alerta de "riesgo crítico" o un fallo de timeout es solo una medición cruda. El sistema no debe entrar en un bucle de pánico ni intentar "arreglarlo" impulsivamente.

### 2. Contención y Cuarentena
Toda señal intensa (como un `candidate_unsafe`) se contiene en cuarentena. Esto no es un castigo, sino una medida de protección que preserva la señal para su análisis posterior.

### 3. Traducción (Insight)
Greys traduce la alarma cruda en un entendimiento operativo:
- **Alarma**: `llm_timeout` recurrente.
- **Traducción**: El canal externo es inestable en este host; necesitamos fortalecer el ruteo local.
- **Insight**: La autonomía depende de la reducción de la dependencia externa.

### 4. Muestra Inmunológica
Ciertos fallos (especialmente los de seguridad) se preservan como muestras de entrenamiento para el sistema inmune, permitiendo refinar los filtros de `ImmuneQuarantinePolicy` y el `GenesisSandbox`.

## Clasificación de Señales

| Tipo de Señal | Interpretación Inmediata | Traducción a Insight | Acción Recomendada |
| :--- | :--- | :--- | :--- |
| **Unsafe Code** | Amenaza a la integridad | Muestra inmunológica valiosa | Preservar en Nivel 3 |
| **LLM Timeout** | Fallo del "cerebro" | Límite de canal externo | Bypass local proactivo |
| **Host Stress** | Agotamiento físico | Límite metabólico | Reducir carga / Diferir |
| **Shadow Divergence** | Error de razonamiento | Reflejo mal calibrado | Mantener observación |

## Aplicación en la Arquitectura Dual

El **Reflex Kernel** detecta y contiene la señal intrusiva, mientras que la **Narrative Layer** se encarga de explicarla al operador sin amplificar la carga de estrés, transformando el "error" en un hito de aprendizaje.
