import os
import pytest

@pytest.fixture(autouse=True)
def allow_llm_calls_in_tests():
    """
    Permite llamadas al LLM durante los tests por defecto, 
    asumiendo que los tests mockean el Transceiver.
    """
    os.environ["GREYS_ALLOW_REAL_LLM_IN_TESTS"] = "1"
    yield
    # No la quitamos para no interferir con otros procesos si fuera necesario, 
    # pero como es autouse, se ejecutará siempre.
