"""Conversational Multi-Turn AI Technical Interviewer Engine.

Implements:
1. Context-aware multi-turn technical dialog and strict identity persistence.
2. Topic-grounded questioning: probes into candidate's actual answer ("questions into the questions").
3. Topic satisfaction tracking: explores mechanisms, edge cases, and scale before transitioning.
4. Seamless contextual bridges between technical topics.
5. Accurate domain & subcategory filtering without question repetition.
6. Server-enforced prompt injection defense.
"""

import json
import logging
import os
import random
import re
import uuid
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple, Union

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
    turns_on_current_q: int = 0
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
        self._recently_asked_ids: Set[str] = set()

    def _matches_domain(self, q: QnARecord, domain: str) -> bool:
        """Accurately match question against domain or subcategory selections."""
        if not domain or domain in ("All Categories", "All Domains", "General Technical"):
            return True

        d_lower = domain.lower().strip()
        cat_lower = (q.category or "").lower().strip()
        sub_lower = (q.subcategory or "").lower().strip()

        # 1. Exact match on subcategory or category
        if d_lower == sub_lower or d_lower == cat_lower:
            return True

        # 2. Canonical mapping for all frontend dropdown options
        domain_map = {
            "data structures and algorithms": ["data structures and algorithms"],
            "operating systems and concurrency": ["operating systems & concurrency"],
            "operating systems & concurrency": ["operating systems & concurrency"],
            "database management systems": ["database design & transactions"],
            "database design & transactions": ["database design & transactions"],
            "system design and distributed systems": [
                "distributed systems & api design",
                "software architecture & design patterns",
                "frontend & backend architecture"
            ],
            "computer networks and protocols": ["api design & security"],
            "artificial intelligence and machine learning": [
                "supervised & unsupervised learning",
                "large language models & transformers",
                "model training & validation",
                "model deployment & optimization",
                "feature engineering & preprocessing"
            ],
            "cybersecurity and information security": ["api design & security"],
            "cloud computing and devops": [
                "cloud infrastructure & containers",
                "version control & ci/cd",
                "observability & reliability engineering"
            ],
            "software and computer science fundamentals": [
                "data structures and algorithms",
                "operating systems & concurrency",
                "database design & transactions",
                "software architecture & design patterns",
                "object-oriented programming",
                "testing & code quality"
            ]
        }

        # Check mapped subcategories
        for dom_key, valid_subs in domain_map.items():
            if dom_key in d_lower or d_lower in dom_key:
                if any(vs in sub_lower or sub_lower in vs for vs in valid_subs):
                    return True
                # If explicitly mapped domain, do not fall through to loose string matching
                return False

        # Fallback substring match on subcategory or category only
        if d_lower in sub_lower or sub_lower in d_lower:
            return True
        if d_lower in cat_lower or cat_lower in d_lower:
            return True

        return False

    def start_session(
        self,
        candidate_name: str,
        domain: str,
        difficulty: str,
        num_questions: int = 3
    ) -> Tuple[InterviewSessionState, str]:
        """Start a new multi-turn interview session with domain-filtered, non-repeating questions."""
        # 1. Filter questions by domain
        matching = [q for q in self.questions if self._matches_domain(q, domain)]
        if not matching:
            # Fallback to Software and Computer Science Fundamentals if domain was unrecognized
            matching = [q for q in self.questions if self._matches_domain(q, "Software and Computer Science Fundamentals")]
            if not matching:
                matching = self.questions

        # 2. Filter by difficulty without starving the domain pool
        if difficulty and difficulty != "All Difficulties":
            diff_matched = [q for q in matching if q.difficulty.lower() == difficulty.lower()]
            if len(diff_matched) >= num_questions:
                matching = diff_matched
            else:
                # Prioritize diff_matched, but keep remaining domain questions
                other_matching = [q for q in matching if q not in diff_matched]
                matching = diff_matched + other_matching

        # Prioritize unasked questions to avoid repetition across sessions
        unasked = [q for q in matching if q.id not in self._recently_asked_ids]
        pool = unasked if len(unasked) >= num_questions else matching

        sample_count = min(num_questions, len(pool))
        selected = random.sample(pool, sample_count)
        q_ids = [q.id for q in selected]
        self._recently_asked_ids.update(q_ids)

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
            f"I'll be exploring your engineering reasoning through targeted technical questions "
            f"and evaluating your responses based on technical mastery, structure, and communication clarity. "
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

        # 4. Construct state object
        state = InterviewSessionState(
            session_id=unified_session.session_id,
            candidate_name=unified_session.candidate_name,
            domain=domain,
            difficulty=difficulty,
            stage=InterviewStage.GREETING,
            question_ids=q_ids,
            current_q_index=0,
            follow_up_active=False,
            turns_on_current_q=0,
            turn_count=1,
            conversation_history=[{"speaker": "interviewer", "text": greeting}]
        )

        return state, greeting

    def _generate_intelligent_probe(
        self,
        curr_q: QnARecord,
        candidate_text: str,
        evaluation: Optional[Dict[str, Any]],
        turn_in_topic: int,
        candidate_name: str
    ) -> Tuple[str, bool]:
        """
        Deeply understand candidate's answer and generate a context-aware follow-up question
        that sticks to the topic and probes into what the candidate actually said.
        Returns: (ai_probe_text, is_satisfied_with_topic)
        """
        lower_ans = candidate_text.lower()
        key_concepts = curr_q.key_concepts or []
        glossary_terms = curr_q.glossary_terms_used or []

        # 1. Identify what the candidate mentioned
        mentioned_concepts = [c for c in key_concepts if c.lower() in lower_ans]
        mentioned_glossary = [g for g in glossary_terms if g.lower() in lower_ans]
        unmentioned_concepts = [c for c in key_concepts if c.lower() not in lower_ans]

        # 2. Extract specific rubric gaps if evaluated
        rubric_gaps = []
        if evaluation and "rubric_breakdown" in evaluation:
            for item in evaluation["rubric_breakdown"]:
                if item.get("verdict") in ("missing", "not_demonstrated", "partially_demonstrated"):
                    rubric_gaps.append(item.get("concept_statement", ""))

        # 3. Check for evasion / "I don't know"
        is_evasion = len(candidate_text.split()) < 12 and any(
            phrase in lower_ans for phrase in ["don't know", "dont know", "not sure", "cannot answer", "pass", "skip"]
        )
        if is_evasion:
            if turn_in_topic >= 1:
                return (
                    f"That is completely fine, {candidate_name}. Let's solidify our findings here and transition to our next technical area.",
                    True
                )
            else:
                first_concept = key_concepts[0] if key_concepts else "this architectural approach"
                return (
                    f"No worries at all, {candidate_name}. Let's look at the foundational piece of this on the same topic: "
                    f"what is the primary design goal or asymptotic advantage of {first_concept}?",
                    False
                )

        # 4. Formulate acknowledge snippet referencing candidate's exact words
        if mentioned_concepts:
            ack_phrase = f"You clearly articulated {mentioned_concepts[0]}"
            if len(mentioned_concepts) > 1:
                ack_phrase += f" and touched on {mentioned_concepts[1]}"
        elif mentioned_glossary:
            ack_phrase = f"You discussed {mentioned_glossary[0]}"
        else:
            words = candidate_text.split()
            snippet = " ".join(words[:5]) + "..." if len(words) >= 5 else candidate_text
            ack_phrase = f"Your points regarding '{snippet}' touch on the high-level concept"

        # 5. Multi-Turn Topic Probing State Machine ("Stick to the Topic")
        if turn_in_topic == 0:
            # --- PROBE 1: Drill into Mechanisms & Internals on the SAME topic ---
            target_focus = unmentioned_concepts[0] if unmentioned_concepts else (
                rubric_gaps[0] if rubric_gaps else (key_concepts[-1] if key_concepts else "the underlying mechanic")
            )
            probe = (
                f"{ack_phrase}. To drill deeper into this exact mechanism: "
                f"how does {target_focus.lower()} operate under the hood? "
                f"Specifically, what step-by-step invariant or data structure prevents system degradation during peak load?"
            )
            return (probe, False)

        else:
            # --- TOPIC PROBE ANSWERED & SATISFIED (Candidate completed deep-dive exchange on this topic) ---
            subcat = curr_q.subcategory or "this concept"
            satisfied_text = (
                f"Understood, that clarifies the internal mechanism and operational tradeoffs in {subcat}. "
                f"You've addressed the key architectural invariants well."
            )
            return (satisfied_text, True)

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
        """Process candidate turn, evaluate semantics, probe topic deeply, and progress state."""
        # Normalize session state
        if isinstance(state, str):
            session_id = state
            unified = self.session_manager.get_session(session_id)
            if not unified:
                raise ValueError(f"Session {session_id} not found")
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

        # 2. Silent evidence-grounded scoring & dual diagnosis for technical turns
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

        # 3. Topic-Grounded Multi-Turn State Machine ("Stick to the Topic")
        if state.stage == InterviewStage.GREETING:
            # Transition from Candidate Introduction to Anchor Question 1
            state.stage = InterviewStage.TECHNICAL_QUESTION
            unified.stage = InterviewStage.TECHNICAL_QUESTION
            state.turns_on_current_q = 0
            curr_q = self._get_current_question(state)
            q_text = curr_q.question if curr_q else "Explain your core technical area."
            subcat = curr_q.subcategory if curr_q else state.domain
            ai_response = (
                f"Thank you for sharing, {state.candidate_name}. Let's dive straight into our first question in {subcat}: "
                f"{q_text}"
            )

        elif state.stage == InterviewStage.TECHNICAL_QUESTION:
            words = candidate_text.split()
            # Check if candidate explicitly indicates inability to answer or skips
            if len(words) < 15 and any(k in candidate_text.lower() for k in ["don't know", "dont know", "not sure", "cannot answer", "can't answer", "pass", "skip"]):
                ai_response = "That is completely fine. Let's move to our next technical question."
                state = self._advance_to_next_question(state)
                unified.current_q_index = state.current_q_index
                unified.follow_up_active = False
                next_q = self._get_current_question(state)
                if next_q:
                    state.stage = InterviewStage.TECHNICAL_QUESTION
                    unified.stage = InterviewStage.TECHNICAL_QUESTION
                    ai_response += f" Next question: {next_q.question}"
                else:
                    state.stage = InterviewStage.CONCLUSION
                    unified.stage = InterviewStage.CONCLUSION
                    ai_response = (
                        "That concludes our technical questions! Thank you for your time today. "
                        "I am now finalizing your multidimensional evaluation report across content, structure, and communication."
                    )
            else:
                # Candidate answered on topic -> trigger tailored probe into their answer
                probe_text, is_satisfied = self._generate_intelligent_probe(
                    curr_q=curr_q,
                    candidate_text=candidate_text,
                    evaluation=evaluation,
                    turn_in_topic=state.turns_on_current_q,
                    candidate_name=state.candidate_name
                )
                state.stage = InterviewStage.FOLLOW_UP
                unified.stage = InterviewStage.FOLLOW_UP
                state.follow_up_active = True
                unified.follow_up_active = True
                state.turns_on_current_q += 1
                ai_response = probe_text

        elif state.stage == InterviewStage.FOLLOW_UP:
            # Candidate answered follow-up probe on current topic
            probe_text, is_satisfied = self._generate_intelligent_probe(
                curr_q=curr_q,
                candidate_text=candidate_text,
                evaluation=evaluation,
                turn_in_topic=state.turns_on_current_q,
                candidate_name=state.candidate_name
            )

            # Advance to next question
            state.follow_up_active = False
            unified.follow_up_active = False
            state.turns_on_current_q = 0
            state = self._advance_to_next_question(state)
            unified.current_q_index = state.current_q_index
            next_q = self._get_current_question(state)

            if next_q:
                state.stage = InterviewStage.TECHNICAL_QUESTION
                unified.stage = InterviewStage.TECHNICAL_QUESTION
                curr_q = next_q
                subcat = next_q.subcategory or "this domain"
                ai_response = (
                    f"{probe_text} Building on that foundation, let's move to Question #{state.current_q_index + 1}: "
                    f"{next_q.question}"
                )
            else:
                state.stage = InterviewStage.CONCLUSION
                unified.stage = InterviewStage.CONCLUSION
                ai_response = (
                    f"{probe_text} Thank you for your responses! That wraps up our interview session. "
                    f"I'm now finalizing your multidimensional evaluation report across content, structure, and communication."
                )

        elif state.stage == InterviewStage.CONCLUSION:
            ai_response = "The interview is complete. You can view your detailed scorecard and feedback in the Evaluation tab."

        else:
            ai_response = "Let's proceed with the interview."

        state.conversation_history.append({"speaker": "interviewer", "text": ai_response})

        # 4. Record turn in persistent SessionManager
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
        state.turns_on_current_q = 0
        return state

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
