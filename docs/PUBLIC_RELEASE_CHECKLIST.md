# Checklist de Publicación Pública

Este documento sirve como guía final antes de cambiar la visibilidad del repositorio de **Cognitive Suite** a público.

## 1. Seguridad y Secretos
- [x] **Árbol Actual (HEAD)**: Verificado mediante `git grep` que no hay `/home/[USER]` ni otros paths locales absolutos en los archivos trackeados actualmente.
- [ ] **Historial de Git**: Se han detectado huellas en commits antiguos. Se requiere exportación saneada (ver [Auditoría de Historial](PUBLIC_HISTORY_AUDIT.md)).
- [x] **Secretos**: No hay API Keys, Tokens o Passwords en el código actual.
- [x] **Auditoría de IAFA**: El secreto por defecto en `src/main.py` (`secreto_seguro`) es para uso experimental local y se recomienda cambiarlo vía env var.
- [x] **Gitignore**: Confirmado que `.env`, `logs/`, y `assets/memory/` están bloqueados.

## 2. Privacidad de Datos
- [x] **Ledgers**: Los archivos `.jsonl` en `assets/memory/` no están en el historial de Git.
- [x] **Cuarentena**: Los candidatos en `assets/quarantine/` están ignorados.
- [x] **Logs**: La carpeta `logs/` está limpia de archivos trackeados.
- [x] **Fixtures**: Los archivos de prueba en `tests/fixtures/` son genéricos y no contienen datos de usuario reales.

## 3. Identidad y Rebranding
- [x] **README**: Refleja el nombre **Cognitive Suite**.
- [x] **Documentación**: El plan de rebranding y la identidad del proyecto están actualizados.
- [x] **Licencia**: Confirmar presencia de `LICENSE` (MIT).

## 4. Calidad Técnica
- [x] **Tests**: La suite completa (514+ tests) pasa al 100%.
- [x] **Imports**: Todos los módulos funcionan bajo `PYTHONPATH=src`.
- [x] **Documentación**: Los documentos en `docs/` son coherentes con la arquitectura actual.

## 5. Límites de Responsabilidad
- [x] **Aviso Experimental**: El README y los documentos de identidad advierten que el sistema es experimental.
- [x] **Human-in-the-loop**: Se recalca que el sistema no toma decisiones de modificación de código sin aprobación humana.

## Qué queda PRIVADO (Fuera del repositorio)
- Configuraciones `.env` personalizadas.
- Historiales de conversación reales (`dream_journal.jsonl`, etc).
- Archivos PDF o documentos del usuario procesados durante las pruebas.
- Pesos de modelos locales si se llegaran a persistir en binario.
