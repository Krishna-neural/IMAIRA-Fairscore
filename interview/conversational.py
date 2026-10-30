"""Conversational Multi-Turn AI Technical Interviewer Engine.

Implements context-aware multi-turn dialog, strict identity persistence,
prompt-injection defense, and stage-driven technical interview progression,
fully integrated with persistent SessionManager.
"""

import json
import logging
import os
import random
import re
import uuid
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union

from pydantic import BaseModel, Field

from interview.session_manager import (
    InterviewStage,
    SessionManager,
    TurnRecord,
    UnifiedSession,
)
from score.qanda import QnARecord, get_qanda_by_id, load_qanda
from score.turn_evaluator import TurnEvaluator

logger = logging.getLogger("imaira.conversational")

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
    """Stateful technical interviewer managing dialog and stage transitions with persistent storage."""

    def __init__(
        self,
        questions: Optional[List[QnARecord]] = None,
        session_manager: Optional[SessionManager] = None
    ):
        repo_root = Path(__file__).resolve().parent.parent
        q_path = repo_root / "data" / "QandA.json"
        self.questions = questions or load_qanda(q_path if q_path.exists() else "data/QandA.json")
        self.questions_by_id = {q.id: q for q in self.questions}
        self.session_manager = session_manager or SessionManager()
        self.turn_evaluator = TurnEvaluator()

    def start_session(
        self,
        candidate_name: str,
        domain: str,
        difficulty: str,
        num_questions: int = 3
    ) -> Tuple[InterviewSessionState, str]:
        """Start a new multi-turn interview session with persistence."""
        # 1. Filter questions by domain and difficulty
        matching = [
            q for q in self.questions
            if (domain == "All Categories" or q.category == domain) and
               (difficulty == "All Difficulties" or q.difficulty == difficulty)
        ]
        if not matching:
            matching = self.questions

        # Pick unique questions without duplicates
        sample_count = min(num_questions, len(matching))
        selected = random.sample(matching, sample_count)
        q_ids = [q.id for q in selected]

        # 2. Create persistent unified session
        unified_session = self.session_manager.create_session(
            candidate_name=candidate_name or "Candidate",
            domain=domain,
            difficulty=difficulty,
            num_questions=num_questions,
            question_ids=q_ids
        )

        greeting = (
            f"Hello {unified_session.candidate_name}! Welcome to IMAIRA FairScore. "
            f"I'm your AI technical interviewer today for {domain}. "
            f"I'll be asking you a series of technical questions and evaluating your responses "
            f"based on technical mastery, structure, and communication clarity. "
            f"To get started, could you briefly introduce yourself and your technical background?"
        )

        # 3. Record initial greeting turn in persistent store
        self.session_manager.record_turn(
            session_id=unified_session.session_id,
            speaker="interviewer",
            raw_utterance=greeting,
            ai_response=greeting,
            stage=InterviewStage.GREETING.value
        )

        # 4. Construct legacy-compatible state object
        state = InterviewSessionState(
            session_id=unified_session.session_id,
            candidate_name=unified_session.candidate_name,
            domain=domain,
            difficulty=difficulty,
            stage=InterviewStage.GREETING,
            question_ids=q_ids,
            current_q_index=0,
            follow_up_active=False,
            turn_count=1,
            conversation_history=[{"speaker": "interviewer", "text": greeting}]
        )

        return state, greeting

    def process_turn(
        self,
        state: Union[InterviewSessionState, str],
        candidate_utterance: str,
        raw_utterance: Optional[str] = None,
        recovered_utterance: Optional[str] = None,
        slice_recovery_log: Optional[List[Dict[str, Any]]] = None,
        evaluation: Optional[Dict[str, Any]] = None,
        word_timings: Optional[List[Dict[str, Any]]] = None,
        audio_path: Optional[str] = None
    ) -> Dict[str, Any]:
        """Process candidate turn, enforce identity, update stage, and generate AI response."""
        # Normalize session state
        if isinstance(state, str):
            session_id = state
            unified = self.session_manager.get_session(session_id)
            if not unified:
                raise ValueError(f"Session {session_id} not found")
            # Build Pydantic state
            p_state = InterviewSessionState(
                session_id=unified.session_id,
                candidate_name=unified.candidate_name,
                domain=unified.domain,
                difficulty=unified.difficulty,
                stage=unified.stage,
                question_ids=unified.question_ids,
                current_q_index=unified.current_q_index,
                follow_up_active=unified.follow_up_active,
                turn_count=len(unified.turns)
            )
            state = p_state
        else:
            unified = self.session_manager.get_session(state.session_id)
            if not unified:
                # Fallback: create persistent session if not yet registered
                unified = self.session_manager.create_session(
                    candidate_name=state.candidate_name,
                    domain=state.domain,
                    difficulty=state.difficulty,
                    num_questions=len(state.question_ids),
                    question_ids=state.question_ids
                )
                unified.current_q_index = state.current_q_index
                unified.stage = state.stage
                unified.follow_up_active = state.follow_up_active
                self.session_manager.save_session(unified)

        candidate_text = candidate_utterance.strip()
        state.turn_count += 1
        state.conversation_history.append({"speaker": "candidate", "text": candidate_text})

        curr_q = self._get_current_question(state)
        q_id = curr_q.id if curr_q else None
        q_prompt = curr_q.question if curr_q else None

        # 1. Anti-manipulation check
        injection_warning = detect_prompt_injection(candidate_text)
        if injection_warning:
            ai_response = (
                "I am IMAIRA FairScore's dedicated technical interviewer. My role and evaluation "
                "criteria are server-enforced and cannot be altered. Let's stay focused on your interview."
            )
            state.conversation_history.append({"speaker": "interviewer", "text": ai_response})
            
            # Record candidate attack turn & interviewer refusal in persistent store
            self.session_manager.record_turn(
                session_id=state.session_id,
                speaker="candidate",
                raw_utterance=raw_utterance or candidate_text,
                recovered_utterance=recovered_utterance or candidate_text,
                ai_response=ai_response,
                stage=state.stage.value if isinstance(state.stage, InterviewStage) else str(state.stage),
                question_id=q_id,
                question_text=q_prompt,
                word_timings=word_timings,
                slice_recovery_log=slice_recovery_log,
                evaluation=evaluation,
                injection_detected=True,
                audio_path=audio_path
            )

            return {
                "ai_response": ai_response,
                "stage": state.stage.value if isinstance(state.stage, InterviewStage) else str(state.stage),
                "current_question": curr_q,
                "injection_detected": True,
                "session_state": state.model_dump()
            }

        # Stage 4: Silent evidence-grounded scoring & dual diagnosis for technical questions
        if curr_q and state.stage in (InterviewStage.TECHNICAL_QUESTION, InterviewStage.FOLLOW_UP) and not injection_warning:
            try:
                evaluation = self.turn_evaluator.evaluate_turn(
                    question_id=curr_q.id,
                    question_text=curr_q.question,
                    recovered_utterance=recovered_utterance or candidate_text,
                    raw_utterance=raw_utterance or candidate_text,
                    slice_recovery_log=slice_recovery_log,
                    word_timings=word_timings,
                    curr_q=curr_q
                )
            except Exception as e:
                logger.warning(f"Turn evaluation error for question {curr_q.id}: {e}")
                evaluation = None

        # 2. Stage-based state machine
        if state.stage == InterviewStage.GREETING:
            state.stage = InterviewStage.TECHNICAL_QUESTION
            unified.stage = InterviewStage.TECHNICAL_QUESTION
            curr_q = self._get_current_question(state)
            q_text = curr_q.question if curr_q else "Explain your core technical area."
            ai_response = (
                f"Thank you for sharing, {state.candidate_name}. Let's dive straight into our first question: "
                f"{q_text}"
            )

        elif state.stage == InterviewStage.TECHNICAL_QUESTION:
            words = candidate_text.split()
            # Check if candidate indicated "I don't know"
            if len(words) < 15 and any(k in candidate_text.lower() for k in ["don't know", "dont know", "not sure", "cannot answer", "can't answer", "pass", "skip"]):
                ai_response = "That is completely fine. Let's move to our next technical question."
                state = self._advance_to_next_question(state)
                unified.current_q_index = state.current_q_index
                unified.follow_up_active = False
                next_q = self._get_current_question(state)
                if next_q:
                    ai_response += f" Next question: {next_q.question}"
                else:
                    state.stage = InterviewStage.CONCLUSION
                    unified.stage = InterviewStage.CONCLUSION
                    ai_response = (
                        "That concludes our technical questions! Thank you for your time today. "
                        "I am now generating your comprehensive evaluation across content, structure, and communication."
                    )
            elif not state.follow_up_active:
                # Trigger a relevant follow-up
                state.stage = InterviewStage.FOLLOW_UP
                state.follow_up_active = True
                unified.stage = InterviewStage.FOLLOW_UP
                unified.follow_up_active = True
                ai_response = self._generate_follow_up(curr_q, candidate_text)
            else:
                # Move to next question
                state.follow_up_active = False
                state = self._advance_to_next_question(state)
                unified.current_q_index = state.current_q_index
                unified.follow_up_active = False
                next_q = self._get_current_question(state)
                if next_q:
                    state.stage = InterviewStage.TECHNICAL_QUESTION
                    unified.stage = InterviewStage.TECHNICAL_QUESTION
                    ai_response = f"Thank you for the detailed breakdown. Let's move on to Question #{state.current_q_index + 1}: {next_q.question}"
                else:
                    state.stage = InterviewStage.CONCLUSION
                    unified.stage = InterviewStage.CONCLUSION
                    ai_response = (
                        "Excellent, that completes all technical questions for this interview! "
                        "I'm now finalizing your multidimensional evaluation report."
                    )

        elif state.stage == InterviewStage.FOLLOW_UP:
            state.follow_up_active = False
            state = self._advance_to_next_question(state)
            unified.current_q_index = state.current_q_index
            unified.follow_up_active = False
            next_q = self._get_current_question(state)
            if next_q:
                state.stage = InterviewStage.TECHNICAL_QUESTION
                unified.stage = InterviewStage.TECHNICAL_QUESTION
                ai_response = f"Understood, thank you. Let's move to Question #{state.current_q_index + 1}: {next_q.question}"
            else:
                state.stage = InterviewStage.CONCLUSION
                unified.stage = InterviewStage.CONCLUSION
                ai_response = (
                    "Thank you for your responses! That wraps up our interview session. "
                    "Your evaluation has been compiled and is ready for inspection."
                )

        elif state.stage == InterviewStage.CONCLUSION:
            ai_response = "The interview is complete. You can view your detailed scorecard and feedback in the Evaluation tab."

        else:
            ai_response = "Let's proceed with the interview."

        state.conversation_history.append({"speaker": "interviewer", "text": ai_response})

        # 3. Record turn in persistent SessionManager
        self.session_manager.record_turn(
            session_id=state.session_id,
            speaker="candidate",
            raw_utterance=raw_utterance or candidate_text,
            recovered_utterance=recovered_utterance or candidate_text,
            ai_response=ai_response,
            stage=state.stage.value if isinstance(state.stage, InterviewStage) else str(state.stage),
            question_id=q_id,
            question_text=q_prompt,
            word_timings=word_timings,
            slice_recovery_log=slice_recovery_log,
            evaluation=evaluation,
            injection_detected=False,
            audio_path=audio_path,
            current_q_index=state.current_q_index,
            follow_up_active=state.follow_up_active
        )

        return {
            "ai_response": ai_response,
            "stage": state.stage.value if isinstance(state.stage, InterviewStage) else str(state.stage),
            "current_question": self._get_current_question(state),
            "injection_detected": False,
            "session_state": state.model_dump(),
            "evaluation": evaluation
        }

    def _get_current_question(self, state: Union[InterviewSessionState, UnifiedSession]) -> Optional[QnARecord]:
        q_ids = state.question_ids
        q_idx = state.current_q_index
        if 0 <= q_idx < len(q_ids):
            qid = q_ids[q_idx]
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

    def conclude_session(
        self,
        session_id: str,
        final_scorecard: Dict[str, Any]
    ) -> Optional[UnifiedSession]:
        """Conclude an interview session and record final scorecard."""
        return self.session_manager.conclude_session(session_id, final_scorecard)

    def get_session(self, session_id: str) -> Optional[UnifiedSession]:
        """Retrieve full persistent session."""
        return self.session_manager.get_session(session_id)
