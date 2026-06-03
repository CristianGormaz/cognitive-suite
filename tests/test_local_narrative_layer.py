import pytest
import os
from core.local_narrative_layer import LocalNarrativeLayer, NarrativeResponse

def test_explain_llm_timeout():
    layer = LocalNarrativeLayer()
    res = layer.explain_signal("llm_timeout")
    
    assert "latencia" in res.user_facing_summary
    assert "LlmTimeoutError" in res.technical_summary
    assert res.reassurance_level == "corrective"

def test_explain_host_stress():
    layer = LocalNarrativeLayer()
    res = layer.explain_signal("host_stress_block")
    
    assert "alta carga" in res.user_facing_summary
    assert res.reassurance_level == "protective"

def test_render_user_message():
    layer = LocalNarrativeLayer()
    res = layer.explain_signal("llm_timeout")
    msg = layer.render_user_message(res)
    
    assert "latencia" in msg
    assert "Recomendación:" in msg

def test_render_technical_message():
    layer = LocalNarrativeLayer()
    res = layer.explain_signal("llm_timeout")
    msg = layer.render_technical_message(res)
    
    assert "[LOG]:" in msg
    assert "LlmTimeoutError" in msg
