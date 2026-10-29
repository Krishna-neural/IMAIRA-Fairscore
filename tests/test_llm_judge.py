"""Unit tests for the Evidence-Grounded LLM Evaluation Engine (Gemini 3.8 Flash + QandA.json)."""

import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

import pytest
from contracts.transcript import WordTiming
from score.rubrics import QuestionRubric, SemanticRubricIdea
from score.llm_judge import LLMEvaluationEngine, IMAIRA_SYSTEM_PROMPT_V1


@pytest.fixture
def sample_question():
    return QuestionRubric(
        question_id="Q032",
        question_prompt="Explain how a Hash Map handles collisions and the significance of the load factor.",
        domain="Algorithms",
        semantic_rubric_ideas=[
            SemanticRubricIdea(
                idea_id="Q032_IDEA_1",
                semantic_statement="Hash collisions occur when distinct keys produce identical hash indices, resolved via separate chaining or open addressing.",
                required=True,
                weight=0.34,
                acceptable_paraphrase_guidance="Accepts separate chaining or open addressing."
            ),
            SemanticRubricIdea(
                idea_id="Q032_IDEA_2",
                semantic_statement="Load factor is the ratio of stored elements to total bucket capacity (N / C).",
                required=True,
                weight=0.33,
                acceptable_paraphrase_guidance="Accepts ratio of elements to buckets."
            ),
            SemanticRubricIdea(
                idea_id="Q032_IDEA_3",
                semantic_statement="Exceeding the maximum load factor triggers resizing and rehashing of all entries into a larger array.",
                required=True,
                weight=0.33,
                acceptable_paraphrase_guidance="Accepts table resizing and rehashing."
            )
        ]
    )


@pytest.fixture
def sample_word_timings():
    words = ["a", "hash", "map", "never", "has", "collisions", "because", "unique", "keys"]
    timings = []
    t = 0.0
    for w in words:
        timings.append(WordTiming(word=w, start=t, end=t + 0.3, conf=0.95))
        t += 0.35
    return timings


def test_llm_engine_initialization():
    """Verify engine initializes and loads reference Q&A knowledge."""
    engine = LLMEvaluationEngine()
    assert len(engine.qanda_records) > 0, "Failed to load reference Q&A knowledge base."
    assert "Version: 1.0" in IMAIRA_SYSTEM_PROMPT_V1


def test_qanda_match_lookup():
    """Verify Q&A matcher retrieves canonical reference answers."""
    engine = LLMEvaluationEngine()
    eng_question = QuestionRubric(
        question_id="ENG001",
        question_prompt="Compare Red-Black Trees and AVL Trees in terms of balancing invariants and height.",
        domain="Data Structures",
        semantic_rubric_ideas=[
            SemanticRubricIdea(
                idea_id="ENG001_IDEA_1",
                semantic_statement="AVL trees enforce stricter balance factor limits compared to Red-Black trees.",
                required=True,
                weight=0.5,
                acceptable_paraphrase_guidance="Accepts height differences."
            )
        ]
    )
    match = engine._find_qanda_match(eng_question)
    assert match is not None, f"Should find reference Q&A for {eng_question.question_id}"
    assert "avl" in match.get("question", "").lower() or "avl" in match.get("answer", "").lower()
    assert "answer" in match
    assert len(match["answer"]) > 20


def test_payload_builder_includes_all_sources_of_truth(sample_question, sample_word_timings):
    """Verify that prompt builder injects Q&A, rubrics, transcripts, and timestamps."""
    engine = LLMEvaluationEngine()
    qanda_match = engine._find_qanda_match(sample_question)
    payload = engine._build_user_payload(
        question=sample_question,
        qanda_record=qanda_match,
        raw_transcript="hash map has no collision",
        corrected_transcript="hash map never has collisions",
        word_timings=sample_word_timings
    )

    assert "task_mode: combined" in payload
    assert "Q032" in payload
    assert "Reference Canonical Answer" in payload
    assert "Q032_IDEA_1" in payload
    assert "hash map never has collisions" in payload
    assert "[0.00s -" in payload  # Verifies timestamps injected


def test_process_llm_result_parsing(sample_question, sample_word_timings):
    """Verify parser maps LLM JSON to completeness, correctness, structure, and feedback."""
    engine = LLMEvaluationEngine()
    mock_llm_json = {
        "status": "ok",
        "model_used": "gemini-3.8-flash",
        "content_evaluation": {
            "rubric_judgments": [
                {
                    "idea_id": "Q032_IDEA_1",
                    "judgment": "missing",
                    "evidence_quote": "",
                    "reasoning": "Candidate denied collisions occur."
                },
                {
                    "idea_id": "Q032_IDEA_2",
                    "judgment": "missing",
                    "evidence_quote": "",
                    "reasoning": "Load factor was omitted."
                },
                {
                    "idea_id": "Q032_IDEA_3",
                    "judgment": "missing",
                    "evidence_quote": "",
                    "reasoning": "Resizing was omitted."
                }
            ],
            "technical_correctness": {
                "has_critical_misconception": True,
                "misconceptions_detected": [
                    {
                        "concept": "Hash Map Collisions",
                        "severity": "CRITICAL",
                        "error_explanation": "Collisions are mathematically inevitable by the Pigeonhole Principle.",
                        "candidate_quote": "never has collisions"
                    }
                ]
            }
        },
        "structure_evaluation": {
            "framing": {"score": 2.0, "feedback": "Brief statement", "evidence_quote": "a hash map"},
            "coherence": {"score": 2.5, "feedback": "Grammatically coherent", "evidence_quote": "because unique keys"},
            "closure": {"score": 1.0, "feedback": "Lacks closure", "evidence_quote": "keys"}
        },
        "actionable_feedback": [
            {
                "priority": 1,
                "issue": "Denied existence of hash collisions.",
                "evidence_quote": "never has collisions",
                "why_it_matters": "Collision handling is core to hash maps.",
                "improvement_action": "Study chaining and open addressing.",
                "example_sentence": "Collisions occur when different keys hash to the same bucket index."
            }
        ]
    }

    result = engine._process_llm_result(mock_llm_json, sample_question, sample_word_timings)
    assert result["status"] == "ok"
    assert result["content_completeness"] == 1.0
    assert result["content_correctness"] == 1.5  # Critical penalty applied
    assert len(result["where_got_wrong"]) == 1
    assert result["where_got_wrong"][0]["severity"] == "CRITICAL"
    assert len(result["actionable_feedback"]) == 1
    assert result["actionable_feedback"][0]["priority"] == 1


def test_deterministic_offline_fallback(sample_question, sample_word_timings):
    """Verify that when offline, engine executes local fallback without error."""
    engine = LLMEvaluationEngine()
    result = engine._fallback_local_evaluation(
        question=sample_question,
        qanda_record=None,
        transcript="a hash map never has collisions because unique keys",
        word_timings=sample_word_timings
    )

    assert result["status"] == "ok"
    assert result["model_used"] == "deterministic_offline"
    assert 1.0 <= result["content_completeness"] <= 5.0
    assert 1.0 <= result["content_correctness"] <= 5.0
    assert len(result["where_got_wrong"]) >= 1
    assert result["where_got_wrong"][0]["concept"] == "Hash Map Collisions"
