"""
IMAIRA FairScore — Comprehensive Confidence-Aware Uncertainty Engine Test Suite
==============================================================================
Validates:
1. ASR Uncertainty Detection & Dimension Separation (Recognition vs Rubric).
2. Audio Slice Verification (Confirm, Abstain, Unresolved).
3. Provisional Scoring Policy & Fairness Guards.
4. Human-in-the-Loop Audit & Rescoring Workflow.
"""

import pytest
from pathlib import Path
from contracts.transcript import WordTiming
from score.uncertainty_models import (
    UncertaintyRecord,
    UncertaintyPolicy,
    RecognitionStatus,
    RubricStatus
)
from score.uncertainty_engine import UncertaintyEngine
from score.evidence_models import (
    RubricCriterion,
    QuestionDefinition,
    EvidenceScorecard,
    CriterionEvaluation,
    EvidenceItem
)
from score.evidence_scorer import DeterministicEvidenceScorer


@pytest.fixture
def sample_question() -> QuestionDefinition:
    return QuestionDefinition(
        question_id="TEST_DS_001",
        question="What is a hash map and how does it handle collisions?",
        domain="Data Structures",
        difficulty="Intermediate",
        total_marks=10.0,
        expected_concepts=["Key-Value Mapping", "Hash Function", "Chaining", "Open Addressing"],
        rubric=[
            RubricCriterion(
                criterion_id="R1",
                description="Defines a hash map as an associative data structure mapping keys to values using a hash function.",
                max_points=2.5,
                acceptable_alternatives=["hash table", "associative array"]
            ),
            RubricCriterion(
                criterion_id="R2",
                description="Explains collision concept where multiple keys hash to the same bucket index.",
                max_points=2.5,
                acceptable_alternatives=["hash collision", "index conflict"]
            ),
            RubricCriterion(
                criterion_id="R3",
                description="Explains Separate Chaining using linked lists or trees per bucket.",
                max_points=2.5,
                acceptable_alternatives=["chaining", "linked list in bucket"]
            ),
            RubricCriterion(
                criterion_id="R4",
                description="Explains Open Addressing using linear probing to search adjacent slots.",
                max_points=2.5,
                acceptable_alternatives=["linear probing", "probing"]
            )
        ]
    )


@pytest.fixture
def engine() -> UncertaintyEngine:
    return UncertaintyEngine()


@pytest.fixture
def scorer() -> DeterministicEvidenceScorer:
    return DeterministicEvidenceScorer()


# -------------------------------------------------------------------------------------------------
# 1. ASR UNCERTAINTY DETECTION TESTS
# -------------------------------------------------------------------------------------------------

def test_asr_uncertainty_low_confidence_flagged(sample_question, engine):
    """Low ASR confidence below threshold must be flagged as suspicious."""
    word_timings = [
        WordTiming(word="A", start=0.0, end=0.2, conf=0.98),
        WordTiming(word="hash", start=0.3, end=0.6, conf=0.42),  # low conf!
        WordTiming(word="map", start=0.7, end=1.0, conf=0.95),
        WordTiming(word="handles", start=1.1, end=1.5, conf=0.92),
        WordTiming(word="collisions", start=1.6, end=2.2, conf=0.88),
    ]

    records = engine.detect_suspicious_segments(word_timings, sample_question)
    assert len(records) >= 1
    low_conf_rec = next(r for r in records if r.original_text == "hash")
    assert low_conf_rec.uncertainty_level in ("medium", "high")
    assert low_conf_rec.asr_confidence == 0.42
    assert "R1" in low_conf_rec.linked_criterion_ids


def test_asr_uncertainty_phonetic_confusion_detection(sample_question, engine):
    """Phonetic substitution (e.g. 'has map' for 'hash map') is detected as candidate error."""
    word_timings = [
        WordTiming(word="a", start=0.0, end=0.2, conf=0.90),
        WordTiming(word="has", start=0.3, end=0.5, conf=0.75),  # resembles 'hash'
        WordTiming(word="map", start=0.6, end=0.9, conf=0.90),
    ]

    records = engine.detect_suspicious_segments(word_timings, sample_question)
    assert len(records) >= 1
    has_rec = next(r for r in records if r.original_text == "has")
    assert has_rec.corrected_text == "hash"
    assert "R1" in has_rec.linked_criterion_ids


def test_asr_uncertainty_graceful_missing_confidence(sample_question, engine):
    """When ASR provider supplies no confidence score, gracefully label 'unavailable'."""
    word_timings = [
        WordTiming(word="chain", start=2.0, end=2.5, conf=None),  # Missing conf
    ]

    records = engine.detect_suspicious_segments(word_timings, sample_question)
    assert len(records) >= 1
    assert records[0].uncertainty_level == "unavailable"


# -------------------------------------------------------------------------------------------------
# 2. AUDIO VERIFICATION TESTS
# -------------------------------------------------------------------------------------------------

def test_audio_verification_confirms_correction(engine):
    """When audio supports the proposed candidate, mark audio_verified."""
    rec = UncertaintyRecord(
        segment_id="S001",
        question_id="TEST_DS_001",
        original_text="has map",
        corrected_text="hash map",
        start=1.0,
        end=2.0,
        asr_confidence=0.55
    )

    # Phonetic similarity between 'has map' and 'hash map' is >= 85%
    verified_rec = engine.verify_segment_against_audio(rec, audio_path=None)
    # Without audio file, stays unresolved
    assert verified_rec.correction_status == "unresolved"

    # With mock recovery pipeline that confirms correction
    class MockRecoveryPipeline:
        def recheck_span(self, audio_path, t_start, t_end, candidate_term):
            return {"decision": "CORRECTED", "recheck_conf": 0.92}

    import tempfile
    with tempfile.NamedTemporaryFile(suffix=".wav") as tmp:
        p = Path(tmp.name)
        v_rec = engine.verify_segment_against_audio(rec, audio_path=p, recovery_pipeline=MockRecoveryPipeline())
        assert v_rec.correction_status == "audio_verified"
        assert v_rec.recognition_status == "verified"
        assert v_rec.rubric_status == "satisfied"


def test_audio_verification_supports_original(engine):
    """When acoustic slice recheck rejects correction, preserve original transcript."""
    rec = UncertaintyRecord(
        segment_id="S002",
        question_id="TEST_DS_001",
        original_text="has table",
        corrected_text="hash map",
        start=1.0,
        end=2.0,
        asr_confidence=0.70
    )

    class MockRecoveryAbstain:
        def recheck_span(self, audio_path, t_start, t_end, candidate_term):
            return {"decision": "ABSTAINED", "recheck_conf": 0.20}

    import tempfile
    with tempfile.NamedTemporaryFile(suffix=".wav") as tmp:
        p = Path(tmp.name)
        v_rec = engine.verify_segment_against_audio(rec, audio_path=p, recovery_pipeline=MockRecoveryAbstain())
        assert v_rec.correction_status == "no_correction"
        assert v_rec.recognition_status == "verified"


# -------------------------------------------------------------------------------------------------
# 3. RUBRIC INTEGRATION & PROVISIONAL SCORING TESTS
# -------------------------------------------------------------------------------------------------

def test_rubric_uncertainty_provisional_credit_for_ambiguous_audio(sample_question, scorer, engine):
    """
    CRITICAL RULE: Recognition uncertainty must not become rubric failure.
    If a criterion is missing purely because audio is ambiguous, award capped provisional credit.
    """
    transcript = "We handle collisions using open addressing."
    raw_evals = [
        {"criterion_id": "R1", "status": "missing", "evidence": [], "reason": ""},  # ASR was unclear on hash map
        {"criterion_id": "R2", "status": "missing", "evidence": [], "reason": ""},
        {"criterion_id": "R3", "status": "missing", "evidence": [], "reason": ""},
        {"criterion_id": "R4", "status": "satisfied", "evidence": [{"text": "open addressing"}], "reason": "Accurate"}
    ]

    # S001 is ambiguous on R1
    u_recs = [
        UncertaintyRecord(
            segment_id="S001",
            question_id="TEST_DS_001",
            original_text="has mumble",
            corrected_text="hash map",
            start=0.5,
            end=1.5,
            asr_confidence=0.40,
            recognition_status="uncertain",
            correction_status="unresolved",
            linked_criterion_ids=["R1"]
        )
    ]

    scorecard = scorer.calculate_scorecard(
        question=sample_question,
        raw_evidence_evaluations=raw_evals,
        misconceptions=[],
        transcript_text=transcript,
        raw_structure_scores={"framing": 3.0, "coherence": 3.0, "closure": 3.0},
        uncertainty_records=u_recs,
        uncertainty_engine=engine
    )

    r1_eval = next(c for c in scorecard.criteria_evaluations if c.criterion_id == "R1")
    # Candidate awarded capped provisional credit rather than 0 marks
    assert r1_eval.evaluation_state == "provisional"
    assert r1_eval.awarded_points == round(2.5 * 0.50, 2)  # 1.25 pts
    assert r1_eval.provisional_marks == 1.25
    assert scorecard.provisional_score_active is True
    assert scorecard.evaluation_state == "provisional"
    assert "IMAIRA could not reliably establish one technical term" in r1_eval.uncertainty_notice


def test_rubric_uncertainty_genuine_missing_knowledge_gets_zero(sample_question, scorer, engine):
    """Genuine missing concept with clear audio gets 0 marks without false provisional credit."""
    transcript = "A hash map maps keys to values."
    raw_evals = [
        {"criterion_id": "R1", "status": "satisfied", "evidence": [{"text": "maps keys to values"}], "reason": ""},
        {"criterion_id": "R2", "status": "missing", "evidence": [], "reason": ""},
        {"criterion_id": "R3", "status": "missing", "evidence": [], "reason": ""},
        {"criterion_id": "R4", "status": "missing", "evidence": [], "reason": ""}
    ]

    # No uncertainty records linked to R2, R3, or R4
    scorecard = scorer.calculate_scorecard(
        question=sample_question,
        raw_evidence_evaluations=raw_evals,
        misconceptions=[],
        transcript_text=transcript,
        raw_structure_scores={"framing": 3.0, "coherence": 3.0, "closure": 3.0},
        uncertainty_records=[],
        uncertainty_engine=engine
    )

    r3_eval = next(c for c in scorecard.criteria_evaluations if c.criterion_id == "R3")
    assert r3_eval.awarded_points == 0.0
    assert r3_eval.evaluation_state == "final_verified"
    assert scorecard.provisional_score_active is False


def test_audio_verified_correction_earns_full_credit(sample_question, scorer, engine):
    """When acoustic recheck confirms spoken term, award full 100% credit for the criterion."""
    transcript = "A hash map maps keys to values. We use separate chaining to handle collisions."
    raw_evals = [
        {"criterion_id": "R1", "status": "satisfied", "evidence": [{"text": "maps keys to values"}], "reason": ""},
        {"criterion_id": "R2", "status": "missing", "evidence": [], "reason": ""},  # initially missed due to 'collishun'
        {"criterion_id": "R3", "status": "satisfied", "evidence": [{"text": "separate chaining"}], "reason": ""},
        {"criterion_id": "R4", "status": "missing", "evidence": [], "reason": ""}
    ]

    u_recs = [
        UncertaintyRecord(
            segment_id="S003",
            question_id="TEST_DS_001",
            original_text="collishun",
            corrected_text="collision",
            start=4.0,
            end=4.8,
            asr_confidence=0.50,
            recognition_status="verified",
            correction_status="audio_verified",  # Audio confirmed!
            linked_criterion_ids=["R2"]
        )
    ]

    scorecard = scorer.calculate_scorecard(
        question=sample_question,
        raw_evidence_evaluations=raw_evals,
        misconceptions=[],
        transcript_text=transcript,
        raw_structure_scores={"framing": 4.0, "coherence": 4.0, "closure": 4.0},
        uncertainty_records=u_recs,
        uncertainty_engine=engine
    )

    r2_eval = next(c for c in scorecard.criteria_evaluations if c.criterion_id == "R2")
    assert r2_eval.status == "satisfied"
    assert r2_eval.awarded_points == 2.5
    assert r2_eval.evaluation_state == "final_verified"


# -------------------------------------------------------------------------------------------------
# 4. HUMAN-IN-THE-LOOP AUDITABILITY TESTS
# -------------------------------------------------------------------------------------------------

def test_human_review_approval_elevates_to_final_verified(sample_question, scorer, engine):
    """Human approval of uncertain segment upgrades score from provisional to final verified."""
    transcript = "Linear probing checks adjacent slots."
    raw_evals = [
        {"criterion_id": "R1", "status": "missing", "evidence": [], "reason": ""},
        {"criterion_id": "R2", "status": "missing", "evidence": [], "reason": ""},
        {"criterion_id": "R3", "status": "missing", "evidence": [], "reason": ""},
        {"criterion_id": "R4", "status": "satisfied", "evidence": [{"text": "linear probing"}], "reason": ""}
    ]

    u_recs = [
        UncertaintyRecord(
            segment_id="S010",
            question_id="TEST_DS_001",
            original_text="mumble chaining",
            corrected_text="separate chaining",
            start=1.0,
            end=2.0,
            recognition_status="uncertain",
            correction_status="unresolved",
            linked_criterion_ids=["R3"]
        )
    ]

    # Initial provisional scorecard
    scorecard = scorer.calculate_scorecard(
        question=sample_question,
        raw_evidence_evaluations=raw_evals,
        misconceptions=[],
        transcript_text=transcript,
        raw_structure_scores={"framing": 3.0, "coherence": 3.0, "closure": 3.0},
        uncertainty_records=u_recs,
        uncertainty_engine=engine
    )

    assert scorecard.evaluation_state == "provisional"
    init_marks = scorecard.total_awarded_marks  # R4(2.5) + R3 provisional(1.25) = 3.75

    # Human expert reviews audio and approves!
    rescored = engine.apply_human_review(
        scorecard=scorecard,
        segment_id="S010",
        decision="human_approved",
        approved_text="separate chaining",
        reviewer_notes="Audio clearly articulates separate chaining with light background hum."
    )

    assert rescored.evaluation_state == "final_verified"
    assert rescored.provisional_score_active is False
    r3_eval = next(c for c in rescored.criteria_evaluations if c.criterion_id == "R3")
    assert r3_eval.awarded_points == 2.5  # Upgraded to full marks
    assert rescored.total_awarded_marks == 2.5 + 2.5  # 5.0


def test_human_review_rejection_confirms_missing(sample_question, scorer, engine):
    """Human rejection of uncertain segment revokes provisional marks to 0.0 with confirmed gap."""
    transcript = "Linear probing checks adjacent slots."
    raw_evals = [
        {"criterion_id": "R1", "status": "missing", "evidence": [], "reason": ""},
        {"criterion_id": "R2", "status": "missing", "evidence": [], "reason": ""},
        {"criterion_id": "R3", "status": "missing", "evidence": [], "reason": ""},
        {"criterion_id": "R4", "status": "satisfied", "evidence": [{"text": "linear probing"}], "reason": ""}
    ]

    u_recs = [
        UncertaintyRecord(
            segment_id="S011",
            question_id="TEST_DS_001",
            original_text="mumble chaining",
            corrected_text="separate chaining",
            start=1.0,
            end=2.0,
            recognition_status="uncertain",
            correction_status="unresolved",
            linked_criterion_ids=["R3"]
        )
    ]

    scorecard = scorer.calculate_scorecard(
        question=sample_question,
        raw_evidence_evaluations=raw_evals,
        misconceptions=[],
        transcript_text=transcript,
        raw_structure_scores={"framing": 3.0, "coherence": 3.0, "closure": 3.0},
        uncertainty_records=u_recs,
        uncertainty_engine=engine
    )

    # Human expert listens and confirms candidate said "simple training", NOT "separate chaining"
    rescored = engine.apply_human_review(
        scorecard=scorecard,
        segment_id="S011",
        decision="human_rejected",
        reviewer_notes="Candidate said 'simple training', which is not a collision technique."
    )

    assert rescored.evaluation_state == "final_verified"
    r3_eval = next(c for c in rescored.criteria_evaluations if c.criterion_id == "R3")
    assert r3_eval.awarded_points == 0.0
    assert r3_eval.status == "missing"
    assert rescored.total_awarded_marks == 2.5  # Only R4 remains
