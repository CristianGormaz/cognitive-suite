from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Mapping, Optional

from core.iafa_auditor import IafaAuditor
from core.task_envelope import TaskEnvelope
from perception.document_processor import DOCX_MIME_TYPE, DocumentProcessor


PDF_MIME_TYPE = "application/pdf"
TEXT_MIME_TYPE = "text/plain"
TEXT_EXTENSIONS = {".txt", ".md", ".csv", ".json", ".log", ".py", ".yaml", ".yml"}


class IngestionRouterError(ValueError):
    """Raised when raw input cannot be converted into a safe TaskEnvelope."""


@dataclass(frozen=True)
class IngestionRoute:
    input_kind: str
    output_kind: str
    processor: str


class IngestionRouter:
    """
    Entry boundary for Greys inputs.

    The router receives raw data, classifies it, creates TaskEnvelope objects,
    delegates format-specific extraction, and optionally audits every envelope
    transition before anything reaches the LLM.
    """

    def __init__(self, document_processor: Optional[DocumentProcessor] = None, auditor: Optional[IafaAuditor] = None):
        self.document_processor = document_processor or DocumentProcessor()
        self.auditor = auditor

    async def route_text(
        self,
        text: str,
        origin: str = "user",
        source_name: Optional[str] = None,
        declared_intent: Optional[str] = None,
        metadata: Optional[Mapping[str, Any]] = None,
        created_at: Optional[str] = None,
    ) -> TaskEnvelope:
        envelope = TaskEnvelope.from_text(
            text,
            origin=origin,
            source_name=source_name,
            declared_intent=declared_intent,
            metadata=self._merge_metadata(
                metadata,
                {
                    "ingestion": {
                        "router": self.__class__.__name__,
                        "route": IngestionRoute("text", "text", "none").__dict__,
                    }
                },
            ),
            created_at=created_at,
        )
        await self._audit(envelope, "ingestion.text.accepted")
        return envelope

    async def route_file_bytes(
        self,
        payload_bytes: bytes,
        filename: str,
        origin: str = "user",
        declared_intent: Optional[str] = None,
        metadata: Optional[Mapping[str, Any]] = None,
        mime_type: Optional[str] = None,
        created_at: Optional[str] = None,
    ) -> TaskEnvelope:
        input_kind = self.classify_file(filename, mime_type)

        if input_kind == "docx":
            return await self._route_docx(
                payload_bytes,
                filename,
                origin,
                declared_intent,
                metadata,
                mime_type,
                created_at,
            )
        if input_kind == "text":
            return await self._route_text_file(
                payload_bytes,
                filename,
                origin,
                declared_intent,
                metadata,
                mime_type,
                created_at,
            )
        if input_kind == "pdf":
            return await self._route_pdf(
                payload_bytes,
                filename,
                origin,
                declared_intent,
                metadata,
                mime_type,
                created_at,
            )

        raise IngestionRouterError(f"Unsupported input type for {filename}")

    async def route_path(
        self,
        path: str,
        origin: str = "user",
        declared_intent: Optional[str] = None,
        metadata: Optional[Mapping[str, Any]] = None,
        mime_type: Optional[str] = None,
        created_at: Optional[str] = None,
    ) -> TaskEnvelope:
        file_path = Path(path)
        if not file_path.is_file():
            raise IngestionRouterError(f"Input path is not a file: {path}")

        # Inject original path into metadata for downstream skills (experimental)
        extended_metadata = self._merge_metadata(metadata, {"ingestion": {"source_path": str(file_path.absolute())}})

        return await self.route_file_bytes(
            file_path.read_bytes(),
            filename=file_path.name,
            origin=origin,
            declared_intent=declared_intent,
            metadata=extended_metadata,
            mime_type=mime_type,
            created_at=created_at,
        )

    async def _route_pdf(
        self,
        payload_bytes: bytes,
        filename: str,
        origin: str,
        declared_intent: Optional[str],
        metadata: Optional[Mapping[str, Any]],
        mime_type: Optional[str],
        created_at: Optional[str],
    ) -> TaskEnvelope:
        # Tarea 3: Validar tamaño (5MB)
        MAX_SIZE = 5 * 1024 * 1024
        if len(payload_bytes) > MAX_SIZE:
             raise IngestionRouterError(f"PDF file '{filename}' exceeds maximum allowed size (5MB)")

        envelope = TaskEnvelope.from_file_bytes(
            payload_bytes,
            filename=filename,
            origin=origin,
            declared_intent=declared_intent or "pdf_reader",
            metadata=self._merge_metadata(
                metadata,
                {
                    "ingestion": {
                        "router": self.__class__.__name__,
                        "route": IngestionRoute("pdf", "pdf_reader", "experimental_skill").__dict__,
                        "status": "pdf_detected",
                        "capability_required": "file:pdf_reader"
                    }
                },
            ),
            created_at=created_at,
            mime_type=mime_type or PDF_MIME_TYPE,
            embed_payload=False, # No embeber para ahorrar espacio en ledgers y respetar privacidad
        )
        await self._audit(envelope, "ingestion.pdf.detected")
        return envelope

    @staticmethod
    def classify_file(filename: str, mime_type: Optional[str] = None) -> str:
        suffix = Path(filename).suffix.lower()
        normalized_mime = (mime_type or "").lower()

        if suffix == ".docx" or normalized_mime == DOCX_MIME_TYPE:
            return "docx"
        if suffix == ".pdf" or normalized_mime == PDF_MIME_TYPE:
            return "pdf"
        if suffix in TEXT_EXTENSIONS or normalized_mime.startswith("text/"):
            return "text"
        return "unsupported"

    async def _route_docx(
        self,
        payload_bytes: bytes,
        filename: str,
        origin: str,
        declared_intent: Optional[str],
        metadata: Optional[Mapping[str, Any]],
        mime_type: Optional[str],
        created_at: Optional[str],
    ) -> TaskEnvelope:
        raw_envelope = TaskEnvelope.from_file_bytes(
            payload_bytes,
            filename=filename,
            origin=origin,
            declared_intent=declared_intent or "extract_text",
            metadata=self._merge_metadata(
                metadata,
                {
                    "ingestion": {
                        "router": self.__class__.__name__,
                        "route": IngestionRoute("docx", "text", "DocumentProcessor").__dict__,
                    }
                },
            ),
            created_at=created_at,
            mime_type=mime_type or DOCX_MIME_TYPE,
            embed_payload=False,
        )
        await self._audit(raw_envelope, "ingestion.file.accepted")

        text_envelope = self.document_processor.docx_to_text_envelope(
            raw_envelope,
            payload_bytes=payload_bytes,
            created_at=created_at,
        )
        await self._audit(
            text_envelope,
            "ingestion.document.processed",
            {"source_task_id": raw_envelope.task_id},
        )
        return text_envelope

    async def _route_text_file(
        self,
        payload_bytes: bytes,
        filename: str,
        origin: str,
        declared_intent: Optional[str],
        metadata: Optional[Mapping[str, Any]],
        mime_type: Optional[str],
        created_at: Optional[str],
    ) -> TaskEnvelope:
        raw_envelope = TaskEnvelope.from_file_bytes(
            payload_bytes,
            filename=filename,
            origin=origin,
            declared_intent=declared_intent,
            metadata=self._merge_metadata(
                metadata,
                {
                    "ingestion": {
                        "router": self.__class__.__name__,
                        "route": IngestionRoute("text_file", "text", "utf-8").__dict__,
                    }
                },
            ),
            created_at=created_at,
            mime_type=mime_type or TEXT_MIME_TYPE,
            embed_payload=False,
        )
        await self._audit(raw_envelope, "ingestion.file.accepted")

        try:
            text = payload_bytes.decode("utf-8")
        except UnicodeDecodeError as exc:
            raise IngestionRouterError(f"Text file is not valid UTF-8: {filename}") from exc

        text_envelope = TaskEnvelope.from_text(
            text,
            origin="ingestion_router",
            source_name=f"{filename}.txt" if not filename.endswith(".txt") else filename,
            declared_intent=declared_intent,
            metadata={
                "source_task": raw_envelope.to_audit_record_details(),
                "ingestion": {
                    "router": self.__class__.__name__,
                    "route": IngestionRoute("text_file", "text", "utf-8").__dict__,
                },
            },
            created_at=created_at,
        )
        await self._audit(
            text_envelope,
            "ingestion.text_file.processed",
            {"source_task_id": raw_envelope.task_id},
        )
        return text_envelope

    async def _audit(self, envelope: TaskEnvelope, event_name: str, details: Optional[Dict[str, Any]] = None) -> None:
        if self.auditor:
            await self.auditor.log_task_envelope(envelope, event_name=event_name, details=details)

    @staticmethod
    def _merge_metadata(
        metadata: Optional[Mapping[str, Any]],
        additions: Mapping[str, Any],
    ) -> Dict[str, Any]:
        merged = dict(metadata or {})
        for key, value in additions.items():
            if isinstance(value, Mapping) and isinstance(merged.get(key), Mapping):
                nested = dict(merged[key])
                nested.update(value)
                merged[key] = nested
            else:
                merged[key] = value
        return merged
