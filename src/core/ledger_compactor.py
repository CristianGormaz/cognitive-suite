from __future__ import annotations

import json
import logging
import os
import time
from collections import Counter
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional

logger = logging.getLogger("LedgerCompactor")

COMPACT_LEDGER_VERSION = "ledger-compact-summary.v1"

@dataclass
class CompactSummary:
    ledger_name: str
    generated_at: float
    original_event_count: int
    archived_event_count: int
    retained_event_count: int
    event_type_counts: Dict[str, int] = field(default_factory=dict)
    failure_type_counts: Dict[str, int] = field(default_factory=dict)
    status_counts: Dict[str, int] = field(default_factory=dict)
    top_proposal_signatures: List[tuple] = field(default_factory=list)
    top_missing_capabilities: List[tuple] = field(default_factory=list)
    schema_version: str = COMPACT_LEDGER_VERSION

    def to_json(self) -> str:
        return json.dumps(asdict(self), ensure_ascii=False)

class LedgerCompactor:
    """
    Gestiona la higiene y compactación de los ledgers de memoria de Greys-v3.
    """

    def __init__(self, memory_dir: str = "assets/memory"):
        self.memory_dir = Path(memory_dir)
        self.archive_dir = self.memory_dir / "archive"
        self.compact_dir = self.memory_dir / "compact"

    def inventory_ledgers(self) -> List[Path]:
        return sorted(list(self.memory_dir.glob("*.jsonl")))

    def run_compaction(self, keep_recent: int = 200, dry_run: bool = True) -> Dict[str, Any]:
        """Ejecuta el ciclo de compactación para todos los ledgers."""
        results = {}
        ledgers = self.inventory_ledgers()
        
        timestamp_str = time.strftime("%Y%m%d")
        daily_archive = self.archive_dir / timestamp_str
        
        if not dry_run:
            daily_archive.mkdir(parents=True, exist_ok=True)
            self.compact_dir.mkdir(parents=True, exist_ok=True)

        for ledger_path in ledgers:
            results[ledger_path.name] = self.compact_jsonl_ledger(
                ledger_path, daily_archive, keep_recent, dry_run
            )
            
        return results

    def compact_jsonl_ledger(self, path: Path, archive_dir: Path, keep_recent: int, dry_run: bool) -> Dict[str, Any]:
        """Compacta un archivo individual."""
        events = []
        bad_lines = 0
        
        if not path.exists():
            return {"status": "error", "reason": "not_found"}

        try:
            with open(path, "r", encoding="utf-8", errors="ignore") as f:
                for line in f:
                    if not line.strip(): continue
                    try:
                        events.append(json.loads(line))
                    except Exception:
                        bad_lines += 1
        except Exception as e:
            return {"status": "error", "reason": str(e)}

        total_count = len(events)
        if total_count <= keep_recent:
            return {"status": "skipped", "reason": "below_threshold", "count": total_count}

        archived_count = total_count - keep_recent
        to_archive = events[:archived_count]
        retained = events[archived_count:]

        # Generar resumen
        summary = self.summarize_events(path.name, to_archive, archived_count, len(retained))

        if not dry_run:
            # 1. Guardar archivo
            archive_path = archive_dir / f"{path.stem}_{int(time.time())}.jsonl"
            with open(archive_path, "w", encoding="utf-8") as f:
                for ev in to_archive:
                    f.write(json.dumps(ev) + "\n")
            
            # 2. Guardar compacto
            compact_path = self.compact_dir / f"{path.stem}_summary.jsonl"
            with open(compact_path, "a", encoding="utf-8") as f:
                f.write(summary.to_json() + "\n")
                
            # 3. Sobrescribir original con los retenidos
            with open(path, "w", encoding="utf-8") as f:
                for ev in retained:
                    f.write(json.dumps(ev) + "\n")

        return {
            "status": "compacted" if not dry_run else "dry_run_ready",
            "total": total_count,
            "archived": archived_count,
            "retained": len(retained),
            "bad_lines": bad_lines
        }

    def summarize_events(self, ledger_name: str, events: List[Dict[str, Any]], archived: int, retained: int) -> CompactSummary:
        event_types = Counter()
        failure_types = Counter()
        statuses = Counter()
        signatures = Counter()
        missing = Counter()

        for e in events:
            if e.get("event_type"): event_types[e.get("event_type")] += 1
            if e.get("failure_type"): failure_types[e.get("failure_type")] += 1
            if e.get("status"): statuses[e.get("status")] += 1
            if e.get("proposal_signature"): signatures[e.get("proposal_signature")] += 1
            if e.get("missing_capability_signature"): missing[e.get("missing_capability_signature")] += 1

        return CompactSummary(
            ledger_name=ledger_name,
            generated_at=time.time(),
            original_event_count=archived + retained,
            archived_event_count=archived,
            retained_event_count=retained,
            event_type_counts=dict(event_types.most_common(10)),
            failure_type_counts=dict(failure_types.most_common(10)),
            status_counts=dict(statuses.most_common(10)),
            top_proposal_signatures=signatures.most_common(5),
            top_missing_capabilities=missing.most_common(5)
        )

    def load_compact_summaries(self, ledger_name: str) -> List[Dict[str, Any]]:
        """Carga resúmenes compactos para un ledger específico."""
        compact_path = self.compact_dir / f"{Path(ledger_name).stem}_summary.jsonl"
        summaries = []
        if not compact_path.exists():
            return summaries
            
        try:
            with open(compact_path, "r", encoding="utf-8") as f:
                for line in f:
                    if line.strip():
                        summaries.append(json.loads(line))
        except Exception as e:
            logger.error(f"Error loading compact summaries for {ledger_name}: {e}")
        return summaries
