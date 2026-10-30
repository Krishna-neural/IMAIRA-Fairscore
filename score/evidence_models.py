"""
IMAIRA FairScore — Evidence-First Data Contracts and Models
===========================================================
Defines Pydantic models for structured question rubrics, extracted evidence spans,
deterministic criterion scoring, and explainable candidate feedback.
"""

from typing import List, Optional, Literal, Dict, Any
from pydantic import BaseModel, Field, field_validator
from score.uncertainty_models import (
    UncertaintyRecord,
    RecognitionStatus,
    RubricStatus,
    EvaluationState
)


class RubricCriterion(BaseModel):
    """A single, non-overlapping evaluation criterion with clear scoring boundaries."""
    criterion_id: str = Field(..., description="Unique criterion identifier, e.g. 'R1', 'C1'")
    description: str = Field(..., description="Specific conceptual requirement being evaluated")
    max_points: float = Field(default=1.0, ge=0.1, description="Maximum marks allocated to this criterion")
    scoring_guidelines: Optional[str] = Field(default=None, description="Detailed guidance for full vs partial credit")
    acceptable_alternatives: Optional[List[str]] = Field(default=None, description="Acceptable equivalent terminology or phrasing")


class QuestionDefinition(BaseModel):
    """Structured question definition containing metadata and evaluation rubrics."""
    question_id: str = Field(..., description="Unique question identifier, e.g. 'DS_001', 'Q032'")
    question: str = Field(..., description="Spoken interview question text")
    domain: str = Field(default="Computer Science", description="Technical domain or subject")
    difficulty: Literal["Beginner", "Intermediate", "Advanced", "Expert"] = Field(default="Intermediate")
    total_marks: float = Field(default=10.0, ge=1.0, description="Total maximum marks for the question")
    expected_concepts: List[str] = Field(default_factory=list, description="Key concepts expected in an answer")
    rubric: List[RubricCriterion] = Field(..., description="Criterion breakdown equaling total_marks")

    @field_validator("rubric")
    @classmethod
    def validate_rubric_weights(cls, rubric: List[RubricCriterion]) -> List[RubricCriterion]:
        if not rubric:
            raise ValueError("Question rubric must contain at least one criterion.")
        return rubric


class EvidenceItem(BaseModel):
    """An exact, traceable quotation extracted from the candidate's response."""
    text: str = Field(..., description="Verbatim text quote from the candidate transcript")
    source_start: int = Field(default=0, ge=0, description="Character start offset in transcript")
    source_end: int = Field(default=0, ge=0, description="Character end offset in transcript")
    timestamp_start: Optional[float] = Field(default=None, ge=0.0, description="Audio start time in seconds")
    timestamp_end: Optional[float] = Field(default=None, ge=0.0, description="Audio end time in seconds")


class CriterionEvaluation(BaseModel):
    """Evaluation result for an individual rubric criterion with traceable evidence."""
    criterion_id: str
    description: str
    status: Literal["satisfied", "partially_satisfied", "missing"]
    evidence: List[EvidenceItem] = Field(default_factory=list)
    max_points: float
    awarded_points: float
    reason: str = Field(..., description="Technical justification for marks awarded or withheld")
    what_was_right: Optional[str] = Field(default=None, description="Actual quote and why it earned marks")
    what_was_missing: Optional[str] = Field(default=None, description="Missing concept that candidate omitted")
    how_to_improve: Optional[str] = Field(default=None, description="Concise actionable advice <= 30 words")
    
    # Implementation 2: Confidence-Aware Evaluation extensions
    evaluation_state: EvaluationState = Field(default="final_verified")
    provisional_marks: float = Field(default=0.0)
    recognition_status: RecognitionStatus = Field(default="verified")
    uncertainty_record_ids: List[str] = Field(default_factory=list)
    uncertainty_notice: Optional[str] = Field(default=None)


class MisconceptionItem(BaseModel):
    """A detected factual or conceptual error in the candidate's explanation."""
    concept: str
    severity: Literal["CRITICAL", "MODERATE", "MINOR"]
    error_explanation: str
    candidate_quote: Optional[str] = None
    timestamp: Optional[str] = None


class EvidenceScorecard(BaseModel):
    """Complete, transparent evaluation scorecard with full evidence trail."""
    question_id: str
    question: str
    domain: str
    difficulty: str
    total_max_marks: float
    total_awarded_marks: float
    percentage_score: float
    content_completeness_5pt: float
    content_correctness_5pt: float
    answer_structure_5pt: float
    calibrated_content_5pt: float
    calibrated_structure_5pt: float
    overall_fairscore_5pt: float
    criteria_evaluations: List[CriterionEvaluation]
    misconceptions: List[MisconceptionItem] = Field(default_factory=list)
    structure_breakdown: Dict[str, float] = Field(default_factory=dict)
    summary_verdict: str = Field(default="Completed")
    
    # Implementation 2: Confidence-Aware Evaluation extensions
    evaluation_state: EvaluationState = Field(default="final_verified")
    provisional_marks_total: float = Field(default=0.0)
    provisional_score_active: bool = Field(default=False)
    manual_review_pending: bool = Field(default=False)
    uncertainty_records: List[UncertaintyRecord] = Field(default_factory=list)


def load_evidence_question_bank(path=None) -> Dict[str, QuestionDefinition]:
    """Load question bank definitions from JSON."""
    import json
    from pathlib import Path
    bank_path = path or (Path(__file__).resolve().parent.parent / "data" / "evidence_question_bank.json")
    if not bank_path.exists():
        return {}
    with open(bank_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    return {item["question_id"]: QuestionDefinition(**item) for item in data}


def question_rubric_to_evidence_question(rubric) -> QuestionDefinition:
    """Convert an existing QuestionRubric into a structured QuestionDefinition."""
    criteria = []
    total_pts = sum(idea.weight for idea in rubric.semantic_rubric_ideas)
    # Scale to 10.0 points total
    scale = 10.0 / total_pts if total_pts > 0 else 1.0
    for idea in rubric.semantic_rubric_ideas:
        pts = round(idea.weight * scale, 2)
        guidance = getattr(idea, "acceptable_paraphrase_guidance", "Accepts standard engineering descriptions.")
        criteria.append(
            RubricCriterion(
                criterion_id=idea.idea_id,
                description=idea.semantic_statement,
                max_points=pts,
                scoring_guidelines=guidance,
                acceptable_alternatives=[w.strip() for w in guidance.split(",") if len(w.strip()) > 3]
            )
        )
    return QuestionDefinition(
        question_id=rubric.question_id,
        question=rubric.question_prompt,
        domain=rubric.domain,
        difficulty="Intermediate",
        total_marks=10.0,
        expected_concepts=[c.description[:30] for c in criteria],
        rubric=criteria
    )

