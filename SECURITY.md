# Security Policy

> **Historical snapshot note**
>
> This repository is a public, sanitized snapshot from June 2026. It is not the current implementation mirror and this file must not be read as a promise of active security maintenance for the current private development line.

## Supported Versions

No active support matrix is asserted by this historical snapshot.

The June 2026 snapshot stated:

> Greys-v3 es un proyecto experimental. Actualmente solo la rama `main` recibe actualizaciones y parches de seguridad.
>
> | Version | Supported          |
> | ------- | ------------------ |
> | v3.x    | :white_check_mark: |
> | < v3.0  | :x:                |

That statement is preserved as historical record and is not a current support commitment.

## Reporting a Vulnerability

Do **not** publish vulnerability details, exploit steps, secrets, or attack vectors in a public GitHub Issue.

If you need to report a potential security problem and no private reporting channel is enabled for this repository, you may open a minimal public Issue requesting a private contact path. Do not include technical vulnerability details in that Issue.

The June snapshot contained a different public-Issue reporting instruction. That historical instruction is superseded by the policy above and is not reproduced here as an actionable reporting path.

## Prácticas de Seguridad Operativa del snapshot de junio de 2026

The following historical guidance is preserved verbatim:

1. **Datos Sensibles:** Nunca subas al repositorio tu directorio `assets/memory/`, `assets/quarantine/`, ni archivos de configuración locales como `.env`.
2. **Candidatos en Cuarentena:** El código en `assets/quarantine/genesis_candidates/` es, por definición, no confiable. No lo ejecutes manualmente fuera del ciclo de evaluación del `SkillPromotionGate` y `GenesisSandbox`.
3. **Dependencias:** Ninguna dependencia externa debe añadirse a `requirements.txt` sin haber pasado por el `DependencyReviewLedger`. La instalación automática de paquetes está desactivada por diseño.
4. **Habilidades Experimentales:** El directorio `src/skills/experimental/` requiere el uso explícito de una `GREYS_EXPERIMENTAL_SKILL_ALLOWLIST` para cargar cualquier código en runtime.
5. **Promoción a Estable:** El directorio `src/skills/stable/` es el núcleo operativo. No se debe mover código a esta carpeta sin una revisión humana exhaustiva y pruebas de integración superadas en la fase experimental.
