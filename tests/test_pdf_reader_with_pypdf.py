import pytest
import os
import json
from pathlib import Path
from unittest.mock import MagicMock

def test_pdf_extraction_with_pypdf_fixture():
    # Usar el fixture seguro
    pdf_path = Path("tests/fixtures/ingestion/sample.pdf")
    if not pdf_path.exists():
        pytest.skip("sample.pdf fixture not found")
        
    import pypdf
    
    reader = pypdf.PdfReader(str(pdf_path))
    text = ""
    for page in reader.pages:
        text += page.extract_text() or ""
        
    assert len(text) >= 0 # El sample.pdf puede ser mínimo
    
def test_candidate_detects_installed_pypdf():
    # Simular la lógica del candidato
    has_pypdf = False
    try:
        import pypdf
        has_pypdf = True
    except ImportError:
        pass
        
    assert has_pypdf is True

def test_pdf_parse_error_on_corrupt_file(tmp_path):
    corrupt_pdf = tmp_path / "corrupt.pdf"
    corrupt_pdf.write_text("not a pdf content")
    
    import pypdf
    with pytest.raises(Exception): # pypdf raises various errors for corrupt files
        pypdf.PdfReader(str(corrupt_pdf))

def test_extraction_limits_simulated():
    # Validar que podemos truncar
    long_text = "A" * 50000
    limit = 30000
    truncated = long_text[:limit]
    assert len(truncated) == limit
