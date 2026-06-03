import pytest
from core.ingestion_failure_ledger import IngestionFailureLedger
from cognition.iafa_transceiver import (
    LlmTimeoutError, LlmConnectionError, LlmMalformedJsonError, 
    LlmEmptyResponseError, LlmHostStressedError, LlmCircuitOpenError
)

def test_classify_llm_timeout():
    err = LlmTimeoutError("timeout occurred")
    assert IngestionFailureLedger.classify_failure(err) == "llm_timeout"

def test_classify_llm_connection():
    err = LlmConnectionError("connection failed")
    assert IngestionFailureLedger.classify_failure(err) == "llm_transport_error"

def test_classify_llm_malformed_json():
    err = LlmMalformedJsonError("bad json")
    assert IngestionFailureLedger.classify_failure(err) == "llm_malformed_json"

def test_classify_llm_empty_response():
    err = LlmEmptyResponseError("empty response")
    assert IngestionFailureLedger.classify_failure(err) == "llm_empty_response"

def test_classify_llm_host_stressed():
    err = LlmHostStressedError("stress")
    assert IngestionFailureLedger.classify_failure(err) == "host_stress_block"

def test_classify_llm_circuit_open():
    err = LlmCircuitOpenError("circuit open")
    assert IngestionFailureLedger.classify_failure(err) == "llm_circuit_open"

def test_classify_legacy_errors():
    err = RuntimeError("Ollama no respondió")
    assert IngestionFailureLedger.classify_failure(err) == "llm_timeout"
