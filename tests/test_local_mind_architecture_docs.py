import pytest
from pathlib import Path

def test_docs_exist():
    docs = [
        "docs/LOCAL_MIND_ARCHITECTURE.md",
        "docs/MINIMAL_NEURAL_LAYER.md",
        "docs/DEEPSEEK_EXPERIENCE_DISTILLATION.md"
    ]
    for d in docs:
        assert Path(d).exists(), f"Document {d} missing"

def test_architecture_concepts_present():
    content = Path("docs/LOCAL_MIND_ARCHITECTURE.md").read_text()
    assert "Reflex Kernel" in content
    assert "Narrative Layer" in content
    assert "Dual-Piece" in content or "Dos Piezas" in content
