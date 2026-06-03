import pytest
import os
from core.local_intent_router import LocalIntentRouter, LocalIntentDecision
from core.task_envelope import TaskEnvelope

def test_route_text_basic_keywords():
    router = LocalIntentRouter()
    
    d1 = router.route_text("hola")
    assert d1.matched is True
    assert d1.intent_category == "chat"
    assert d1.proposed_action == "respond"
    assert d1.bypass_llm is True
    
    d2 = router.route_text("¿quién eres?")
    assert d2.matched is True
    assert d2.reason == "identity"

def test_route_text_partial_keyword_match():
    router = LocalIntentRouter()
    
    d = router.route_text("me das ayuda por favor")
    assert d.matched is True
    assert "help" in d.reason
    assert d.confidence == 0.9

def test_route_pdf_disabled_globally():
    os.environ["GREYS_EXPERIMENTAL_SKILLS_ENABLED"] = "0"
    router = LocalIntentRouter()
    
    envelope = TaskEnvelope.from_file_bytes(b"%PDF-1.4", filename="test.pdf")
    
    d = router.route_pdf(envelope)
    assert d.matched is True
    assert d.reason == "pdf_reader_available_but_disabled"
    assert d.execution_payload["message_key"] == "pdf_reader_available_but_disabled"

def test_route_pdf_not_allowlisted():
    os.environ["GREYS_EXPERIMENTAL_SKILLS_ENABLED"] = "1"
    os.environ["GREYS_EXPERIMENTAL_SKILL_ALLOWLIST"] = "other_skill"
    router = LocalIntentRouter()
    
    envelope = TaskEnvelope.from_file_bytes(b"%PDF-1.4", filename="test.pdf")
    
    d = router.route_pdf(envelope)
    assert d.matched is True
    assert d.reason == "pdf_reader_not_allowlisted"

def test_route_pdf_deterministic_success():
    os.environ["GREYS_EXPERIMENTAL_SKILLS_ENABLED"] = "1"
    os.environ["GREYS_EXPERIMENTAL_SKILL_ALLOWLIST"] = "pdf_reader_basic"
    router = LocalIntentRouter()
    
    envelope = TaskEnvelope.from_file_bytes(
        b"%PDF-1.4", 
        filename="test.pdf", 
        metadata={"ingestion": {"source_path": "/path/to/test.pdf"}}
    )
    
    d = router.route_pdf(envelope)
    assert d.matched is True
    assert d.proposed_action == "pdf_reader_basic"
    assert d.requires_iafa is True
    assert d.execution_payload["target_path"] == "/path/to/test.pdf"
