import pytest
from core.quorum_promotion_readiness import QuorumPromotionReadiness, QuorumEvidence

@pytest.fixture
def readiness(tmp_path):
    return QuorumPromotionReadiness(memory_dir=str(tmp_path))

def test_qrs_increases_with_unique_evidence(readiness):
    evidence = [
        QuorumEvidence(
            source="src1", evidence_type="test", candidate_id="c1",
            signal_count=5, unique_signal_count=4, duplicate_count=1,
            confidence=0.9, temporal_span_hours=24.0, risk_score=0.0,
            context_score=0.9, human_approval_present=False, rollback_available=True
        ),
        QuorumEvidence(
            source="src2", evidence_type="test", candidate_id="c1",
            signal_count=5, unique_signal_count=4, duplicate_count=1,
            confidence=0.9, temporal_span_hours=24.0, risk_score=0.0,
            context_score=0.9, human_approval_present=False, rollback_available=True
        )
    ]
    assessment = readiness.assess_candidate("c1", "reflex", evidence)
    assert assessment.quorum_readiness_score > 0.0
    assert assessment.readiness_state == "ready_for_human_review"

def test_qrs_penalizes_duplicates(readiness):
    # Alta redundancia: 10 señales, solo 1 única
    evidence = [
        QuorumEvidence(
            source="src1", evidence_type="test", candidate_id="c1",
            signal_count=10, unique_signal_count=1, duplicate_count=9,
            confidence=0.9, temporal_span_hours=24.0, risk_score=0.0,
            context_score=0.9, human_approval_present=False, rollback_available=True
        )
    ]
    assessment = readiness.assess_candidate("c1", "reflex", evidence)
    assert assessment.duplication_penalty > 0.3
    assert assessment.readiness_state == "false_quorum_suspected"

def test_qrs_penalizes_single_source_rumination(readiness):
    # Muchos señales de una sola fuente
    evidence = [
        QuorumEvidence(
            source="dream_mode", evidence_type="dream", candidate_id="c1",
            signal_count=20, unique_signal_count=15, duplicate_count=5,
            confidence=0.8, temporal_span_hours=1.0, risk_score=0.0,
            context_score=0.8, human_approval_present=False, rollback_available=True
        )
    ]
    assessment = readiness.assess_candidate("c1", "reflex", evidence)
    assert assessment.false_quorum_risk > 0.2
    assert assessment.readiness_state == "false_quorum_suspected"

def test_qrs_requires_rollback(readiness):
    evidence = [
        QuorumEvidence(
            source="src1", evidence_type="test", candidate_id="c1",
            signal_count=10, unique_signal_count=10, duplicate_count=0,
            confidence=1.0, temporal_span_hours=48.0, risk_score=0.0,
            context_score=1.0, human_approval_present=True, rollback_available=False
        )
    ]
    assessment = readiness.assess_candidate("c1", "reflex", evidence)
    assert assessment.readiness_state == "insufficient_evidence"
    assert "Rollback no disponible" in assessment.reason_summary

def test_promotion_allowed_always_false(readiness):
    evidence = [
        QuorumEvidence(
            source="src1", evidence_type="test", candidate_id="c1",
            signal_count=100, unique_signal_count=100, duplicate_count=0,
            confidence=1.0, temporal_span_hours=100.0, risk_score=0.0,
            context_score=1.0, human_approval_present=True, rollback_available=True
        )
    ]
    assessment = readiness.assess_candidate("c1", "reflex", evidence)
    assert assessment.promotion_allowed is False
