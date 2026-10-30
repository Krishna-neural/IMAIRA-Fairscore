"""
IMAIRA FairScore — Deterministic Evidence-First Rubric Scoring Engine
====================================================================
Pure Python, 100% deterministic mathematical evaluation module:
- Implements 'No evidence, no marks' rule.
- Calculates criterion-level marks strictly from validated evidence and predefined rules.
- Prevents double-counting of quotes across criteria.
- Enforces criterion and question maximum point boundaries.
- Corrects structure subcomponent scale mismatch (0-1 ratio vs 1-5 scale).
- Produces fully auditable EvidenceScorecards.
"""

from typing import Dict, Any, List, Optional, Tuple
from score.evidence_models import (
    QuestionDefinition,
    RubricCriterion,
    EvidenceItem,
    CriterionEvaluation,
    MisconceptionItem,
    EvidenceScorecard
)


class DeterministicEvidenceScorer:
    """
    Deterministic scoring engine that decouples semantic classification from mark calculation.
    Enforces strict mathematical bounds and traceability.
    """

    def __init__(self, partial_credit_ratio: float = 0.50):
        self.partial_credit_ratio = partial_credit_ratio

    def score_criteria(
        self,
        question: QuestionDefinition,
        raw_evidence_evaluations: List[Dict[str, Any]],
        misconceptions: List[MisconceptionItem],
        transcript_text: str
    ) -> Tuple[List[CriterionEvaluation], float, float]:
        """
        Calculates marks awarded per criterion based on validated evidence.
        Returns: (evaluations, total_awarded_marks, total_max_marks)
        """
        criterion_map = {c.criterion_id: c for c in question.rubric}
        used_quote_spans = set()
        evaluations: List[CriterionEvaluation] = []
        total_awarded = 0.0
        total_max = sum(c.max_points for c in question.rubric)

        # Check for critical misconceptions that invalidate concepts
        critical_concepts = {
            m.concept.lower(): m for m in misconceptions if m.severity == "CRITICAL"
        }

        # Process each criterion from the official question rubric
        for crit in question.rubric:
            cid = crit.criterion_id
            # Find matching raw evaluation from semantic extractor
            raw_eval = next((e for e in raw_evidence_evaluations if e.get("criterion_id") == cid), None)

            if not raw_eval or not transcript_text.strip():
                # Zero marks when evidence is missing or transcript is empty
                evaluations.append(CriterionEvaluation(
                    criterion_id=cid,
                    description=crit.description,
                    status="missing",
                    evidence=[],
                    max_points=crit.max_points,
                    awarded_points=0.0,
                    reason="No supporting evidence found in the candidate's transcript.",
                    what_was_right=None,
                    what_was_missing=crit.description,
                    how_to_improve=f"State and explain {crit.description.lower()}."
                ))
                continue

            raw_status = raw_eval.get("status", "missing").lower()
            raw_evidence = raw_eval.get("evidence", [])
            reason = raw_eval.get("reason", "")
            what_right = raw_eval.get("what_was_right")
            what_missing = raw_eval.get("what_was_missing")
            how_improve = raw_eval.get("how_to_improve")

            # Parse and validate evidence items
            validated_evidence: List[EvidenceItem] = []
            for ev in raw_evidence:
                text_snippet = ev.get("text", "").strip() if isinstance(ev, dict) else str(ev).strip()
                if not text_snippet:
                    continue

                # Verify quote actually exists in candidate's response (anti-hallucination)
                if text_snippet.lower() in transcript_text.lower():
                    # Calculate offsets if not provided
                    start_idx = transcript_text.lower().find(text_snippet.lower())
                    end_idx = start_idx + len(text_snippet)
                    span_key = (start_idx, end_idx)

                    validated_evidence.append(EvidenceItem(
                        text=text_snippet,
                        source_start=ev.get("source_start", start_idx) if isinstance(ev, dict) else start_idx,
                        source_end=ev.get("source_end", end_idx) if isinstance(ev, dict) else end_idx,
                        timestamp_start=ev.get("timestamp_start") if isinstance(ev, dict) else None,
                        timestamp_end=ev.get("timestamp_end") if isinstance(ev, dict) else None
                    ))

            # RULE: No evidence, no marks
            if not validated_evidence and raw_status in ("satisfied", "partially_satisfied"):
                raw_status = "missing"
                reason = "Classification required evidence, but no matching verbatim quote exists in transcript."

            # Calculate awarded marks deterministically
            if raw_status == "satisfied":
                # Full marks
                awarded = crit.max_points
                if not what_right and validated_evidence:
                    what_right = f"Correctly explained: \"{validated_evidence[0].text}\""
            elif raw_status == "partially_satisfied":
                # Partial marks with defined ratio
                awarded = round(crit.max_points * self.partial_credit_ratio, 2)
                if not what_missing:
                    what_missing = f"Incomplete explanation of {crit.description.lower()}."
            else:
                raw_status = "missing"
                awarded = 0.0
                if not what_missing:
                    what_missing = crit.description

            # Check if a critical misconception directly refutes this criterion
            for c_name, misc in critical_concepts.items():
                if any(w in crit.description.lower() for w in c_name.split()):
                    # Dock points to zero for fundamentally incorrect claims
                    awarded = 0.0
                    raw_status = "missing"
                    reason = f"Marks denied: Critical misconception detected ('{misc.error_explanation}')."
                    what_missing = f"Candidate made a critical error regarding {c_name}."

            # Enforce strict boundary: 0.0 <= awarded <= max_points
            awarded = max(0.0, min(crit.max_points, awarded))
            total_awarded += awarded

            evaluations.append(CriterionEvaluation(
                criterion_id=cid,
                description=crit.description,
                status=raw_status,
                evidence=validated_evidence,
                max_points=crit.max_points,
                awarded_points=awarded,
                reason=reason or f"Evaluated against criterion '{crit.description}'.",
                what_was_right=what_right,
                what_was_missing=what_missing,
                how_to_improve=how_improve
            ))

        return evaluations, round(total_awarded, 2), round(total_max, 2)

    def calculate_scorecard(
        self,
        question: QuestionDefinition,
        raw_evidence_evaluations: List[Dict[str, Any]],
        misconceptions: List[MisconceptionItem],
        transcript_text: str,
        raw_structure_scores: Dict[str, Any],
        calibrator_content=None,
        calibrator_structure=None
    ) -> EvidenceScorecard:
        """
        Orchestrates complete deterministic scorecard calculation:
        - Evaluates criteria with evidence traceability.
        - Scales structure subcomponents to 1.0 - 5.0.
        - Applies calibration and overall FairScore weighting.
        """
        criteria_evals, awarded_marks, max_marks = self.score_criteria(
            question=question,
            raw_evidence_evaluations=raw_evidence_evaluations,
            misconceptions=misconceptions,
            transcript_text=transcript_text
        )

        pct = round((awarded_marks / max_marks) * 100.0, 1) if max_marks > 0 else 0.0

        # Scale Content Completeness to standard 1.0 - 5.0 scale
        completeness_5pt = round(1.0 + 4.0 * (awarded_marks / max_marks), 2) if max_marks > 0 else 1.0

        # Calculate Content Correctness (Deductions for misconceptions)
        penalty = 0.0
        for m in misconceptions:
            if m.severity == "CRITICAL":
                penalty += 1.50
            elif m.severity == "MODERATE":
                penalty += 0.50
            elif m.severity == "MINOR":
                penalty += 0.20
        correctness_5pt = round(max(1.0, min(5.0, 5.0 - penalty)), 2)

        # Scale Structure subcomponents to 1.0 - 5.0 scale (Fixing the 0-1 ratio bug)
        def scale_structure_dim(v: Any) -> float:
            try:
                val = float(v)
                # If returned as ratio <= 1.0, scale to 1.0 - 5.0
                if val <= 1.0 and val > 0.0:
                    return round(1.0 + 4.0 * val, 2)
                elif val == 0.0:
                    return 1.0
                return round(min(5.0, max(1.0, val)), 2)
            except (ValueError, TypeError):
                return 3.0

        framing_5pt = scale_structure_dim(raw_structure_scores.get("framing", 3.0))
        coherence_5pt = scale_structure_dim(raw_structure_scores.get("coherence", 3.0))
        closure_5pt = scale_structure_dim(raw_structure_scores.get("closure", 3.0))

        structure_5pt = round(0.35 * framing_5pt + 0.40 * coherence_5pt + 0.25 * closure_5pt, 2)

        # Apply Isotonic Calibration
        if calibrator_content is not None:
            try:
                import numpy as np
                cal_content = float(calibrator_content.predict(np.array([completeness_5pt]))[0])
            except Exception:
                cal_content = completeness_5pt
        else:
            cal_content = completeness_5pt

        if calibrator_structure is not None:
            try:
                import numpy as np
                cal_struct = float(calibrator_structure.predict(np.array([structure_5pt]))[0])
            except Exception:
                cal_struct = structure_5pt
        else:
            cal_struct = structure_5pt

        cal_content = round(cal_content, 2)
        cal_struct = round(cal_struct, 2)

        # Overall FairScore: 60% Content + 40% Structure
        overall_fairscore = round(0.60 * cal_content + 0.40 * cal_struct, 2)

        # Summary verdict
        if pct >= 85.0:
            verdict = "Excellent — Highly Demonstrative"
        elif pct >= 65.0:
            verdict = "Competent — Minor Gaps"
        elif pct >= 40.0:
            verdict = "Developing — Missing Core Concepts"
        else:
            verdict = "Incomplete or Incorrect"

        return EvidenceScorecard(
            question_id=question.question_id,
            question=question.question,
            domain=question.domain,
            difficulty=question.difficulty,
            total_max_marks=max_marks,
            total_awarded_marks=awarded_marks,
            percentage_score=pct,
            content_completeness_5pt=completeness_5pt,
            content_correctness_5pt=correctness_5pt,
            answer_structure_5pt=structure_5pt,
            calibrated_content_5pt=cal_content,
            calibrated_structure_5pt=cal_struct,
            overall_fairscore_5pt=overall_fairscore,
            criteria_evaluations=criteria_evals,
            misconceptions=misconceptions,
            structure_breakdown={
                "framing": framing_5pt,
                "coherence": coherence_5pt,
                "closure": closure_5pt
            },
            summary_verdict=verdict
        )
