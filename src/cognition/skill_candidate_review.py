from __future__ import annotations

import hashlib
import json
import logging
import os
import time
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional

logger = logging.getLogger("SkillCandidateReview")

REVIEW_LEDGER_VERSION = "skill-review.v1"
DEFAULT_REVIEW_LEDGER_PATH = "assets/memory/skill_candidate_review_ledger.jsonl"
QUARANTINE_DIR = "assets/quarantine/genesis_candidates"

VALID_STATUSES = {
    "pending_review",
    "approved_for_future_promotion",
    "rejected_by_human",
    "needs_dependency",
    "unsafe_rejected",
    "needs_more_tests"
}

@dataclass(frozen=True)
class SkillCandidateSummary:
    candidate_id: str
    capability_signature: str
    code_sha256: str
    file_size: int
    created_at: float
    dangerous_calls_detected: List[str]
    current_status: str = "pending_review"

@dataclass(frozen=True)
class ReviewEvent:
    candidate_id: str
    capability_signature: str
    code_sha256: str
    status: str
    reason_summary: Optional[str]
    reviewer: str = "human"
    timestamp: float = field(default_factory=time.time)
    schema_version: str = REVIEW_LEDGER_VERSION

    def to_json(self) -> str:
        return json.dumps(asdict(self))

class SkillCandidateReview:
    """
    Gestiona la revisión humana de candidatos a habilidades en cuarentena.
    """

    def __init__(
        self, 
        quarantine_dir: str = QUARANTINE_DIR,
        ledger_path: str = DEFAULT_REVIEW_LEDGER_PATH
    ):
        self.quarantine_path = Path(quarantine_dir)
        self.ledger_path = Path(ledger_path)
        self._ensure_paths()

    def _ensure_ensure_paths(self):
        # typo in prompt, fixing to _ensure_paths
        pass

    def _ensure_paths(self):
        if not self.quarantine_path.exists():
            self.quarantine_path.mkdir(parents=True, exist_ok=True)
        if not self.ledger_path.parent.exists():
            self.ledger_path.parent.mkdir(parents=True, exist_ok=True)

    def list_candidates(self) -> List[SkillCandidateSummary]:
        """Lista todos los archivos .py en la carpeta de cuarentena."""
        summaries = []
        for file in self.quarantine_path.glob("*.py"):
            code = file.read_text(encoding="utf-8")
            sha256 = hashlib.sha256(code.encode("utf-8")).hexdigest()
            
            # Simple static check
            dangerous = []
            if "os." in code: dangerous.append("os")
            if "sys." in code: dangerous.append("sys")
            if "subprocess" in code: dangerous.append("subprocess")
            if "eval(" in code: dangerous.append("eval")
            if "exec(" in code: dangerous.append("exec")
            if "open(" in code: dangerous.append("open")
            
            # Extract capability signature from filename if possible
            # filename format: candidate_{safe_intent}_{hash}.py
            name_parts = file.stem.split("_")
            sig = "unknown"
            if len(name_parts) >= 2:
                sig = name_parts[1]
                if sig == "solve" and "integral" in name_parts:
                    sig = "math:solve_integral"

            summaries.append(SkillCandidateSummary(
                candidate_id=file.name,
                capability_signature=sig,
                code_sha256=sha256,
                file_size=file.stat().st_size,
                created_at=file.stat().st_mtime,
                dangerous_calls_detected=dangerous,
                current_status=self.get_candidate_status(file.name)
            ))
        return summaries

    def summarize_candidate(self, candidate_id: str) -> Dict[str, Any]:
        """Devuelve un resumen seguro de un candidato específico."""
        file = self.quarantine_path / candidate_id
        if not file.exists():
            raise FileNotFoundError(f"Candidate {candidate_id} not found")
            
        code = file.read_text(encoding="utf-8")
        sha256 = hashlib.sha256(code.encode("utf-8")).hexdigest()
        
        # Only show first and last few lines
        lines = code.splitlines()
        preview = lines[:5]
        if len(lines) > 10:
            preview.append("...")
            preview.extend(lines[-5:])
            
        return {
            "candidate_id": candidate_id,
            "sha256": sha256,
            "preview": "\n".join(preview),
            "status": self.get_candidate_status(candidate_id)
        }

    def get_candidate_status(self, candidate_id: str) -> str:
        """Obtiene el último estado registrado para un candidato."""
        history = self.load_review_history()
        relevant = [e for e in history if e.candidate_id == candidate_id]
        if not relevant:
            return "pending_review"
        return relevant[-1].status

    def mark_candidate_status(self, candidate_id: str, status: str, reason: Optional[str] = None):
        """Registra una decisión de revisión para un candidato."""
        if status not in VALID_STATUSES:
            raise ValueError(f"Invalid status: {status}. Valid: {VALID_STATUSES}")
            
        file = self.quarantine_path / candidate_id
        if not file.exists():
            raise FileNotFoundError(f"Candidate {candidate_id} not found")
            
        code = file.read_text(encoding="utf-8")
        sha256 = hashlib.sha256(code.encode("utf-8")).hexdigest()
        
        # Determine capability signature
        summaries = self.list_candidates()
        summary = next((s for s in summaries if s.candidate_id == candidate_id), None)
        sig = summary.capability_signature if summary else "unknown"

        event = ReviewEvent(
            candidate_id=candidate_id,
            capability_signature=sig,
            code_sha256=sha256,
            status=status,
            reason_summary=reason
        )
        
        try:
            with open(self.ledger_path, "a", encoding="utf-8") as f:
                f.write(event.to_json() + "\n")
        except Exception as exc:
            logger.error(f"Error writing to review ledger: {exc}")
            raise

    def load_review_history(self, limit: int = 100) -> List[ReviewEvent]:
        """Carga el historial de revisiones del ledger."""
        events = []
        if not self.ledger_path.exists():
            return events

        try:
            with open(self.ledger_path, "r", encoding="utf-8") as f:
                lines = f.readlines()
                for line in lines[-limit:]:
                    line = line.strip()
                    if not line: continue
                    try:
                        data = json.loads(line)
                        events.append(ReviewEvent(**data))
                    except Exception:
                        continue
        except Exception as exc:
            logger.error(f"Error reading review ledger: {exc}")
        return events
