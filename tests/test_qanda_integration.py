"""Focused compatibility and regression tests for QandA.json integration."""

import json
from pathlib import Path
import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent

from score.qanda import (
    QnARecord,
    QnAFileNotFoundError,
    QnAValidationError,
    load_qanda,
    audit_qanda_quality,
    get_qanda_by_id
)
from score.rubrics import load_rubrics, validate_rubrics
from score.calibrate import load_and_verify_datasets, evaluate_held_out_guarded, HeldOutAccessError

def test_qanda_valid_loading():
    """Verify data/QandA.json parses successfully and meets all schema constraints."""
    qanda_path = REPO_ROOT / "data" / "QandA.json"
    assert qanda_path.exists(), f"Expected QandA.json at {qanda_path}"

    records = load_qanda(qanda_path)
    assert len(records) == 120, f"Expected 120 records, got {len(records)}"

    seen_ids = set()
    for r in records:
        assert r.id not in seen_ids, f"Duplicate ID: {r.id}"
        seen_ids.add(r.id)
        assert r.category
        assert r.subcategory
        assert r.difficulty in {"Intermediate", "Advanced", "Expert"}
        assert r.question_type
        assert len(r.question) > 10
        assert len(r.answer) > 20
        assert isinstance(r.glossary_terms_used, list)
        assert isinstance(r.key_concepts, list)

def test_qanda_missing_file_handling():
    """Verify attempting to load a non-existent file raises QnAFileNotFoundError."""
    with pytest.raises(QnAFileNotFoundError):
        load_qanda(REPO_ROOT / "data" / "non_existent_dataset.json")

def test_qanda_malformed_json_handling(tmp_path):
    """Verify loading malformed JSON raises QnAValidationError."""
    bad_json = tmp_path / "bad.json"
    with open(bad_json, "w", encoding="utf-8") as f:
        f.write("{ invalid json [")

    with pytest.raises(QnAValidationError) as exc_info:
        load_qanda(bad_json)
    assert "Malformed JSON" in str(exc_info.value)

def test_qanda_missing_or_invalid_fields(tmp_path):
    """Verify records with missing required fields or incorrect types raise QnAValidationError."""
    # Missing 'answer'
    missing_answer = tmp_path / "missing_answer.json"
    with open(missing_answer, "w", encoding="utf-8") as f:
        json.dump([{
            "id": "ENG001",
            "category": "Cat",
            "subcategory": "Subcat",
            "difficulty": "Intermediate",
            "question_type": "Conceptual",
            "question": "A question?"
            # answer missing
        }], f)

    with pytest.raises(QnAValidationError) as exc_info:
        load_qanda(missing_answer)
    assert "validation error" in str(exc_info.value).lower()

    # Wrong type: glossary_terms_used is integer
    wrong_type = tmp_path / "wrong_type.json"
    with open(wrong_type, "w", encoding="utf-8") as f:
        json.dump([{
            "id": "ENG001",
            "category": "Cat",
            "subcategory": "Subcat",
            "difficulty": "Intermediate",
            "question_type": "Conceptual",
            "question": "A question?",
            "answer": "An answer.",
            "glossary_terms_used": 12345
        }], f)

    with pytest.raises(QnAValidationError) as exc_info:
        load_qanda(wrong_type)
    assert "validation error" in str(exc_info.value).lower()

    # Empty string for question
    empty_str = tmp_path / "empty_str.json"
    with open(empty_str, "w", encoding="utf-8") as f:
        json.dump([{
            "id": "ENG001",
            "category": "Cat",
            "subcategory": "Subcat",
            "difficulty": "Intermediate",
            "question_type": "Conceptual",
            "question": "   ",
            "answer": "An answer."
        }], f)

    with pytest.raises(QnAValidationError) as exc_info:
        load_qanda(empty_str)
    assert "validation error" in str(exc_info.value).lower()

def test_qanda_duplicate_ids_detected(tmp_path):
    """Verify dataset with duplicate record IDs is rejected with QnAValidationError."""
    dup_file = tmp_path / "duplicates.json"
    record = {
        "id": "ENG001",
        "category": "Cat",
        "subcategory": "Subcat",
        "difficulty": "Intermediate",
        "question_type": "Conceptual",
        "question": "Question 1?",
        "answer": "Answer 1."
    }
    with open(dup_file, "w", encoding="utf-8") as f:
        json.dump([record, record], f)

    with pytest.raises(QnAValidationError) as exc_info:
        load_qanda(dup_file)
    assert "Duplicate record ID" in str(exc_info.value)

def test_qanda_quality_audit_detects_boilerplate_and_flags_risks():
    """Verify audit accurately reports clean dataset metrics and detects templated boilerplate when present."""
    # 1. Production QandA.json (rebuilt, clean, non-templated with full rubrics)
    records = load_qanda(REPO_ROOT / "data" / "QandA.json")
    audit = audit_qanda_quality(records)

    assert audit["total_records"] == 120
    assert audit["unique_ids"] == 120
    assert audit["boilerplate_ratio"] == 0.0  # 0% template-derived answers
    assert audit["has_semantic_rubric_ideas"] is True
    assert audit["recommended_role"] == "SCORING_AND_REFERENCE_KNOWLEDGE_BASE"
    assert audit["suitable_for_rubric_replacement"] is True
    assert audit["suitable_for_calibration"] is False

    # 2. Synthetic legacy templated dataset (verifies audit detection capabilities)
    templated_sample = [
        {
            "id": "ENG999",
            "category": "Software Engineering",
            "subcategory": "Testing",
            "difficulty": "Intermediate",
            "question_type": "Conceptual",
            "question": "How to test distributed system under requirement #1?",
            "answer": "In this domain we balance time complexity and space complexity while maintaining SOLID principles and mutex locks.",
            "glossary_terms_used": ["mutex", "SOLID"],
            "key_concepts": ["Concurrency"]
        }
    ]
    templated_audit = audit_qanda_quality(templated_sample)
    assert templated_audit["boilerplate_ratio"] == 1.0
    assert templated_audit["recommended_role"] == "REFERENCE_KNOWLEDGE_BASE_ONLY"
    assert templated_audit["suitable_for_rubric_replacement"] is False
    assert len(templated_audit["scoring_risks"]) >= 4

def test_qanda_to_rubric_conversion():
    """Verify all 120 QandA records convert cleanly to valid QuestionRubric objects."""
    records = load_qanda(REPO_ROOT / "data" / "QandA.json")
    rubrics_converted = [r.to_rubric() for r in records]

    assert len(rubrics_converted) == 120
    is_valid, msg, meta = validate_rubrics(rubrics_converted)
    assert is_valid is True, f"Rubric validation failed: {msg}"
    assert meta["num_questions"] == 120
    assert meta["total_ideas"] >= 240  # At least 2 ideas per question

def test_qanda_to_rubric_missing_ideas_raises_error():
    """Verify to_rubric raises ValueError if semantic_rubric_ideas is empty or missing."""
    bare_record = QnARecord(
        id="ENG001",
        category="Software",
        subcategory="Algorithms",
        difficulty="Intermediate",
        question_type="Conceptual",
        question="What is a hash table?",
        answer="A data structure mapping keys to values using a hash function.",
        semantic_rubric_ideas=None
    )
    with pytest.raises(ValueError) as exc_info:
        bare_record.to_rubric()
    assert "cannot convert to questionrubric without semantic propositions" in str(exc_info.value).lower()

def test_qanda_does_not_mutate_or_overwrite_cpu1_rubrics_or_datasets():
    """Verify integrating QandA.json preserves all existing CPU 1 rubrics, datasets, and lockbox safeguards."""
    # 1. 120 Rubrics intact
    rubrics = load_rubrics(REPO_ROOT / "data" / "rubrics_120.json")
    assert len(rubrics) == 120
    is_valid, msg, meta = validate_rubrics(rubrics)
    assert is_valid is True
    assert meta["num_questions"] == 120

    # 2. 240 Dev and 60 Held-out datasets intact and disjoint
    dev_data, heldout_data = load_and_verify_datasets(
        dev_path=REPO_ROOT / "data" / "dataset_dev_240.json",
        heldout_path=REPO_ROOT / "data" / "dataset_heldout_60.json",
        allow_heldout_load=True
    )
    assert len(dev_data) == 240
    assert len(heldout_data) == 60
    assert {e["example_id"] for e in dev_data}.isdisjoint({e["example_id"] for e in heldout_data})

    # 3. Lockbox guard remains active
    with pytest.raises(HeldOutAccessError):
        evaluate_held_out_guarded(run_held_out_final_once=False)

def test_qanda_get_by_id_lookup():
    """Verify lookup helper retrieves correct record or returns None for unknown IDs."""
    record = get_qanda_by_id("ENG001", path=REPO_ROOT / "data" / "QandA.json")
    assert record is not None
    assert record.id == "ENG001"
    assert record.category == "Software and Computer Science Fundamentals"
    assert record.subcategory == "Data Structures and Algorithms"

    unknown = get_qanda_by_id("NON_EXISTENT_ID", path=REPO_ROOT / "data" / "QandA.json")
    assert unknown is None
