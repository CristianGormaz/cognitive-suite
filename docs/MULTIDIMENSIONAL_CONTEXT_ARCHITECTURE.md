# Arquitectura de Contexto Multidimensional: Greys-v3

En la construcción de autonomía segura, un plano técnico (como una tasa de coincidencia o un script de prueba) no entrega contexto absoluto. Greys-v3 utiliza un **Marco de Contexto Arquitectónico** para evaluar la viabilidad de cualquier decisión antes de su ejecución o promoción.

## El Principio del Arquitecto

Un arquitecto no solo mira el diseño; evalúa el entorno, los flujos de materiales, la seguridad de los trabajadores y el impacto temporal de la obra. De la misma forma, Greys evalúa cinco dimensiones críticas:

### 1. Environment Context (Entorno)
Mide el estado del host físico y los servicios de soporte.
- **Factores**: Carga de CPU/RAM, temperatura, disponibilidad de Ollama, integridad del sistema de archivos.
- **Impacto**: Si el host está bajo estrés, incluso un reflejo correcto puede ser bloqueado para proteger el hardware.

### 2. Flow Context (Flujos)
Mide la dinámica de los datos y procesos actuales.
- **Factores**: Tasa de ingreso de archivos, latencia de ledgers, volumen de logs, ruteo activo.
- **Impacto**: Evita la saturación de procesos y asegura que la trazabilidad sea completa.

### 3. Human Context (Dimensión Humana)
Mide la relación entre el sistema y el operador.
- **Factores**: Claridad narrativa, cantidad de alertas mostradas, necesidad de revisión manual, fatiga cognitiva del operador.
- **Impacto**: Reduce el ruido y asegura que Greys sea comprensible y útil, no una fuente de estrés.

### 4. Temporal Context (Dimensión Temporal)
Mide la validez de la evidencia a lo largo del tiempo.
- **Factores**: Tendencias (rising/falling), deuda técnica acumulada, tiempo desde la última promoción, decaimiento de señales.
- **Impacto**: Un reflejo que funcionó ayer puede ser irrelevante hoy si la tendencia del sistema ha cambiado.

### 5. Constraint Context (Reglas y Restricciones)
Mide la alineación con las políticas inmutables.
- **Factores**: Evaluación IAFA, listas de permisos (allowlist), reglas de privacidad, estado de la cuarentena.
- **Impacto**: Garantiza que ninguna decisión autónoma rompa los mandatos fundamentales de seguridad.

## Proceso de Evaluación Contextual

Antes de que un reflejo pase de "Shadow Mode" a "Active Local Decision", el `MultidimensionalContextEngine` genera un **Frame de Contexto**. La promoción solo se recomienda si el puntaje global es alto y no existen bloqueos críticos en las dimensiones de restricción o entorno.

Este enfoque asegura que la evolución de Greys-v3 sea **situacional**, adaptándose no solo a lo que es técnicamente posible, sino a lo que es contextualmente correcto en cada momento.
