import pytest
import os
import time
from unittest.mock import patch, AsyncMock
from cognition.iafa_transceiver import IafaTransceiver, LlmTimeoutError, LlmCircuitOpenError
from core.task_envelope import TaskEnvelope

@pytest.fixture
def envelope():
    return TaskEnvelope.from_text("test")

@pytest.mark.asyncio
async def test_query_llm_retries_on_timeout(envelope):
    transceiver = IafaTransceiver()
    
    # Mock _safe_request to fail once with timeout, then succeed
    mock_request = AsyncMock(side_effect=[
        LlmTimeoutError("timeout"),
        {"response": '{"status": "ok"}'}
    ])
    transceiver._safe_request = mock_request
    
    with patch.dict("os.environ", {"GREYS_LLM_MAX_RETRIES": "1", "GREYS_LLM_RETRY_BACKOFF_SECONDS": "0"}):
        res = await transceiver.query_llm(envelope, json_format=True)
    
    assert res == '{"status": "ok"}'
    assert mock_request.call_count == 2

@pytest.mark.asyncio
async def test_query_llm_exhausts_retries(envelope):
    transceiver = IafaTransceiver()
    
    mock_request = AsyncMock(side_effect=LlmTimeoutError("timeout"))
    transceiver._safe_request = mock_request
    
    with patch.dict("os.environ", {"GREYS_LLM_MAX_RETRIES": "1", "GREYS_LLM_RETRY_BACKOFF_SECONDS": "0"}):
        with pytest.raises(LlmTimeoutError):
            await transceiver.query_llm(envelope, json_format=True)
            
    assert mock_request.call_count == 2

@pytest.mark.asyncio
async def test_query_llm_circuit_breaker_opens_and_blocks(envelope):
    transceiver = IafaTransceiver()
    # Force enable circuit breaker for test
    from cognition.iafa_transceiver import LlmCircuitBreaker
    transceiver.circuit_breaker = LlmCircuitBreaker(max_failures=1, cooldown_seconds=10)
    # Sincronizar el gate con el nuevo CB
    transceiver.gate.circuit_breaker = transceiver.circuit_breaker
    mock_request = AsyncMock(side_effect=LlmTimeoutError("timeout"))
    transceiver._safe_request = mock_request
    
    with patch.dict("os.environ", {"GREYS_LLM_MAX_RETRIES": "0", "GREYS_LLM_RETRY_BACKOFF_SECONDS": "0"}):
        # First call fails, triggers CB open
        with pytest.raises(LlmTimeoutError):
            await transceiver.query_llm(envelope)
            
        assert transceiver.circuit_breaker.is_open is True
        
        # Second call is blocked by CB
        with pytest.raises(LlmCircuitOpenError):
            await transceiver.query_llm(envelope)
            
    assert mock_request.call_count == 1
