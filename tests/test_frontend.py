"""Unit and integration test suite for the IMAIRA-Fairscore Mock Interviewer Frontend."""

import json
from pathlib import Path
from unittest.mock import patch, MagicMock
import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent

from score.qanda import QnARecord, load_qanda
from frontend.session import (
    STATE_SETUP,
    STATE_INTERVIEWING,
    STATE_FEEDBACK,
    STATE_COMPLETED,
    start_interview,
    record_evaluation,
    advance_question,
    reset_interview,
)
from frontend.api_client import (
    check_fairscore_health,
    check_asr_health,
    submit_answer_to_backend
)


# Mock Streamlit session state dict
class MockSessionState(dict):
    def __getattr__(self, key):
        return self.get(key)
    def __setattr__(self, key, value):
        self[key] = value


@pytest.fixture(autouse=True)
def mock_streamlit_state(monkeypatch):
    """Provide clean isolated session state for each test."""
    mock_state = MockSessionState({
        "interview_state": STATE_SETUP,
        "session_id": "test_sess_001",
        "all_questions": [],
        "selected_questions": [],
        "current_question_idx": 0,
        "candidate_answers": {},
        "evaluations": {},
        "is_evaluating": False,
        "error_message": None
    })
    monkeypatch.setattr("streamlit.session_state", mock_state)
    return mock_state


def test_frontend_loads_120_qanda_dataset():
    """Verify frontend can load and parse all 120 questions from data/QandA.json."""
    records = load_qanda(REPO_ROOT / "data" / "QandA.json")
    assert len(records) == 120
    assert all(isinstance(r, QnARecord) for r in records)


def test_interview_setup_filtering_and_no_duplicates():
    """Verify setup filters by category and difficulty without duplicate question IDs."""
    records = load_qanda(REPO_ROOT / "data" / "QandA.json")

    # Filter by specific category
    success = start_interview(
        category="Software and Computer Science Fundamentals",
        difficulty="All Difficulties",
        num_questions=3,
        records=records,
        seed=42
    )
    assert success is True

    import streamlit as st
    selected = st.session_state.selected_questions
    assert len(selected) == 3
    assert len(set(q.id for q in selected)) == 3  # Zero duplicates
    assert all(q.category == "Software and Computer Science Fundamentals" for q in selected)
    assert st.session_state.interview_state == STATE_INTERVIEWING
    assert st.session_state.current_question_idx == 0


def test_interview_state_lifecycle_progression():
    """Verify progression through questions until completion."""
    import streamlit as st
    records = load_qanda(REPO_ROOT / "data" / "QandA.json")

    start_interview(
        category="All Categories",
        difficulty="All Difficulties",
        num_questions=2,
        records=records,
        seed=101
    )
    assert st.session_state.interview_state == STATE_INTERVIEWING
    q1 = st.session_state.selected_questions[0]
    q2 = st.session_state.selected_questions[1]

    # Submit answer for Question 1
    record_evaluation(q1.id, "Answer for question 1.", {"scores": {"content": 80, "structure": 75, "communication": 85}, "overall_score": 80.0})
    assert st.session_state.interview_state == STATE_FEEDBACK
    assert q1.id in st.session_state.candidate_answers
    assert q1.id in st.session_state.evaluations

    # Advance to Question 2
    advance_question()
    assert st.session_state.interview_state == STATE_INTERVIEWING
    assert st.session_state.current_question_idx == 1

    # Submit answer for Question 2
    record_evaluation(q2.id, "Answer for question 2.", {"scores": {"content": 90, "structure": 85, "communication": 90}, "overall_score": 88.5})
    assert st.session_state.interview_state == STATE_FEEDBACK

    # Advance past last question -> COMPLETED
    advance_question()
    assert st.session_state.interview_state == STATE_COMPLETED

    # Reset
    reset_interview()
    assert st.session_state.interview_state == STATE_SETUP
    assert len(st.session_state.selected_questions) == 0


def test_direct_pipeline_evaluation_integration():
    """Verify submit_answer_to_backend runs offline and yields valid structured scores."""
    result = submit_answer_to_backend(
        session_id="test_sess_direct",
        question_id="ENG001",
        question_text="Compare Red-Black Trees and AVL Trees in terms of balancing invariants.",
        answer_text="AVL trees enforce strict balance factor of 1, while Red Black trees use color invariants.",
        duration_sec=60.0,
        force_direct=True
    )
    assert result["status"] == "completed"
    assert "scores" in result
    assert "content" in result["scores"]
    assert "structure" in result["scores"]
    assert "communication" in result["scores"]
    assert 0 <= result["scores"]["content"] <= 100
    assert 0 <= result["scores"]["structure"] <= 100
    assert 0 <= result["scores"]["communication"] <= 100
    assert "feedback" in result
    assert result["execution_mode"] == "DIRECT_PIPELINE"


def test_api_client_handles_offline_gracefully():
    """Verify health checks report offline when services are not running without crashing."""
    with patch("requests.get", side_effect=Exception("Connection refused")):
        f_health = check_fairscore_health()
        assert f_health["online"] is False

        a_health = check_asr_health()
        assert a_health["online"] is False
