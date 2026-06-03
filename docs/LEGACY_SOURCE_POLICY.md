# Política de Fuentes Heredadas (Greys-v2)

Greys-v2 se considera una fuente arqueológica **no confiable**. Debido a la corrupción de archivos detectada y a la divergencia crítica de contratos, se establece la siguiente política de rescate.

## Principios de No Contaminación

1.  **Prohibición de Importación**: NUNCA importar módulos de `greys-v2` dentro de `src/` de `greys-v3`.
2.  **Prohibición de Copia Directa**: NO copiar archivos `.py` desde la versión legacy a la carpeta de habilidades o motores activos.
3.  **Aislamiento de Cuarentena**: Si se desea probar una idea de v2, esta debe ser re-escrita desde cero en un Blueprint Markdown.

## Procedimiento de Rescate Seguro

Para rescatar una funcionalidad de Greys-v2, se deben seguir estos pasos:

1.  **Inventario Conceptual**: Registrar el archivo y su propósito en `docs/LEGACY_GREYS_V2_INVENTORY.md`.
2.  **Blueprint Markdown**: Crear un diseño técnico en `docs/legacy_blueprints/` describiendo cómo se adaptará a la arquitectura v3.
3.  **Candidato Limpio**: Generar el código en la carpeta de cuarentena (`assets/quarantine/`) sin heredar clases base antiguas.
4.  **Validación de Ciclo**: El candidato debe pasar por `GenesisSandbox`, `SkillCandidateReview` y `SkillPromotionGate` antes de ser promovido.

## Datos de Referencia (Solo Lectura)

Los archivos JSON como `constitution.json` o `purpose_tree.json` pueden leerse para extraer parámetros, pero su lógica de carga debe ser re-implementada en v3 para asegurar la compatibilidad.
