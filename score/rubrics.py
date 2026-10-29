"""Semantic Rubric models, loader, validation helper, and version hashing for IMAIRA-Fairscore."""

import hashlib
import json
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union
from pydantic import BaseModel, Field, field_validator

class SemanticRubricIdea(BaseModel):
    idea_id: str
    semantic_statement: str
    required: bool = True
    weight: float = Field(default=1.0, ge=0.0)
    acceptable_paraphrase_guidance: str

    @field_validator("semantic_statement")
    @classmethod
    def validate_semantic_statement(cls, v: str) -> str:
        v_stripped = v.strip()
        words = v_stripped.split()
        if len(words) < 5:
            raise ValueError(
                f"Rubric statement '{v}' is too short ({len(words)} words). "
                "Must be a complete conceptual proposition, not a bare keyword list."
            )
        return v_stripped

class ScoreScale(BaseModel):
    min: int = 1
    max: int = 5

class QuestionRubric(BaseModel):
    question_id: str
    question_prompt: str
    domain: str
    target_score_scale: ScoreScale = Field(default_factory=ScoreScale)
    semantic_rubric_ideas: List[SemanticRubricIdea]

    @field_validator("semantic_rubric_ideas")
    @classmethod
    def validate_ideas(cls, ideas: List[SemanticRubricIdea]) -> List[SemanticRubricIdea]:
        if not ideas:
            raise ValueError("Every question must contain at least one semantic rubric idea.")
        return ideas

def compute_rubric_version_hash(rubrics: Union[Dict[str, QuestionRubric], List[QuestionRubric], List[Dict[str, Any]]]) -> str:
    """Compute a deterministic SHA-256 hash representing the exact version of the 120 rubrics."""
    if isinstance(rubrics, dict):
        items = list(rubrics.values())
    else:
        items = rubrics

    canonical = []
    for item in items:
        if isinstance(item, QuestionRubric):
            canonical.append(item.model_dump())
        elif isinstance(item, dict):
            canonical.append(item)
        else:
            raise TypeError(f"Unsupported item type in rubrics: {type(item)}")

    canonical_sorted = sorted(canonical, key=lambda x: x["question_id"])
    serialized = json.dumps(canonical_sorted, sort_keys=True, separators=(',', ':'))
    return hashlib.sha256(serialized.encode("utf-8")).hexdigest()

def validate_rubrics(rubrics_data: Union[Dict[str, Any], List[Dict[str, Any]], str, Path]) -> Tuple[bool, str, Dict[str, Any]]:
    """Audit and validate that all 120 questions follow the semantic proposition principle."""
    if isinstance(rubrics_data, (str, Path)):
        with open(rubrics_data, "r", encoding="utf-8") as f:
            raw = json.load(f)
    elif isinstance(rubrics_data, dict):
        raw = list(rubrics_data.values())
    else:
        raw = rubrics_data

    if len(raw) != 120:
        return False, f"Expected exactly 120 questions, got {len(raw)}", {}

    seen_ids = set()
    total_ideas = 0
    parsed: Dict[str, QuestionRubric] = {}

    for idx, item in enumerate(raw):
        if isinstance(item, QuestionRubric):
            q = item
        else:
            q = QuestionRubric(**item)
        if q.question_id in seen_ids:
            return False, f"Duplicate question_id detected: {q.question_id}", {}
        seen_ids.add(q.question_id)

        for idea in q.semantic_rubric_ideas:
            words = idea.semantic_statement.split()
            if len(words) < 5:
                return False, f"Idea {idea.idea_id} in {q.question_id} has fewer than 5 words: keyword violation", {}
            total_ideas += 1

        parsed[q.question_id] = q

    version_hash = compute_rubric_version_hash(parsed)
    metadata = {
        "num_questions": len(parsed),
        "total_ideas": total_ideas,
        "rubric_version_hash": version_hash,
        "domains": sorted(list({q.domain for q in parsed.values()}))
    }
    return True, "All 120 rubrics validated successfully against semantic proposition standards.", metadata

def load_rubrics(path: Union[str, Path] = "data/rubrics_120.json") -> Dict[str, QuestionRubric]:
    """Load and validate all 120 question rubrics from disk."""
    p = Path(path)
    if not p.exists():
        raise FileNotFoundError(f"Rubrics file not found at {p.resolve()}")

    with open(p, "r", encoding="utf-8") as f:
        data = json.load(f)

    is_valid, msg, meta = validate_rubrics(data)
    if not is_valid:
        raise ValueError(f"Rubric validation failed: {msg}")

    return {item["question_id"]: QuestionRubric(**item) for item in data}
