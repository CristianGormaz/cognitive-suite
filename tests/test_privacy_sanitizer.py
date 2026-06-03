import pytest
from core.privacy_sanitizer import sanitize_path_for_logs, redact_local_paths, sanitize_exception_message

def test_redact_local_paths():
    text = "Error in /home/user/greys-v3/main.py at line 10"
    redacted = redact_local_paths(text)
    assert "/home/[REDACTED]" in redacted
    assert "user" not in redacted
    assert "greys-v3" in redacted # greys-v3 is not part of the user path pattern

def test_sanitize_path_for_logs():
    path = "/home/user/secret/file.pdf"
    sanitized = sanitize_path_for_logs(path)
    assert sanitized.startswith("file_ref:")
    assert "file.pdf" in sanitized
    assert "user" not in sanitized
    assert "secret" not in sanitized

def test_sanitize_exception_message():
    try:
        raise FileNotFoundError("Could not find /home/user/data.txt")
    except Exception as e:
        sanitized = sanitize_exception_message(e)
        assert "/home/[REDACTED]" in sanitized
        assert "user" not in sanitized
