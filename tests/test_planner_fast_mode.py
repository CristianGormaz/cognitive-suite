import asyncio
import pytest
import os
from unittest.mock import AsyncMock, MagicMock, patch
from cognition.llm_planner import LLMPlanner, FAST_PLANNER_SYSTEM_PROMPT
from core.task_envelope import TaskEnvelope

@pytest.mark.asyncio
async def test_planner_fast_mode_activation():
    mock_transceiver = MagicMock()
    mock_transceiver.query_llm = AsyncMock(return_value='{"intent_category": "chat", "proposed_action": "respond", "iafa_friction_estimates": {"R":0.1,"I":0.1,"N":0.1}, "execution_payload": {"target_path": "n/a", "extracted_tags": []}}')
    
    planner = LLMPlanner(mock_transceiver)
    envelope = TaskEnvelope.from_text("hola")
    
    # Test via parameter
    await planner.plan(envelope, fast_mode=True)
    
    args, kwargs = mock_transceiver.query_llm.call_args
    assert kwargs["system_prompt"] == FAST_PLANNER_SYSTEM_PROMPT
    assert kwargs["options"]["num_predict"] == 256

@pytest.mark.asyncio
async def test_planner_fast_mode_env_activation():
    mock_transceiver = MagicMock()
    mock_transceiver.query_llm = AsyncMock(return_value='{"intent_category": "chat", "proposed_action": "respond", "iafa_friction_estimates": {"R":0.1,"I":0.1,"N":0.1}, "execution_payload": {"target_path": "n/a", "extracted_tags": []}}')
    
    planner = LLMPlanner(mock_transceiver)
    envelope = TaskEnvelope.from_text("hola")
    
    # Test via environment variable
    with patch.dict(os.environ, {"GREYS_PLANNER_FAST_MODE": "1", "GREYS_OLLAMA_FAST_NUM_PREDICT": "128"}):
        await planner.plan(envelope)
        
    args, kwargs = mock_transceiver.query_llm.call_args
    assert kwargs["system_prompt"] == FAST_PLANNER_SYSTEM_PROMPT
    assert kwargs["options"]["num_predict"] == 128
