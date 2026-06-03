import pytest
import os
import ast
from pathlib import Path

def test_promoted_pdf_reader_static_safety():
    promoted_path = Path("src/skills/experimental/skill_pdf_reader_basic.py")
    assert promoted_path.exists(), "Promoted file not found"
    
    code = promoted_path.read_text()
    tree = ast.parse(code)
    
    # Check for forbidden nodes/calls
    for node in ast.walk(tree):
        if isinstance(node, ast.Call):
            func_name = ""
            if isinstance(node.func, ast.Name):
                func_name = node.func.id
            elif isinstance(node.func, ast.Attribute):
                func_name = node.func.attr
                
            assert func_name not in ["eval", "exec", "system", "popen", "spawn"], f"Dangerous call detected: {func_name}"
            
    # Check for library usage
    assert "import pypdf" in code
    assert "import os" in code # Allowed for Medium Risk metadata

def test_promoted_pdf_reader_compiles():
    import py_compile
    res = py_compile.compile("src/skills/experimental/skill_pdf_reader_basic.py")
    assert res is not None

def test_promoted_pdf_reader_has_limits():
    code = Path("src/skills/experimental/skill_pdf_reader_basic.py").read_text()
    assert "MAX_FILE_SIZE_BYTES = 5 * 1024 * 1024" in code
    assert "MAX_CHARS = 30000" in code
    assert "extracted_text[:500]" in code # Preview
