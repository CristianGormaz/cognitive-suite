import os
import json
import pytest
from unittest.mock import MagicMock, AsyncMock
from pathlib import Path
from cognition.dream_mode import DreamMode

@pytest.mark.asyncio
async def test_dream_mode_loads_focus_from_env(tmp_path):
    focus_dir = tmp_path / "dream_focus"
    focus_dir.mkdir()
    focus_file = focus_dir / "test_focus.json"
    focus_file.write_text(json.dumps({
        "focus_id": "test_focus",
        "priority_topics": ["topic1"],
        "forbidden_actions": ["action1"]
    }))
    
    os.environ["GREYS_DREAM_FOCUS_ID"] = "test_focus"
    os.environ["GREYS_DREAM_MODE_ENABLED"] = "1"
    
    # Mock dependencies
    transceiver = AsyncMock()
    tension_ledger = MagicMock()
    failure_ledger = MagicMock()
    stress_guard = MagicMock()
    stress_guard.is_host_under_stress.return_value = False
    
    dream = DreamMode(transceiver, tension_ledger, failure_ledger, stress_guard, focus_dir=str(focus_dir))
    
    # We only want to test the focus loading, not run the whole session
    focus_data = dream._load_initial_focus()
    assert focus_data.get("focus_id") == "test_focus"
    
    os.environ.pop("GREYS_DREAM_FOCUS_ID", None)

@pytest.mark.asyncio
async def test_dream_mode_loads_latest_focus_automatically(tmp_path):
    focus_dir = tmp_path / "dream_focus"
    focus_dir.mkdir()
    
    # Create two focus files
    f1 = focus_dir / "focus1.json"
    f1.write_text(json.dumps({"focus_id": "focus1", "priority_topics": ["t"], "forbidden_actions": ["a"]}))
    
    import time
    time.sleep(0.1)
    
    f2 = focus_dir / "focus2.json"
    f2.write_text(json.dumps({"focus_id": "focus2", "priority_topics": ["t"], "forbidden_actions": ["a"]}))
    
    dream = DreamMode(AsyncMock(), MagicMock(), MagicMock(), MagicMock(), focus_dir=str(focus_dir))
    focus_data = dream._load_initial_focus()
    
    # Should load focus2 as it is newer
    assert focus_data.get("focus_id") == "focus2"

@pytest.mark.asyncio
async def test_dream_mode_falls_back_on_invalid_focus(tmp_path):
    focus_dir = tmp_path / "dream_focus"
    focus_dir.mkdir()
    
    # Invalid focus (missing forbidden_actions)
    f1 = focus_dir / "invalid.json"
    f1.write_text(json.dumps({"focus_id": "invalid", "priority_topics": ["t"]}))
    
    dream = DreamMode(AsyncMock(), MagicMock(), MagicMock(), MagicMock(), focus_dir=str(focus_dir))
    focus_data = dream._load_initial_focus()
    
    assert focus_data == {}
