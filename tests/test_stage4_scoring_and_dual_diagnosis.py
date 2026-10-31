"""Unit and integration test suite for Stage 4: Evidence-First Scoring & Dual Diagnosis Integration.

Verifies:
1. Live per-turn deterministic rubric scoring and isotonic calibration.
2. Dual Diagnosis bifurcation:
   - Technical Knowledge Gaps (missing concepts, marks lost, model sentence fix).
   - Pronunciation & Articulation Improvements (recovered slices, coaching tip, 0.0 penalty).
3. Confidence-aware uncertainty protection (acoustic ambiguity never penalizes technical mark).
4. Silent session persistence in SQLite and mirror JSON.
5. Multi-turn cumulative FairScore aggregation on session conclusion.
"""

import pytest
from pathlib import Path

from score.turn_evaluator import TurnEvaluator
from score.qanda import get_qanda_by_id
from api.main import (
    start_interview_session,
    process_interview_turn,
    conclude_interview,
    get_interview_session,
    StartInterviewRequest,
    InterviewTurnRequest,
    ConcludeInterviewRequest,
    session_manager,
    conversational_engine,
)


@pytest.fixture
def evaluator():
    return TurnEvaluator()


# ==============================================================================
# 1. TurnEvaluator Unit Tests
# ==============================================================================

def test_turn_evaluator_complete_technical_answer(evaluator):
    """Verify high-quality technical response achieves high FairScore with demonstrated rubric ideas."""
    q_id = "ENG008"
    curr_q = get_qanda_by_id(q_id)
    assert curr_q is not None

    answer = (
        "In message-driven distributed systems, brokers provide at-least-once delivery making duplicates inevitable. "
        "We track unique idempotency keys in an atomic Redis store or database transaction to detect and skip duplicate events."
    )

    eval_res = evaluator.evaluate_turn(
        question_id=q_id,
        question_text=curr_q.question,
        recovered_utterance=answer,
        raw_utterance=answer,
        curr_q=curr_q
    )

    # 1. Scoring dimensions
    scores = eval_res["scores"]
    assert scores["calibrated_content_5pt"] >= 3.0
    assert scores["overall_fairscore_5pt"] >= 2.0
    assert scores["content_pct"] >= 60

    # 2. Rubric breakdown
    rubric = eval_res["rubric_breakdown"]
    assert len(rubric) == 2
    assert all(r["verdict"] == "demonstrated" for r in rubric)
    assert all(r["marks_lost"] == 0.0 for r in rubric)

    # 3. Dual Diagnosis
    dual = eval_res["dual_diagnosis"]
    assert dual["accent_penalty_applied"] is False
    assert dual["acoustic_protection_active"] is True
    # All satisfied indicates complete mastery
    assert len(dual["technical_knowledge_gaps"]) == 1
    assert dual["technical_knowledge_gaps"][0]["status"] == "satisfied"


def test_turn_evaluator_dual_diagnosis_bifurcation(evaluator):
    """Verify clear distinction between technical knowledge gaps and accent/pronunciation improvements."""
    q_id = "ENG008"
    curr_q = get_qanda_by_id(q_id)
    assert curr_q is not None

    # Candidate omits idempotency keys/atomic transactions (Idea 2) and has accent slip on 'reddis'
    recovered_answer = "Message brokers provide at-least-once delivery so duplicate messages are inevitable in distributed systems."
    raw_answer = "Message brokers provide at-least-once delivery so duplicate messages are inevitable in distributed systems."
    slice_log = [{
        "status": "CORRECTED",
        "original_text": "reddis",
        "verified_text": "Redis",
        "time_range": "2.1s - 2.8s",
        "phonetic_match": True
    }]

    eval_res = evaluator.evaluate_turn(
        question_id=q_id,
        question_text=curr_q.question,
        recovered_utterance=recovered_answer,
        raw_utterance=raw_answer,
        slice_recovery_log=slice_log,
        curr_q=curr_q
    )

    dual = eval_res["dual_diagnosis"]

    # Category A: Technical Knowledge Gap identified
    tech_gaps = dual["technical_knowledge_gaps"]
    assert len(tech_gaps) >= 1
    missing_idea2 = next((g for g in tech_gaps if "ENG008_IDEA_2" in g["criterion_id"] or "idempotency" in g["concept"].lower()), None)
    assert missing_idea2 is not None
    assert missing_idea2["marks_lost"] > 0.0
    assert len(missing_idea2["model_sentence_fix"]) > 10

    # Category B: Pronunciation Improvement identified with ZERO mark penalty
    pronounce = dual["pronunciation_improvements"]
    assert len(pronounce) == 1
    assert pronounce[0]["spoken_slice"] == "reddis"
    assert pronounce[0]["canonical_term"] == "Redis"
    assert pronounce[0]["score_deduction"] == 0.0
    assert "Pronounce 'Redis' clearly" in pronounce[0]["coaching_tip"]

    # Invariance check
    assert dual["accent_penalty_applied"] is False


def test_turn_evaluator_acoustic_uncertainty_provisional_credit(evaluator):
    """Verify ambiguous acoustic slices trigger provisional credit without penalizing technical score."""
    q_id = "ENG008"
    curr_q = get_qanda_by_id(q_id)

    # Abstained acoustic slice
    slice_log = [{
        "status": "ABSTAINED",
        "original_text": "indem",
        "candidate_term": "idempotent",
        "time_range": "1.0s - 1.5s",
        "reason": "Insufficient acoustic confidence"
    }]

    eval_res = evaluator.evaluate_turn(
        question_id=q_id,
        question_text=curr_q.question,
        recovered_utterance="Brokers provide at-least-once delivery.",
        raw_utterance="Brokers provide at-least-once delivery.",
        slice_recovery_log=slice_log,
        curr_q=curr_q
    )

    assert eval_res["uncertainty"]["provisional_credit_applied"] is True
    dual = eval_res["dual_diagnosis"]
    assert dual["pronunciation_improvements"][0]["status"] == "PROVISIONAL_ABSTAINED"
    assert dual["pronunciation_improvements"][0]["score_deduction"] == 0.0


# ==============================================================================
# 2. End-to-End Interview Turn & Session Persistence Integration Tests
# ==============================================================================

def test_interview_turn_silent_evaluation_and_persistence():
    """Verify live turn execution silently runs evaluator and persists evaluation payload in SQLite."""
    # 1. Start interview
    start_res = start_interview_session(StartInterviewRequest(
        candidate_name="Ada Lovelace",
        domain="Software and Computer Science Fundamentals",
        difficulty="Intermediate",
        num_questions=1
    ))
    sess_id = start_res["session_id"]

    # 2. Candidate answers greeting
    turn1 = process_interview_turn(InterviewTurnRequest(
        session_id=sess_id,
        candidate_utterance="Hello! I am ready to begin the technical evaluation."
    ))
    assert turn1["stage"] == "TECHNICAL_QUESTION"

    # 3. Candidate answers Technical Question with technical content and accent slip
    q_detail = turn1.get("current_question_detail") or {}
    q_id = q_detail.get("id") or "ENG008"
    curr_q = get_qanda_by_id(q_id)

    # Candidate says "semfor" and "has map"
    turn2 = process_interview_turn(InterviewTurnRequest(
        session_id=sess_id,
        candidate_utterance="We synchronize processes using a semfor and resolve collisions in a has map."
    ))

    # 4. Assert evaluation is returned in response
    eval_data = turn2.get("evaluation")
    assert eval_data is not None
    assert "scores" in eval_data
    assert "overall_fairscore_5pt" in eval_data["scores"]
    assert "dual_diagnosis" in eval_data
    assert eval_data["dual_diagnosis"]["accent_penalty_applied"] is False

    # 5. Assert evaluation is persisted in SQLite session storage
    sess = session_manager.get_session(sess_id)
    assert sess is not None
    cand_turns = [t for t in sess.turns if t.speaker == "candidate"]
    assert len(cand_turns) == 2  # Turn 1: greeting response, Turn 2: technical answer
    tech_turn = cand_turns[1]
    assert tech_turn.evaluation is not None
    assert tech_turn.evaluation["question_id"] == q_id
    assert tech_turn.evaluation["dual_diagnosis"]["accent_penalty_applied"] is False


def test_multi_turn_conclude_cumulative_fairscore_aggregation():
    """Verify conclude_session auto-aggregates multi-turn FairScores, content/structure, and dual diagnoses."""
    start_res = start_interview_session(StartInterviewRequest(
        candidate_name="Alan Turing",
        domain="Software and Computer Science Fundamentals",
        difficulty="Intermediate",
        num_questions=2
    ))
    sess_id = start_res["session_id"]

    # Turn 1: Greeting
    process_interview_turn(InterviewTurnRequest(
        session_id=sess_id,
        candidate_utterance="Hello, I specialize in cryptography and computability theory."
    ))

    # Turn 2: Question 1
    process_interview_turn(InterviewTurnRequest(
        session_id=sess_id,
        candidate_utterance="Brokers deliver messages at least once so duplicates are inevitable. We track unique idempotency keys in Redis."
    ))

    # Turn 3: Conclude interview
    conclude_res = conclude_interview(ConcludeInterviewRequest(session_id=sess_id))
    assert conclude_res["status"] == "completed"
    assert conclude_res["stage"] == "COMPLETED"

    final_sc = conclude_res["final_scorecard"]
    assert final_sc is not None
    assert final_sc["candidate_name"] == "Alan Turing"
    assert final_sc["questions_evaluated"] >= 1
    assert "overall_fairscore" in final_sc
    assert "overall_fairscore_5pt" in final_sc
    assert "content_score" in final_sc
    assert "structure_score" in final_sc
    assert "cumulative_dual_diagnosis" in final_sc
    assert final_sc["cumulative_dual_diagnosis"]["accent_penalty_applied"] is False
