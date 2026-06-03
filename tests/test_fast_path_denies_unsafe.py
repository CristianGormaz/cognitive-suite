import pytest
from core.fast_path_reflex_gate import FastPathReflexGate

@pytest.fixture
def gate(tmp_path):
    return FastPathReflexGate(memory_dir=str(tmp_path))

def test_fast_path_denies_ambiguous_or_generalized(gate):
    # Intentos generalizados del clasificador
    assessment = gate.assess_reflex(
        pattern_id="p1", reflex_name="generalized_greeting_reflex", input_signature="hola",
        active_local=True, risk_score=0.0, human_approved=True, rollback_available=True
    )
    assert assessment.fast_path_allowed is False
    assert assessment.block_reason == "is_ambiguous_or_generalized"
    
    # unknown_safe
    assessment2 = gate.assess_reflex(
        pattern_id="p2", reflex_name="no_action_unknown_safe", input_signature="hola",
        active_local=True, risk_score=0.0, human_approved=True, rollback_available=True
    )
    assert assessment2.fast_path_allowed is False
    assert assessment2.block_reason == "is_ambiguous_or_generalized"

def test_fast_path_denies_side_effects(gate):
    # Uso de LLM
    assessment = gate.assess_reflex(
        pattern_id="p1", reflex_name="basic_greeting_reflex", input_signature="hola",
        active_local=True, risk_score=0.0, human_approved=True, rollback_available=True,
        uses_llm=True
    )
    assert assessment.fast_path_allowed is False
    assert assessment.block_reason == "has_prohibited_side_effects"

    # Uso de Archivos
    assessment2 = gate.assess_reflex(
        pattern_id="p1", reflex_name="basic_greeting_reflex", input_signature="hola",
        active_local=True, risk_score=0.0, human_approved=True, rollback_available=True,
        uses_files=True
    )
    assert assessment2.fast_path_allowed is False
