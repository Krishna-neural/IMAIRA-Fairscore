"""Session state management for the IMAIRA-Fairscore AI Mock Interviewer."""

import random
import uuid
from typing import Any, Dict, List, Optional
import streamlit as st

from score.qanda import QnARecord, load_qanda

STATE_SETUP = "SETUP"
STATE_INTERVIEWING = "INTERVIEWING"
STATE_FEEDBACK = "FEEDBACK"
STATE_COMPLETED = "COMPLETED"


def init_session_state():
    """Initialize default keys in Streamlit session state."""
    defaults = {
        "interview_state": STATE_SETUP,
        "session_id": str(uuid.uuid4())[:8],
        "all_questions": [],
        "selected_questions": [],
        "current_question_idx": 0,
        "candidate_answers": {},  # question_id -> str
        "evaluations": {},        # question_id -> dict
        "is_evaluating": False,
        "error_message": None,
        "category_choice": "All Categories",
        "difficulty_choice": "All Difficulties",
        "num_questions_choice": 3
    }
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v


def load_dataset_cached(path: str = "data/QandA.json") -> List[QnARecord]:
    """Load question dataset with caching in session state."""
    if not st.session_state.get("all_questions"):
        try:
            records = load_qanda(path)
            st.session_state.all_questions = records
        except Exception as e:
            st.session_state.error_message = f"Failed to load questions from {path}: {e}"
            st.session_state.all_questions = []
    return st.session_state.all_questions


def start_interview(
    category: str,
    difficulty: str,
    num_questions: int,
    records: List[QnARecord],
    seed: Optional[int] = None
) -> bool:
    """Filter questions and initialize an active interview session."""
    filtered = list(records)

    if category != "All Categories":
        filtered = [q for q in filtered if q.category == category]

    if difficulty != "All Difficulties":
        filtered = [q for q in filtered if q.difficulty == difficulty]

    if not filtered:
        st.session_state.error_message = "No questions found matching your category and difficulty criteria."
        return False

    rng = random.Random(seed)
    n = min(num_questions, len(filtered))
    chosen = rng.sample(filtered, n)

    st.session_state.session_id = f"sess_{uuid.uuid4().hex[:8]}"
    st.session_state.selected_questions = chosen
    st.session_state.current_question_idx = 0
    st.session_state.candidate_answers = {}
    st.session_state.evaluations = {}
    st.session_state.interview_state = STATE_INTERVIEWING
    st.session_state.error_message = None
    return True


def record_evaluation(question_id: str, answer_text: str, eval_data: Dict[str, Any]):
    """Store candidate answer and evaluation output."""
    st.session_state.candidate_answers[question_id] = answer_text
    st.session_state.evaluations[question_id] = eval_data
    st.session_state.interview_state = STATE_FEEDBACK


def advance_question():
    """Proceed to the next question or complete the interview."""
    idx = st.session_state.current_question_idx + 1
    if idx < len(st.session_state.selected_questions):
        st.session_state.current_question_idx = idx
        st.session_state.interview_state = STATE_INTERVIEWING
    else:
        st.session_state.interview_state = STATE_COMPLETED


def reset_interview():
    """Reset session state to return to setup screen."""
    st.session_state.interview_state = STATE_SETUP
    st.session_state.session_id = f"sess_{uuid.uuid4().hex[:8]}"
    st.session_state.selected_questions = []
    st.session_state.current_question_idx = 0
    st.session_state.candidate_answers = {}
    st.session_state.evaluations = {}
    st.session_state.error_message = None
