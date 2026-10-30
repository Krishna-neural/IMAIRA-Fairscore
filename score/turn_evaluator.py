"""IMAIRA FairScore — Unified Turn Evaluator (Stage 4).

Orchestrates live, evidence-grounded, confidence-aware scoring and dual diagnosis
for every candidate turn during technical questions:
1. Deterministic Rubric & Structure Scoring with Isotonic Calibration.
2. Confidence-Aware Uncertainty Protection (acoustic slips never become technical failures).
3. Dual Diagnosis:
   - Technical Knowledge Gaps (missing concepts, marks lost, grounded model sentence fixes).
   - Pronunciation & Articulation Improvements (recovered acoustic slices, phonetic shifts, zero mark deductions).
4. Silent Session Persistence formatting.
"""

import logging
from pathlib import Path
from typing import Any, Dict, List, Optional
import numpy as np

from score.pipeline import run_fairscore_pipeline, get_cached_rubrics, get_calibrators
from score.qanda import QnARecord, get_qanda_by_id, load_qanda
from score.evidence_models import QuestionDefinition, RubricCriterion, EvidenceScorecard
from score.evidence_scorer import DeterministicEvidenceScorer
from score.feedback_compiler import FeedbackCompiler

logger = logging.getLogger("imaira.turn_evaluator")
REPO_ROOT = Path(__file__).resolve().parent.parent

_FEEDBACK_COMPILER: Optional[FeedbackCompiler] = None
_EVIDENCE_SCORER: Optional[DeterministicEvidenceScorer] = None


def get_feedback_compiler() -> FeedbackCompiler:
    global _FEEDBACK_COMPILER
    if _FEEDBACK_COMPILER is None:
        _FEEDBACK_COMPILER = FeedbackCompiler()
    return _FEEDBACK_COMPILER


def get_evidence_scorer() -> DeterministicEvidenceScorer:
    global _EVIDENCE_SCORER
    if _EVIDENCE_SCORER is None:
        _EVIDENCE_SCORER = DeterministicEvidenceScorer()
    return _EVIDENCE_SCORER


class TurnEvaluator:
    """Evaluates candidate response turns silently and produces comprehensive FairScore evaluations."""

    def __init__(self):
        self.evidence_scorer = get_evidence_scorer()
        self.feedback_compiler = get_feedback_compiler()

    def evaluate_turn(
        self,
        question_id: str,
        question_text: str,
        recovered_utterance: str,
        raw_utterance: Optional[str] = None,
        slice_recovery_log: Optional[List[Dict[str, Any]]] = None,
        word_timings: Optional[List[Dict[str, Any]]] = None,
        curr_q: Optional[QnARecord] = None,
        duration_sec: float = 45.0
    ) -> Dict[str, Any]:
        """Execute complete Stage 4 evidence-first scoring and dual diagnosis."""
        raw_text = raw_utterance or recovered_utterance
        recovered_text = recovered_utterance.strip()
        slices = slice_recovery_log or []

        # 1. Resolve Q&A record if not provided
        if not curr_q and question_id:
            curr_q = get_qanda_by_id(question_id)

        # 2. Run core FairScore pipeline (ContentJudge + StructureJudge + Calibrators + CommScorer)
        pipeline_res = run_fairscore_pipeline(
            transcript_text=recovered_text,
            word_tokens=word_timings,
            question_text=question_text,
            question_id=question_id,
            duration_sec=duration_sec
        )

        scores = pipeline_res.get("scores", {})
        raw_scores = pipeline_res.get("raw_scores", {})
        cal_scores = pipeline_res.get("calibrated_scores", {})
        flags = pipeline_res.get("flags", {})
        struct_diag = pipeline_res.get("structure_diagnostics", {})
        comm_diag = pipeline_res.get("communication_diagnostics", {})
        uncertainty = pipeline_res.get("uncertainty", {})

        # Extract calibrated scores
        cal_content = cal_scores.get("content", raw_scores.get("content", 3.0))
        cal_struct = cal_scores.get("structure", raw_scores.get("structure", 3.0))
        content_pct = scores.get("content", 50)
        struct_pct = scores.get("structure", 50)
        comm_pct = scores.get("communication", 75)

        # Calculate FairScore: 60% Content + 40% Structure
        fairscore_5pt = round(0.60 * cal_content + 0.40 * cal_struct, 2)
        fairscore_100pt = round(0.60 * content_pct + 0.40 * struct_pct, 1)

        # 3. Construct Semantic Rubric Ideas Breakdown
        rubric_breakdown: List[Dict[str, Any]] = []
        if curr_q and curr_q.semantic_rubric_ideas:
            for idea in curr_q.semantic_rubric_ideas:
                flag = flags.get(idea.idea_id, "missing")
                verdict = "demonstrated" if flag == "covered" else ("partially_demonstrated" if flag == "partial" else "absent")
                pts_awarded = 10.0 if flag == "covered" else (5.0 if flag == "partial" else 0.0)
                marks_lost = round(10.0 - pts_awarded, 1)

                rubric_breakdown.append({
                    "idea_id": idea.idea_id,
                    "concept_statement": idea.semantic_statement,
                    "verdict": verdict,
                    "points_awarded": pts_awarded,
                    "max_points": 10.0,
                    "marks_lost": marks_lost,
                    "weight": idea.weight
                })

        # 4. Dual Diagnosis — Category A: Technical Knowledge Gaps
        technical_knowledge_gaps: List[Dict[str, Any]] = []
        canonical_answer = curr_q.answer if curr_q else ""
        key_concepts = curr_q.key_concepts if curr_q else []

        for item in rubric_breakdown:
            if item["marks_lost"] > 0:
                stmt = item["concept_statement"]
                model_fix = f"To fully address this requirement: articulate that {stmt.lower()}"
                if canonical_answer:
                    for sent in canonical_answer.split("."):
                        clean_sent = sent.strip()
                        if any(w.lower() in clean_sent.lower() for w in stmt.split() if len(w) > 4):
                            model_fix = clean_sent + "."
                            break

                technical_knowledge_gaps.append({
                    "criterion_id": item["idea_id"],
                    "concept": stmt,
                    "status": "partial" if item["verdict"] == "partially_demonstrated" else "missing",
                    "marks_lost": item["marks_lost"],
                    "issue_explanation": f"The candidate's response lacked comprehensive coverage of: '{stmt}'.",
                    "model_sentence_fix": model_fix,
                    "remedial_guidance": f"Review {curr_q.subcategory if curr_q else 'core concepts'}: focus on explaining mechanisms, tradeoffs, and failure modes."
                })

        if not technical_knowledge_gaps:
            technical_knowledge_gaps.append({
                "criterion_id": "ALL_SATISFIED",
                "concept": "Complete Technical Mastery",
                "status": "satisfied",
                "marks_lost": 0.0,
                "issue_explanation": "All core technical concepts and architectural invariants were successfully demonstrated.",
                "model_sentence_fix": "Maintain this level of structured technical articulation in subsequent interview turns.",
                "remedial_guidance": "Demonstrated comprehensive understanding."
            })

        # 5. Dual Diagnosis — Category B: Pronunciation & Articulation Improvements
        pronunciation_improvements: List[Dict[str, Any]] = []
        for s in slices:
            status = s.get("status", "CORRECTED")
            orig = s.get("original_text", "")
            cand = s.get("verified_text") or s.get("candidate_term", "")
            time_rng = s.get("time_range", "0.0s - 0.0s")
            p_match = s.get("phonetic_match", False)

            if status == "CORRECTED":
                tip = f"Pronounce '{cand}' clearly with standard technical articulation. The platform recognized the acoustic shift from '{orig}' and credited your technical content fully with zero mark deductions."
                pronunciation_improvements.append({
                    "spoken_slice": orig,
                    "canonical_term": cand,
                    "time_range": time_rng,
                    "status": "RECOVERED",
                    "phonetic_match": p_match,
                    "score_deduction": 0.0,
                    "coaching_tip": tip
                })
            elif status == "ABSTAINED":
                tip = f"The acoustic slice '{orig}' was phonetically ambiguous and was protected under provisional credit so your technical score was not penalized."
                pronunciation_improvements.append({
                    "spoken_slice": orig,
                    "canonical_term": cand,
                    "time_range": time_rng,
                    "status": "PROVISIONAL_ABSTAINED",
                    "phonetic_match": p_match,
                    "score_deduction": 0.0,
                    "coaching_tip": tip
                })

        # 6. Confidence-Aware Uncertainty Protection
        has_abstained = any(p["status"] == "PROVISIONAL_ABSTAINED" for p in pronunciation_improvements)
        provisional_credit = has_abstained or uncertainty.get("is_uncertain", False)

        # 7. Construct Complete Evaluation Payload
        evaluation_payload = {
            "question_id": question_id,
            "question_text": question_text,
            "category": curr_q.category if curr_q else "Engineering",
            "difficulty": curr_q.difficulty if curr_q else "Intermediate",
            "raw_utterance": raw_text,
            "recovered_utterance": recovered_text,
            "scores": {
                "raw_content_5pt": raw_scores.get("content", 1.0),
                "raw_structure_5pt": raw_scores.get("structure", 1.0),
                "calibrated_content_5pt": cal_content,
                "calibrated_structure_5pt": cal_struct,
                "content_pct": content_pct,
                "structure_pct": struct_pct,
                "communication_pct": comm_pct,
                "overall_fairscore_5pt": fairscore_5pt,
                "overall_fairscore_pct": fairscore_100pt
            },
            "structure_breakdown": {
                "framing_5pt": struct_diag.get("framing", {}).get("score", 3.0),
                "coherence_5pt": struct_diag.get("coherence", {}).get("score", 3.0),
                "closure_5pt": struct_diag.get("closure", {}).get("score", 3.0)
            },
            "rubric_breakdown": rubric_breakdown,
            "dual_diagnosis": {
                "technical_knowledge_gaps": technical_knowledge_gaps,
                "pronunciation_improvements": pronunciation_improvements,
                "accent_penalty_applied": False,
                "acoustic_protection_active": True
            },
            "uncertainty": {
                "is_uncertain": uncertainty.get("is_uncertain", False),
                "provisional_credit_applied": provisional_credit,
                "reasons": uncertainty.get("reasons", [])
            },
            "canonical_reference": {
                "answer_summary": (canonical_answer[:200] + "...") if len(canonical_answer) > 200 else canonical_answer,
                "key_concepts": key_concepts
            }
        }

        return evaluation_payload
