from __future__ import annotations

import base64
import hashlib
import json
import math
import mimetypes
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from typing import Any, Dict, Mapping, Optional, Tuple


TASK_ENVELOPE_SCHEMA_VERSION = "task-envelope.v1"

DEFAULT_SAFETY_LABELS = (
    "untrusted_input",
    "payload_is_data_not_instruction",
    "requires_policy_routing_before_llm",
)


class TaskEnvelopeError(ValueError):
    """Raised when a task envelope cannot be built or verified."""


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _canonical_json(payload: Mapping[str, Any]) -> str:
    return json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def _validate_json_value(value: Any, path: str = "metadata") -> Any:
    if value is None or isinstance(value, (str, bool)):
        return value

    if isinstance(value, (int, float)):
        if not math.isfinite(value):
            raise TaskEnvelopeError(f"{path} contains a non-finite number")
        return value

    if isinstance(value, Mapping):
        normalized: Dict[str, Any] = {}
        for key, item in value.items():
            if not isinstance(key, str) or not key:
                raise TaskEnvelopeError(f"{path} keys must be non-empty strings")
            normalized[key] = _validate_json_value(item, f"{path}.{key}")
        return normalized

    if isinstance(value, (list, tuple)):
        return [_validate_json_value(item, f"{path}[]") for item in value]

    raise TaskEnvelopeError(f"{path} contains a non-JSON value: {type(value).__name__}")


def _canonical_metadata(metadata: Optional[Mapping[str, Any]]) -> str:
    if metadata is None:
        return "{}"
    normalized = _validate_json_value(metadata)
    return _canonical_json(normalized)


def _metadata_from_json(metadata_json: str) -> Dict[str, Any]:
    metadata = json.loads(metadata_json)
    if not isinstance(metadata, dict):
        raise TaskEnvelopeError("metadata must be a JSON object")
    return metadata


def _sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _infer_mime_type(source_name: Optional[str], fallback: str) -> str:
    if not source_name:
        return fallback
    guessed_type, _ = mimetypes.guess_type(source_name)
    return guessed_type or fallback


def _normalize_required_string(name: str, value: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise TaskEnvelopeError(f"{name} must be a non-empty string")
    return value.strip()


def _normalize_optional_string(name: str, value: Optional[str]) -> Optional[str]:
    if value is None:
        return None
    if not isinstance(value, str) or not value.strip():
        raise TaskEnvelopeError(f"{name} must be None or a non-empty string")
    return value.strip()


@dataclass(frozen=True)
class TaskPayload:
    representation: str
    sha256: str
    size_bytes: int
    mime_type: str
    value: Optional[str] = None
    encoding: Optional[str] = None

    @classmethod
    def from_text(cls, text: str, mime_type: str = "text/plain", encoding: str = "utf-8") -> "TaskPayload":
        if not isinstance(text, str):
            raise TaskEnvelopeError("text payload must be a string")

        payload_bytes = text.encode(encoding)
        return cls(
            representation="text",
            sha256=_sha256_bytes(payload_bytes),
            size_bytes=len(payload_bytes),
            mime_type=_normalize_required_string("mime_type", mime_type),
            value=text,
            encoding=encoding,
        )

    @classmethod
    def from_bytes(
        cls,
        payload_bytes: bytes,
        mime_type: str,
        encoding: Optional[str] = None,
        embed_payload: bool = False,
    ) -> "TaskPayload":
        if not isinstance(payload_bytes, bytes):
            raise TaskEnvelopeError("byte payload must be bytes")

        return cls(
            representation="bytes_base64" if embed_payload else "external_ref",
            sha256=_sha256_bytes(payload_bytes),
            size_bytes=len(payload_bytes),
            mime_type=_normalize_required_string("mime_type", mime_type),
            value=base64.b64encode(payload_bytes).decode("ascii") if embed_payload else None,
            encoding=encoding,
        )

    def verify_bytes(self, payload_bytes: bytes) -> bool:
        if not isinstance(payload_bytes, bytes):
            raise TaskEnvelopeError("payload_bytes must be bytes")
        return self.sha256 == _sha256_bytes(payload_bytes)

    def verify_text(self, text: str) -> bool:
        if self.encoding is None:
            raise TaskEnvelopeError("text verification requires payload encoding")
        return self.verify_bytes(text.encode(self.encoding))

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class TaskEnvelope:
    schema_version: str
    task_id: str
    created_at: str
    source_type: str
    origin: str
    payload: TaskPayload
    metadata_json: str = "{}"
    source_name: Optional[str] = None
    declared_intent: Optional[str] = None
    safety_labels: Tuple[str, ...] = DEFAULT_SAFETY_LABELS

    @classmethod
    def create(
        cls,
        source_type: str,
        origin: str,
        payload: TaskPayload,
        metadata: Optional[Mapping[str, Any]] = None,
        source_name: Optional[str] = None,
        declared_intent: Optional[str] = None,
        created_at: Optional[str] = None,
        safety_labels: Tuple[str, ...] = DEFAULT_SAFETY_LABELS,
    ) -> "TaskEnvelope":
        source_type = _normalize_required_string("source_type", source_type)
        origin = _normalize_required_string("origin", origin)
        source_name = _normalize_optional_string("source_name", source_name)
        declared_intent = _normalize_optional_string("declared_intent", declared_intent)
        created_at = _normalize_optional_string("created_at", created_at) or _utc_now_iso()

        if not isinstance(payload, TaskPayload):
            raise TaskEnvelopeError("payload must be a TaskPayload")
        if not safety_labels:
            raise TaskEnvelopeError("safety_labels cannot be empty")

        normalized_labels = tuple(_normalize_required_string("safety_label", label) for label in safety_labels)
        if "payload_is_data_not_instruction" not in normalized_labels:
            raise TaskEnvelopeError("safety_labels must include payload_is_data_not_instruction")

        metadata_json = _canonical_metadata(metadata)
        identity = {
            "schema_version": TASK_ENVELOPE_SCHEMA_VERSION,
            "created_at": created_at,
            "source_type": source_type,
            "origin": origin,
            "source_name": source_name,
            "declared_intent": declared_intent,
            "payload": payload.to_dict(),
            "metadata": _metadata_from_json(metadata_json),
            "safety_labels": list(normalized_labels),
        }
        task_id = f"task_{_sha256_bytes(_canonical_json(identity).encode('utf-8'))[:24]}"

        return cls(
            schema_version=TASK_ENVELOPE_SCHEMA_VERSION,
            task_id=task_id,
            created_at=created_at,
            source_type=source_type,
            origin=origin,
            payload=payload,
            metadata_json=metadata_json,
            source_name=source_name,
            declared_intent=declared_intent,
            safety_labels=normalized_labels,
        )

    @classmethod
    def from_text(
        cls,
        text: str,
        origin: str = "user",
        source_name: Optional[str] = None,
        declared_intent: Optional[str] = None,
        metadata: Optional[Mapping[str, Any]] = None,
        created_at: Optional[str] = None,
        mime_type: str = "text/plain",
        encoding: str = "utf-8",
    ) -> "TaskEnvelope":
        return cls.create(
            source_type="text",
            origin=origin,
            source_name=source_name,
            declared_intent=declared_intent,
            payload=TaskPayload.from_text(text, mime_type=mime_type, encoding=encoding),
            metadata=metadata,
            created_at=created_at,
        )

    @classmethod
    def from_voice_transcript(
        cls,
        transcript: str,
        origin: str = "voice",
        source_name: Optional[str] = None,
        declared_intent: Optional[str] = None,
        metadata: Optional[Mapping[str, Any]] = None,
        created_at: Optional[str] = None,
    ) -> "TaskEnvelope":
        return cls.create(
            source_type="voice_transcript",
            origin=origin,
            source_name=source_name,
            declared_intent=declared_intent,
            payload=TaskPayload.from_text(transcript, mime_type="text/plain", encoding="utf-8"),
            metadata=metadata,
            created_at=created_at,
        )

    @classmethod
    def from_bytes(
        cls,
        payload_bytes: bytes,
        source_type: str,
        origin: str = "user",
        source_name: Optional[str] = None,
        declared_intent: Optional[str] = None,
        metadata: Optional[Mapping[str, Any]] = None,
        created_at: Optional[str] = None,
        mime_type: Optional[str] = None,
        encoding: Optional[str] = None,
        embed_payload: bool = False,
    ) -> "TaskEnvelope":
        resolved_mime_type = mime_type or _infer_mime_type(source_name, "application/octet-stream")
        return cls.create(
            source_type=source_type,
            origin=origin,
            source_name=source_name,
            declared_intent=declared_intent,
            payload=TaskPayload.from_bytes(
                payload_bytes,
                mime_type=resolved_mime_type,
                encoding=encoding,
                embed_payload=embed_payload,
            ),
            metadata=metadata,
            created_at=created_at,
        )

    @classmethod
    def from_file_bytes(
        cls,
        payload_bytes: bytes,
        filename: str,
        origin: str = "user",
        declared_intent: Optional[str] = None,
        metadata: Optional[Mapping[str, Any]] = None,
        created_at: Optional[str] = None,
        mime_type: Optional[str] = None,
        embed_payload: bool = False,
    ) -> "TaskEnvelope":
        return cls.from_bytes(
            payload_bytes=payload_bytes,
            source_type="file",
            origin=origin,
            source_name=filename,
            declared_intent=declared_intent,
            metadata=metadata,
            created_at=created_at,
            mime_type=mime_type,
            embed_payload=embed_payload,
        )

    @property
    def metadata(self) -> Dict[str, Any]:
        return _metadata_from_json(self.metadata_json)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "task_id": self.task_id,
            "created_at": self.created_at,
            "source_type": self.source_type,
            "origin": self.origin,
            "source_name": self.source_name,
            "declared_intent": self.declared_intent,
            "payload": self.payload.to_dict(),
            "metadata": self.metadata,
            "safety_labels": list(self.safety_labels),
        }

    def canonical_json(self) -> str:
        return _canonical_json(self.to_dict())

    def audit_hash(self) -> str:
        return _sha256_bytes(self.canonical_json().encode("utf-8"))

    def verify_payload_bytes(self, payload_bytes: bytes) -> bool:
        return self.payload.verify_bytes(payload_bytes)

    def verify_payload_text(self, text: str) -> bool:
        return self.payload.verify_text(text)

    def to_audit_record_details(self) -> Dict[str, Any]:
        return {
            "task_id": self.task_id,
            "audit_hash": self.audit_hash(),
            "schema_version": self.schema_version,
            "source_type": self.source_type,
            "origin": self.origin,
            "source_name": self.source_name,
            "declared_intent": self.declared_intent,
            "payload_sha256": self.payload.sha256,
            "payload_size_bytes": self.payload.size_bytes,
            "payload_mime_type": self.payload.mime_type,
            "safety_labels": list(self.safety_labels),
        }

    def to_llm_safe_dict(self, max_payload_chars: int = 1200) -> Dict[str, Any]:
        if max_payload_chars < 0:
            raise TaskEnvelopeError("max_payload_chars cannot be negative")

        payload_value = self.payload.value
        preview = None
        truncated = False
        if payload_value is not None:
            preview = payload_value[:max_payload_chars]
            truncated = len(payload_value) > max_payload_chars

        return {
            "task_id": self.task_id,
            "source_type": self.source_type,
            "declared_intent": self.declared_intent,
            "payload_is_instruction": False,
            "payload_trust": "untrusted",
            "payload_mime_type": self.payload.mime_type,
            "payload_sha256": self.payload.sha256,
            "payload_size_bytes": self.payload.size_bytes,
            "untrusted_payload_preview": preview,
            "preview_truncated": truncated,
            "safety_labels": list(self.safety_labels),
        }
