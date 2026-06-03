from __future__ import annotations

import base64
from dataclasses import dataclass
from io import BytesIO
from typing import Any, Callable, Optional

from core.task_envelope import TaskEnvelope


DOCUMENT_PROCESSOR_VERSION = "document-processor.v1"

DOCX_MIME_TYPE = "application/vnd.openxmlformats-officedocument.wordprocessingml.document"


class DocumentProcessingError(ValueError):
    """Raised when a document cannot be safely transformed."""


@dataclass(frozen=True)
class ExtractedDocumentText:
    text: str
    paragraph_count: int
    table_count: int
    table_row_count: int


DocxLoader = Callable[[BytesIO], Any]


class DocumentProcessor:
    """
    Converts auditable document envelopes into auditable text envelopes.

    The processor treats document bytes as untrusted data. It verifies the bytes
    against the source TaskEnvelope before parsing and returns a new
    TaskEnvelope; it does not call an LLM.
    """

    def __init__(self, docx_loader: Optional[DocxLoader] = None):
        self.docx_loader = docx_loader

    def docx_to_text_envelope(
        self,
        source_envelope: TaskEnvelope,
        payload_bytes: Optional[bytes] = None,
        created_at: Optional[str] = None,
    ) -> TaskEnvelope:
        self._validate_docx_envelope(source_envelope)
        resolved_bytes = self._resolve_payload_bytes(source_envelope, payload_bytes)

        if not source_envelope.verify_payload_bytes(resolved_bytes):
            raise DocumentProcessingError("payload bytes do not match source envelope sha256")

        extracted = self.extract_docx_text(resolved_bytes)
        output_source_name = self._text_source_name(source_envelope.source_name)

        return TaskEnvelope.from_text(
            extracted.text,
            origin="document_processor",
            source_name=output_source_name,
            declared_intent="plain_text_extraction",
            created_at=created_at,
            metadata={
                "processor": {
                    "name": self.__class__.__name__,
                    "version": DOCUMENT_PROCESSOR_VERSION,
                    "library": "python-docx",
                },
                "source_task": source_envelope.to_audit_record_details(),
                "extraction": {
                    "source_format": "docx",
                    "paragraph_count": extracted.paragraph_count,
                    "table_count": extracted.table_count,
                    "table_row_count": extracted.table_row_count,
                },
            },
        )

    def extract_docx_text(self, payload_bytes: bytes) -> ExtractedDocumentText:
        if not isinstance(payload_bytes, bytes):
            raise DocumentProcessingError("payload_bytes must be bytes")

        document = self._load_docx_document(payload_bytes)
        paragraphs = self._extract_paragraphs(document)
        table_rows = self._extract_table_rows(document)
        text_blocks = paragraphs + table_rows

        return ExtractedDocumentText(
            text="\n".join(text_blocks),
            paragraph_count=len(paragraphs),
            table_count=len(getattr(document, "tables", []) or []),
            table_row_count=len(table_rows),
        )

    def _load_docx_document(self, payload_bytes: bytes) -> Any:
        stream = BytesIO(payload_bytes)
        if self.docx_loader:
            return self.docx_loader(stream)

        try:
            from docx import Document
        except ImportError as exc:
            raise DocumentProcessingError("python-docx is required to process .docx files") from exc

        return Document(stream)

    @staticmethod
    def _extract_paragraphs(document: Any) -> list[str]:
        paragraphs: list[str] = []
        for paragraph in getattr(document, "paragraphs", []) or []:
            text = getattr(paragraph, "text", "")
            if text and text.strip():
                paragraphs.append(text.strip())
        return paragraphs

    @staticmethod
    def _extract_table_rows(document: Any) -> list[str]:
        table_rows: list[str] = []
        for table in getattr(document, "tables", []) or []:
            for row in getattr(table, "rows", []) or []:
                cells = []
                for cell in getattr(row, "cells", []) or []:
                    text = getattr(cell, "text", "")
                    if text and text.strip():
                        cells.append(text.strip())
                if cells:
                    table_rows.append(" | ".join(cells))
        return table_rows

    @staticmethod
    def _validate_docx_envelope(source_envelope: TaskEnvelope) -> None:
        if not isinstance(source_envelope, TaskEnvelope):
            raise DocumentProcessingError("source_envelope must be a TaskEnvelope")

        source_name = (source_envelope.source_name or "").lower()
        mime_type = source_envelope.payload.mime_type
        if mime_type != DOCX_MIME_TYPE and not source_name.endswith(".docx"):
            raise DocumentProcessingError("source envelope is not a .docx document")

    @staticmethod
    def _resolve_payload_bytes(source_envelope: TaskEnvelope, payload_bytes: Optional[bytes]) -> bytes:
        if payload_bytes is not None:
            if not isinstance(payload_bytes, bytes):
                raise DocumentProcessingError("payload_bytes must be bytes")
            return payload_bytes

        if source_envelope.payload.representation != "bytes_base64" or source_envelope.payload.value is None:
            raise DocumentProcessingError("payload_bytes are required for external_ref envelopes")

        try:
            return base64.b64decode(source_envelope.payload.value.encode("ascii"), validate=True)
        except (ValueError, UnicodeEncodeError) as exc:
            raise DocumentProcessingError("embedded payload is not valid base64") from exc

    @staticmethod
    def _text_source_name(source_name: Optional[str]) -> Optional[str]:
        if not source_name:
            return None
        return f"{source_name}.txt"
