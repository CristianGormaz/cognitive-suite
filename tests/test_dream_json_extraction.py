import pytest
import json
from cognition.dream_mode import DreamMode, DreamLlmParseError

def test_extract_json_object_safely_basic():
    text = '{"summary": "test", "evolution_options": []}'
    result = DreamMode.extract_json_object_safely(text)
    assert result["summary"] == "test"

def test_extract_json_object_safely_with_think():
    text = '<think>some reasoning</think>{"summary": "test", "evolution_options": []}'
    result = DreamMode.extract_json_object_safely(text)
    assert result["summary"] == "test"

def test_extract_json_object_safely_truncated():
    text = 'some text before {"summary": "test", "evolution_options": []} some text after'
    result = DreamMode.extract_json_object_safely(text)
    assert result["summary"] == "test"

def test_extract_json_object_safely_fails_on_unterminated():
    text = '{"summary": "test", "evolution_options":'
    with pytest.raises(DreamLlmParseError) as excinfo:
        DreamMode.extract_json_object_safely(text)
    assert "No JSON object found" in str(excinfo.value)

def test_extract_json_object_safely_malformed_but_balanced():
    # If it has { and } but is still malformed JSON
    text = '{"summary": "test", "evolution_options": [}'
    with pytest.raises(DreamLlmParseError) as excinfo:
        DreamMode.extract_json_object_safely(text)
    assert "Malformed or truncated JSON" in str(excinfo.value)

def test_extract_json_object_safely_empty():
    with pytest.raises(DreamLlmParseError) as excinfo:
        DreamMode.extract_json_object_safely("")
    assert "Empty response" in str(excinfo.value)
