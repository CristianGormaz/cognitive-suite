import pytest
from unittest.mock import MagicMock, patch
from cognition.dream_mode import DreamMode
import os

@pytest.mark.asyncio
async def test_dream_mode_no_autoinstall():
    # El DreamMode no debe tener acceso ni llamar a GenesisEngine ni DynamicSkillLoader
    # Aquí verificamos que no existan esos atributos o que no se usen en run_once
    mock_trans = MagicMock()
    mock_tension = MagicMock()
    mock_failure = MagicMock()
    mock_guard = MagicMock()
    mock_guard.get_stress_snapshot.return_value = {}
    
    dream = DreamMode(mock_trans, mock_tension, mock_failure, mock_guard)
    
    # Verificamos que run_once no reciba el motor de génesis ni el loader
    # (por inspección de código y diseño, no están en __init__)
    assert not hasattr(dream, "genesis_engine")
    assert not hasattr(dream, "skill_loader")
    
    # Simulamos un ciclo
    with patch.dict(os.environ, {"GREYS_DREAM_LLM_ENABLED": "0"}):
        result = await dream.run_once(1)
        
    assert result.cycle == 1
    assert result.source == "dream_mode"

def test_dream_prompt_is_safe():
    dream = DreamMode(MagicMock(), MagicMock(), MagicMock(), MagicMock())
    prompt = dream.build_reflection_prompt(0, [], {}, [])
    
    # El prompt debe exigir JSON y prohibir ejecución
    assert "JSON" in prompt
    assert "do_not_execute" in prompt
    assert "Evidencia" in prompt
