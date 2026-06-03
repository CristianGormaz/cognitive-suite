import asyncio
import pytest
import os
from unittest.mock import AsyncMock, MagicMock, patch
from cognition.iafa_transceiver import IafaTransceiver
from core.task_envelope import TaskEnvelope

@pytest.mark.asyncio
async def test_iafa_transceiver_respects_env_options():
    env_vars = {
        "GREYS_OLLAMA_URL": "http://test-host:11434",
        "GREYS_OLLAMA_TEMPERATURE": "0.5",
        "GREYS_OLLAMA_NUM_PREDICT": "128",
        "GREYS_OLLAMA_FORMAT_JSON": "1",
        "GREYS_OLLAMA_KEEP_ALIVE": "10m"
    }
    
    with patch.dict(os.environ, env_vars):
        transceiver = IafaTransceiver()
        assert transceiver.host == "http://test-host:11434"
        assert transceiver.keep_alive == "10m"
        assert transceiver.force_json is True
        
        envelope = TaskEnvelope.from_text("hola")
        
        # Mock _safe_request to check payload
        transceiver._safe_request = AsyncMock(return_value={"response": '{"status": "ok"}'})
        
        await transceiver.query_llm(envelope)
        
        args, kwargs = transceiver._safe_request.call_args
        payload = args[1]
        
        assert payload["options"]["temperature"] == 0.5
        assert payload["options"]["num_predict"] == 128
        assert payload["format"] == "json"
        assert payload["keep_alive"] == "10m"

@pytest.mark.asyncio
async def test_iafa_transceiver_defaults():
    with patch.dict(os.environ, {}, clear=True):
        transceiver = IafaTransceiver()
        assert transceiver.host == "http://127.0.0.1:11434"
        assert transceiver.keep_alive == "5m"
        assert transceiver.force_json is False
        
        envelope = TaskEnvelope.from_text("hola")
        transceiver._safe_request = AsyncMock(return_value={"response": '{"status": "ok"}'})
        
        await transceiver.query_llm(envelope)
        
        args, kwargs = transceiver._safe_request.call_args
        payload = args[1]
        
        assert payload["options"]["temperature"] == 0.0
        assert "num_predict" not in payload["options"]
        assert "format" not in payload
