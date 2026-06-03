from __future__ import annotations

import logging
from typing import Any, Dict, Optional

logger = logging.getLogger(__name__)

from core.local_narrative_layer import LocalNarrativeLayer

class ResponseManager:
    """
    Gestiona las respuestas básicas de Greys-v3 para el usuario.
    v0.3: Integración con LocalNarrativeLayer para traducción de señales.
    """

    def __init__(self):
        self.narrative = LocalNarrativeLayer()
        self.default_responses = {
            "chat": {
                "hola": "Hola, soy Greys-v3. Estoy operativo en modo texto.",
                "quien eres": "Soy Greys-v3, una entidad cognitiva en desarrollo enfocada en la autonomía segura.",
                "¿quién eres?": "Soy Greys-v3, una entidad cognitiva en desarrollo enfocada en la autonomía segura.",
                "status": "Sistemas operativos. Guardian metabólico activo. Sin estrés detectado.",
                "estado": "Sistemas operativos. Guardian metabólico activo. Sin estrés detectado.",
                "ayuda": "Puedo conversar contigo en modo texto, clasificar tus intenciones y auto-protegerme si el sistema está bajo estrés.",
                "que puedes hacer": "Puedo clasificar entradas, pasar por IAFA para validar seguridad y responder de forma básica. Algunas funciones avanzadas como Spark están en fase de prueba.",
                "escuchas": "Sí, te leo perfectamente en modo texto.",
                "activo": "Estoy activo y escuchando. ¿En qué puedo ayudarte?",
            }
        }

    def generate_response(
        self, 
        intent_category: str, 
        input_text: str,
        execution_payload: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Genera una respuesta basada en la intención y el texto de entrada.
        """
        # 0. Prioridad: Decisiones locales vía Narrativa Local
        if intent_category == "pdf_ingestion" and execution_payload:
            m_key = execution_payload.get("message_key")
            if m_key:
                # Mapear message_key a signal_type de narrativa si es necesario
                sig_map = {
                    "pdf_reader_available_but_disabled": "pdf_disabled_by_configuration",
                    "pdf_reader_not_allowlisted": "pdf_reader_not_allowlisted",
                    "host_under_stress": "host_stress_block"
                }
                sig_type = sig_map.get(m_key, m_key)
                narrative_res = self.narrative.explain_signal(sig_type)
                return self.narrative.render_user_message(narrative_res)

        intent_responses = self.default_responses.get(intent_category, {})
        
        # 1. Prioridad: message_key en payload para otras categorías
        if execution_payload and "message_key" in execution_payload:
            m_key = execution_payload["message_key"]
            if m_key in intent_responses:
                return intent_responses[m_key]

        # Limpiamos caracteres comunes de puntuación
        clean_input = input_text.lower().strip()
        for char in "¿?!!¡,.":
            clean_input = clean_input.replace(char, "")
        clean_input = clean_input.strip()
        
        # 2. Coincidencia exacta
        if clean_input in intent_responses:
            return intent_responses[clean_input]
            
        # 3. Búsqueda por palabras clave para "chat"
        if intent_category == "chat":
            if any(w in clean_input for w in ["escuchas", "oyes", "lee"]):
                return intent_responses["escuchas"]
            if any(w in clean_input for w in ["quien eres", "quién eres", "eres"]):
                return intent_responses["quien eres"]
            if any(w in clean_input for w in ["hacer", "puedes", "capacidades"]):
                return intent_responses["que puedes hacer"]
            if any(w in clean_input for w in ["ayuda", "help", "comandos"]):
                return intent_responses["ayuda"]
            if any(w in clean_input for w in ["estado", "status", "vitals"]):
                return intent_responses["status"]
            if any(w in clean_input for w in ["activo", "encendido", "on"]):
                return intent_responses["activo"]
            if "hola" in clean_input:
                return intent_responses["hola"]

            return "Entendí tu mensaje, pero aún estoy en modo respuesta básica."
            
        return f"Entendido ({intent_category}). Procesando..."
