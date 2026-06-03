from __future__ import annotations

import asyncio
import hashlib
import hmac
import json
import os
import time
from dataclasses import asdict, dataclass, field
from typing import Any, Dict, Iterable, Optional

from core.task_envelope import TaskEnvelope


class IafaAuditError(ValueError):
    """Raised when an audit entry cannot be decoded or verified."""


@dataclass(frozen=True)
class IafaAuditRecord:
    timestamp: float
    action: str
    score: float
    threshold: float
    allowed: bool
    details: Dict[str, Any] = field(default_factory=dict)

    def to_payload(self) -> Dict[str, Any]:
        payload = asdict(self)
        payload["record_type"] = "iafa_decision"
        return payload


class IafaAuditor:
    """
    Append-only IAFA audit log.

    The auditor is infrastructure: it does not score, authorize, call models, or
    know how IAFA calculates decisions. It signs canonical JSON payloads and can
    verify them later.
    """

    def __init__(self, log_path: str = "assets/memory/iafa_audit.log", secret_key: str = "default_secret"):
        self.log_path = log_path
        self.secret_key = secret_key.encode("utf-8")

    @staticmethod
    def _canonical_json(payload: Dict[str, Any]) -> str:
        try:
            return json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False)
        except (TypeError, ValueError) as exc:
            raise IafaAuditError("audit payload must be strict JSON") from exc

    def _generate_signature(self, payload: Dict[str, Any]) -> str:
        entry_bytes = self._canonical_json(payload).encode("utf-8")
        return hmac.new(self.secret_key, entry_bytes, digestmod=hashlib.sha256).hexdigest()

    def build_entry(self, record: IafaAuditRecord) -> Dict[str, Any]:
        return self.build_entry_from_payload(record.to_payload())

    def build_entry_from_payload(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        return {
            "payload": payload,
            "signature": self._generate_signature(payload),
        }

    def encode_entry(self, record: IafaAuditRecord) -> str:
        return self._canonical_json(self.build_entry(record))

    def encode_payload(self, payload: Dict[str, Any]) -> str:
        return self._canonical_json(self.build_entry_from_payload(payload))

    def verify_entry(self, entry: Dict[str, Any]) -> bool:
        payload = entry.get("payload")
        signature = entry.get("signature")
        if not isinstance(payload, dict) or not isinstance(signature, str):
            return False
        return hmac.compare_digest(signature, self._generate_signature(payload))

    def decode_entry(self, line: str) -> Dict[str, Any]:
        try:
            entry = json.loads(line)
        except json.JSONDecodeError as exc:
            raise IafaAuditError("audit entry is not valid JSON") from exc

        if not self.verify_entry(entry):
            raise IafaAuditError("audit entry signature is invalid")
        return entry

    def _write_to_disk_sync(self, log_entry: str) -> None:
        log_dir = os.path.dirname(self.log_path)
        if log_dir:
            os.makedirs(log_dir, exist_ok=True)

        with open(self.log_path, "a", encoding="utf-8") as audit_file:
            audit_file.write(log_entry + "\n")

    async def append(self, record: IafaAuditRecord) -> None:
        log_entry = self.encode_entry(record)
        loop = asyncio.get_running_loop()
        await loop.run_in_executor(None, self._write_to_disk_sync, log_entry)

    async def append_payload(self, payload: Dict[str, Any]) -> None:
        log_entry = self.encode_payload(payload)
        loop = asyncio.get_running_loop()
        await loop.run_in_executor(None, self._write_to_disk_sync, log_entry)

    async def log_decision(
        self,
        action_name: str,
        score: float,
        threshold: float,
        allowed: bool,
        details: Optional[Dict[str, Any]] = None,
        timestamp: Optional[float] = None,
    ) -> None:
        record = IafaAuditRecord(
            timestamp=time.time() if timestamp is None else float(timestamp),
            action=action_name,
            score=float(score),
            threshold=float(threshold),
            allowed=bool(allowed),
            details=details or {},
        )
        await self.append(record)

    async def log_task_envelope(
        self,
        envelope: TaskEnvelope,
        event_name: str = "task_envelope.created",
        details: Optional[Dict[str, Any]] = None,
        timestamp: Optional[float] = None,
    ) -> None:
        if not isinstance(envelope, TaskEnvelope):
            raise IafaAuditError("envelope must be a TaskEnvelope")
        if not isinstance(event_name, str) or not event_name.strip():
            raise IafaAuditError("event_name must be a non-empty string")

        payload = {
            "timestamp": time.time() if timestamp is None else float(timestamp),
            "record_type": "task_envelope",
            "event": event_name.strip(),
            "task": envelope.to_audit_record_details(),
            "details": details or {},
        }
        await self.append_payload(payload)

    def iter_verified_entries(self) -> Iterable[Dict[str, Any]]:
        with open(self.log_path, "r", encoding="utf-8") as audit_file:
            for line in audit_file:
                stripped_line = line.strip()
                if stripped_line:
                    yield self.decode_entry(stripped_line)
