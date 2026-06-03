"""
Consultor de Tiempo Local v0 (Re-implementado para Greys-v3)

Este módulo proporciona capacidades de consulta temporal básica sin dependencias externas.
Generado proactivamente como candidato en cuarentena.
"""
from __future__ import annotations
from datetime import datetime
from typing import Any, Dict, Optional

def _generated_skill_impl(context: Dict[str, Any]) -> Dict[str, Any]:
    """
    Punto de entrada estándar para habilidades de Greys-v3.
    """
    input_text = context.get("task", {}).get("payload_preview", "").lower()
    return handle_time_query(input_text)

def handle_time_query(text: str, now: Optional[datetime] = None) -> Dict[str, Any]:
    """
    Lógica principal de la consulta temporal.
    """
    current_now = now or datetime.now()
    
    # Heurística de detección de intención dentro de la skill
    is_time = any(w in text for w in ["hora", "tiempo", "qué hora", "que hora"])
    is_date = any(w in text for w in ["fecha", "día", "dia", "calendario", "qué día", "que dia"])
    is_weather = any(w in text for w in ["clima", "pronóstico", "pronostico", "temperatura", "sol", "lluvia", "llover", "nieve", "viento"])

    if is_weather:
        return {
            "status": "unsupported",
            "capability": "time:local_query",
            "response_text": "Puedo responder fecha u hora local, pero no clima ni pronósticos online en esta versión.",
            "confidence": 0.9
        }

    response_text = ""
    
    if is_time:
        response_text = f"La hora actual es {current_now.strftime('%H:%M:%S')}."
    elif is_date:
        # Formato: lunes, 31 de mayo de 2026
        # Nota: strftime %A depende del locale, aquí usamos algo genérico
        response_text = f"Hoy es {current_now.strftime('%d/%m/%Y')}."
    else:
        # Saludo temporal
        hour = current_now.hour
        if 5 <= hour < 12: greeting = "Buenos días"
        elif 12 <= hour < 20: greeting = "Buenas tardes"
        else: greeting = "Buenas noches"
        response_text = f"{greeting}. Estoy operativo en modo temporal local."

    return {
        "status": "ok",
        "capability": "time:local_query",
        "response_text": response_text,
        "iso_datetime": current_now.isoformat(),
        "confidence": 0.8 if (is_time or is_date) else 0.5
    }
