from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional

logger = logging.getLogger("DreamFocusValidator")

REQUIRED_FIELDS = {"focus_id", "priority_topics", "forbidden_actions"}

class DreamFocusValidator:
    """
    Valida archivos de foco para Dream Mode.
    """

    def validate_file(self, file_path: str | Path) -> bool:
        try:
            path = Path(file_path)
            if not path.exists():
                return False
            
            content = path.read_text(encoding="utf-8")
            return self.validate_json(content)
        except Exception as exc:
            logger.warning(f"Error al validar archivo de foco {file_path}: {exc}")
            return False

    def validate_json(self, content: str) -> bool:
        try:
            data = json.loads(content)
            if not isinstance(data, dict):
                logger.warning("Focus data must be a JSON object.")
                return False
            
            # Verificar campos requeridos
            missing = REQUIRED_FIELDS - set(data.keys())
            if missing:
                logger.warning(f"Focus data missing required fields: {missing}")
                return False
            
            # Verificar que forbidden_actions no esté vacío
            if not data.get("forbidden_actions"):
                logger.warning("Focus data 'forbidden_actions' cannot be empty.")
                return False
                
            return True
        except json.JSONDecodeError as exc:
            logger.warning(f"Invalid JSON in focus data: {exc}")
            return False
        except Exception as exc:
            logger.warning(f"Unexpected error validating focus JSON: {exc}")
            return False

    def get_fallback_focus(self) -> Dict[str, Any]:
        return {
            "focus_id": "fallback_general",
            "priority_topics": ["general_evolution"],
            "forbidden_actions": ["modify_code", "execute_genesis"],
            "mode": "safe"
        }
