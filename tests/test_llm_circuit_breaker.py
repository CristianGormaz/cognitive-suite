import pytest
import time
from unittest.mock import patch, AsyncMock
from cognition.iafa_transceiver import LlmCircuitBreaker, LlmCircuitOpenError

def test_circuit_breaker_opens_after_max_failures():
    cb = LlmCircuitBreaker(max_failures=3, cooldown_seconds=10)
    
    assert cb.check_status() is True
    cb.record_failure()
    cb.record_failure()
    assert cb.check_status() is True
    
    cb.record_failure()
    assert cb.check_status() is False
    assert cb.is_open is True

def test_circuit_breaker_resets_on_success():
    cb = LlmCircuitBreaker(max_failures=3, cooldown_seconds=10)
    cb.record_failure()
    cb.record_failure()
    cb.record_success()
    
    assert cb.failures == 0
    assert cb.is_open is False

def test_circuit_breaker_cooldown():
    cb = LlmCircuitBreaker(max_failures=2, cooldown_seconds=1)
    cb.record_failure()
    cb.record_failure()
    
    assert cb.check_status() is False
    
    # Simulate time passing
    cb.last_failure_time = time.time() - 2
    
    # Should enter half-open state
    assert cb.check_status() is True
