# Security Policy

> **Historical snapshot note**
>
> This repository is a public, sanitized snapshot from June 2026. It is not the current implementation mirror and this file must not be read as a promise of active security maintenance for the current private development line.

## Supported Versions

No active support matrix is asserted by this historical snapshot.

The previous statement that `main` and Greys-v3 `v3.x` were actively receiving security patches described the project at the time of the June 2026 snapshot and is no longer presented as a current support commitment.

## Reporting a Vulnerability

Do **not** publish vulnerability details, exploit steps, secrets, or attack vectors in a public GitHub Issue.

If you need to report a potential security problem and no private reporting channel is enabled for this repository, you may open a minimal public Issue requesting a private contact path. Do not include technical vulnerability details in that Issue.

## Historical operational security practices

The following practices are preserved from the June 2026 snapshot as historical project guidance:

1. **Datos Sensibles:** Nunca subas al repositorio tu directorio `assets/memory/`, `assets/quarantine/`, ni archivos de configuración locales como `.env`.
2. **Candidatos en Cuarentena:** El código en `assets/quarantine/genesis_candidates/` era tratado como no confiable y no debía ejecutarse manualmente fuera del ciclo de evaluación previsto.
3. **Dependencias:** Las dependencias externas debían pasar por revisión antes de añadirse a `requirements.txt`; la instalación automática de paquetes estaba desactivada por diseño.
4. **Habilidades Experimentales:** El directorio `src/skills/experimental/` requería una allowlist explícita para cargar código experimental en runtime.
5. **Promoción a Estable:** El directorio `src/skills/stable/` se trataba como núcleo operativo y cualquier promoción requería revisión humana y pruebas de integración.
