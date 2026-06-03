import unittest
import asyncio
import os
import tempfile
from pathlib import Path
import pytest

from cognition.ingestion_router import IngestionRouter, IngestionRouterError
from core.iafa_auditor import IafaAuditor

class IngestionRouterTests(unittest.IsolatedAsyncioTestCase):
    def test_classify_file(self):
        router = IngestionRouter()
        self.assertEqual(router.classify_file("test.docx"), "docx")
        self.assertEqual(router.classify_file("test.pdf"), "pdf")
        self.assertEqual(router.classify_file("test.txt"), "text")
        self.assertEqual(router.classify_file("test.md"), "text")
        self.assertEqual(router.classify_file("test.unknown"), "unsupported")

    async def test_route_text(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            auditor = IafaAuditor(str(Path(temp_dir) / "audit.log"), secret_key="test-secret")
            router = IngestionRouter(auditor=auditor)
            
            envelope = await router.route_text("Hola mundo", declared_intent="chat")
            self.assertEqual(envelope.source_type, "text")
            self.assertEqual(envelope.origin, "user")
            self.assertEqual(envelope.payload.value, "Hola mundo")
            self.assertEqual(envelope.declared_intent, "chat")

    async def test_route_path_text_file(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            auditor = IafaAuditor(str(Path(temp_dir) / "audit.log"), secret_key="test-secret")
            router = IngestionRouter(auditor=auditor)
            
            test_file = Path(temp_dir) / "test.txt"
            test_file.write_text("contenido de prueba")
            
            envelope = await router.route_path(str(test_file))
            self.assertEqual(envelope.source_type, "text")
            self.assertEqual(envelope.payload.value, "contenido de prueba")

    async def test_pdf_is_recognized_with_conditional_support(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            auditor = IafaAuditor(str(Path(temp_dir) / "audit.log"), secret_key="test-secret")
            router = IngestionRouter(auditor=auditor)

            pdf_path = "tests/fixtures/ingestion/sample.pdf"
            if not os.path.exists(pdf_path):
                # Fallback to bytes if fixture missing in CI
                envelope = await router.route_file_bytes(b"%PDF-1.4", filename="test.pdf")
            else:
                envelope = await router.route_path(pdf_path)

            self.assertEqual(envelope.payload.mime_type, "application/pdf")
            self.assertEqual(envelope.metadata["ingestion"]["status"], "pdf_detected")
            
            # Check audit (wait for async write)
            await asyncio.sleep(0.1)
            entries = list(auditor.iter_verified_entries())
            self.assertTrue(any(e.get("payload", {}).get("event") in ["ingestion.file.accepted", "ingestion.pdf.detected"] for e in entries))
