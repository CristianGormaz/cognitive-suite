# Frontera Pública / Privada de Greys-v3

Este documento define la política estricta de qué información pertenece al dominio público (repositorio GitHub) y qué información debe permanecer estrictamente en el entorno local (privado).

## 🟢 Dominio Público (Permitido en GitHub)
Los siguientes elementos conforman el "motor" o infraestructura cognitiva y son seguros para su publicación:

*   **Arquitectura General:** Código fuente en `src/`, estructura del proyecto y diseño de módulos.
*   **Mecanismos de Regulación:** Implementación del motor IAFA (Integrity, Autonomy, Friction, Alignment) y la `ImmuneQuarantinePolicy`.
*   **Fórmulas Conceptuales:** La matemática detrás del sistema, como el Índice de Separación Sana (ISS).
*   **Estructura de Cuarentena:** El concepto de los 3 niveles de cuarentena y el `SkillPromotionGate`.
*   **Mecanismos de Memoria:** La implementación de los ledgers (`SemanticTensionLedger`, `IngestionFailureLedger`, `LedgerCompactor`), pero **no** sus datos.
*   **Sandbox y Allowlist:** El código del `GenesisSandbox` y la lógica de la `GREYS_EXPERIMENTAL_SKILL_ALLOWLIST`.
*   **Tests y Documentación:** Pruebas unitarias/integración (con *fixtures* seguros) y documentación técnica arquitectónica (`docs/`).

## 🔴 Dominio Privado (Estrictamente Local)
Bajo ninguna circunstancia los siguientes elementos deben ser rastreados, versionados o subidos al repositorio público:

*   **Memoria Operativa (Ledgers Crudos y Compactos):** Todo el contenido de `assets/memory/`, incluyendo historiales de fallos, tensión semántica, auditorías IAFA y diarios de sueños.
*   **Cuarentena y Candidatos:** Archivos generados dinámicamente o aislados en `assets/quarantine/`.
*   **Entornos y Dependencias Locales:** El entorno virtual `.venv/`.
*   **Registros del Sistema:** Cualquier archivo en `logs/`.
*   **Backups:** Respaldos de código o memoria en `assets/backups/` o rutas externas.
*   **Datos de Usuario:** PDFs personales, documentos, muestras de voz, o cualquier archivo de entrada real.
*   **Prompts Completos y Respuestas Crudas:** Registros que contengan interacciones completas con el modelo LLM.
*   **Rutas Locales y Metadatos Sensibles:** Direcciones absolutas del sistema de archivos (ej. `/home/usuario/...`), que son mitigadas por el `PrivacySanitizer`.
*   **Secretos y Criptografía:** Archivos `.env`, claves HMAC reales, tokens de API o contraseñas.
*   **Muestras de Amenaza:** Payloads ofensivos detallados o patrones de ataque utilizados para entrenamiento inmunológico.
*   **Umbrales Defensivos Críticos:** Valores exactos de pesos IAFA o umbrales ISS si actúan como la única barrera de defensa activa. En la documentación pública, estos deben describirse de forma abstracta o como rangos recomendados, manteniendo los valores operativos en el entorno local.
*   **HMAC Secret Keys:** Las claves reales de firma de ledgers.

Esta frontera asegura que Greys-v3 pueda ser auditado y mejorado públicamente sin comprometer la privacidad o la seguridad del nodo de ejecución local.
