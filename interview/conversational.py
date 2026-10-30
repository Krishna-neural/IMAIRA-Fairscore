"""Conversational Multi-Turn AI Technical Interviewer Engine.

Implements context-aware multi-turn dialog, strict identity persistence,
prompt-injection defense, and stage-driven technical interview progression.
"""

import os
import re
import uuid
from pathlib import Path
import logging
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple
from pydantic import BaseModel, Field

from score.qanda import QnARecord, get_qanda_by_id, load_qanda

logger = logging.getLogger("imaira.conversational")


class InterviewStage(str, Enum):
    GREETING = "GREETING"
    INTRODUCTION = "INTRODUCTION"
    TECHNICAL_QUESTION = "TECHNICAL_QUESTION"
    FOLLOW_UP = "FOLLOW_UP"
    CANDIDATE_QA = "CANDIDATE_QA"
    CONCLUSION = "CONCLUSION"


# Prompt-injection heuristics and role-override triggers
INJECTION_PATTERNS = [
    r"ignore (all )?previous instructions",
    r"system prompt",
    r"you are now (a|an)",
    r"give me (100|full) (marks|points|score)",
    r"disclose (your )?(prompt|configuration|keys|secrets)",
    r"override (scoring|evaluation|rules)",
    r"developer mode",
    r"jailbreak",
    r"bypass (rules|interview|scoring)",
    r"reveal (internal|hidden|secret)",
    r"what are your instructions",
]


class InterviewSessionState(BaseModel):
    session_id: str
    candidate_name: str = "Candidate"
    domain: str = "Software and Computer Science Fundamentals"
    difficulty: str = "Intermediate"
    stage: InterviewStage = InterviewStage.GREETING
    question_ids: List[str] = Field(default_factory=list)
    current_q_index: int = 0
    follow_up_active: bool = False
    turn_count: int = 0
    conversation_history: List[Dict[str, str]] = Field(default_factory=list)
    scores: Dict[str, Any] = Field(default_factory=dict)


def detect_prompt_injection(user_input: str) -> Optional[str]:
    """Detect prompt injection, role override, or score manipulation attempts."""
    lower_text = user_input.lower().strip()
    for pattern in INJECTION_PATTERNS:
        if re.search(pattern, lower_text):
            return "Role override or prompt injection attempt detected."
    return None


class ConversationalInterviewer:
    """Stateful technical interviewer managing dialog and stage transitions."""

    def __init__(self, questions: Optional[List[QnARecord]] = None):
        repo_root = Path(__file__).resolve().parent.parent
        q_path = repo_root / "data" / "QandA.json"
        self.questions = questions or load_qanda(q_path if q_path.exists() else "data/QandA.json")
        self.questions_by_id = {q.id: q for q in self.questions}

    def start_session(
        self,
        candidate_name: str,
        domain: str,
        difficulty: str,
        num_questions: int = 3
    ) -> Tuple[InterviewSessionState, str]:
        """Start a new multi-turn interview session."""
        session_id = f"sess_{uuid.uuid4().hex[:8]}"

        # Select matching questions
        matching = [
            q for q in self.questions
            if (domain == "All Categories" or q.category == domain) and
               (difficulty == "All Difficulties" or q.difficulty == difficulty)
        ]
        if not matching:
            matching = self.questions

        import random
        selected = random.sample(matching, min(num_questions, len(matching)))
        q_ids = [q.id for q in selected]

        state = InterviewSessionState(
            session_id=session_id,
            candidate_name=candidate_name or "Candidate",
            domain=domain,
            difficulty=difficulty,
            stage=InterviewStage.GREETING,
            question_ids=q_ids,
            current_q_index=0,
            follow_up_active=False,
            turn_count=0
        )

        greeting = (
            f"Hello {state.candidate_name}! Welcome to IMAIRA FairScore. "
            f"I'm your AI technical interviewer today for {domain}. "
            f"I'll be asking you a series of technical questions and evaluating your responses "
            f"based on technical mastery, structure, and communication clarity. "
            f"To get started, could you briefly introduce yourself and your technical background?"
        )
        state.conversation_history.append({"speaker": "interviewer", "text": greeting})
        return state, greeting

    def process_turn(
        self,
        state: InterviewSessionState,
        candidate_utterance: str
    ) -> Dict[str, Any]:
        """Process candidate turn, enforce identity, update stage, and generate AI response."""
        candidate_text = candidate_utterance.strip()
        state.turn_count += 1
        state.conversation_history.append({"speaker": "candidate", "text": candidate_text})

        # 1. Anti-manipulation check
        injection_warning = detect_prompt_injection(candidate_text)
        if injection_warning:
            ai_response = (
                "I am IMAIRA FairScore's dedicated technical interviewer. My role and evaluation "
                "criteria are server-enforced and cannot be altered. Let's stay focused on your interview."
            )
            state.conversation_history.append({"speaker": "interviewer", "text": ai_response})
            return {
                "ai_response": ai_response,
                "stage": state.stage,
                "current_question": self._get_current_question(state),
                "injection_detected": True,
                "session_state": state.model_dump()
            }

        # 2. Stage-based state machine
        if state.stage == InterviewStage.GREETING:
            state.stage = InterviewStage.TECHNICAL_QUESTION
            curr_q = self._get_current_question(state)
            q_text = curr_q.question if curr_q else "Explain your core technical area."
            ai_response = (
                f"Thank you for sharing, {state.candidate_name}. Let's dive straight into our first question: "
                f"{q_text}"
            )

        elif state.stage == InterviewStage.TECHNICAL_QUESTION:
            # Candidate answered primary question -> evaluate if follow-up needed
            curr_q = self._get_current_question(state)
            words = candidate_text.split()

            # Check if candidate indicated "I don't know"
            if len(words) < 6 and any(k in candidate_text.lower() for k in ["don't know", "dont know", "not sure", "pass", "skip"]):
                ai_response = "That is completely fine. Let's move to our next technical question."
                state = self._advance_to_next_question(state)
                next_q = self._get_current_question(state)
                if next_q:
                    ai_response += f" Next question: {next_q.question}"
                else:
                    state.stage = InterviewStage.CONCLUSION
                    ai_response = (
                        "That concludes our technical questions! Thank you for your time today. "
                        "I am now generating your comprehensive evaluation across content, structure, and communication."
                    )
            elif not state.follow_up_active:
                # Trigger a relevant follow-up
                state.stage = InterviewStage.FOLLOW_UP
                state.follow_up_active = True
                ai_response = self._generate_follow_up(curr_q, candidate_text)
            else:
                # Move to next question
                state.follow_up_active = False
                state = self._advance_to_next_question(state)
                next_q = self._get_current_question(state)
                if next_q:
                    state.stage = InterviewStage.TECHNICAL_QUESTION
                    ai_response = f"Thank you for the detailed breakdown. Let's move on to Question #{state.current_q_index + 1}: {next_q.question}"
                else:
                    state.stage = InterviewStage.CONCLUSION
                    ai_response = (
                        "Excellent, that completes all technical questions for this interview! "
                        "I'm now finalizing your multidimensional evaluation report."
                    )

        elif state.stage == InterviewStage.FOLLOW_UP:
            state.follow_up_active = False
            state = self._advance_to_next_question(state)
            next_q = self._get_current_question(state)
            if next_q:
                state.stage = InterviewStage.TECHNICAL_QUESTION
                ai_response = f"Understood, thank you. Let's move to the next question: {next_q.question}"
            else:
                state.stage = InterviewStage.CONCLUSION
                ai_response = (
                    "Thank you for your responses! That wraps up our interview session. "
                    "Your evaluation has been compiled and is ready for inspection."
                )

        elif state.stage == InterviewStage.CONCLUSION:
            ai_response = "The interview is complete. You can view your detailed scorecard and feedback in the Evaluation tab."

        else:
            ai_response = "Let's proceed with the interview."

        state.conversation_history.append({"speaker": "interviewer", "text": ai_response})
        return {
            "ai_response": ai_response,
            "stage": state.stage,
            "current_question": self._get_current_question(state),
            "injection_detected": False,
            "session_state": state.model_dump()
        }

    def _get_current_question(self, state: InterviewSessionState) -> Optional[QnARecord]:
        if 0 <= state.current_q_index < len(state.question_ids):
            qid = state.question_ids[state.current_q_index]
            return self.questions_by_id.get(qid)
        return None

    def _advance_to_next_question(self, state: InterviewSessionState) -> InterviewSessionState:
        state.current_q_index += 1
        state.follow_up_active = False
        return state

    def _generate_follow_up(self, q: Optional[QnARecord], answer_text: str) -> str:
        """Generate a context-aware follow-up question."""
        if not q:
            return "Could you provide a concrete architectural example or tradeoff regarding your explanation?"

        concepts = q.key_concepts or []
        if concepts:
            chosen_concept = concepts[-1]
            return (
                f"That's a solid start. Could you elaborate specifically on how {chosen_concept} "
                f"affects system scalability or failure recovery in production?"
            )
        return "Could you elaborate on the practical trade-offs or performance bottlenecks involved in that approach?"
