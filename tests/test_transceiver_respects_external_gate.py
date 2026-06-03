import pytest
import asyncio
import time
from unittest.mock import AsyncMock, patch
from core.task_envelope import TaskEnvelope
from cognition.iafa_transceiver import IafaTransceiver, LlmDisabledError, LlmCircuitOpenError

@pytest.fixture
def envelope():
    return TaskEnvelope.from_text("test", origin="test_suite")

@pytest.mark.asyncio
async def test_transceiver_raises_disabled_error_when_gate_denies(envelope):
    with patch.dict("os.environ", {"GREYS_FORCE_LOCAL_ONLY": "1", "GREYS_ALLOW_REAL_LLM_IN_TESTS": "0"}):
        transceiver = IafaTransceiver()
        with pytest.raises(LlmDisabledError):
            await transceiver.query_llm(envelope)

@pytest.mark.asyncio
async def test_transceiver_raises_circuit_open_error_when_gate_denies(envelope):
    with patch.dict("os.environ", {
        "GREYS_LLM_CIRCUIT_BREAKER_ENABLED": "1", 
        "GREYS_ALLOW_REAL_LLM_IN_TESTS": "1",
        "GREYS_LLM_MAX_FAILURES": "1",
        "GREYS_LLM_COOLDOWN_SECONDS": "300"
    }):
        transceiver = IafaTransceiver()
        # Forzar apertura del circuito
        transceiver.circuit_breaker.record_failure()
        assert transceiver.circuit_breaker.is_open is True
        
        with pytest.raises(LlmCircuitOpenError):
            await transceiver.query_llm(envelope)

@pytest.mark.asyncio
async def test_preflight_returns_false_when_gate_denies():
    with patch.dict("os.environ", {"GREYS_FORCE_LOCAL_ONLY": "1", "GREYS_ALLOW_REAL_LLM_IN_TESTS": "0"}):
        transceiver = IafaTransceiver()
        result = await transceiver.preflight_ollama()
        assert result is False
