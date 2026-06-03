# Plan de Rebranding: Cognitive Suite

Este documento establece la estrategia para la transición de identidad del proyecto **Greys-v3** a **Cognitive Suite**.

## Contexto
-   **Nombre Actual**: Greys-v3
-   **Nombre Público Propuesto**: Cognitive Suite
-   **Codename Histórico**: Greys
-   **Motivación**: Reflejar la transición de un agente experimental a una suite de herramientas de cognición local supervisada.
## Estrategia de Transición (Fase 0: Documentación)

En esta fase, el rebranding es puramente a nivel de **identidad pública** y **documentación**.

### Estructura de Repositorios
Debido a hallazgos en la [Auditoría de Historial](PUBLIC_HISTORY_AUDIT.md), la estrategia se divide en:
1.  **greys-v3 (Privado)**: Repositorio original. Contiene el historial completo de desarrollo, borradores y huellas locales. Permanecerá como el laboratorio interno.
2.  **cognitive-suite (Público)**: Repositorio nuevo inicializado desde un snapshot limpio (ver [Plan de Exportación Saneada](SANITIZED_PUBLIC_EXPORT_PLAN.md)). Este será el punto de contacto con la comunidad.

### Qué se renombra AHORA
...

1.  **README.md**: Actualización de la cabecera y descripción del proyecto.
2.  **docs/PROJECT_IDENTITY.md**: Formalización del nombre Cognitive Suite como la marca oficial.
3.  **docs/REBRAND_PLAN.md**: Creación de este plan.
4.  **docs/PUBLIC_RELEASE_CHECKLIST.md**: Preparación para la publicación.

### Qué NO se renombra TODAVÍA (Codename Greys)
1.  **Imports de Python**: Todos los módulos seguirán bajo `src/` y referencias internas.
2.  **Variables de Entorno**: Prefijos `GREYS_*` se mantienen para evitar migraciones costosas de scripts de usuario.
3.  **Paths de Archivos**: `assets/memory/`, etc.
4.  **Logs de Sistema**: Los loggers mantendrán el identificador Greys para trazabilidad histórica.
5.  **Tests**: Los nombres de archivos y funciones de test permanecen iguales.

## Riesgos y Mitigación
-   **Riesgo**: Confusión del usuario al ver nombres mezclados.
-   **Mitigación**: Explicar claramente que Cognitive Suite es el sucesor de Greys-v3 y que "Greys" persiste como el núcleo técnico (codename).
-   **Riesgo**: Rotura de dependencias externas o scripts de terceros.
-   **Mitigación**: Mantener las variables de entorno `GREYS_*` como el estándar de configuración oficial hasta la v4.0.

## Rollback
Si se decide cancelar el rebranding:
1.  Revertir cambios en README.md.
2.  Mantener Greys-v3 como nombre público.
3.  Archivar este plan.

## Checklist Pre-Publicación (GitHub)
- [ ] Confirmar que el README refleja la nueva identidad.
- [ ] Validar que no hay secretos expuestos (Fase 1 completada).
- [ ] Asegurar que la licencia esté presente (MIT sugerida).
- [ ] Verificar que la visibilidad del repositorio sea la deseada.
