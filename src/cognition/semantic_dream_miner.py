from __future__ import annotations

import json
import logging
import os
import time
import hashlib
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional

logger = logging.getLogger("SemanticDreamMiner")

SEMANTIC_LEDGER_VERSION = "semantic-principle.v1"
DEFAULT_SEMANTIC_LEDGER_PATH = "assets/memory/semantic_principle_ledger.jsonl"

@dataclass(frozen=True)
class SemanticPrincipleRecord:
    event_id: str
    timestamp: float
    principle_name: str
    context_dimension: str # defensa, resiliencia, privacidad, eficiencia, etc.
    interpretation_summary: str
    source_evidence_refs: List[str]
    related_modules: List[str]
    confidence: float
    novelty_score: float
    usefulness_score: float
    risk_of_overinterpretation: float
    suggested_application: str
    requires_human_review: bool = True
    schema_version: str = SEMANTIC_LEDGER_VERSION

    def to_json(self) -> str:
        return json.dumps(asdict(self), ensure_ascii=False)

class SemanticDreamMiner:
    """
    Motor de minería semántica para Greys-v3.
    Transforma eventos técnicos en principios operativos y dimensiones de contexto.
    """

    def __init__(
        self,
        ledger_path: str = DEFAULT_SEMANTIC_LEDGER_PATH,
        llm_enabled: bool = False
    ):
        self.ledger_path = Path(ledger_path)
        self.llm_enabled = llm_enabled
        self._ensure_dir()

    def _ensure_dir(self):
        if not self.ledger_path.parent.exists():
            self.ledger_path.parent.mkdir(parents=True, exist_ok=True)

    def run_semantic_mining_session(self, 
        recent_failures: List[Any], 
        recent_tension: List[Any], 
        immune_evals: List[Any]
    ) -> List[SemanticPrincipleRecord]:
        """
        Ejecuta una sesión de minería basada en heurísticas locales.
        """
        principles = []
        
        # 1. Detectar principios de Defensa (Corte Sano)
        immune_principles = self._mine_from_immune_evals(recent_failures, immune_evals)
        principles.extend(immune_principles)
        
        # 2. Detectar principios de Resiliencia (Degradación local)
        resilience_principles = self._mine_from_failures(recent_failures)
        principles.extend(resilience_principles)

        # 3. Detectar principios de Autorregulación (Alarma vs Insight)
        signal_principles = self._mine_from_signals(recent_failures, immune_evals)
        principles.extend(signal_principles)
        
        # Filtrar duplicados y rumiación
        unique_principles = self._suppress_redundant_principles(principles)
        
        # Persistir
        for p in unique_principles:
            self.persist_principle(p)
            
        return unique_principles

    def _mine_from_immune_evals(self, failures: List[Any], evals: List[Any]) -> List[SemanticPrincipleRecord]:
        found = []
        # Buscar evaluaciones de nivel 3
        high_risk_evals = [e for e in evals if e.get("recommended_quarantine_level", 0) >= 3]
        
        if high_risk_evals:
            refs = [e.get("item_id") for e in high_risk_evals]
            found.append(SemanticPrincipleRecord(
                event_id=f"sem_{os.urandom(4).hex()}",
                timestamp=time.time(),
                principle_name="cuarentena_como_aprendizaje",
                context_dimension="defensa",
                interpretation_summary="El sistema reconoce que los elementos en cuarentena nivel 3 no son solo fallos, sino muestras de entrenamiento inmunológico.",
                source_evidence_refs=refs,
                related_modules=["immune_quarantine_policy"],
                confidence=0.8,
                novelty_score=1.0, # Placeholder
                usefulness_score=0.9,
                risk_of_overinterpretation=0.2,
                suggested_application="Usar candidatos nivel 3 para generar patrones de bloqueo proactivo."
            ))
        return found

    def _mine_from_failures(self, failures: List[Any]) -> List[SemanticPrincipleRecord]:
        found = []
        # Buscar racha de timeouts o errores LLM seguidos de éxito local
        llm_fails = [f for f in failures if "llm" in getattr(f, "failure_type", "")]
        
        if len(llm_fails) > 5:
            found.append(SemanticPrincipleRecord(
                event_id=f"sem_{os.urandom(4).hex()}",
                timestamp=time.time(),
                principle_name="degradacion_local_como_resiliencia",
                context_dimension="resiliencia",
                interpretation_summary="El sistema identifica que la estabilidad depende de la capacidad de operar en modo local-only ante la latencia del canal externo.",
                source_evidence_refs=["llm_health_ledger"],
                related_modules=["iafa_transceiver", "response_manager"],
                confidence=0.85,
                novelty_score=0.9,
                usefulness_score=0.95,
                risk_of_overinterpretation=0.1,
                suggested_application="Priorizar el desarrollo de heurísticas locales para intenciones críticas."
            ))
        return found

    def _mine_from_signals(self, failures: List[Any], evals: List[Any]) -> List[SemanticPrincipleRecord]:
        found = []
        # Buscar evidencia de alarmas intensas
        unsafe_sigs = [e for e in evals if e.get("recommended_quarantine_level", 0) >= 3]
        llm_fails = [f for f in failures if "llm" in getattr(f, "failure_type", "")]
        
        if unsafe_sigs or len(llm_fails) > 10:
            found.append(SemanticPrincipleRecord(
                event_id=f"sem_{os.urandom(4).hex()}",
                timestamp=time.time(),
                principle_name="alarma_como_senal_no_como_orden",
                context_dimension="autorregulacion",
                interpretation_summary="Una alerta intensa no debe convertirse automáticamente en acción; debe pasar por contención, traducción y evaluación.",
                source_evidence_refs=["ingestion_failure_ledger", "llm_health_ledger"],
                related_modules=["intrusive_signal_policy", "immune_quarantine_policy"],
                confidence=0.9,
                novelty_score=0.95,
                usefulness_score=0.95,
                risk_of_overinterpretation=0.1,
                suggested_application="Usar IntrusiveSignalPolicy para traducir fallos de canal externo y código inseguro en mejoras de ruteo local."
            ))
        return found

    def _suppress_redundant_principles(self, new_principles: List[SemanticPrincipleRecord]) -> List[SemanticPrincipleRecord]:
        """Evita repetir el mismo principio si ya existe en el histórico reciente."""
        existing = self.load_historical_principles(limit=50)
        existing_names = {p.principle_name for p in existing}
        
        # Política anti-rumiación: solo permitir si es nuevo o si ha pasado mucho tiempo (aquí simplificamos a novedad de nombre)
        return [p for p in new_principles if p.principle_name not in existing_names]

    def load_historical_principles(self, limit: int = 100) -> List[SemanticPrincipleRecord]:
        records = []
        if not self.ledger_path.exists():
            return records
        try:
            with open(self.ledger_path, "r", encoding="utf-8") as f:
                lines = f.readlines()
                for line in lines[-limit:]:
                    if line.strip():
                        records.append(SemanticPrincipleRecord(**json.loads(line)))
        except Exception: pass
        return records

    def persist_principle(self, record: SemanticPrincipleRecord):
        try:
            with open(self.ledger_path, "a", encoding="utf-8") as f:
                f.write(record.to_json() + "\n")
        except Exception as exc:
            logger.error(f"Error guardando principio semántico: {exc}")
