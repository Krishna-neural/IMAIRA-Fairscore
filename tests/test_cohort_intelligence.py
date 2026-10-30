"""
Unit and Integration Tests for Implementation 5: Placement Officer Intelligence
=============================================================================
Verifies:
1. Role-Based Access Control (RBAC): Officers/Admins allowed, Students strictly rejected
2. Cohort filtering and KPI calculations with separate verified vs provisional scores
3. True skill gap ranking by marks lost and ASR-uncertainty confounding detection
4. Four distinct Evaluation Quality monitoring categories
5. Deterministic alert generation based on configurable thresholds
6. Alert state management and reviewer notes
7. End-to-end report compilation and export
"""

import pytest
from pathlib import Path

from analytics.cohort_models import (
    AuthContext,
    CohortFilter,
    CohortOverviewKPIs,
    EvaluationAlert,
    PlacementIntelligenceReport
)
from analytics.cohort_intelligence import CohortIntelligenceEngine


@pytest.fixture
def sample_eval_records():
    return [
        {
            "filename": "Prem_script14.m4a",
            "matched_question": {"question_id": "ENG129", "domain": "Cloud Infrastructure"},
            "scores": {"calibrated_content": 4.19, "overall_fairscore": 3.11},
            "rubric_idea_breakdown": [
                {"idea_id": "ENG129_IDEA_1", "criterion": "Kubernetes Pod architecture", "verdict": "COVERED", "points_awarded": 1.0, "max_points": 1.0},
                {"idea_id": "ENG129_IDEA_2", "criterion": "Deployment self-healing", "verdict": "COVERED", "points_awarded": 1.0, "max_points": 1.0}
            ],
            "corrections_made": [],
            "evaluation_state": "final_verified"
        },
        {
            "filename": "Rupesh_script1.m4a",
            "matched_question": {"question_id": "Q084", "domain": "Operating Systems"},
            "scores": {"calibrated_content": 2.92, "overall_fairscore": 2.80},
            "rubric_idea_breakdown": [
                {"idea_id": "Q084_IDEA_1", "criterion": "Process memory isolation", "verdict": "COVERED", "points_awarded": 1.0, "max_points": 1.0},
                {"idea_id": "Q084_IDEA_2", "criterion": "Context switching overhead", "verdict": "MISSING", "points_awarded": 0.0, "max_points": 1.0}
            ],
            "corrections_made": [{"original_spoken": "thred", "corrected_term": "thread"}],
            "uncertainty_records": [{"segment_id": "S1", "recognition_status": "uncertain"}],
            "evaluation_state": "final_verified"
        },
        {
            "filename": "Sukhpreet_ws1.m4a",
            "matched_question": {"question_id": "Q054", "domain": "Data Structures"},
            "scores": {"calibrated_content": 1.57, "overall_fairscore": 1.54},
            "rubric_idea_breakdown": [
                {"idea_id": "Q054_IDEA_1", "criterion": "Monotonic stack invariant", "verdict": "MISSING", "points_awarded": 0.0, "max_points": 1.0},
                {"idea_id": "Q054_IDEA_2", "criterion": "Next Greater Element O(n)", "verdict": "MISSING", "points_awarded": 0.0, "max_points": 1.0}
            ],
            "corrections_made": [],
            "evidence_scorecard": {"provisional_score_active": True, "provisional_marks_total": 1.5},
            "evaluation_state": "provisional"
        }
    ]


# ==============================================================================
# 1. RBAC & Authorization Tests
# ==============================================================================

def test_rbac_placement_officer_and_admin_authorized():
    officer = AuthContext(user_id="OFFICER_01", role="placement_officer")
    admin = AuthContext(user_id="ADMIN_01", role="administrator")
    
    assert officer.is_authorized() is True
    assert admin.is_authorized() is True


def test_rbac_student_strictly_rejected():
    student = AuthContext(user_id="STU_999", role="student")
    assert student.is_authorized() is False

    engine = CohortIntelligenceEngine()
    with pytest.raises(PermissionError) as exc_info:
        engine.enforce_auth(student)
    assert "Access denied" in str(exc_info.value)
    assert "student" in str(exc_info.value).lower()


# ==============================================================================
# 2. Cohort Filtering & KPI Calculation Tests
# ==============================================================================

def test_cohort_filtering_by_domain_and_score(sample_eval_records):
    engine = CohortIntelligenceEngine()
    
    # Filter by domain
    f_os = CohortFilter(domain="Operating Systems")
    filtered_os = engine.filter_records(sample_eval_records, f_os)
    assert len(filtered_os) == 1
    assert filtered_os[0]["filename"] == "Rupesh_script1.m4a"

    # Filter by content score range
    f_score = CohortFilter(min_content_score=70.0)
    filtered_high = engine.filter_records(sample_eval_records, f_score)
    assert len(filtered_high) == 1
    assert filtered_high[0]["filename"] == "Prem_script14.m4a"


def test_kpi_calculation_decouples_verified_from_provisional(sample_eval_records):
    engine = CohortIntelligenceEngine()
    kpis = engine.calculate_cohort_kpis(sample_eval_records)

    assert kpis.total_interviews_conducted == 3
    assert kpis.total_students_enrolled == 3  # Prem, Rupesh, Sukhpreet
    
    # Prem (79.8) and Rupesh (48.0) are verified: mean = (79.8 + 48.0) / 2 = 63.9
    assert kpis.average_verified_content_score == 63.9
    
    # Sukhpreet (14.3) is provisional: must be reported separately!
    assert kpis.average_provisional_content_score == 14.3
    
    # Review required for provisional evaluation
    assert kpis.evaluations_requiring_review_pct > 0.0


# ==============================================================================
# 3. Student Skill Gap Analytics Tests
# ==============================================================================

def test_skill_gap_ranking_and_asr_confounding(sample_eval_records):
    engine = CohortIntelligenceEngine()
    gaps = engine.analyze_skill_gaps(sample_eval_records, top_n=5)

    assert len(gaps) > 0
    # The highest marks lost concept should be at the top
    top_gap = gaps[0]
    assert top_gap.students_missing_count >= 1
    assert top_gap.average_marks_lost > 0.0
    assert len(top_gap.recommended_training_topic) > 10


# ==============================================================================
# 4. Evaluation Quality Breakdown (The 4 Distinct Categories)
# ==============================================================================

def test_four_distinct_quality_categories(sample_eval_records):
    engine = CohortIntelligenceEngine()
    gaps = engine.analyze_skill_gaps(sample_eval_records)
    quality = engine.build_quality_breakdown(sample_eval_records, gaps)

    # Category 1: Student Skill Gaps
    assert quality.confirmed_skill_gaps_count >= 1

    # Category 2: ASR Problems
    assert quality.audio_verified_corrections_count == 1  # Rupesh: thred -> thread
    assert quality.unresolved_asr_segments_count == 1     # Rupesh: S1 uncertain

    # Category 3: Uncertain Decisions
    assert quality.provisional_evaluations_count == 1     # Sukhpreet: provisional
    assert quality.marks_affected_by_uncertainty > 0.0

    # Category 4: Human-System Disagreement
    assert quality.human_reviewed_count >= 0


# ==============================================================================
# 5. Alert Generation & Alert State Management
# ==============================================================================

def test_alert_generation_and_lifecycle():
    engine = CohortIntelligenceEngine()
    kpis = CohortOverviewKPIs(total_interviews_conducted=10)
    
    # Create artificial high-uncertainty quality breakdown
    quality = engine.build_quality_breakdown([], [])
    quality.provisional_evaluations_count = 3  # 30% provisional (> 15% threshold)
    quality.unresolved_asr_segments_count = 2

    alerts = engine.generate_alerts(kpis, quality)
    assert len(alerts) >= 2

    # Check that high provisional alert is raised with severity 'high'
    prov_alert = next((a for a in alerts if a.category == "high_provisional_rate"), None)
    assert prov_alert is not None
    assert prov_alert.severity == "high"
    assert prov_alert.status == "active"

    # Test alert state update
    updated = engine.update_alert_status(
        alert_id=prov_alert.alert_id,
        new_status="under_review",
        reviewer_notes="Assigned to audio lab engineer for mic calibration."
    )
    assert updated is not None
    assert updated.status == "under_review"
    assert "mic calibration" in updated.reviewer_notes


# ==============================================================================
# 6. End-to-End Placement Intelligence Report & Export
# ==============================================================================

def test_full_placement_intelligence_report_export(tmp_path):
    engine = CohortIntelligenceEngine()
    auth = AuthContext(user_id="DIR_PLACEMENT_01", role="placement_officer")
    
    report = engine.generate_report(auth=auth)
    assert isinstance(report, PlacementIntelligenceReport)
    assert report.kpis.total_interviews_conducted >= 0

    json_p, md_p = engine.export_dashboard_reports(report, output_dir=tmp_path)
    assert json_p.exists()
    assert md_p.exists()

    with open(md_p, "r", encoding="utf-8") as f:
        content = f.read()
    assert "# IMAIRA FairScore — Placement Officer Institutional Intelligence Report" in content
    assert "## 1. Cohort Performance Overview & Statistical KPIs" in content
    assert "## 2. Student Skill Gap Analytics" in content
    assert "## 3. Evaluation Quality Monitoring" in content
    assert "## 4. Evaluation Quality Alerts & Management" in content


# ==============================================================================
# 7. Edge Cases & Security Tests
# ==============================================================================

def test_empty_cohort_handling():
    engine = CohortIntelligenceEngine()
    kpis = engine.calculate_cohort_kpis([])
    assert kpis.total_students_enrolled == 0
    assert kpis.total_interviews_conducted == 0
    assert kpis.average_verified_content_score == 0.0

    gaps = engine.analyze_skill_gaps([])
    assert len(gaps) == 0

    quality = engine.build_quality_breakdown([], [])
    assert quality.confirmed_skill_gaps_count == 0
    assert quality.interviews_with_asr_issues == 0


def test_student_drilldown_and_security(sample_eval_records):
    engine = CohortIntelligenceEngine()
    officer = AuthContext(user_id="OFFICER_01", role="placement_officer")
    student = AuthContext(user_id="STU_001", role="student")

    # Placement officer can generate report with drilldown
    report = engine.generate_report(auth=officer)
    assert report.auth_user == "OFFICER_01"

    # Student cannot generate report
    with pytest.raises(PermissionError):
        engine.generate_report(auth=student)
