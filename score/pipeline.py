"""Integrated Scoring Pipeline for IMAIRA-Fairscore.

Reuses the production CPU 1 ContentJudge, StructureJudge, fitted Calibrator models,
Communication scorer, and Feedback generator without duplicating scoring logic.
"""

import logging
import os
import pickle
from pathlib import Path
from typing import Any, Dict, List, Optional
import numpy as np

from score.content import ContentJudge
from score.structure import StructureJudge
from score.calibrate import IsotonicScoreCalibrator
from score.rubrics import QuestionRubric, SemanticRubricIdea, load_rubrics
from score.qanda import load_qanda, get_qanda_by_id
from score.comm import score_communication
from feedback.generate import generate_top_missed_feedback

logger = logging.getLogger(__name__)

REPO_ROOT = Path(__file__).resolve().parent.parent

# Cache singletons for judges and calibrators
_CONTENT_JUDGE: Optional[ContentJudge] = None
_STRUCTURE_JUDGE: Optional[StructureJudge] = None
_CALIBRATOR_CONTENT = None
_CALIBRATOR_STRUCTURE = None
_RUBRICS_CACHE: Optional[Dict[str, QuestionRubric]] = None


def get_content_judge() -> ContentJudge:
    global _CONTENT_JUDGE
    if _CONTENT_JUDGE is None:
        _CONTENT_JUDGE = ContentJudge(cache_dir=REPO_ROOT / ".cache")
    return _CONTENT_JUDGE


def get_structure_judge() -> StructureJudge:
    global _STRUCTURE_JUDGE
    if _STRUCTURE_JUDGE is None:
        _STRUCTURE_JUDGE = StructureJudge(cache_dir=REPO_ROOT / ".cache")
    return _STRUCTURE_JUDGE


class SafeCalibratorUnpickler(pickle.Unpickler):
    """Unpickler that safely maps '__main__' classes to score.calibrate."""
    def find_class(self, module, name):
        import score.calibrate
        if module == "__main__" and hasattr(score.calibrate, name):
            return getattr(score.calibrate, name)
        return super().find_class(module, name)


def get_calibrators():
    global _CALIBRATOR_CONTENT, _CALIBRATOR_STRUCTURE
    if _CALIBRATOR_CONTENT is None:
        c_path = REPO_ROOT / "artifacts" / "calibrator_content.pkl"
        if c_path.exists():
            try:
                with open(c_path, "rb") as f:
                    _CALIBRATOR_CONTENT = SafeCalibratorUnpickler(f).load()
            except Exception as e:
                logger.warning(f"Could not load content calibrator: {e}")

    if _CALIBRATOR_STRUCTURE is None:
        s_path = REPO_ROOT / "artifacts" / "calibrator_structure.pkl"
        if s_path.exists():
            try:
                with open(s_path, "rb") as f:
                    _CALIBRATOR_STRUCTURE = SafeCalibratorUnpickler(f).load()
            except Exception as e:
                logger.warning(f"Could not load structure calibrator: {e}")

    return _CALIBRATOR_CONTENT, _CALIBRATOR_STRUCTURE


def get_cached_rubrics() -> Dict[str, QuestionRubric]:
    global _RUBRICS_CACHE
    if _RUBRICS_CACHE is None:
        # Load from QandA.json if available, fallback to rubrics_120.json
        qanda_path = REPO_ROOT / "data" / "QandA.json"
        if qanda_path.exists():
            try:
                records = load_qanda(qanda_path)
                _RUBRICS_CACHE = {}
                for r in records:
                    if r.semantic_rubric_ideas:
                        _RUBRICS_CACHE[r.id] = r.to_rubric()
            except Exception as e:
                logger.warning(f"Failed to load rubrics from QandA.json: {e}")

        if not _RUBRICS_CACHE:
            rubrics_path = REPO_ROOT / "data" / "rubrics_120.json"
            if rubrics_path.exists():
                _RUBRICS_CACHE = load_rubrics(rubrics_path)
            else:
                _RUBRICS_CACHE = {}
    return _RUBRICS_CACHE


def run_fairscore_pipeline(
    transcript_text: str,
    word_tokens: Optional[List[Dict[str, Any]]] = None,
    rubric_points: Optional[List[Dict[str, Any]]] = None,
    question_text: str = "Explain indexing and concurrency in PostgreSQL.",
    question_id: str = "ENG001",
    duration_sec: float = 60.0
) -> Dict[str, Any]:
    """Execute end-to-end evaluation using production scoring and calibration engines."""
    rubrics = get_cached_rubrics()

    # 1. Resolve QuestionRubric
    q_rubric = rubrics.get(question_id)
    if q_rubric is None:
        # Try matching by question text substring
        for rid, rub in rubrics.items():
            if rub.question_prompt and (rub.question_prompt[:30].lower() in question_text.lower() or
                                        question_text[:30].lower() in rub.question_prompt.lower()):
                q_rubric = rub
                question_id = rid
                break

    if q_rubric is None:
        # Fallback to constructing a QuestionRubric from rubric_points or defaults
        ideas = []
        if rubric_points:
            for idx, p in enumerate(rubric_points):
                text = p.get("text") or p.get("name") or p.get("description") or f"Criterion concept {idx+1}"
                if len(text.split()) < 5:
                    text = f"Candidate comprehensively explains and demonstrates mastery of {text}."
                ideas.append(SemanticRubricIdea(
                    idea_id=str(p.get("criterion_id", p.get("id", f"idea_{idx+1}"))),
                    semantic_statement=text,
                    required=True,
                    weight=float(p.get("weight", p.get("max_marks", 1.0))),
                    acceptable_paraphrase_guidance="Accepts conceptual equivalents and technical paraphrases."
                ))
        if not ideas:
            ideas = [
                SemanticRubricIdea(
                    idea_id="idea_1",
                    semantic_statement="Explains core technical principles and underlying architecture accurately.",
                    required=True,
                    weight=1.0,
                    acceptable_paraphrase_guidance="Accepts conceptual explanation of primary mechanism."
                ),
                SemanticRubricIdea(
                    idea_id="idea_2",
                    semantic_statement="Details system tradeoffs, failure modes, or performance consequences.",
                    required=True,
                    weight=1.0,
                    acceptable_paraphrase_guidance="Accepts analysis of operational bottlenecks and mitigations."
                )
            ]
        q_rubric = QuestionRubric(
            question_id=question_id,
            question_prompt=question_text,
            domain="Engineering",
            semantic_rubric_ideas=ideas
        )

    # 2. Content Judge Execution (CPU 1: 3-run mode voting, T=0, caching)
    content_judge = get_content_judge()
    content_res = content_judge.evaluate(q_rubric, transcript_text)
    raw_content = float(content_res["raw_content_score"])

    # Map idea verdicts to flags and feedback candidates
    flags: Dict[str, str] = {}
    missed_feedback_candidates: List[Dict[str, Any]] = []

    for v in content_res.get("per_idea_verdicts", []):
        iid = v.get("idea_id", "")
        verdict = v.get("verdict", "absent")
        quote = v.get("evidence_span", "")

        if verdict == "demonstrated":
            flags[iid] = "covered"
        elif verdict == "partially_demonstrated":
            flags[iid] = "partial"
            missed_feedback_candidates.append({
                "criterion_id": iid,
                "marks_lost": 5.0,
                "quote": quote or transcript_text[:min(80, len(transcript_text))],
                "fix_sentence": f"Elaborate more precisely on the mechanism of {iid} to earn full marks."
            })
        else:
            flags[iid] = "missing"
            missed_feedback_candidates.append({
                "criterion_id": iid,
                "marks_lost": 10.0,
                "quote": quote or transcript_text[:min(80, len(transcript_text))],
                "fix_sentence": f"Directly address {iid} by explaining its core architectural cause and effect."
            })

    # 3. Structure Judge Execution (CPU 1: Framing, Coherence, Closure)
    structure_judge = get_structure_judge()
    struct_res = structure_judge.evaluate(question_id, question_text, transcript_text)
    raw_struct = float(struct_res["raw_structure_score"])

    # 4. Calibration
    cal_content, cal_struct = get_calibrators()
    if cal_content is not None:
        try:
            calibrated_c = float(np.clip(cal_content.predict(np.array([raw_content]))[0], 1.0, 5.0))
        except Exception:
            calibrated_c = raw_content
    else:
        calibrated_c = raw_content

    if cal_struct is not None:
        try:
            calibrated_s = float(np.clip(cal_struct.predict(np.array([raw_struct]))[0], 1.0, 5.0))
        except Exception:
            calibrated_s = raw_struct
    else:
        calibrated_s = raw_struct

    # Scale 1.0-5.0 to 0-100 percentage
    content_pct = int(round(np.clip((calibrated_c - 1.0) / 4.0 * 100.0, 0, 100)))
    structure_pct = int(round(np.clip((calibrated_s - 1.0) / 4.0 * 100.0, 0, 100)))

    # 5. Communication Scoring
    comm_res = score_communication(transcript_text, duration_seconds=duration_sec)
    comm_score = int(comm_res["score"])

    # 6. Overall Weighted Score (50% Content, 30% Structure, 20% Communication)
    overall_score = round(0.50 * content_pct + 0.30 * structure_pct + 0.20 * comm_score, 1)

    # 7. Actionable Top-3 Feedback Generation
    if struct_res.get("components", {}).get("closure", {}).get("score", 5.0) < 3.0:
        missed_feedback_candidates.append({
            "criterion_id": "Structure Closure",
            "marks_lost": 4.0,
            "quote": transcript_text[-min(60, len(transcript_text)):],
            "fix_sentence": "Conclude your answer with a definitive summary summarizing key tradeoffs."
        })

    top_feedback = generate_top_missed_feedback(missed_feedback_candidates, top_n=3, max_words=30)

    # 8. Token generation
    tokens = word_tokens or [
        {"word": w, "start": round(i * 0.4, 2), "end": round((i + 1) * 0.4, 2), "conf": 0.95, "corrected_from": None}
        for i, w in enumerate(transcript_text.split()[:20])
    ]

    return {
        "transcript": tokens,
        "scores": {
            "content": content_pct,
            "structure": structure_pct,
            "communication": comm_score
        },
        "raw_scores": {
            "content": raw_content,
            "structure": raw_struct
        },
        "calibrated_scores": {
            "content": round(calibrated_c, 2),
            "structure": round(calibrated_s, 2)
        },
        "overall_score": overall_score,
        "flags": flags,
        "feedback": top_feedback,
        "uncertainty": {
            "is_uncertain": content_res.get("is_uncertain", False) or struct_res.get("is_uncertain", False),
            "content_uncertain": content_res.get("is_uncertain", False),
            "structure_uncertain": struct_res.get("is_uncertain", False),
            "reasons": content_res.get("uncertainty_reasons", []) + struct_res.get("uncertainty_reasons", [])
        },
        "structure_diagnostics": struct_res.get("components", {}),
        "communication_diagnostics": comm_res
    }
