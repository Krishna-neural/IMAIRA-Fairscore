"""Reference Q&A Knowledge Base loader, validator, and quality audit module for IMAIRA-Fairscore.

Safely integrates reference questions and answers (e.g. data/QandA.json) without
conflicting with semantic rubrics (data/rubrics_120.json) or calibration datasets.
"""

import json
import logging
import re
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple, Union
from collections import Counter
from pydantic import BaseModel, Field, field_validator
from score.rubrics import SemanticRubricIdea, QuestionRubric

logger = logging.getLogger(__name__)

class QnAValidationError(ValueError):
    """Raised when QandA dataset fails structural or schema validation."""
    pass

class QnAFileNotFoundError(FileNotFoundError):
    """Raised when QandA dataset file cannot be located."""
    pass

class QnARecord(BaseModel):
    """Schema for a single reference question and answer record in QandA.json."""
    id: str = Field(..., description="Unique alphanumeric identifier (e.g. ENG001)")
    category: str = Field(..., description="High-level engineering domain category")
    subcategory: str = Field(..., description="Specific subdiscipline or topic")
    difficulty: str = Field(..., description="Difficulty rating: e.g. Intermediate, Advanced, Expert")
    question_type: str = Field(..., description="Pedagogical type: Conceptual, Scenario-Based, etc.")
    question: str = Field(..., description="Interview question prompt")
    answer: str = Field(..., description="Reference canonical answer")
    glossary_terms_used: List[str] = Field(default_factory=list, description="Technical glossary keywords")
    key_concepts: List[str] = Field(default_factory=list, description="Core technical concepts")
    semantic_rubric_ideas: Optional[List[SemanticRubricIdea]] = Field(
        default=None,
        description="Structured semantic propositions, weights, and paraphrase guidance for CPU 1 scoring"
    )

    def to_rubric(self) -> QuestionRubric:
        """Convert this Q&A record to a CPU 1 QuestionRubric object.
        
        Requires semantic_rubric_ideas to be populated.
        """
        if not self.semantic_rubric_ideas:
            raise ValueError(
                f"Record '{self.id}' does not have semantic_rubric_ideas populated. "
                "Cannot convert to QuestionRubric without semantic propositions."
            )
        return QuestionRubric(
            question_id=self.id,
            question_prompt=self.question,
            domain=self.category,
            semantic_rubric_ideas=self.semantic_rubric_ideas
        )

    @field_validator("id", "category", "subcategory", "difficulty", "question_type", "question", "answer")
    @classmethod
    def check_non_empty_strings(cls, v: str, info) -> str:
        if not isinstance(v, str):
            raise ValueError(f"Field '{info.field_name}' must be a string, got {type(v).__name__}")
        s = v.strip()
        if not s:
            raise ValueError(f"Field '{info.field_name}' must not be empty or whitespace only")
        return s

    @field_validator("glossary_terms_used", "key_concepts")
    @classmethod
    def check_list_of_strings(cls, v: Any, info) -> List[str]:
        if not isinstance(v, list):
            raise ValueError(f"Field '{info.field_name}' must be a list, got {type(v).__name__}")
        for idx, item in enumerate(v):
            if not isinstance(item, str) or not item.strip():
                raise ValueError(f"Item {idx} in '{info.field_name}' must be a non-empty string")
        return [item.strip() for item in v]

def load_qanda(path: Union[str, Path] = "data/QandA.json") -> List[QnARecord]:
    """Load and strictly validate the reference Q&A dataset.
    
    Raises:
        QnAFileNotFoundError: If the specified file does not exist.
        QnAValidationError: If JSON is malformed, root is not a list, IDs are duplicated,
                            or records violate the expected schema.
    """
    file_path = Path(path)
    if not file_path.exists():
        alt_path = Path(__file__).resolve().parent.parent / path
        if alt_path.exists():
            file_path = alt_path
        else:
            raise QnAFileNotFoundError(
            f"QandA dataset file not found at '{file_path}'. "
            f"Please verify the file exists or update configuration."
        )

    try:
        with open(file_path, "r", encoding="utf-8") as f:
            raw_data = json.load(f)
    except json.JSONDecodeError as e:
        raise QnAValidationError(f"Malformed JSON in QandA file '{file_path}': {e}") from e
    except Exception as e:
        raise QnAValidationError(f"Failed to read QandA file '{file_path}': {e}") from e

    if not isinstance(raw_data, list):
        raise QnAValidationError(
            f"Invalid root JSON structure in '{file_path}': expected list of records, "
            f"got {type(raw_data).__name__}"
        )

    if not raw_data:
        raise QnAValidationError(f"QandA file '{file_path}' is empty (0 records).")

    validated_records: List[QnARecord] = []
    seen_ids: Set[str] = set()

    for idx, item in enumerate(raw_data):
        if not isinstance(item, dict):
            raise QnAValidationError(
                f"Record at index {idx} is not a JSON object: {type(item).__name__}"
            )

        record_id = item.get("id")
        if not record_id or not isinstance(record_id, str):
            raise QnAValidationError(f"Record at index {idx} has invalid or missing 'id'")

        if record_id in seen_ids:
            raise QnAValidationError(
                f"Duplicate record ID detected: '{record_id}' at index {idx}"
            )
        seen_ids.add(record_id)

        try:
            record = QnARecord(**item)
            validated_records.append(record)
        except Exception as e:
            raise QnAValidationError(
                f"Schema validation error in record ID '{record_id}' (index {idx}): {e}"
            ) from e

    return validated_records

def audit_qanda_quality(
    records: Union[List[QnARecord], List[Dict[str, Any]]]
) -> Dict[str, Any]:
    """Perform a rigorous, objective data-quality audit on Q&A records.
    
    Identifies templated answers, boilerplate repetition, category distributions,
    and suitability risks for downstream evaluation.
    """
    if not records:
        return {"total_records": 0, "error": "Empty dataset"}

    # Normalize to dicts
    dict_records = [r.model_dump() if isinstance(r, QnARecord) else r for r in records]
    n_total = len(dict_records)

    categories = Counter(r["category"] for r in dict_records)
    subcategories = Counter(r["subcategory"] for r in dict_records)
    difficulties = Counter(r["difficulty"] for r in dict_records)
    question_types = Counter(r["question_type"] for r in dict_records)

    # Question and answer repetition analysis
    answer_texts = [r["answer"] for r in dict_records]
    
    # Identify distinct template stems by clustering common phrasing
    template_clusters = Counter()
    for r in dict_records:
        ans = r["answer"]
        if "balance time complexity" in ans:
            template_clusters["Template 1: SOLID / Mutex / Factory / Testing"] += 1
        elif "overfitting and address concept drift" in ans:
            template_clusters["Template 2: Cross-validation / Weight decay / Quantization"] += 1
        elif "defense in depth" in ans:
            template_clusters["Template 3: OAuth 2.0 / JWT / Kubernetes / Docker"] += 1
        elif "fundamental physical laws" in ans:
            template_clusters["Template 4: Stress-strain / Young's modulus / Kirchhoff"] += 1
        elif "objectives and key results" in ans:
            template_clusters["Template 5: OKRs / LTV / CAC / MRR / Sprint planning"] += 1
        else:
            template_clusters["Custom / Non-Templated"] += 1

    # Question formula analysis
    question_formulas = Counter()
    for r in dict_records:
        q = r["question"]
        if "high-throughput distributed system under requirement" in q:
            question_formulas["Formula 1: distributed system under requirement #N"] += 1
        elif "mitigating overfitting and handling concept drift" in q:
            question_formulas["Formula 2: overfitting/drift for use case #N"] += 1
        elif "highly available, secure, and resilient architecture incorporating" in q:
            question_formulas["Formula 3: secure architecture for workload #N"] += 1
        elif "evaluating structural integrity and performance in" in q:
            question_formulas["Formula 4: structural integrity for scenario #N"] += 1
        elif "align cross-functional teams, track key performance indicators" in q:
            question_formulas["Formula 5: cross-functional/unit economics for initiative #N"] += 1
        else:
            question_formulas["Custom Question Prompt"] += 1

    # Glossary repetition
    glossary_sets = [tuple(sorted(r["glossary_terms_used"])) for r in dict_records]
    common_glossaries = Counter(glossary_sets).most_common(5)

    # Rubric compatibility analysis
    rubric_ideas_count = sum(1 for r in dict_records if r.get("semantic_rubric_ideas") and len(r["semantic_rubric_ideas"]) > 0)
    has_full_rubrics = (rubric_ideas_count == n_total and n_total > 0)
    boilerplate_count = n_total - template_clusters.get("Custom / Non-Templated", 0)
    boilerplate_ratio = round(boilerplate_count / n_total, 4)

    # Determine scoring risks and role suitability
    if boilerplate_ratio == 0.0 and has_full_rubrics:
        scoring_risks = [
            "Dataset is clean and non-templated; includes valid semantic rubric propositions.",
            "Dataset contains zero human candidate evaluation scores and is not suitable for score calibration."
        ]
        recommended_role = "SCORING_AND_REFERENCE_KNOWLEDGE_BASE"
        suitable_for_rubric_replacement = True
    elif boilerplate_ratio == 0.0:
        scoring_risks = [
            "Dataset is clean and non-templated, but lacks semantic_rubric_ideas.",
            "Dataset cannot directly replace rubrics without generating semantic propositions."
        ]
        recommended_role = "REFERENCE_KNOWLEDGE_BASE_ONLY"
        suitable_for_rubric_replacement = False
    else:
        scoring_risks = [
            "Answers are generated from repetitive boilerplate templates with slot-filled subcategories.",
            "Repetitive answers give identical boilerplate across different technical questions.",
            "Dataset contains zero human scores, zero candidate transcripts, and zero multi-rater spread.",
            "Dataset cannot be used for 5-fold cross-validation or agreement ceiling evaluation.",
            "Dataset cannot replace data/rubrics_120.json because it lacks structured semantic propositions, weights, and paraphrase guidance."
        ]
        recommended_role = "REFERENCE_KNOWLEDGE_BASE_ONLY"
        suitable_for_rubric_replacement = False

    return {
        "total_records": n_total,
        "unique_ids": len(set(r["id"] for r in dict_records)),
        "categories": dict(categories),
        "subcategories_count": len(subcategories),
        "difficulties": dict(difficulties),
        "question_types": dict(question_types),
        "question_formulas": dict(question_formulas),
        "answer_template_families": dict(template_clusters),
        "boilerplate_ratio": boilerplate_ratio,
        "has_semantic_rubric_ideas": has_full_rubrics,
        "scoring_risks": scoring_risks,
        "recommended_role": recommended_role,
        "suitable_for_rubric_replacement": suitable_for_rubric_replacement,
        "suitable_for_calibration": False
    }

def get_qanda_by_id(
    record_id: str,
    records: Optional[List[QnARecord]] = None,
    path: Union[str, Path] = "data/QandA.json"
) -> Optional[QnARecord]:
    """Lookup a single reference Q&A record by its unique ID."""
    if records is None:
        records = load_qanda(path)
    for r in records:
        if r.id == record_id:
            return r
    return None
