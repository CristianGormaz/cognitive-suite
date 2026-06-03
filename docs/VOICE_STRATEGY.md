# Estrategia de Voz en Greys-v3

## Principios Fundamentales
1. **Independencia de OVOS**: Greys-v3 no es dependiente de OpenVoiceOS. OVOS es un sistema externo que puede coexistir pero no es obligatorio. Greys-v3 debe priorizar un modo de texto estable y ligero.
2. **Privacidad y Datos Sensibles**: La voz propia del usuario y sus grabaciones son datos biométricos altamente sensibles.
    - No deben subirse a repositorios públicos (GitHub).
    - No deben compartirse con servicios de terceros sin cifrado extremo y consentimiento.
3. **Ética de Clonación**: Cualquier entrenamiento de clon de voz privado debe requerir consentimiento explícito y documentado del dueño de la voz. No se permite el uso de voces de terceros sin autorización.
4. **Desarrollo por Fases**:
    - **Fase 1 (Actual)**: Estabilidad en modo texto, bajo consumo de recursos (CPU/RAM) y respuesta básica.
    - **Fase 2**: Evaluación de motores locales ligeros como Piper (TTS) y Vosk (STT) para una "voz estándar" de Greys.
    - **Fase 3**: Módulos experimentales de voz privada/clonada, siempre como opción opt-in y local.

## Estado de Carga Basal
Se ha detectado que procesos externos (como `ovos-dinkum-listener`) pueden consumir >100% de CPU. Greys-v3 debe ser capaz de operar de forma independiente incluso si estos servicios están activos, pero se recomienda detenerlos para mejorar la latencia de Ollama/DeepSeek.

## Recomendaciones Técnicas
- Mantener `GREYS_EVOLUTION_UI_ENABLED=0` y `GREYS_SPARK_ENABLED=0` en entornos con recursos limitados.
- Utilizar el `SystemStressGuard` para pausar inferencias si la carga del sistema (Load Avg) supera el umbral de seguridad.
