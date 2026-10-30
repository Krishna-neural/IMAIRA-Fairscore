"""
IMAIRA FairScore — Uncertainty Data Contracts & Models
======================================================
Defines two independent uncertainty dimensions:
1. Recognition Uncertainty: Whether speech recognition reliably established what was said.
2. Rubric Uncertainty: Whether the candidate demonstrated required technical knowledge.

Core Product Principle:
An uncertain recording is not proof of missing knowledge.
An unverified correction is not proof of correct knowledge.
And an absent keyword is not automatically evidence of an absent concept.
"""

from typing import List, Optional, Literal, Dict, Any
from datetime import datetime
from pydantic import BaseModel, Field


RecognitionStatus = Literal["verified", "uncertain", "unresolved", "manual_review"]
RubricStatus = Literal["satisfied", "partially_satisfied", "not_satisfied", "uncertain", "pending_verification"]
CorrectionStatus = Literal["audio_verified", "unresolved", "no_correction", "manual_review"]
UncertaintyLevel = Literal["low", "medium", "high", "unavailable"]
VerificationMethod = Literal["audio_recheck", "phonetic_acoustic", "manual", "none"]
ReviewStatus = Literal["automated", "pending_human_review", "human_approved", "human_rejected"]
EvaluationState = Literal["final_verified", "provisional", "pending_review"]


class UncertaintyRecord(BaseModel):
    """
    Extensible record tracking suspicious transcript spans, audio verification outcomes,
    and their links to rubric criteria.
    """
    segment_id: str = Field(..., description="Unique identifier for the segment, e.g. 'S014'")
    session_id: Optional[str] = Field(default=None, description="Interview session identifier")
    question_id: str = Field(..., description="Target question identifier, e.g. 'DS_001'")
    original_text: str = Field(..., description="Raw transcript text as recognized by initial ASR")
    corrected_text: Optional[str] = Field(default=None, description="Proposed or verified replacement text")
    start: float = Field(..., ge=0.0, description="Audio start time in seconds")
    end: float = Field(..., ge=0.0, description="Audio end time in seconds")
    asr_confidence: Optional[float] = Field(default=None, ge=0.0, le=1.0, description="Acoustic model confidence score")
    
    # Two Independent Dimensions
    recognition_status: RecognitionStatus = Field(default="uncertain")
    rubric_status: RubricStatus = Field(default="pending_verification")
    
    correction_status: CorrectionStatus = Field(default="unresolved")
    uncertainty_level: UncertaintyLevel = Field(default="medium")
    verification_method: VerificationMethod = Field(default="audio_recheck")
    linked_criterion_ids: List[str] = Field(default_factory=list, description="Rubric criteria dependent on this term")
    verification_reason: str = Field(default="", description="Detailed rationale for the verification decision")
    
    review_status: ReviewStatus = Field(default="automated")
    created_at: str = Field(default_factory=lambda: datetime.utcnow().isoformat())
    updated_at: str = Field(default_factory=lambda: datetime.utcnow().isoformat())
    human_reviewer_notes: Optional[str] = Field(default=None)
    applied_to_score: bool = Field(default=False)

    def to_dict(self) -> Dict[str, Any]:
        return self.model_dump()


class UncertaintyPolicy(BaseModel):
    """Configurable policy governing uncertainty thresholds and provisional scoring."""
    enable_provisional_credit: bool = Field(
        default=True,
        description="Whether to award limited provisional marks for criteria affected by ambiguous audio"
    )
    provisional_credit_ratio: float = Field(
        default=0.50,
        ge=0.0,
        le=0.75,
        description="Proportion of criterion points awarded as provisional credit (capped at 50%)"
    )
    low_confidence_threshold: float = Field(
        default=0.65,
        ge=0.0,
        le=1.0,
        description="Confidence below which segments are flagged as suspicious"
    )
    critical_confidence_threshold: float = Field(
        default=0.35,
        ge=0.0,
        le=1.0,
        description="Confidence below which segments require mandatory audio recheck"
    )
    acoustic_match_threshold: float = Field(
        default=85.0,
        ge=50.0,
        le=100.0,
        description="Fuzzy match percentage required for audio confirmation"
    )
    require_manual_review_on_ambiguous: bool = Field(
        default=True,
        description="Flag evaluations for human review when audio remains unresolved"
    )
