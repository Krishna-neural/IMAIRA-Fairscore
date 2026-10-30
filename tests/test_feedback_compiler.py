"""
Unit and Integration Tests for Implementation 4: Feedback Compiler
==================================================================
Verifies:
1. Deterministic ranking by marks lost (Marks Lost = Max Marks - Awarded Marks)
2. Top-3 selection by default, and fewer when fewer genuine weaknesses exist
3. No artificial weaknesses or duplicate concept generation
4. Quote validation (rejects fabricated quotes, allows verified quotes)
5. Timestamp validation (rejects inverted, negative, or out-of-bounds timestamps)
6. Confidence-Aware filtering (unresolved ASR cannot generate punitive knowledge-gap feedback)
7. Anti-fluff and conciseness validation
8. Personalized Improvement Plan generation (Objectives, Practice Task, Self-Assessment)
9. End-to-end report compilation and export
"""

import pytest
from pathlib import Path

from score.feedback_models import (
    FeedbackCompilerInput,
    FeedbackCriterionInput,
    FeedbackOpportunity,
    EvidenceQuote,
    CompiledFeedbackReport
)
from score.feedback_validator import FeedbackValidator
from score.feedback_compiler import FeedbackCompiler
from score.evidence_models import (
    EvidenceScorecard,
    CriterionEvaluation,
    EvidenceItem
)


@pytest.fixture
def sample_compiler_input():
    return FeedbackCompilerInput(
        interview_id="TEST_INT_001",
        question_id="DS_001",
        question_text="What is a hash map and how does it handle collisions?",
        rubric_version="1.0",
        total_marks=10.0,
        criteria=[
            FeedbackCriterionInput(
                criterion_id="R1",
                description="Defines a hash map using key-value pairs and hashing",
                max_points=2.0,
                awarded_points=2.0,
                marks_lost=0.0,
                status="satisfied",
                evidence_quotes=[
                    EvidenceQuote(quote="A hash map stores key-value pairs using a hash function.", start=2.0, end=6.5)
                ]
            ),
            FeedbackCriterionInput(
                criterion_id="R2",
                description="Explains collision resolution using separate chaining",
                max_points=3.0,
                awarded_points=1.0,
                marks_lost=2.0,
                status="partially_satisfied",
                evidence_quotes=[
                    EvidenceQuote(quote="Sometimes keys collide at the same bucket.", start=10.0, end=14.0)
                ],
                missing_concepts=["Linked list chaining at bucket", "Lookup degradation to O(k)"]
            ),
            FeedbackCriterionInput(
                criterion_id="R3",
                description="Explains open addressing techniques: linear probing and quadratic probing",
                max_points=3.0,
                awarded_points=0.0,
                marks_lost=3.0,
                status="missing",
                evidence_quotes=[],
                missing_concepts=["Linear probing", "Quadratic probing", "Double hashing"]
            ),
            FeedbackCriterionInput(
                criterion_id="R4",
                description="Analyzes average O(1) vs worst-case O(n) time complexity",
                max_points=2.0,
                awarded_points=1.0,
                marks_lost=1.0,
                status="partially_satisfied",
                evidence_quotes=[
                    EvidenceQuote(quote="It is O(1) on average.", start=22.0, end=25.0)
                ]
            )
        ],
        original_transcript="A hash map stores key-value pairs using a hash function. Sometimes keys collide at the same bucket. It is O(1) on average.",
        corrected_transcript="A hash map stores key-value pairs using a hash function. Sometimes keys collide at the same bucket. It is O(1) on average.",
        audio_duration_sec=35.0
    )


# ==============================================================================
# 1. Deterministic Ranking Tests
# ==============================================================================

def test_deterministic_ranking_by_marks_lost(sample_compiler_input):
    compiler = FeedbackCompiler()
    ranked = compiler.rank_weaknesses(sample_compiler_input.criteria)

    # Criteria lost: R3 (3.0 pts), R2 (2.0 pts), R4 (1.0 pt), R1 (0.0 pts - excluded)
    assert len(ranked) == 3
    assert ranked[0].criterion_id == "R3"
    assert ranked[0].marks_lost == 3.0
    assert ranked[1].criterion_id == "R2"
    assert ranked[1].marks_lost == 2.0
    assert ranked[2].criterion_id == "R4"
    assert ranked[2].marks_lost == 1.0


def test_tie_breaking_prioritizes_missing_over_partial():
    compiler = FeedbackCompiler()
    criteria = [
        FeedbackCriterionInput(
            criterion_id="CRIT_A",
            description="Concept A",
            max_points=2.0,
            awarded_points=1.0,
            marks_lost=1.0,
            status="partially_satisfied"
        ),
        FeedbackCriterionInput(
            criterion_id="CRIT_B",
            description="Concept B",
            max_points=2.0,
            awarded_points=1.0,
            marks_lost=1.0,
            status="missing"
        )
    ]
    ranked = compiler.rank_weaknesses(criteria)
    # Both lost 1.0 mark, but CRIT_B is completely missing -> should rank first
    assert ranked[0].criterion_id == "CRIT_B"
    assert ranked[1].criterion_id == "CRIT_A"


# ==============================================================================
# 2. Top-3 Selection & Non-Fabrication Tests
# ==============================================================================

def test_top_three_selection_default(sample_compiler_input):
    compiler = FeedbackCompiler(max_opportunities=3)
    ranked = compiler.rank_weaknesses(sample_compiler_input.criteria)
    top_opps = compiler.select_top_opportunities(ranked)

    assert len(top_opps) == 3
    assert [o.criterion_id for o in top_opps] == ["R3", "R2", "R4"]


def test_fewer_than_three_weaknesses_does_not_fabricate_filler():
    compiler = FeedbackCompiler(max_opportunities=3)
    # Only 1 criterion lost marks
    criteria = [
        FeedbackCriterionInput(
            criterion_id="C1",
            description="Concept 1",
            max_points=5.0,
            awarded_points=5.0,
            marks_lost=0.0,
            status="satisfied"
        ),
        FeedbackCriterionInput(
            criterion_id="C2",
            description="Concept 2",
            max_points=5.0,
            awarded_points=3.0,
            marks_lost=2.0,
            status="partially_satisfied"
        )
    ]
    ranked = compiler.rank_weaknesses(criteria)
    top_opps = compiler.select_top_opportunities(ranked)

    # Must return exactly 1 recommendation, not 3!
    assert len(top_opps) == 1
    assert top_opps[0].criterion_id == "C2"


def test_completely_correct_answer_generates_zero_weaknesses():
    compiler = FeedbackCompiler()
    criteria = [
        FeedbackCriterionInput(
            criterion_id="C1",
            description="Concept 1",
            max_points=5.0,
            awarded_points=5.0,
            marks_lost=0.0,
            status="satisfied"
        ),
        FeedbackCriterionInput(
            criterion_id="C2",
            description="Concept 2",
            max_points=5.0,
            awarded_points=5.0,
            marks_lost=0.0,
            status="satisfied"
        )
    ]
    inp = FeedbackCompilerInput(
        question_id="Q001",
        question_text="Sample question",
        criteria=criteria
    )
    report = compiler.compile(inp)
    assert len(report.opportunities) == 0
    assert report.total_marks_lost == 0.0


# ==============================================================================
# 3. Quote & Timestamp Validation Tests
# ==============================================================================

def test_quote_validation_accepts_verbatim_quote():
    validator = FeedbackValidator()
    transcript = "Dependency injection means passing dependencies from the outside via constructor."
    quote = "passing dependencies from the outside via constructor"
    is_valid, msg = validator.validate_quote(quote, transcript)
    assert is_valid is True


def test_quote_validation_rejects_fabricated_quote():
    validator = FeedbackValidator()
    transcript = "Dependency injection means passing dependencies from the outside via constructor."
    fabricated = "We utilize an automated inversion container to instantiate singleton proxies."
    is_valid, msg = validator.validate_quote(fabricated, transcript)
    assert is_valid is False
    assert "Fabricated quote" in msg


def test_timestamp_validation_valid_range():
    validator = FeedbackValidator()
    is_valid, msg = validator.validate_timestamp(start=5.2, end=12.8, audio_duration_sec=30.0)
    assert is_valid is True


def test_timestamp_validation_rejects_negative_or_inverted():
    validator = FeedbackValidator()
    # Negative
    ok, msg = validator.validate_timestamp(start=-2.0, end=5.0)
    assert ok is False

    # Inverted
    ok, msg = validator.validate_timestamp(start=15.0, end=10.0)
    assert ok is False
    assert "Inverted" in msg


def test_timestamp_validation_rejects_out_of_bounds():
    validator = FeedbackValidator()
    # Duration is 20s, end is 45s
    ok, msg = validator.validate_timestamp(start=10.0, end=45.0, audio_duration_sec=20.0)
    assert ok is False
    assert "out of bounds" in msg


# ==============================================================================
# 4. Rubric Linkage & Anti-Fluff Validation Tests
# ==============================================================================

def test_rubric_linkage_rejects_nonexistent_or_unlost_criterion():
    validator = FeedbackValidator()
    valid_map = {"R1": 2.0, "R2": 0.0}  # R2 had 0 marks lost!

    # Nonexistent
    ok, msg = validator.validate_rubric_linkage("R999", 2.0, valid_map)
    assert ok is False

    # Unlost criterion
    ok, msg = validator.validate_rubric_linkage("R2", 1.0, valid_map)
    assert ok is False
    assert "earned full marks" in msg


def test_validator_rejects_motivational_fluff():
    validator = FeedbackValidator()
    fluff_text = "Great job on the answer! Don't worry, you can do it next time."
    ok, msg = validator.validate_quality_and_fluff(fluff_text)
    assert ok is False
    assert "motivational fluff detected" in msg


# ==============================================================================
# 5. Confidence-Aware Uncertainty Filtering Tests
# ==============================================================================

def test_uncertain_asr_cannot_produce_punitive_failure_statement():
    validator = FeedbackValidator()
    opp = FeedbackOpportunity(
        opportunity_id="FB_001",
        criterion_id="R1",
        title="Improve Hashing",
        marks_lost=2.0,
        max_points=2.0,
        awarded_points=0.0,
        issue="You failed to understand and explain hashing mechanisms.",
        why_it_matters="Vital for hash maps.",
        action="Study hashing.",
        suggested_answer="A hash function maps keys to buckets uniformly.",
        feedback_status="validated"  # Incorrectly marked validated!
    )
    # When ASR is uncertain, punitive wording must fail
    ok, msg = validator.validate_uncertainty(
        opp,
        criterion_evaluation_state="provisional",
        recognition_status="uncertain"
    )
    assert ok is False
    assert "Punitive statement" in msg or "Feedback status must be 'provisional'" in msg


def test_compiler_properly_labels_provisional_feedback_under_uncertainty():
    compiler = FeedbackCompiler()
    criteria = [
        FeedbackCriterionInput(
            criterion_id="R1",
            description="Explains hash map load factor and rehashing",
            max_points=3.0,
            awarded_points=1.5,
            marks_lost=1.5,
            status="partially_satisfied",
            recognition_status="uncertain",
            evaluation_state="provisional",
            uncertainty_notice="Acoustic confusion detected around 'load factor'."
        )
    ]
    inp = FeedbackCompilerInput(
        question_id="DS_001",
        question_text="Explain hash map load factor",
        criteria=criteria,
        evaluation_state="provisional"
    )
    report = compiler.compile(inp)
    assert len(report.opportunities) == 1
    opp = report.opportunities[0]
    assert opp.feedback_status == "provisional"
    assert "Verification Required" in opp.title
    assert "speech recognition uncertainty" in opp.issue.lower()


# ==============================================================================
# 6. End-to-End Compilation & Personalized Plan Tests
# ==============================================================================

def test_full_feedback_compilation_and_plan(sample_compiler_input, tmp_path):
    compiler = FeedbackCompiler()
    report = compiler.compile(sample_compiler_input)

    assert isinstance(report, CompiledFeedbackReport)
    assert len(report.opportunities) == 3
    assert report.total_marks_lost == 6.0
    assert report.total_awarded_marks == 4.0

    # Verify Personalized Improvement Plan
    plan = report.improvement_plan
    assert plan is not None
    assert len(plan.plan_items) == 3
    item1 = plan.plan_items[0]
    assert item1.criterion_id == "R3"
    assert len(item1.learning_objectives) >= 3
    assert len(item1.expected_answer_components) >= 2
    assert len(item1.self_assessment_criteria) >= 2
    assert len(item1.practice_task) > 10

    # Test report export
    json_path, md_path = compiler.export_reports(report, output_dir=tmp_path)
    assert json_path.exists()
    assert md_path.exists()

    with open(md_path, "r", encoding="utf-8") as f:
        md_content = f.read()
    assert "# IMAIRA FairScore — Personalized Candidate Feedback & Learning Plan" in md_content
    assert "## 1. Top Actionable Improvement Opportunities" in md_content
    assert "## 2. Personalized Learning Curriculum & Practice Tasks" in md_content
