# Blueprint: High Quality Sovereignty (HQS) Principles

## Nombre Conceptual
`hqs_principles`

## Propósito
Definir los límites éticos y de soberanía de Greys-v3 basándose en la "Constitución" histórica.

## Problema que resolvía en v2
Controlaba la tensión cognitiva y evitaba que el sistema tomara decisiones que comprometieran su autonomía o la del usuario.

## Por qué NO se copia el código
- El módulo original `hqs.py` era extremadamente inconsistente y mezclaba lógica de UI con lógica de motor.
- Los contratos de "enmiendas constitucionales" estaban rotos.

## Rediseño para Greys-v3
- **Implementación**: Integrar como un conjunto de reglas en el `IAFAEngine` y en el `EvolutionDialog`.
- **Estructura**: Usar el JSON histórico (`assets/constitution.json`) solo como referencia para los umbrales de `IAFA`.

## Contratos Mínimos
- Entrada: Acción propuesta.
- Salida: `{"allowed": bool, "sovereignty_score": float, "reason": str}`

## Riesgos
- Parálisis por exceso de precaución (over-blocking).

## Tests Esperados
- Validar que acciones que violan la "sovereignty" son bloqueadas por IAFA.
