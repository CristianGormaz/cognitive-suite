import pytest
from core.response_manager import ResponseManager

def test_response_manager_handles_pdf_disabled():
    mgr = ResponseManager()
    
    # Simular ruteo local de PDF desactivado
    payload = {"message_key": "pdf_reader_available_but_disabled"}
    res = mgr.generate_response("pdf_ingestion", "n/a", execution_payload=payload)
    
    assert "desactivado por configuración" in res
    assert "Recomendación: Habilita el modo experimental" in res

def test_response_manager_handles_host_stress():
    mgr = ResponseManager()
    
    payload = {"message_key": "host_under_stress"}
    res = mgr.generate_response("pdf_ingestion", "n/a", execution_payload=payload)
    
    assert "alta carga" in res
    assert "diferir tareas pesadas" in res

def test_response_manager_maintains_generic_chat():
    mgr = ResponseManager()
    res = mgr.generate_response("chat", "hola")
    assert "Hola, soy Greys-v3" in res
