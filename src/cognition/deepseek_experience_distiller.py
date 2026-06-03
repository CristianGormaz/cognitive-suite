from __future__ import annotations

import json
import logging
import os
import time
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional

logger = logging.getLogger("DeepseekDistiller")

DISTILLED_LEDGER_PATH = "assets/memory/distilled_reasoning_ledger.jsonl"

@dataclass(frozen=True)
class DistilledReasoningPattern:
    pattern_id: str
    pattern_name: str
    source_refs: List[str]
    trigger_signature: str
    local_rule_summary: str
    recommended_action: str
    confidence: float
    usefulness_score: float
    risk_score: float
    target_module: str
    can_become_local_heuristic: bool = True
    requires_human_review: bool = True
    timestamp: float = field(default_factory=time.time)
    schema_version: str = "distilled-reasoning.v1"

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

class DeepseekExperienceDistiller:
    """
    Destila experiencia técnica acumulada a partir de los ledgers de Greys-v3.
    Convierte análisis profundos del LLM en patrones de decisión locales (Reflejos).
    """

    def __init__(self, memory_dir: str = "assets/memory"):
        self.memory_dir = Path(memory_dir)
        self.ledger_path = self.memory_dir / "distilled_reasoning_ledger.jsonl"

    def run_distillation_session(self) -> List[DistilledReasoningPattern]:
        """Ejecuta una sesión completa de destilación analizando múltiples fuentes."""
        logger.info("Iniciando sesión de destilación de experiencia...")
        patterns = []
        
        # 1. Destilar desde fallos LLM (Reflejo de evitación)
        patterns.extend(self.distill_from_llm_failures())
        
        # 2. Destilar desde principios semánticos (Reflejo de gobernanza)
        patterns.extend(self.distill_from_semantic_principles())
        
        # 3. Destilar desde diarios de sueño (Reflejo evolutivo)
        patterns.extend(self.distill_from_dream_journal())

        # Persistir hallazgos
        for p in patterns:
            self.persist_distilled_pattern(p)
            
        return patterns

    def distill_from_llm_failures(self) -> List[DistilledReasoningPattern]:
        """Identifica patrones de fallo recurrentes para proponer bypass local."""
        health_path = self.memory_dir / "llm_health_ledger.jsonl"
        if not health_path.exists(): return []
        
        patterns = []
        timeouts = 0
        
        try:
            with open(health_path, "r", encoding="utf-8") as f:
                for line in f:
                    if not line.strip(): continue
                    entry = json.loads(line)
                    if entry.get("status") == "llm_timeout":
                        timeouts += 1
            
            if timeouts > 10:
                patterns.append(DistilledReasoningPattern(
                    pattern_id=f"dist_{os.urandom(4).hex()}",
                    pattern_name="avoid_llm_for_known_intents",
                    source_refs=["llm_health_ledger"],
                    trigger_signature="high_timeout_frequency",
                    local_rule_summary="Ante alta latencia recurrente, priorizar ruteo determinístico para intenciones comunes.",
                    recommended_action="enable_strict_local_routing",
                    confidence=0.9,
                    usefulness_score=0.95,
                    risk_score=0.1,
                    target_module="LocalIntentRouter"
                ))
        except Exception as exc:
            logger.error(f"Error destilando fallos LLM: {exc}")
            
        return patterns

    def distill_from_semantic_principles(self) -> List[DistilledReasoningPattern]:
        """Convierte sabiduría semántica en reglas operativas."""
        principle_path = self.memory_dir / "semantic_principle_ledger.jsonl"
        if not principle_path.exists(): return []
        
        patterns = []
        try:
            with open(principle_path, "r", encoding="utf-8") as f:
                for line in f:
                    if not line.strip(): continue
                    p = json.loads(line)
                    if p.get("principle_name") == "cuarentena_como_aprendizaje":
                        patterns.append(DistilledReasoningPattern(
                            pattern_id=f"dist_{os.urandom(4).hex()}",
                            pattern_name="quarantine_as_training_sample",
                            source_refs=[p["event_id"]],
                            trigger_signature="level_3_quarantine_event",
                            local_rule_summary="Usar muestras de código inseguro para refinar filtros estáticos en el Sandbox.",
                            recommended_action="extract_unsafe_ast_patterns",
                            confidence=0.8,
                            usefulness_score=0.9,
                            risk_score=0.2,
                            target_module="ImmuneQuarantinePolicy"
                        ))
        except Exception: pass
        return patterns

    def distill_from_dream_journal(self) -> List[DistilledReasoningPattern]:
        """Extrae patrones detectados por DeepSeek durante el Modo Sueño."""
        journal_path = self.memory_dir / "dream_journal.jsonl"
        if not journal_path.exists(): return []
        
        patterns = []
        try:
            with open(journal_path, "r", encoding="utf-8") as f:
                for line in f:
                    if not line.strip(): continue
                    entry = json.loads(line)
                    reflection = entry.get("llm_reflection")
                    if not reflection: continue
                    
                    obs = reflection.get("observed_patterns", [])
                    if any("math:solve_integral" in o for o in obs):
                        patterns.append(DistilledReasoningPattern(
                            pattern_id=f"dist_{os.urandom(4).hex()}",
                            pattern_name="dependency_debt_math",
                            source_refs=[entry["event_id"]],
                            trigger_signature="math_failure_recurrence",
                            local_rule_summary="La resolución de integrales falla por falta de sympy. No intentar llamar LLM para esto hasta instalar dependencia.",
                            recommended_action="block_unsupported_math",
                            confidence=0.95,
                            usefulness_score=0.8,
                            risk_score=0.05,
                            target_module="LocalIntentRouter"
                        ))
        except Exception: pass
        return patterns

    def persist_distilled_pattern(self, pattern: DistilledReasoningPattern):
        """Guarda el patrón en el ledger de destilación."""
        try:
            self.memory_dir.mkdir(parents=True, exist_ok=True)
            with open(self.ledger_path, "a", encoding="utf-8") as f:
                f.write(json.dumps(pattern.to_dict()) + "\n")
        except Exception as exc:
            logger.error(f"Error persistiendo patrón destilado: {exc}")

    def load_distilled_patterns(self, limit: int = 20) -> List[DistilledReasoningPattern]:
        """Carga patrones destilados recientes."""
        patterns = []
        if not self.ledger_path.exists(): return patterns
        try:
            with open(self.ledger_path, "r", encoding="utf-8") as f:
                lines = f.readlines()
                for line in lines[-limit:]:
                    if line.strip():
                        data = json.loads(line)
                        patterns.append(DistilledReasoningPattern(**data))
        except Exception: pass
        return patterns
