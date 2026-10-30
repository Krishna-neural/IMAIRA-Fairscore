"""
IMAIRA FairScore — Placement Officer Intelligence Data Contracts & Models
==========================================================================
Defines models for:
1. Role-Based Access Control (RBAC) & Data Governance Context
2. Cohort Filtering Specifications (Department, Batch, Domain, Evaluation Status)
3. Cohort Performance Intelligence KPIs (Verified vs Provisional Scores, Distributions)
4. Student Skill Gap Analytics (Concept Failure Rates, Marks Lost, Uncertainty Filtering)
5. Evaluation Quality Monitoring (Skill Gaps, ASR Issues, Uncertainties, Human Disagreements)
6. Intelligent Deterministic Evaluation Quality Alerts with Configurable Severity
7. Comprehensive Placement Intelligence Package with Traceability
"""

from typing import List, Dict, Any, Optional, Literal
from datetime import datetime
from pydantic import BaseModel, Field


UserRole = Literal["placement_officer", "administrator", "faculty", "student"]
AlertSeverity = Literal["critical", "high", "medium", "low", "informational"]
AlertStatus = Literal["active", "under_review", "resolved", "dismissed"]
QualityCategory = Literal[
    "student_skill_gap",
    "asr_recognition_problem",
    "uncertain_evaluation_decision",
    "human_system_disagreement",
    "fairness_audit_failure",
    "high_provisional_rate",
    "human_score_disagreement"
]


class AuthContext(BaseModel):
    """Role-Based Access Control (RBAC) security context for institutional dashboards."""
    user_id: str = Field(..., description="Unique user identifier")
    role: UserRole = Field(default="placement_officer", description="User privilege role")
    assigned_departments: List[str] = Field(default_factory=list, description="Allowed academic departments")
    can_view_pii: bool = Field(default=False, description="Whether officer can inspect identifiable candidate info")
    session_token: Optional[str] = None

    def is_authorized(self) -> bool:
        """Only placement officers and administrators can access cohort intelligence."""
        return self.role in {"placement_officer", "administrator"}


class CohortFilter(BaseModel):
    """Multi-dimensional cohort filtering parameters."""
    department: Optional[str] = None
    batch_year: Optional[str] = None
    domain: Optional[str] = None
    evaluation_status: Optional[str] = None  # 'all', 'final_verified', 'provisional', 'pending_review'
    min_content_score: Optional[float] = None
    max_content_score: Optional[float] = None


class CohortOverviewKPIs(BaseModel):
    """Executive KPI summary across a selected candidate cohort."""
    total_students_enrolled: int = Field(default=0, ge=0)
    total_interviews_conducted: int = Field(default=0, ge=0)
    completed_evaluations_count: int = Field(default=0, ge=0)
    
    # Decoupled scores: Never mix verified and provisional scores without labeling!
    average_verified_content_score: float = Field(default=0.0, ge=0.0, le=100.0)
    average_provisional_content_score: Optional[float] = Field(default=None, ge=0.0, le=100.0)
    
    median_content_score: float = Field(default=0.0, ge=0.0, le=100.0)
    content_score_std_dev: float = Field(default=0.0, ge=0.0)
    
    evaluations_requiring_review_pct: float = Field(default=0.0, ge=0.0, le=100.0)
    unresolved_evaluations_count: int = Field(default=0, ge=0)
    
    score_distribution_buckets: Dict[str, int] = Field(
        default_factory=lambda: {"0-39": 0, "40-59": 0, "60-79": 0, "80-100": 0}
    )


class SkillGapItem(BaseModel):
    """A specific conceptual weakness detected across multiple candidate evaluations."""
    concept_name: str
    criterion_id: str
    domain: str
    students_assessed_count: int = Field(..., ge=1)
    students_missing_count: int = Field(..., ge=0)
    failure_rate_pct: float = Field(..., ge=0.0, le=100.0)
    average_marks_lost: float = Field(..., ge=0.0)
    max_possible_marks: float = Field(..., ge=0.1)
    
    # Quality filter: False if failure is heavily skewed by ASR speech recognition errors
    is_confirmed_skill_gap: bool = Field(default=True)
    asr_uncertainty_impact_pct: float = Field(default=0.0, ge=0.0, le=100.0)
    recommended_training_topic: str = ""


class EvaluationQualityBreakdown(BaseModel):
    """
    Categorical decomposition of cohort assessment issues into 4 independent dimensions:
    1. Student Skill Gaps (Confirmed knowledge deficiencies)
    2. ASR Recognition Problems (Acoustic mis-transcriptions and slice recoveries)
    3. Uncertain Decisions (Provisional credit, ambiguous audio)
    4. Human vs System Disagreements (MAE against gold standards)
    """
    confirmed_skill_gaps_count: int = 0
    top_skill_gaps: List[SkillGapItem] = Field(default_factory=list)
    
    asr_problems_count: int = 0
    suspicious_segments_count: int = 0
    audio_verified_corrections_count: int = 0
    unresolved_asr_segments_count: int = 0
    interviews_with_asr_issues: int = 0
    
    uncertain_evaluations_count: int = 0
    provisional_evaluations_count: int = 0
    pending_human_reviews_count: int = 0
    marks_affected_by_uncertainty: float = 0.0
    
    human_reviewed_count: int = 0
    human_system_mae: Optional[float] = None
    significant_disagreements_count: int = 0


class EvaluationAlert(BaseModel):
    """Deterministic system health alert notifying placement officers of evaluation risks."""
    alert_id: str
    category: QualityCategory
    severity: AlertSeverity
    title: str
    description: str
    affected_interview_count: int = 1
    affected_domain_or_criterion: Optional[str] = None
    detection_timestamp: str = Field(default_factory=lambda: datetime.utcnow().isoformat())
    status: AlertStatus = "active"
    recommended_action: str
    reviewer_notes: Optional[str] = None


class PlacementIntelligenceReport(BaseModel):
    """Master institutional report packaging cohort analytics, skill gaps, and quality health."""
    report_id: str
    generated_at: str = Field(default_factory=lambda: datetime.utcnow().isoformat())
    auth_user: str
    cohort_filter: CohortFilter
    kpis: CohortOverviewKPIs
    quality_breakdown: EvaluationQualityBreakdown
    alerts: List[EvaluationAlert] = Field(default_factory=list)
    fairness_summary: Optional[Dict[str, Any]] = None
    top_feedback_recommendations: List[Dict[str, Any]] = Field(default_factory=list)
    domain_performance: Dict[str, float] = Field(default_factory=dict)
