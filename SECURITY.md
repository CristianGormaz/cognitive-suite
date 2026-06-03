# Security Policy

## Supported Versions

Greys-v3 es un proyecto experimental. Actualmente solo la rama `main` recibe actualizaciones y parches de seguridad.

| Version | Supported          |
| ------- | ------------------ |
| v3.x    | :white_check_mark: |
| < v3.0  | :x:                |

## Reporting a Vulnerability

Si descubres un problema de seguridad en la arquitectura base, por favor abre un Issue detallando el vector de ataque teórico. Dado que Greys-v3 es de uso estrictamente local, las vulnerabilidades suelen implicar riesgos de escape del sandbox o fugas de metadatos a logs.

## Prácticas de Seguridad Operativa (Usuario)

1. **Datos Sensibles:** Nunca subas al repositorio tu directorio `assets/memory/`, `assets/quarantine/`, ni archivos de configuración locales como `.env`.
2. **Candidatos en Cuarentena:** El código en `assets/quarantine/genesis_candidates/` es, por definición, no confiable. No lo ejecutes manualmente fuera del ciclo de evaluación del `SkillPromotionGate` y `GenesisSandbox`.
3. **Dependencias:** Ninguna dependencia externa debe añadirse a `requirements.txt` sin haber pasado por el `DependencyReviewLedger`. La instalación automática de paquetes está desactivada por diseño.
4. **Habilidades Experimentales:** El directorio `src/skills/experimental/` requiere el uso explícito de una `GREYS_EXPERIMENTAL_SKILL_ALLOWLIST` para cargar cualquier código en runtime.
5. **Promoción a Estable:** El directorio `src/skills/stable/` es el núcleo operativo. No se debe mover código a esta carpeta sin una revisión humana exhaustiva y pruebas de integración superadas en la fase experimental.
