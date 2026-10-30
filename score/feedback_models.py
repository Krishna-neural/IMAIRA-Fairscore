"""
IMAIRA FairScore — Feedback Compiler Data Contracts & Models
============================================================
Defines data structures for:
1. Structured Feedback Input (consuming EvidenceScorecard & Uncertainty records)
2. Ranked Improvement Opportunities (Marks Lost = Max Marks - Awarded Marks)
3. Confidence-Aware Feedback Items (verified, provisional, pending verification)
4. Personalized Improvement Plans (Learning Objectives, Practice Tasks, Self-Assessment)
5. Comprehensive Compiled Feedback Reports with Full Audit Traceability
"""

from typing import List, Dict, Any, Optional, Literal
from datetime import datetime
from pydantic import BaseModel, Field


FeedbackStatus = Literal["validated", "provisional", "pending_verification", "rejected"]
CriterionStatus = Literal["satisfied", "partially_satisfied", "missing"]


class EvidenceQuote(BaseModel):
    """Traceable transcript quotation supporting feedback."""
    quote: str = Field(default="", description="Verbatim quote from candidate transcript")
    start: Optional[float] = Field(default=None, ge=0.0, description="Audio start offset in seconds")
    end: Optional[float] = Field(default=None, ge=0.0, description="Audio end offset in seconds")
    verification_status: str = Field(default="verified", description="'verified', 'unresolved', 'audio_verified'")


class FeedbackOpportunity(BaseModel):
    """An individual actionable improvement opportunity grounded in rubric evidence."""
    opportunity_id: str = Field(..., description="Unique ID, e.g. 'FB_001'")
    criterion_id: str = Field(..., description="Target rubric criterion ID, e.g. 'R3' or 'Q084_IDEA_2'")
    title: str = Field(..., description="Concise weakness title")
    marks_lost: float = Field(..., ge=0.0, description="Maximum Marks - Awarded Marks")
    max_points: float = Field(..., ge=0.1, description="Maximum marks allocated to this criterion")
    awarded_points: float = Field(..., ge=0.0, description="Marks awarded to candidate")
    
    evidence: Optional[EvidenceQuote] = Field(default=None, description="Supporting transcript quote and timestamp")
    issue: str = Field(..., description="What the candidate missed or explained incompletely")
    why_it_matters: str = Field(..., description="Why this engineering concept is critical in practice")
    action: str = Field(..., description="Specific, concise study/practice advice (<= 35 words)")
    suggested_answer: str = Field(..., description="Technically correct model explanation demonstrating full marks")
    
    feedback_status: FeedbackStatus = Field(default="validated", description="Validation and confidence state")
    uncertainty_notice: Optional[str] = Field(default=None, description="Notice if affected by speech recognition ambiguity")
    priority_rank: int = Field(default=1, ge=1, description="1 = highest impact weakness")


class ImprovementPlanItem(BaseModel):
    """A personalized learning module targeting a specific rubric gap."""
    plan_id: str = Field(..., description="Module identifier, e.g. 'PLAN_001'")
    criterion_id: str = Field(..., description="Target criterion ID")
    concept_to_revise: str = Field(..., description="Core technical topic to master")
    why_needed: str = Field(..., description="Why revision is required based on evaluation")
    learning_objectives: List[str] = Field(..., description="Specific conceptual milestones")
    practice_task: str = Field(..., description="Concrete interview question or coding/architecture task")
    expected_answer_components: List[str] = Field(..., description="Must-include points in a successful response")
    self_assessment_criteria: List[str] = Field(..., description="Checklist for self-evaluation")
    marks_lost: float = Field(..., ge=0.0, description="Marks at risk")


class PersonalizedImprovementPlan(BaseModel):
    """Curated learning curriculum generated from highest-impact evaluation gaps."""
    interview_id: Optional[str] = Field(default=None)
    question_id: str
    question_text: str
    total_marks_lost: float = Field(default=0.0, ge=0.0)
    plan_items: List[ImprovementPlanItem] = Field(default_factory=list)


class FeedbackCriterionInput(BaseModel):
    """Input structure for an individual rubric criterion being fed to the compiler."""
    criterion_id: str
    description: str
    max_points: float = Field(..., ge=0.1)
    awarded_points: float = Field(..., ge=0.0)
    marks_lost: float = Field(default=0.0, ge=0.0)
    status: CriterionStatus = "satisfied"
    evidence_quotes: List[EvidenceQuote] = Field(default_factory=list)
    missing_concepts: List[str] = Field(default_factory=list)
    reasoning: str = ""
    recognition_status: str = "verified"
    evaluation_state: str = "final_verified"
    uncertainty_notice: Optional[str] = None


class FeedbackCompilerInput(BaseModel):
    """Structured input consumed by Feedback Compiler from evaluation engines."""
    interview_id: str = Field(default="INT_001")
    question_id: str
    question_text: str
    rubric_version: str = "1.0"
    total_marks: float = 10.0
    criteria: List[FeedbackCriterionInput]
    original_transcript: str = ""
    corrected_transcript: str = ""
    audio_duration_sec: Optional[float] = None
    evaluation_state: str = "final_verified"
    provisional_score_active: bool = False


class CompiledFeedbackReport(BaseModel):
    """Complete, auditable feedback package with traceable evidence and learning plan."""
    feedback_id: str
    interview_id: str
    question_id: str
    question_text: str
    total_marks: float
    total_awarded_marks: float
    total_marks_lost: float
    opportunities: List[FeedbackOpportunity] = Field(default_factory=list)
    improvement_plan: Optional[PersonalizedImprovementPlan] = None
    validation_summary: Dict[str, Any] = Field(default_factory=dict)
    model_used: str = "deterministic_evidence_fallback"
    created_at: str = Field(default_factory=lambda: datetime.utcnow().isoformat())
