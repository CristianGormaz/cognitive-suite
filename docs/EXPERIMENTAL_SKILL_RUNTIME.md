# Activación Runtime de Skills Experimentales

Este documento describe el mecanismo de seguridad para habilitar habilidades en fase experimental dentro de Greys-v3.

## Filosofía de Activación

Para garantizar que el núcleo estable de Greys-v3 no se vea afectado por código en desarrollo, la carga de habilidades experimentales sigue el principio de **Privilegio Mínimo** y **Denegación por Defecto**.

1.  **Desactivado por Defecto**: Las habilidades en `src/skills/experimental/` no se cargan a menos que se activen explícitamente.
2.  **Allowlist Obligatoria**: No basta con habilitar el modo experimental; cada habilidad debe estar listada en una allowlist para ser cargada.
3.  **Aislamiento**: El `DynamicSkillLoader` busca recursivamente en el directorio de habilidades pero respeta las restricciones de seguridad y la allowlist.

## Configuración

Se controla mediante variables de entorno:

-   `GREYS_EXPERIMENTAL_SKILLS_ENABLED=1`: Habilita el subsistema de carga experimental.
-   `GREYS_EXPERIMENTAL_SKILL_ALLOWLIST=nombre_skill_1,nombre_skill_2`: Lista separada por comas de las habilidades permitidas.

Ejemplo para activar el Consultor de Tiempo y el Lector PDF:
```bash
GREYS_EXPERIMENTAL_SKILLS_ENABLED=1 \
GREYS_EXPERIMENTAL_SKILL_ALLOWLIST=consultor_tiempo_local,pdf_reader_basic \
python src/main.py
```

## HITO: PDF Ingestion routed through controlled runtime (2026-06-02)
*   **Activación**: Requiere `GREYS_EXPERIMENTAL_SKILLS_ENABLED=1` y la entrada `pdf_reader_basic` en la allowlist.
*   **Integración**: El `IngestionRouter` detecta PDFs y los delega al flujo de despacho dinámico.
*   **Seguridad**: IAFA Medium Risk. Privacidad estricta por defecto.

## Trazabilidad y Ledgers

Cada intento de invocación experimental se registra para auditoría técnica y fatiga cognitiva:

-   **`experimental_skill_invoked`**: Éxito en la ejecución de la habilidad.
-   **`experimental_skill_failed`**: Fallo durante el runtime de la habilidad (no afecta al núcleo).
-   **`experimental_skill_blocked_by_iafa`**: IAFA bloqueó la ejecución por razones de seguridad o tensión.

## Rollback

Si una habilidad experimental causa inestabilidad, se puede:
1.  Eliminarla de la `ALLOWLIST`.
2.  Desactivar `EXPERIMENTAL_SKILLS_ENABLED`.
3.  El sistema volverá automáticamente al modo de respuesta básica o fallback proactivo (Spark).

## Próximos Pasos

Una habilidad que demuestre estabilidad y valor en modo experimental puede ser promovida a **Stable**, donde la allowlist ya no será obligatoria para su ejecución.
