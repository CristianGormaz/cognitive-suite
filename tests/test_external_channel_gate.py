import pytest
import os
from core.external_channel_gate import ExternalChannelGate

@pytest.fixture
def mock_stress_guard():
    class MockStress:
        def __init__(self): self.stressed = False
        def is_host_under_stress(self): return self.stressed
    return MockStress()

@pytest.fixture
def mock_circuit_breaker():
    class MockCB:
        def __init__(self): self.open = False
        def check_status(self): return not self.open
    return MockCB()

def test_gate_blocks_force_local_only(mock_stress_guard, mock_circuit_breaker):
    os.environ["GREYS_FORCE_LOCAL_ONLY"] = "1"
    gate = ExternalChannelGate(mock_stress_guard, mock_circuit_breaker)
    decision = gate.can_call_llm({"mode": "interactive"})
    assert decision.allowed is False
    assert "GREYS_FORCE_LOCAL_ONLY" in decision.reason
    os.environ.pop("GREYS_FORCE_LOCAL_ONLY", None)

def test_gate_blocks_dream_llm_disabled(mock_stress_guard, mock_circuit_breaker):
    os.environ["GREYS_DREAM_LLM_ENABLED"] = "0"
    gate = ExternalChannelGate(mock_stress_guard, mock_circuit_breaker)
    decision = gate.can_call_llm({"mode": "dream"})
    assert decision.allowed is False
    assert "GREYS_DREAM_LLM_ENABLED" in decision.reason
    os.environ.pop("GREYS_DREAM_LLM_ENABLED", None)

def test_gate_blocks_on_host_stress(mock_stress_guard, mock_circuit_breaker):
    mock_stress_guard.stressed = True
    gate = ExternalChannelGate(mock_stress_guard, mock_circuit_breaker)
    decision = gate.can_call_llm({"mode": "interactive"})
    assert decision.allowed is False
    assert "host is under stress" in decision.reason

def test_gate_blocks_on_circuit_open(mock_stress_guard, mock_circuit_breaker):
    mock_circuit_breaker.open = True
    gate = ExternalChannelGate(mock_stress_guard, mock_circuit_breaker)
    decision = gate.can_call_llm({"mode": "interactive"})
    assert decision.allowed is False
    assert "LLM Circuit Breaker is OPEN" in decision.reason

def test_gate_blocks_in_pytest_by_default(mock_stress_guard, mock_circuit_breaker):
    # PYTEST_CURRENT_TEST should be set by pytest automatically
    # Forzamos a 0 porque conftest lo pone a 1
    os.environ["GREYS_ALLOW_REAL_LLM_IN_TESTS"] = "0"
    gate = ExternalChannelGate(mock_stress_guard, mock_circuit_breaker)
    decision = gate.can_call_llm({"mode": "interactive"})
    assert decision.allowed is False
    assert "test environment" in decision.reason
    os.environ.pop("GREYS_ALLOW_REAL_LLM_IN_TESTS", None)

def test_gate_allows_when_everything_ok(mock_stress_guard, mock_circuit_breaker):
    os.environ["GREYS_ALLOW_REAL_LLM_IN_TESTS"] = "1"
    gate = ExternalChannelGate(mock_stress_guard, mock_circuit_breaker)
    decision = gate.can_call_llm({"mode": "interactive"})
    assert decision.allowed is True
    os.environ.pop("GREYS_ALLOW_REAL_LLM_IN_TESTS", None)
