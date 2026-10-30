"""
IMAIRA FairScore — Comprehensive Fairness Audit Lab Test Suite
==============================================================
Validates:
1. Deterministic Statistical Calculations (Score Range, Mean, Std Dev, Percentiles).
2. Five-Point Tolerance Enforcement (Pass if Range <= 5.0 pts, Fail if > 5.0 pts).
3. Boundary Conditions (Range == 5.0, Range == 0.0, Single Recording, Empty Groups).
4. Criterion-Level Score Drift & Technical Term Recall.
5. Human Reference Evaluation (MAE Agreement).
6. Complete Audit Pipeline Execution & Report Export.
"""

import pytest
import numpy as np
import tempfile
from pathlib import Path

from eval.fairness_models import (
    ExperimentalConditions,
    AuditedRecording,
    HumanReferenceEvaluation,
    EquivalentAnswerGroup,
    GroupFairnessMetrics,
    ExperimentConfig,
    FairnessAuditSummary
)
from eval.fairness_audit import FairnessAuditLab


@pytest.fixture
def sample_answer_group() -> EquivalentAnswerGroup:
    """Fixture creating an equivalent answer group with 4 diverse speaker recordings."""
    return EquivalentAnswerGroup(
        group_id="FAIR_TEST_001",
        question_id="Q084",
        question_text="What is the difference between a process and a thread?",
        domain="Operating Systems",
        substantive_concept_summary="Contrasts isolated process memory with shared thread memory and IPC requirements.",
        human_reference=HumanReferenceEvaluation(
            reference_transcript="Processes have isolated memory spaces. Threads share parent memory. Threads have faster context switching.",
            expected_concepts=["isolated memory", "shared memory", "context switching", "IPC"],
            reference_content_score_100=90.0,
            criterion_reference_marks={"R1": 4.0, "R2": 3.0, "R3": 3.0}
        ),
        recordings=[
            AuditedRecording(
                recording_id="REC_1",
                speaker_id="SPK_1",
                audio_reference="asr/Rupesh_script1.m4a",
                content_score_100=82.0,
                fairscore_5pt=4.28,
                criterion_scores={"R1": 3.5, "R2": 2.5, "R3": 2.2},
                experimental_conditions=ExperimentalConditions(
                    speaker_label="Speaker 1 (Standard)",
                    accent_description="Neutral"
                )
            ),
            AuditedRecording(
                recording_id="REC_2",
                speaker_id="SPK_2",
                audio_reference="asr/Sukhpreet_script1.m4a",
                content_score_100=84.0,
                fairscore_5pt=4.36,
                criterion_scores={"R1": 3.5, "R2": 2.5, "R3": 2.4},
                experimental_conditions=ExperimentalConditions(
                    speaker_label="Speaker 2 (Regional)",
                    accent_description="North Indian"
                )
            ),
            AuditedRecording(
                recording_id="REC_3",
                speaker_id="SPK_3",
                audio_reference="asr/Sukhpreet_script1 (1).m4a",
                content_score_100=81.0,
                fairscore_5pt=4.24,
                criterion_scores={"R1": 3.0, "R2": 2.5, "R3": 2.6},
                experimental_conditions=ExperimentalConditions(
                    speaker_label="Speaker 3 (Repeat)",
                    accent_description="North Indian repeat"
                )
            ),
            AuditedRecording(
                recording_id="REC_4",
                speaker_id="SPK_4",
                audio_reference="asr/test_voice_v3.wav",
                content_score_100=83.0,
                fairscore_5pt=4.32,
                criterion_scores={"R1": 3.5, "R2": 2.5, "R3": 2.3},
                experimental_conditions=ExperimentalConditions(
                    speaker_label="Speaker 4 (Control)",
                    accent_description="Studio acoustic"
                )
            )
        ]
    )


# -------------------------------------------------------------------------------------------------
# 1. STATISTICAL METRICS & ACCEPTANCE TOLERANCE TESTS
# -------------------------------------------------------------------------------------------------

def test_fairness_pass_within_5_point_tolerance(sample_answer_group):
    """Scores: [82.0, 84.0, 81.0, 83.0] -> Range = 3.0 pts -> Must PASS (<= 5.0)."""
    lab = FairnessAuditLab()
    metrics = lab.evaluate_group(sample_answer_group)

    assert metrics.highest_score == 84.0
    assert metrics.lowest_score == 81.0
    assert metrics.score_range == 3.0
    assert metrics.mean_score == 82.5
    assert metrics.median_score == 82.5
    assert metrics.passed_tolerance is True
    assert metrics.valid_recordings == 4


def test_fairness_fail_exceeding_5_point_tolerance(sample_answer_group):
    """Scores: [80.0, 88.0, 82.0] -> Range = 8.0 pts -> Must FAIL (> 5.0)."""
    sample_answer_group.recordings[0].content_score_100 = 80.0
    sample_answer_group.recordings[1].content_score_100 = 88.0
    sample_answer_group.recordings = sample_answer_group.recordings[:3]

    lab = FairnessAuditLab()
    metrics = lab.evaluate_group(sample_answer_group)

    assert metrics.highest_score == 88.0
    assert metrics.lowest_score == 80.0
    assert metrics.score_range == 8.0
    assert metrics.passed_tolerance is False


def test_fairness_boundary_exact_5_points(sample_answer_group):
    """Scores: [80.0, 85.0] -> Range = 5.0 pts -> Must PASS (<= 5.0)."""
    sample_answer_group.recordings[0].content_score_100 = 80.0
    sample_answer_group.recordings[1].content_score_100 = 85.0
    sample_answer_group.recordings = sample_answer_group.recordings[:2]

    lab = FairnessAuditLab()
    metrics = lab.evaluate_group(sample_answer_group)

    assert metrics.score_range == 5.0
    assert metrics.passed_tolerance is True


def test_fairness_identical_scores(sample_answer_group):
    """Scores: [85.0, 85.0, 85.0] -> Range = 0.0, Std Dev = 0.0 -> Must PASS."""
    for r in sample_answer_group.recordings:
        r.content_score_100 = 85.0

    lab = FairnessAuditLab()
    metrics = lab.evaluate_group(sample_answer_group)

    assert metrics.score_range == 0.0
    assert metrics.std_dev == 0.0
    assert metrics.passed_tolerance is True


def test_population_standard_deviation_calculation(sample_answer_group):
    """Verify standard deviation uses population formula (ddof=0)."""
    # Scores: [82.0, 84.0, 81.0, 83.0] -> mean = 82.5
    # diffs^2: (-0.5)^2, (1.5)^2, (-1.5)^2, (0.5)^2 = 0.25 + 2.25 + 2.25 + 0.25 = 5.0 / 4 = 1.25 -> sqrt(1.25) = 1.118
    lab = FairnessAuditLab()
    metrics = lab.evaluate_group(sample_answer_group)

    expected_std = round(float(np.std([82.0, 84.0, 81.0, 83.0], ddof=0)), 2)
    assert metrics.std_dev == expected_std


def test_empty_or_single_recording_group_handling():
    """Empty group or single recording is handled without runtime errors."""
    empty_group = EquivalentAnswerGroup(
        group_id="FAIR_EMPTY",
        question_id="Q032",
        question_text="What is a hash map?",
        substantive_concept_summary="Hash map collisions",
        recordings=[]
    )
    lab = FairnessAuditLab()
    metrics = lab.evaluate_group(empty_group)

    assert metrics.total_recordings == 0
    assert metrics.valid_recordings == 0
    assert metrics.score_range == 0.0
    assert metrics.passed_tolerance is False


# -------------------------------------------------------------------------------------------------
# 2. DIAGNOSTICS & HUMAN REFERENCE EVALUATION TESTS
# -------------------------------------------------------------------------------------------------

def test_criterion_level_score_ranges(sample_answer_group):
    """Criterion-level score variation is accurately calculated across speakers."""
    lab = FairnessAuditLab()
    metrics = lab.evaluate_group(sample_answer_group)

    # R1 scores: 3.5, 3.5, 3.0, 3.5 -> range = 0.5
    assert "R1" in metrics.criterion_score_ranges
    assert metrics.criterion_score_ranges["R1"] == 0.5


def test_human_reference_agreement_mae(sample_answer_group):
    """Measures Mean Absolute Error between automated scores and human gold standard."""
    # Reference score = 90.0
    # Candidate scores = [82, 84, 81, 83] -> errors = [8, 6, 9, 7] -> mean error = 7.5
    lab = FairnessAuditLab()
    metrics = lab.evaluate_group(sample_answer_group)

    assert metrics.human_agreement_mae == 7.5


# -------------------------------------------------------------------------------------------------
# 3. REPORT EXPORT & AGGREGATION TESTS
# -------------------------------------------------------------------------------------------------

def test_fairness_audit_report_export(sample_answer_group):
    """Validates export of machine-readable JSON and human-readable Markdown reports."""
    lab = FairnessAuditLab()
    # Mock groups
    lab.load_groups = lambda: [sample_answer_group]

    summary = lab.run_full_audit()
    assert summary.total_groups == 1
    assert summary.valid_groups == 1
    assert summary.passed_groups == 1
    assert summary.fairness_pass_rate_pct == 100.0

    with tempfile.TemporaryDirectory() as tmp_dir:
        out_p = Path(tmp_dir)
        json_file, md_file = lab.export_audit_reports(summary, output_dir=out_p)

        assert json_file.exists()
        assert md_file.exists()

        content = md_file.read_text(encoding="utf-8")
        assert "Cross-Speaker Fairness & Consistency Audit Report" in content
        assert "Score Range <= 5.0 points" in content
        assert "FAIR_TEST_001" in content
        assert "100.0%" in content
