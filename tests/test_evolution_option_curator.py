import pytest
import os
import time
from pathlib import Path
from cognition.evolution_option_queue import EvolutionOption, EvolutionOptionQueue
from cognition.evolution_option_curator import EvolutionOptionCurator, CuratedEvolutionOption

@pytest.fixture
def mock_queue(tmp_path):
    queue_path = tmp_path / "evolution_option_queue.jsonl"
    queue = EvolutionOptionQueue(queue_path=str(queue_path))
    
    # Options to cluster
    options = [
        # Timeout family
        EvolutionOption(
            option_id="opt_1", timestamp=time.time(), title="Aumentar timeout",
            summary="Aumentar el timeout del LLM para evitar errores.", priority_score=1.0
        ),
        EvolutionOption(
            option_id="opt_2", timestamp=time.time(), title="Optimizar timeout LLM",
            summary="Reducir timeouts mediante optimización.", priority_score=1.2
        ),
        # Unknown failure family
        EvolutionOption(
            option_id="opt_3", timestamp=time.time(), title="Diagnosticar unknown",
            summary="Investigar fallos desconocidos.", priority_score=0.8
        ),
        # Math family
        EvolutionOption(
            option_id="opt_4", timestamp=time.time(), title="Resolver integral",
            summary="Solucionar la integral pendiente.", priority_score=1.5
        ),
        # Other
        EvolutionOption(
            option_id="opt_5", timestamp=time.time(), title="Random option",
            summary="Something else.", priority_score=0.5
        ),
    ]
    for opt in options:
        queue.append_option(opt)
    return queue

def test_evolution_option_curator_clustering(mock_queue, tmp_path):
    curated_path = tmp_path / "evolution_option_curated.jsonl"
    curator = EvolutionOptionCurator(queue=mock_queue, curated_path=str(curated_path))
    
    pending = mock_queue.list_pending()
    clusters = curator.cluster_similar_options(pending)
    
    assert len(clusters["timeout_performance"]) == 2
    assert len(clusters["unknown_failure"]) == 1
    assert len(clusters["math_integrals"]) == 1
    assert len(clusters["other"]) == 1

def test_evolution_option_curator_merging(mock_queue, tmp_path):
    curated_path = tmp_path / "evolution_option_curated.jsonl"
    curator = EvolutionOptionCurator(queue=mock_queue, curated_path=str(curated_path))
    
    curated = curator.curate_and_save()
    
    # We expect 4 curated options (3 families + 1 other)
    # Actually, in my implementation, 'other' is not currently merged into curated if it's single? 
    # Let's check implementation. Ah, 'other' is just another key in clusters.
    # The loop iterates over clusters.items(). So 'other' should be there.
    assert len(curated) == 4
    
    timeout_opt = next(c for c in curated if c.family == "timeout_performance")
    assert timeout_opt.merged_count == 2
    assert "Consolidación" in timeout_opt.title
    assert timeout_opt.priority_score == 1.2
    
    assert curated_path.exists()

def test_load_curated_pending(mock_queue, tmp_path):
    curated_path = tmp_path / "evolution_option_curated.jsonl"
    curator = EvolutionOptionCurator(queue=mock_queue, curated_path=str(curated_path))
    
    curator.curate_and_save()
    pending = curator.load_curated_pending()
    
    assert len(pending) == 4
    # Ranking by priority
    assert pending[0].priority_score == 1.5 # Math integral
