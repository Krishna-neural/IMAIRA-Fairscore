"""Unified Session Data Model & Persistence Manager for IMAIRA FairScore.

Provides persistent storage (SQLite with fallback to JSON) and complete
lifecycle tracking for candidate interview sessions, multi-turn utterances,
acoustic slice recovery logs, and per-question scorecards.
"""

import json
import logging
import sqlite3
import time
import uuid
from dataclasses import asdict, dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional

logger = logging.getLogger("imaira.session_manager")

REPO_ROOT = Path(__file__).resolve().parent.parent
SESSIONS_DIR = REPO_ROOT / "artifacts" / "sessions"
DB_PATH = REPO_ROOT / "artifacts" / "sessions.db"


class InterviewStage(str, Enum):
    SETUP = "SETUP"
    GREETING = "GREETING"
    TECHNICAL_QUESTION = "TECHNICAL_QUESTION"
    FOLLOW_UP = "FOLLOW_UP"
    CONCLUSION = "CONCLUSION"
    COMPLETED = "COMPLETED"


@dataclass
class TurnRecord:
    turn_id: int
    stage: str
    speaker: str  # "candidate" or "interviewer"
    raw_utterance: str
    recovered_utterance: str = ""
    audio_path: Optional[str] = None
    word_timings: List[Dict[str, Any]] = field(default_factory=list)
    slice_recovery_log: List[Dict[str, Any]] = field(default_factory=list)
    question_id: Optional[str] = None
    question_text: Optional[str] = None
    evaluation: Optional[Dict[str, Any]] = None
    ai_response: str = ""
    injection_detected: bool = False
    timestamp: float = field(default_factory=time.time)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "TurnRecord":
        return cls(**data)


@dataclass
class UnifiedSession:
    session_id: str
    candidate_name: str
    domain: str
    difficulty: str
    num_questions: int
    question_ids: List[str] = field(default_factory=list)
    current_q_index: int = 0
    stage: InterviewStage = InterviewStage.GREETING
    follow_up_active: bool = False
    turns: List[TurnRecord] = field(default_factory=list)
    final_scorecard: Optional[Dict[str, Any]] = None
    created_at: float = field(default_factory=time.time)
    updated_at: float = field(default_factory=time.time)

    def to_dict(self) -> Dict[str, Any]:
        d = asdict(self)
        d["stage"] = self.stage.value if isinstance(self.stage, InterviewStage) else str(self.stage)
        d["turns"] = [t.to_dict() if isinstance(t, TurnRecord) else t for t in self.turns]
        return d

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "UnifiedSession":
        turns_data = data.get("turns", [])
        turns = [TurnRecord.from_dict(t) if isinstance(t, dict) else t for t in turns_data]
        stage_str = data.get("stage", InterviewStage.GREETING.value)
        try:
            stage_enum = InterviewStage(stage_str)
        except ValueError:
            stage_enum = InterviewStage.GREETING
        
        return cls(
            session_id=data["session_id"],
            candidate_name=data.get("candidate_name", "Candidate"),
            domain=data.get("domain", "Software and Computer Science Fundamentals"),
            difficulty=data.get("difficulty", "Intermediate"),
            num_questions=data.get("num_questions", 3),
            question_ids=data.get("question_ids", []),
            current_q_index=data.get("current_q_index", 0),
            stage=stage_enum,
            follow_up_active=data.get("follow_up_active", False),
            turns=turns,
            final_scorecard=data.get("final_scorecard"),
            created_at=data.get("created_at", time.time()),
            updated_at=data.get("updated_at", time.time()),
        )


class SessionManager:
    """Persistent SQLite-backed Session Manager with automatic directory & schema creation."""

    def __init__(self, db_path: Optional[Path] = None, json_dir: Optional[Path] = None):
        self.db_path = db_path or DB_PATH
        self.json_dir = json_dir or SESSIONS_DIR
        self._init_storage()

    def _init_storage(self) -> None:
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self.json_dir.mkdir(parents=True, exist_ok=True)

        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS sessions (
                    session_id TEXT PRIMARY KEY,
                    candidate_name TEXT,
                    domain TEXT,
                    difficulty TEXT,
                    stage TEXT,
                    current_q_index INTEGER,
                    num_questions INTEGER,
                    data_json TEXT,
                    created_at REAL,
                    updated_at REAL
                )
                """
            )
            cursor.execute(
                """
                CREATE INDEX IF NOT EXISTS idx_sessions_updated ON sessions (updated_at DESC)
                """
            )
            conn.commit()

    def create_session(
        self,
        candidate_name: str,
        domain: str,
        difficulty: str,
        num_questions: int,
        question_ids: List[str]
    ) -> UnifiedSession:
        session_id = f"sess_{uuid.uuid4().hex[:10]}"
        now = time.time()
        session = UnifiedSession(
            session_id=session_id,
            candidate_name=candidate_name.strip() or "Candidate",
            domain=domain,
            difficulty=difficulty,
            num_questions=num_questions,
            question_ids=question_ids,
            current_q_index=0,
            stage=InterviewStage.GREETING,
            follow_up_active=False,
            turns=[],
            created_at=now,
            updated_at=now,
        )
        self.save_session(session)
        logger.info(f"Created new interview session {session_id} for '{candidate_name}' ({len(question_ids)} questions)")
        return session

    def save_session(self, session: UnifiedSession) -> None:
        session.updated_at = time.time()
        session_dict = session.to_dict()
        data_json = json.dumps(session_dict, indent=2)

        # 1. Save to SQLite
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute(
                    """
                    INSERT OR REPLACE INTO sessions (
                        session_id, candidate_name, domain, difficulty,
                        stage, current_q_index, num_questions, data_json,
                        created_at, updated_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        session.session_id,
                        session.candidate_name,
                        session.domain,
                        session.difficulty,
                        session.stage.value if isinstance(session.stage, InterviewStage) else str(session.stage),
                        session.current_q_index,
                        session.num_questions,
                        data_json,
                        session.created_at,
                        session.updated_at
                    )
                )
                conn.commit()
        except Exception as e:
            logger.error(f"Failed to write session {session.session_id} to SQLite: {e}")

        # 2. Also write JSON mirror file for transparent inspection & backups
        try:
            json_file = self.json_dir / f"{session.session_id}.json"
            json_file.write_text(data_json, encoding="utf-8")
        except Exception as e:
            logger.warning(f"Failed to write mirror JSON for session {session.session_id}: {e}")

    def get_session(self, session_id: str) -> Optional[UnifiedSession]:
        # 1. Query SQLite
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT data_json FROM sessions WHERE session_id = ?", (session_id,))
                row = cursor.fetchone()
                if row and row[0]:
                    data = json.loads(row[0])
                    return UnifiedSession.from_dict(data)
        except Exception as e:
            logger.error(f"SQLite read failed for session {session_id}: {e}")

        # 2. Fallback to mirror JSON file
        json_file = self.json_dir / f"{session_id}.json"
        if json_file.exists():
            try:
                data = json.loads(json_file.read_text(encoding="utf-8"))
                return UnifiedSession.from_dict(data)
            except Exception as e:
                logger.error(f"Fallback JSON read failed for session {session_id}: {e}")

        return None

    def list_sessions(self, limit: int = 50) -> List[UnifiedSession]:
        sessions = []
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "SELECT data_json FROM sessions ORDER BY updated_at DESC LIMIT ?",
                    (limit,)
                )
                for row in cursor.fetchall():
                    if row and row[0]:
                        try:
                            sessions.append(UnifiedSession.from_dict(json.loads(row[0])))
                        except Exception:
                            continue
        except Exception as e:
            logger.error(f"Failed to list sessions from SQLite: {e}")
        return sessions

    def record_turn(
        self,
        session_id: str,
        speaker: str,
        raw_utterance: str,
        recovered_utterance: str = "",
        ai_response: str = "",
        stage: Optional[str] = None,
        question_id: Optional[str] = None,
        question_text: Optional[str] = None,
        word_timings: Optional[List[Dict[str, Any]]] = None,
        slice_recovery_log: Optional[List[Dict[str, Any]]] = None,
        evaluation: Optional[Dict[str, Any]] = None,
        injection_detected: bool = False,
        audio_path: Optional[str] = None,
        current_q_index: Optional[int] = None,
        follow_up_active: Optional[bool] = None
    ) -> Optional[TurnRecord]:
        session = self.get_session(session_id)
        if not session:
            logger.error(f"Cannot record turn: session {session_id} not found.")
            return None

        turn_id = len(session.turns) + 1
        current_stage = stage or (session.stage.value if isinstance(session.stage, InterviewStage) else str(session.stage))

        turn = TurnRecord(
            turn_id=turn_id,
            stage=current_stage,
            speaker=speaker,
            raw_utterance=raw_utterance,
            recovered_utterance=recovered_utterance or raw_utterance,
            audio_path=audio_path,
            word_timings=word_timings or [],
            slice_recovery_log=slice_recovery_log or [],
            question_id=question_id,
            question_text=question_text,
            evaluation=evaluation,
            ai_response=ai_response,
            injection_detected=injection_detected,
            timestamp=time.time()
        )
        session.turns.append(turn)
        if stage:
            try:
                session.stage = InterviewStage(stage)
            except Exception:
                pass
        if current_q_index is not None:
            session.current_q_index = current_q_index
        if follow_up_active is not None:
            session.follow_up_active = follow_up_active
        self.save_session(session)
        return turn

    def conclude_session(
        self,
        session_id: str,
        final_scorecard: Optional[Dict[str, Any]] = None
    ) -> Optional[UnifiedSession]:
        session = self.get_session(session_id)
        if not session:
            return None

        # Auto-aggregate from turn evaluations if final_scorecard is omitted
        if not final_scorecard:
            eval_turns = [t for t in session.turns if t.evaluation and isinstance(t.evaluation, dict)]
            if eval_turns:
                content_scores = [t.evaluation.get("scores", {}).get("content_pct", 50) for t in eval_turns]
                struct_scores = [t.evaluation.get("scores", {}).get("structure_pct", 50) for t in eval_turns]
                comm_scores = [t.evaluation.get("scores", {}).get("communication_pct", 75) for t in eval_turns]
                fair_5pt = [t.evaluation.get("scores", {}).get("overall_fairscore_5pt", 3.0) for t in eval_turns]
                fair_pct = [t.evaluation.get("scores", {}).get("overall_fairscore_pct", 50.0) for t in eval_turns]

                avg_content = round(sum(content_scores) / len(content_scores), 1)
                avg_struct = round(sum(struct_scores) / len(struct_scores), 1)
                avg_comm = round(sum(comm_scores) / len(comm_scores), 1)
                avg_fair_5pt = round(sum(fair_5pt) / len(fair_5pt), 2)
                avg_fair_pct = round(sum(fair_pct) / len(fair_pct), 1)

                all_tech_gaps = []
                all_pronounce = []
                for t in eval_turns:
                    dual = t.evaluation.get("dual_diagnosis", {})
                    all_tech_gaps.extend(dual.get("technical_knowledge_gaps", []))
                    all_pronounce.extend(dual.get("pronunciation_improvements", []))

                final_scorecard = {
                    "session_id": session_id,
                    "candidate_name": session.candidate_name,
                    "domain": session.domain,
                    "difficulty": session.difficulty,
                    "questions_evaluated": len(eval_turns),
                    "total_turns": len(session.turns),
                    "overall_fairscore": avg_fair_pct,
                    "overall_fairscore_5pt": avg_fair_5pt,
                    "content_score": avg_content,
                    "structure_score": avg_struct,
                    "communication_score": avg_comm,
                    "summary_verdict": "Demonstrates Solid Competence" if avg_fair_pct >= 65.0 else ("Developing Competence" if avg_fair_pct >= 40.0 else "Needs Foundational Review"),
                    "cumulative_dual_diagnosis": {
                        "technical_knowledge_gaps": all_tech_gaps,
                        "pronunciation_improvements": all_pronounce,
                        "accent_penalty_applied": False,
                        "acoustic_protection_active": True
                    }
                }
            else:
                final_scorecard = {
                    "session_id": session_id,
                    "overall_fairscore": 0.0,
                    "summary_verdict": "No evaluated responses"
                }

        session.stage = InterviewStage.COMPLETED
        session.final_scorecard = final_scorecard
        self.save_session(session)
        logger.info(f"Session {session_id} concluded with FairScore {final_scorecard.get('overall_fairscore')}")
        return session
