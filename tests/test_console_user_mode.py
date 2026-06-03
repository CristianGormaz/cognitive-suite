import os
import pytest
from unittest.mock import patch, MagicMock, AsyncMock
from main import MainOrchestrator

@pytest.mark.asyncio
async def test_debug_output_disabled():
    # Simulamos que GREYS_DEBUG_OUTPUT no está seteado o es 0
    with patch.dict(os.environ, {"GREYS_DEBUG_OUTPUT": "0"}):
        with patch("main.logger") as mock_logger:
            with patch("builtins.print") as mock_print:
                orchestrator = await MainOrchestrator.create_default()
                
                # Mock de process_input para devolver un resultado con respuesta
                mock_result = MagicMock()
                mock_result.details = {"response_text": "Respuesta de prueba"}
                mock_result.to_dict.return_value = {"key": "val"}
                mock_result.status = "executed"
                
                with patch.object(orchestrator, "process_input", return_value=mock_result):
                    # Simulamos una entrada en run_interactive
                    with patch("sys.stdin.readline", side_effect=["hola\n", "exit\n"]):
                        try:
                            await orchestrator.run_interactive()
                        except (StopIteration, SystemExit, EOFError):
                            pass
                    
                    # Verificamos que se imprimió la respuesta
                    mock_print.assert_any_call("\n[Greys]: Respuesta de prueba\n")
                    
                    # Verificamos que logger.info NO recibió el Main result
                    for call in mock_logger.info.call_args_list:
                        args = call[0]
                        if len(args) > 1 and "Main result" in args[0]:
                            pytest.fail("Main result loggeado en INFO cuando DEBUG_OUTPUT está desactivado")

@pytest.mark.asyncio
async def test_debug_output_enabled():
    with patch.dict(os.environ, {"GREYS_DEBUG_OUTPUT": "1"}):
        with patch("main.logger") as mock_logger:
            with patch("builtins.print") as mock_print:
                orchestrator = await MainOrchestrator.create_default()
                
                mock_result = MagicMock()
                mock_result.details = {"response_text": "Respuesta de prueba"}
                mock_result.to_dict.return_value = {"key": "val"}
                mock_result.status = "executed"
                
                with patch.object(orchestrator, "process_input", return_value=mock_result):
                    with patch("sys.stdin.readline", side_effect=["hola\n", "exit\n"]):
                        try:
                            await orchestrator.run_interactive()
                        except (StopIteration, SystemExit, EOFError):
                            pass
                    
                    # Verificamos que logger.info SÍ recibió el Main result
                    found = False
                    for call in mock_logger.info.call_args_list:
                        args = call[0]
                        if len(args) > 1 and "Main result" in args[0]:
                            found = True
                            break
                    assert found, "Main result NO loggeado en INFO cuando DEBUG_OUTPUT está activado"
