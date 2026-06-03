# Blueprint: Consultor de Tiempo (Legacy v2 Rescued)

## Nombre Conceptual
`consultor_tiempo`

## Propósito
Permitir que Greys-v3 consulte y reporte la hora y fecha actual de forma segura.

## Problema que resolvía en v2
Proporcionaba contexto temporal básico para que el sistema pudiera saludar y planificar tareas basadas en el tiempo.

## Por qué NO se copia el código
- El código original usaba patrones `Singleton(type)` complejos e innecesarios.
- El contrato de `BaseSkill` en v2 es incompatible con el de v3.
- Contenía trazas de logs con formatos obsoletos.

## Rediseño para Greys-v3
- **Implementación**: Skill de Python puro sin librerías externas pesadas.
- **Acceso**: Usar solo la librería estándar `datetime`.
- **Salida**: Devolver un `Dict[str, Any]` compatible con el `ResponseManager`.

## Contratos Mínimos
- Entrada: No requiere parámetros adicionales.
- Salida: `{"status": "success", "iso_datetime": "...", "human_readable": "..."}`

## Riesgos
- Exposición de zona horaria local (bajo riesgo).

## Tests Esperados
- Verificar que devuelve una fecha válida.
- Verificar que el formato de texto es natural.
