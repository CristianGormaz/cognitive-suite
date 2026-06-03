import pytest
from core.bio_inspired_pattern_atlas import BioInspiredPatternAtlas

def test_atlas_lists_patterns():
    atlas = BioInspiredPatternAtlas()
    patterns = atlas.list_patterns()
    assert len(patterns) >= 5
    ids = [p.pattern_id for p in patterns]
    assert "dendritic_preprocessing" in ids
    assert "quorum_sensing" in ids

def test_get_pattern():
    atlas = BioInspiredPatternAtlas()
    p = atlas.get_pattern("basket_cell_inhibition")
    assert p is not None
    assert "IAFA" in p.greys_equivalent

def test_summarize_risks():
    atlas = BioInspiredPatternAtlas()
    risks = atlas.summarize_risks()
    assert len(risks) >= 5
    assert "anti_pattern" in risks[0]
    assert "danger" in risks[0]
