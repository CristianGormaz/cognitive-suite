import json
from core.dream_focus_validator import DreamFocusValidator

def test_dream_focus_validator_valid():
    validator = DreamFocusValidator()
    valid_json = {
        "focus_id": "test",
        "priority_topics": ["a"],
        "forbidden_actions": ["b"]
    }
    assert validator.validate_json(json.dumps(valid_json)) is True

def test_dream_focus_validator_invalid_missing_fields():
    validator = DreamFocusValidator()
    invalid_json = {"focus_id": "test"}
    assert validator.validate_json(json.dumps(invalid_json)) is False

def test_dream_focus_validator_invalid_empty_forbidden():
    validator = DreamFocusValidator()
    invalid_json = {
        "focus_id": "test",
        "priority_topics": ["a"],
        "forbidden_actions": []
    }
    assert validator.validate_json(json.dumps(invalid_json)) is False

def test_dream_focus_validator_malformed_json():
    validator = DreamFocusValidator()
    assert validator.validate_json("{invalid") is False
