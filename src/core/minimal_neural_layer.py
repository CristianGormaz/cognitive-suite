from __future__ import annotations

import logging
import json
from pathlib import Path
from typing import Any, Dict, List, Optional

logger = logging.getLogger("MinimalNeuralLayer")

class MinimalNeuralLayer:
    """
    Capa de razonamiento simbólico v0. 
    Funciona como una memoria de patrones destilados (Reflejos).
    No entrena pesos en esta versión; utiliza coincidencia de firmas semánticas.
    """

    def __init__(self, memory_dir: str = "assets/memory"):
        self.memory_dir = Path(memory_dir)
        self.ledger_path = self.memory_dir / "distilled_reasoning_ledger.jsonl"
        self.patterns: List[Dict[str, Any]] = []
        self.load_patterns()

    def load_patterns(self):
        """Carga los patrones destilados desde el ledger."""
        self.patterns = []
        if not self.ledger_path.exists(): return
        try:
            with open(self.ledger_path, "r", encoding="utf-8") as f:
                for line in f:
                    if line.strip():
                        self.patterns.append(json.loads(line))
            logger.info(f"Cargados {len(self.patterns)} patrones en la capa neural mínima.")
        except Exception as exc:
            logger.error(f"Error cargando patrones neurales: {exc}")

    def match_pattern(self, context: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Busca un patrón que coincida con el contexto actual.
        Prioridad: trigger_signature > intent_category > action.
        """
        signature = context.get("trigger_signature")
        intent = context.get("intent_category")
        action = context.get("action")
        
        candidates = []
        for p in self.patterns:
            score = 0.0
            if signature and p.get("trigger_signature") == signature:
                score += 0.8
            if intent and p.get("decision_category") == intent:
                score += 0.4
            if action and p.get("recommended_action") == action:
                score += 0.2
            
            if score > 0:
                # Ajustar por confianza del patrón original
                final_confidence = min(1.0, score * p.get("confidence", 1.0))
                candidates.append((final_confidence, p))
        
        if not candidates: return None
        
        # Devolver el de mayor confianza
        candidates.sort(key=lambda x: x[0], reverse=True)
        best_conf, best_p = candidates[0]
        
        # Inyectar confianza calculada en el resultado temporal
        result = dict(best_p)
        result["match_confidence"] = round(best_conf, 2)
        return result

    def suggest_reflex(self, context: Dict[str, Any]) -> Optional[str]:
        """Sugiere una acción local basada en la memoria de patrones."""
        pattern = self.match_pattern(context)
        if pattern and pattern.get("match_confidence", 0.0) > 0.5:
            logger.info(f"Patrón neural detectado: {pattern['pattern_name']} (Confianza match: {pattern['match_confidence']})")
            return pattern.get("recommended_action")
        return None

    def explain_match(self, pattern_name: str) -> str:
        """Explica por qué se activó un patrón."""
        for p in self.patterns:
            if p.get("pattern_name") == pattern_name:
                return f"Reflejo activado por: {p.get('local_rule_summary')} (Fuente: {p.get('source_refs')})"
        return "Patrón desconocido."
