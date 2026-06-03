import os
import hashlib
import re
from typing import Any, Optional

def hash_identifier(value: str, length: int = 12) -> str:
    """Genera un hash corto para identificar un valor sin exponerlo."""
    if not value:
        return "none"
    return hashlib.sha256(value.encode("utf-8")).hexdigest()[:length]

def sanitize_path_for_logs(path: str) -> str:
    """Reemplaza una ruta absoluta por una referencia basada en hash."""
    if not path:
        return "unknown_path"
    filename = os.path.basename(path)
    file_hash = hash_identifier(path)
    return f"file_ref:{file_hash}:{filename}"

def redact_local_paths(text: str) -> str:
    """Busca y ofusca patrones que parezcan rutas locales o nombres de usuario."""
    if not text:
        return ""
    
    # Redactar /home/usuario
    home_pattern = r"/home/[a-zA-Z0-9._-]+"
    text = re.sub(home_pattern, "/home/[REDACTED]", text)
    
    # Redactar C:\Users\usuario (por si acaso)
    win_pattern = r"[a-zA-Z]:\\Users\\[a-zA-Z0-9._-]+"
    text = re.sub(win_pattern, "[REDACTED_WIN_PATH]", text)
    
    return text

def sanitize_exception_message(exc: Exception) -> str:
    """Extrae el mensaje de una excepción y redacta información sensible."""
    msg = str(exc)
    return redact_local_paths(msg)
