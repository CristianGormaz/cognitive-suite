import asyncio
import sys
import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from io import StringIO

from main import MainOrchestrator

@pytest.mark.asyncio
async def test_stdin_command_guard_ignores_shell_commands():
    orchestrator = MainOrchestrator(
        ingestion_router=MagicMock(),
        planner=MagicMock(),
        dispatcher=MagicMock(),
        cognitive_orchestrator=MagicMock(),
        genesis_engine=MagicMock(),
        skill_loader=MagicMock(),
        auditor=MagicMock()
    )
    
    from main import MainProcessResult
    fake_result = MainProcessResult("test_id", "test_stage", "test_status", {})
    orchestrator.process_input = AsyncMock(return_value=fake_result)
    
    # Simulate sys.stdin.readline
    lines = [
        "hola\n",
        "GREYS_SPARK_ENABLED=1 python src/main.py\n",
        "export GREYS_OLLAMA_TIMEOUT=100\n",
        "ollama run deepseek-r1:8b\n",
        "cd /\n",
        "/quit\n"
    ]
    
    def fake_readline():
        if lines:
            return lines.pop(0)
        return ""
        
    with patch("sys.stdin.readline", side_effect=fake_readline):
        await orchestrator.run_interactive()
    
    # process_input should only be called once, for "hola"
    orchestrator.process_input.assert_called_once_with("hola")
