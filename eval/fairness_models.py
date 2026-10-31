"""
IMAIRA FairScore — Fairness Audit Lab Data Contracts & Models
=============================================================
Defines data structures for:
1. Equivalent Answer Groups across different speakers and acoustic conditions.
2. Controlled Experimental Conditions & Provenance.
3. Deterministic Statistical Metrics (Score Range <= 5.0 pts, Mean, Std Dev, Percentiles).
4. Diagnostic Fairness Attribution & Human Reference Evaluation.
"""

from typing import List, Dict, Any, Optional, Literal
from datetime import datetime
from pydantic import BaseModel, Field


class ExperimentalConditions(BaseModel):
    """Acoustic and environmental metadata for an audited recording."""
    recording_environment: str = Field(default="natural", description="e.g. 'quiet', 'noisy_cafeteria', 'controlled'")
    microphone_type: str = Field(default="built-in", description="e.g. 'headset', 'laptop_mic', 'smartphone'")
    speech_style: str = Field(default="natural", description="e.g. 'scripted', 'spontaneous', 'fast_paced'")
    speaker_label: str = Field(..., description="Anonymized speaker identifier, e.g. 'Speaker 1 (North Indian)'")
    accent_description: Optional[str] = Field(default=None, description="Documented dialect / acoustic characteristics")
    language_mixing: bool = Field(default=False, description="Whether speech contains Hindi-English code-mixing")


class AuditedRecording(BaseModel):
    """An individual candidate recording participating in a fairness experiment."""
    recording_id: str = Field(..., description="Unique recording identifier, e.g. 'REC_001'")
    speaker_id: str = Field(..., description="Anonymized speaker ID, e.g. 'SPK_RUPESH'")
    audio_reference: str = Field(..., description="Path to audio file in asr/ or workspace")
    experimental_conditions: ExperimentalConditions
    
    # Execution outputs from the production pipeline
    raw_transcript: Optional[str] = None
    corrected_transcript: Optional[str] = None
    audio_duration_sec: Optional[float] = None
    content_score_100: Optional[float] = Field(default=None, ge=0.0, le=100.0)
    fairscore_5pt: Optional[float] = Field(default=None, ge=1.0, le=5.0)
    criterion_scores: Dict[str, float] = Field(default_factory=dict)
    uncertainty_record_ids: List[str] = Field(default_factory=list)
    provisional_score_active: bool = False
    evaluation_state: str = "final_verified"


class HumanReferenceEvaluation(BaseModel):
    """Gold-standard human expert reference evaluation for substantive equivalence."""
    reference_transcript: str
    expected_concepts: List[str] = Field(default_factory=list)
    reference_content_score_100: float = Field(..., ge=0.0, le=100.0)
    criterion_reference_marks: Dict[str, float] = Field(default_factory=dict)
    evaluator_notes: Optional[str] = None


class EquivalentAnswerGroup(BaseModel):
    """
    A set of recordings from different speakers communicating the same substantive technical content.
    """
    group_id: str = Field(..., description="Unique group identifier, e.g. 'FAIR_001'")
    question_id: str = Field(..., description="Associated interview question, e.g. 'Q084'")
    question_text: str = Field(..., description="Spoken interview question text")
    domain: str = Field(default="Computer Science")
    rubric_version: str = Field(default="1.0")
    expected_answer_reference: str = Field(default="REF_DEFAULT")
    substantive_concept_summary: str = Field(..., description="Summary of the core technical concept common to all recordings")
    recordings: List[AuditedRecording] = Field(default_factory=list)
    human_reference: Optional[HumanReferenceEvaluation] = None


class GroupFairnessMetrics(BaseModel):
    """Statistical evaluation metrics for a single equivalent answer group."""
    group_id: str
    question_id: str
    total_recordings: int
    valid_recordings: int
    highest_score: float
    lowest_score: float
    score_range: float = Field(..., description="Score Range = max(Si) - min(Si) on 0-100 scale")
    mean_score: float
    median_score: float
    std_dev: float = Field(..., description="Population standard deviation")
    percentiles: Dict[str, float] = Field(default_factory=dict)  # p25, p50, p75, p90
    passed_tolerance: bool = Field(..., description="True if score_range <= tolerance_threshold (default <= 5.0)")
    tolerance_threshold: float = 5.0
    
    # Diagnostics
    criterion_score_ranges: Dict[str, float] = Field(default_factory=dict)
    technical_term_recall: float = 1.0
    false_correction_rate: float = 0.0
    provisional_evaluations_count: int = 0
    diagnostic_attribution: Dict[str, Any] = Field(default_factory=dict)
    human_agreement_mae: Optional[float] = None


class ExperimentConfig(BaseModel):
    """Reproducibility metadata capturing exact execution parameters."""
    experiment_id: str
    dataset_version: str = "1.0"
    tolerance_threshold: float = 5.0
    asr_model: str = "faster-whisper/large-v3"
    gemini_model: str = "gemini-3.5-flash"
    scoring_version: str = "2.0-evidence-first"
    created_at: str = Field(default_factory=lambda: datetime.utcnow().isoformat())


class FairnessAuditSummary(BaseModel):
    """Comprehensive executive summary across all audited answer groups."""
    experiment_config: ExperimentConfig
    total_groups: int
    valid_groups: int
    passed_groups: int
    failed_groups: int
    fairness_pass_rate_pct: float = Field(..., description="Percentage of groups satisfying the 5-point tolerance")
    average_score_range: float
    max_observed_score_range: float
    group_metrics: List[GroupFairnessMetrics] = Field(default_factory=list)
    overall_recommendation: str = "COMPLIANT"
