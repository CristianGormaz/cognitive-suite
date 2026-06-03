import pytest
import os
import json
from unittest.mock import patch, AsyncMock
from cognition.iafa_transceiver import IafaTransceiver, LlmTimeoutError
from core.task_envelope import TaskEnvelope

@pytest.fixture
def envelope():
    return TaskEnvelope.from_text("test health ledger")

@pytest.mark.asyncio
async def test_llm_health_ledger_records_success(envelope, tmp_path):
    ledger_path = tmp_path / "llm_health.jsonl"
    
    transceiver = IafaTransceiver()
    mock_request = AsyncMock(return_value={"response": "ok"})
    transceiver._safe_request = mock_request
    
    with patch.dict("os.environ", {"GREYS_LLM_HEALTH_LEDGER": str(ledger_path), "GREYS_LLM_MAX_RETRIES": "0"}):
        await transceiver.query_llm(envelope)
        
    assert ledger_path.exists()
    content = ledger_path.read_text()
    data = json.loads(content.strip())
    
    assert data["status"] == "success"
    assert data["error_type"] is None
    assert "prompt_chars" in data
    assert "prompt_hash" in data

@pytest.mark.asyncio
async def test_llm_health_ledger_records_failure(envelope, tmp_path):
    ledger_path = tmp_path / "llm_health.jsonl"
    
    transceiver = IafaTransceiver()
    mock_request = AsyncMock(side_effect=LlmTimeoutError("timeout"))
    transceiver._safe_request = mock_request
    
    with patch.dict("os.environ", {"GREYS_LLM_HEALTH_LEDGER": str(ledger_path), "GREYS_LLM_MAX_RETRIES": "0"}):
        with pytest.raises(LlmTimeoutError):
            await transceiver.query_llm(envelope)
            
    assert ledger_path.exists()
    content = ledger_path.read_text()
    data = json.loads(content.strip())
    
    assert data["status"] == "llm_timeout"
    assert data["error_type"] == "llm_timeout"
    assert "timeout" in data["error_detail"]
