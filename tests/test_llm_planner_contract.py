import pytest
from cognition.llm_planner import LLMPlanner, LLMPlanParseError
from core.task_envelope import TaskEnvelope

def test_extract_json_clean():
    raw = '{"intent_category": "chat", "proposed_action": "respond", "iafa_friction_estimates": {"R": 0.1, "I": 0.1, "N": 0.1}, "execution_payload": {"target_path": "n/a", "extracted_tags": []}}'
    thought, json_text = LLMPlanner.extract_thought_and_json(raw)
    assert thought == ""
    assert json_text == raw

def test_extract_json_with_think():
    raw = '<think>I should respond to this.</think>{"intent_category": "chat", "proposed_action": "respond", "iafa_friction_estimates": {"R": 0.1, "I": 0.1, "N": 0.1}, "execution_payload": {"target_path": "n/a", "extracted_tags": []}}'
    thought, json_text = LLMPlanner.extract_thought_and_json(raw)
    assert thought == "I should respond to this."
    assert json_text.startswith("{")
    assert json_text.endswith("}")

def test_extract_json_with_text_around():
    raw = 'Sure! Here is the plan: {"intent_category": "chat", "proposed_action": "respond", "iafa_friction_estimates": {"R": 0.1, "I": 0.1, "N": 0.1}, "execution_payload": {"target_path": "n/a", "extracted_tags": []}} Hope it helps!'
    thought, json_text = LLMPlanner.extract_thought_and_json(raw)
    assert json_text.startswith("{")
    assert json_text.endswith("}")
    assert "intent_category" in json_text

def test_extract_json_with_emoji():
    raw = '{"intent_category": "chat", "proposed_action": "respond", "iafa_friction_estimates": {"R": 0.1, "I": 0.1, "N": 0.1}, "execution_payload": {"target_path": "n/a", "extracted_tags": []}} 😊'
    thought, json_text = LLMPlanner.extract_thought_and_json(raw)
    assert json_text.startswith("{")
    assert json_text.endswith("}")

def test_extract_json_with_spanish_text():
    raw = 'Aquí tienes el JSON: {"intent_category": "chat", "proposed_action": "respond", "iafa_friction_estimates": {"R": 0.1, "I": 0.1, "N": 0.1}, "execution_payload": {"target_path": "n/a", "extracted_tags": []}}'
    thought, json_text = LLMPlanner.extract_thought_and_json(raw)
    assert json_text.startswith("{")
    assert json_text.endswith("}")

def test_extract_json_invalid():
    raw = 'No JSON here!'
    with pytest.raises(LLMPlanParseError):
        LLMPlanner.extract_thought_and_json(raw)

def test_extract_json_unbalanced():
    raw = '{"intent": "chat" oops'
    with pytest.raises(LLMPlanParseError):
        LLMPlanner.extract_thought_and_json(raw)
