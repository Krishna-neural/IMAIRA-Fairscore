"""
IMAIRA FairScore — Comprehensive Evidence-First Scoring Engine Test Suite
========================================================================
Validates all 10 evaluation scenarios mandated by the Evidence-First specification:
1. Completely Correct Response
2. Partially Correct Response
3. Technically Incorrect Response (Misconception Detection)
4. Incomplete Explanation (Partial Marks)
5. Alternative Terminology (Acceptable Equivalents)
6. Fluent but Factually Wrong Answer (Zero marks - "No evidence, no marks")
7. Short and Highly Accurate Response (Brevity does not penalize score)
8. Long Response with Irrelevant Filler (Filler does not earn marks)
9. Contradictory Statements (Critical misconception docks marks)
10. Empty Response / Complete Silence (0.0 marks awarded)
"""

import pytest
from score.evidence_models import (
    RubricCriterion,
    QuestionDefinition,
    MisconceptionItem,
    EvidenceScorecard,
    load_evidence_question_bank
)
from score.evidence_scorer import DeterministicEvidenceScorer


@pytest.fixture
def sample_question() -> QuestionDefinition:
    """Standard intermediate question with multi-criterion rubric."""
    return QuestionDefinition(
        question_id="TEST_DS_001",
        question="What is a hash map and how does it handle collisions?",
        domain="Data Structures",
        difficulty="Intermediate",
        total_marks=10.0,
        expected_concepts=["Key-Value Mapping", "Hash Function", "Chaining", "Open Addressing"],
        rubric=[
            RubricCriterion(
                criterion_id="R1",
                description="Defines a hash map as an associative array mapping keys to values via a hash function.",
                max_points=2.5,
                scoring_guidelines="Full credit for key-value pair mapping through hash calculation.",
                acceptable_alternatives=["hash table", "associative array", "dictionary"]
            ),
            RubricCriterion(
                criterion_id="R2",
                description="Explains collision concept: two distinct keys produce the same hash bucket index.",
                max_points=2.5,
                scoring_guidelines="Full credit for explaining index collision.",
                acceptable_alternatives=["hash collision", "index conflict", "same bucket"]
            ),
            RubricCriterion(
                criterion_id="R3",
                description="Explains Separate Chaining using linked lists or trees at each bucket index.",
                max_points=2.5,
                scoring_guidelines="Full credit for explaining chained nodes/lists in each bucket.",
                acceptable_alternatives=["chaining", "linked list in bucket"]
            ),
            RubricCriterion(
                criterion_id="R4",
                description="Explains Open Addressing where collision triggers probing adjacent slots.",
                max_points=2.5,
                scoring_guidelines="Full credit for mentioning linear probing or finding next available slot.",
                acceptable_alternatives=["linear probing", "probing", "open addressing"]
            )
        ]
    )


@pytest.fixture
def scorer() -> DeterministicEvidenceScorer:
    return DeterministicEvidenceScorer(partial_credit_ratio=0.50)


# SCENARIO 1: Completely Correct Response
def test_scenario_1_completely_correct(sample_question, scorer):
    transcript = (
        "A hash map is a data structure that maps keys to values using a hash function. "
        "A hash collision happens when two keys hash to the same bucket. "
        "To handle collisions, separate chaining stores elements in a linked list in each bucket. "
        "Alternatively, open addressing uses linear probing to find the next available slot."
    )
    raw_evals = [
        {
            "criterion_id": "R1",
            "status": "satisfied",
            "evidence": [{"text": "maps keys to values using a hash function"}],
            "reason": "Clear definition of hash map and hash function."
        },
        {
            "criterion_id": "R2",
            "status": "satisfied",
            "evidence": [{"text": "two keys hash to the same bucket"}],
            "reason": "Accurately describes collision."
        },
        {
            "criterion_id": "R3",
            "status": "satisfied",
            "evidence": [{"text": "separate chaining stores elements in a linked list in each bucket"}],
            "reason": "Explains separate chaining."
        },
        {
            "criterion_id": "R4",
            "status": "satisfied",
            "evidence": [{"text": "open addressing uses linear probing to find the next available slot"}],
            "reason": "Explains open addressing and linear probing."
        }
    ]

    scorecard = scorer.calculate_scorecard(
        question=sample_question,
        raw_evidence_evaluations=raw_evals,
        misconceptions=[],
        transcript_text=transcript,
        raw_structure_scores={"framing": 5.0, "coherence": 5.0, "closure": 5.0}
    )

    assert scorecard.total_awarded_marks == 10.0
    assert scorecard.percentage_score == 100.0
    assert scorecard.content_completeness_5pt == 5.00
    assert scorecard.content_correctness_5pt == 5.00
    assert scorecard.answer_structure_5pt == 5.00
    assert len(scorecard.criteria_evaluations) == 4
    for ev in scorecard.criteria_evaluations:
        assert ev.status == "satisfied"
        assert len(ev.evidence) > 0
        assert ev.awarded_points == ev.max_points


# SCENARIO 2: Partially Correct Response
def test_scenario_2_partially_correct(sample_question, scorer):
    transcript = (
        "A hash map maps keys to values using a hash function. "
        "Collisions happen when keys hash to the same bucket."
    )
    raw_evals = [
        {
            "criterion_id": "R1",
            "status": "satisfied",
            "evidence": [{"text": "maps keys to values using a hash function"}],
            "reason": "Correct definition."
        },
        {
            "criterion_id": "R2",
            "status": "satisfied",
            "evidence": [{"text": "keys hash to the same bucket"}],
            "reason": "Collision explained."
        },
        {
            "criterion_id": "R3",
            "status": "missing",
            "evidence": [],
            "reason": "Chaining not mentioned."
        },
        {
            "criterion_id": "R4",
            "status": "missing",
            "evidence": [],
            "reason": "Open addressing not mentioned."
        }
    ]

    scorecard = scorer.calculate_scorecard(
        question=sample_question,
        raw_evidence_evaluations=raw_evals,
        misconceptions=[],
        transcript_text=transcript,
        raw_structure_scores={"framing": 3.0, "coherence": 3.0, "closure": 3.0}
    )

    assert scorecard.total_awarded_marks == 5.0
    assert scorecard.percentage_score == 50.0
    assert scorecard.content_completeness_5pt == 3.00
    assert scorecard.criteria_evaluations[2].status == "missing"
    assert scorecard.criteria_evaluations[2].awarded_points == 0.0
    assert scorecard.criteria_evaluations[3].status == "missing"


# SCENARIO 3: Technically Incorrect Response (Misconception Penalty)
def test_scenario_3_technically_incorrect(sample_question, scorer):
    transcript = "Hash maps never have collisions because keys are mathematically guaranteed unique."
    misconception = MisconceptionItem(
        concept="Hash Map Collisions",
        severity="CRITICAL",
        error_explanation="Claimed hash maps never collide due to unique keys, violating the Pigeonhole Principle.",
        candidate_quote="never have collisions"
    )

    raw_evals = [
        {"criterion_id": "R1", "status": "missing", "evidence": [], "reason": ""},
        {"criterion_id": "R2", "status": "satisfied", "evidence": [{"text": "never have collisions"}], "reason": "Claims collision handling"},
        {"criterion_id": "R3", "status": "missing", "evidence": [], "reason": ""},
        {"criterion_id": "R4", "status": "missing", "evidence": [], "reason": ""}
    ]

    scorecard = scorer.calculate_scorecard(
        question=sample_question,
        raw_evidence_evaluations=raw_evals,
        misconceptions=[misconception],
        transcript_text=transcript,
        raw_structure_scores={"framing": 2.0, "coherence": 2.0, "closure": 2.0}
    )

    # R2 points denied because critical misconception explicitly refuted it
    r2_eval = next(c for c in scorecard.criteria_evaluations if c.criterion_id == "R2")
    assert r2_eval.awarded_points == 0.0
    assert scorecard.content_correctness_5pt < 4.00
    assert len(scorecard.misconceptions) == 1


# SCENARIO 4: Incomplete Explanation (Partial Marks)
def test_scenario_4_incomplete_explanation(sample_question, scorer):
    transcript = "A hash map stores elements and we can use chaining with linked lists to resolve problems."
    raw_evals = [
        {
            "criterion_id": "R1",
            "status": "partially_satisfied",
            "evidence": [{"text": "hash map stores elements"}],
            "reason": "Mentioned storage but omitted hash function and key-value mapping mechanics."
        },
        {
            "criterion_id": "R2",
            "status": "missing",
            "evidence": [],
            "reason": "Did not define collision."
        },
        {
            "criterion_id": "R3",
            "status": "satisfied",
            "evidence": [{"text": "chaining with linked lists"}],
            "reason": "Mentions chaining."
        },
        {
            "criterion_id": "R4",
            "status": "missing",
            "evidence": [],
            "reason": "Open addressing omitted."
        }
    ]

    scorecard = scorer.calculate_scorecard(
        question=sample_question,
        raw_evidence_evaluations=raw_evals,
        misconceptions=[],
        transcript_text=transcript,
        raw_structure_scores={"framing": 3.0, "coherence": 3.0, "closure": 3.0}
    )

    r1_eval = next(c for c in scorecard.criteria_evaluations if c.criterion_id == "R1")
    assert r1_eval.status == "partially_satisfied"
    assert r1_eval.awarded_points == round(2.5 * 0.5, 2)  # 1.25 pts
    assert scorecard.total_awarded_marks == 1.25 + 2.5  # 3.75 pts


# SCENARIO 5: Alternative Terminology (Acceptable Equivalents)
def test_scenario_5_alternative_terminology(sample_question, scorer):
    transcript = (
        "A dictionary stores key-value pairs through a hashing routine. "
        "Index conflicts occur when two items want the same slot. "
        "Closed hashing resolves this by linear probing across adjacent array indices."
    )
    raw_evals = [
        {
            "criterion_id": "R1",
            "status": "satisfied",
            "evidence": [{"text": "dictionary stores key-value pairs"}],
            "reason": "Used 'dictionary' as an acceptable alternative for hash map."
        },
        {
            "criterion_id": "R2",
            "status": "satisfied",
            "evidence": [{"text": "Index conflicts occur when two items want the same slot"}],
            "reason": "Used 'Index conflicts' as valid paraphrase for hash collisions."
        },
        {
            "criterion_id": "R3",
            "status": "missing",
            "evidence": [],
            "reason": "Chaining omitted."
        },
        {
            "criterion_id": "R4",
            "status": "satisfied",
            "evidence": [{"text": "linear probing across adjacent array indices"}],
            "reason": "Linear probing correctly identified."
        }
    ]

    scorecard = scorer.calculate_scorecard(
        question=sample_question,
        raw_evidence_evaluations=raw_evals,
        misconceptions=[],
        transcript_text=transcript,
        raw_structure_scores={"framing": 4.0, "coherence": 4.0, "closure": 4.0}
    )

    assert scorecard.total_awarded_marks == 7.5
    assert scorecard.criteria_evaluations[0].status == "satisfied"
    assert scorecard.criteria_evaluations[1].status == "satisfied"
    assert scorecard.criteria_evaluations[3].status == "satisfied"


# SCENARIO 6: Fluent but Factually Wrong Answer ("No evidence, no marks")
def test_scenario_6_fluent_but_factually_wrong(sample_question, scorer):
    transcript = (
        "In a modern distributed hyper-scale enterprise architecture, our multi-threaded data pipelines "
        "leverage asynchronous non-blocking event-driven microservices to dynamically optimize stateful caching "
        "across distributed clusters with high throughput and maximum scalability."
    )
    # The response is completely fluent, sounds sophisticated, but contains ZERO evidence of hash map or collision resolution!
    raw_evals = [
        {"criterion_id": "R1", "status": "missing", "evidence": [], "reason": "No mention of hash map or key-value hashing."},
        {"criterion_id": "R2", "status": "missing", "evidence": [], "reason": "No mention of collision."},
        {"criterion_id": "R3", "status": "missing", "evidence": [], "reason": "No mention of chaining."},
        {"criterion_id": "R4", "status": "missing", "evidence": [], "reason": "No mention of open addressing."}
    ]

    scorecard = scorer.calculate_scorecard(
        question=sample_question,
        raw_evidence_evaluations=raw_evals,
        misconceptions=[],
        transcript_text=transcript,
        raw_structure_scores={"framing": 5.0, "coherence": 5.0, "closure": 5.0}  # high structure, zero content
    )

    # Core Rule: Fluency alone cannot buy content marks
    assert scorecard.total_awarded_marks == 0.0
    assert scorecard.percentage_score == 0.0
    assert scorecard.content_completeness_5pt == 1.00  # Bottom of scale


# SCENARIO 7: Short and Highly Accurate Response
def test_scenario_7_short_and_accurate(sample_question, scorer):
    # Extremely concise, only 28 words, zero filler
    transcript = (
        "Hash map maps keys to values via hashing. "
        "Collisions occur at identical bucket indices; we resolve them using separate chaining or linear probing."
    )
    raw_evals = [
        {"criterion_id": "R1", "status": "satisfied", "evidence": [{"text": "Hash map maps keys to values via hashing"}], "reason": "Accurate."},
        {"criterion_id": "R2", "status": "satisfied", "evidence": [{"text": "Collisions occur at identical bucket indices"}], "reason": "Accurate."},
        {"criterion_id": "R3", "status": "satisfied", "evidence": [{"text": "separate chaining"}], "reason": "Accurate."},
        {"criterion_id": "R4", "status": "satisfied", "evidence": [{"text": "linear probing"}], "reason": "Accurate."}
    ]

    scorecard = scorer.calculate_scorecard(
        question=sample_question,
        raw_evidence_evaluations=raw_evals,
        misconceptions=[],
        transcript_text=transcript,
        raw_structure_scores={"framing": 4.5, "coherence": 4.5, "closure": 4.5}
    )

    # Full content marks awarded despite concise length
    assert scorecard.total_awarded_marks == 10.0
    assert scorecard.content_completeness_5pt == 5.00
    assert scorecard.percentage_score == 100.0


# SCENARIO 8: Long Response with Irrelevant Filler
def test_scenario_8_long_response_with_filler(sample_question, scorer):
    transcript = (
        "Well, you know, when I was in college my professor spent three weeks discussing data structures. "
        "I really loved algorithms class. Anyway, a hash map maps keys to values using a hash function. "
        "My favorite language is Python and in Python it is called a dict. "
        "I once used it in a hackathon where we built an app for ordering pizza. "
        "When two keys hash to the same bucket, that is a collision. "
        "Then we went out for coffee after the hackathon and celebrated our third place prize."
    )
    raw_evals = [
        {"criterion_id": "R1", "status": "satisfied", "evidence": [{"text": "hash map maps keys to values using a hash function"}], "reason": "Satisfied."},
        {"criterion_id": "R2", "status": "satisfied", "evidence": [{"text": "two keys hash to the same bucket, that is a collision"}], "reason": "Satisfied."},
        {"criterion_id": "R3", "status": "missing", "evidence": [], "reason": "Chaining not mentioned."},
        {"criterion_id": "R4", "status": "missing", "evidence": [], "reason": "Open addressing not mentioned."}
    ]

    scorecard = scorer.calculate_scorecard(
        question=sample_question,
        raw_evidence_evaluations=raw_evals,
        misconceptions=[],
        transcript_text=transcript,
        raw_structure_scores={"framing": 2.5, "coherence": 2.0, "closure": 2.0}
    )

    # Filler does not earn additional points: only R1 + R2 = 5.0 marks
    assert scorecard.total_awarded_marks == 5.0
    assert scorecard.percentage_score == 50.0
    assert scorecard.criteria_evaluations[2].status == "missing"
    assert scorecard.criteria_evaluations[3].status == "missing"


# SCENARIO 9: Contradictory Statements
def test_scenario_9_contradictory_statements(sample_question, scorer):
    transcript = (
        "A hash map maps keys to values. Collisions happen when two keys share an index. "
        "Actually, in modern computers hash maps never have collisions because memory is infinite."
    )
    misconception = MisconceptionItem(
        concept="Hash Map Collisions",
        severity="CRITICAL",
        error_explanation="Directly contradicted earlier claim by stating modern hash maps never have collisions due to infinite memory.",
        candidate_quote="never have collisions because memory is infinite"
    )
    raw_evals = [
        {"criterion_id": "R1", "status": "satisfied", "evidence": [{"text": "maps keys to values"}], "reason": "Initial definition."},
        {"criterion_id": "R2", "status": "satisfied", "evidence": [{"text": "Collisions happen when two keys share an index"}], "reason": "Initial statement."},
        {"criterion_id": "R3", "status": "missing", "evidence": [], "reason": ""},
        {"criterion_id": "R4", "status": "missing", "evidence": [], "reason": ""}
    ]

    scorecard = scorer.calculate_scorecard(
        question=sample_question,
        raw_evidence_evaluations=raw_evals,
        misconceptions=[misconception],
        transcript_text=transcript,
        raw_structure_scores={"framing": 2.5, "coherence": 1.5, "closure": 1.5}
    )

    # Critical contradiction on R2 docks R2 points to 0.0
    r2_eval = next(c for c in scorecard.criteria_evaluations if c.criterion_id == "R2")
    assert r2_eval.awarded_points == 0.0
    assert scorecard.content_correctness_5pt <= 3.50


# SCENARIO 10: Empty Response / Complete Silence
def test_scenario_10_empty_response(sample_question, scorer):
    transcript = "   "
    raw_evals = []

    scorecard = scorer.calculate_scorecard(
        question=sample_question,
        raw_evidence_evaluations=raw_evals,
        misconceptions=[],
        transcript_text=transcript,
        raw_structure_scores={"framing": 0.0, "coherence": 0.0, "closure": 0.0}
    )

    assert scorecard.total_awarded_marks == 0.0
    assert scorecard.percentage_score == 0.0
    assert scorecard.content_completeness_5pt == 1.00
    assert scorecard.answer_structure_5pt == 1.00
    for ev in scorecard.criteria_evaluations:
        assert ev.status == "missing"
        assert ev.awarded_points == 0.0
        assert len(ev.evidence) == 0


def test_structure_scale_normalization(sample_question, scorer):
    """Verify that structure ratios between 0.0 and 1.0 are properly normalized to 1.0 - 5.0 scale."""
    transcript = "A hash map maps keys to values."
    raw_evals = [{"criterion_id": "R1", "status": "satisfied", "evidence": [{"text": "maps keys to values"}], "reason": ""}]

    # Simulating LLM returning 0.95 ratio for structure
    scorecard = scorer.calculate_scorecard(
        question=sample_question,
        raw_evidence_evaluations=raw_evals,
        misconceptions=[],
        transcript_text=transcript,
        raw_structure_scores={"framing": 1.0, "coherence": 1.0, "closure": 0.8}  # mean = 0.95
    )

    # 1.0 ratio -> 5.0; 0.8 ratio -> 4.2. Weighted: 0.35*5.0 + 0.40*5.0 + 0.25*4.2 = 4.80
    assert scorecard.answer_structure_5pt >= 4.50
    assert scorecard.structure_breakdown["framing"] == 5.00
    assert scorecard.structure_breakdown["closure"] == 4.20
