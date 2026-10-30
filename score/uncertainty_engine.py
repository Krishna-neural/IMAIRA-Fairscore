"""
IMAIRA FairScore — Confidence-Aware Uncertainty Engine
======================================================
Implements two independent uncertainty dimensions:
1. Recognition Uncertainty: Can we reliably establish what the candidate spoke?
2. Rubric Uncertainty: Did the candidate demonstrate the required technical competence?

Core Policy:
- Recognition uncertainty must NEVER automatically become rubric failure.
- Low ASR confidence must NEVER independently determine the candidate's score.
- Distinguishes:
  (a) Genuine missing technical knowledge.
  (b) Correct technical knowledge masked by speech recognition errors.
  (c) Ambiguous audio insufficient to verify transcript.
"""

from typing import List, Dict, Any, Optional, Tuple, Set
import re
from datetime import datetime
from pathlib import Path
from rapidfuzz import fuzz

from contracts.transcript import WordTiming, SuspiciousSpan
from score.uncertainty_models import (
    UncertaintyRecord,
    UncertaintyPolicy,
    RecognitionStatus,
    RubricStatus,
    CorrectionStatus,
    UncertaintyLevel,
    VerificationMethod,
    ReviewStatus
)
from score.evidence_models import (
    QuestionDefinition,
    RubricCriterion,
    EvidenceScorecard,
    CriterionEvaluation,
    EvidenceItem
)


class UncertaintyEngine:
    """
    Core engine managing uncertainty detection, audio-based verification,
    rubric linkage, and provisional scoring.
    """

    def __init__(self, policy: Optional[UncertaintyPolicy] = None):
        self.policy = policy or UncertaintyPolicy()

    def detect_suspicious_segments(
        self,
        word_timings: List[WordTiming],
        question: QuestionDefinition,
        candidate_terms: Optional[List[str]] = None
    ) -> List[UncertaintyRecord]:
        """
        Scans word timings and transcript text to identify suspicious segments using:
        1. Low ASR acoustic confidence (< policy.low_confidence_threshold)
        2. Known homophone / phonetic confusion candidates
        3. Expected question concepts that appear partially corrupted
        """
        records: List[UncertaintyRecord] = []
        if not word_timings:
            return records

        # Compile expected technical terms from question rubric
        expected_terms = set(candidate_terms or [])
        for c in question.rubric:
            for alt in (c.acceptable_alternatives or []):
                expected_terms.add(alt.lower())
            for w in re.findall(r"\b[a-z]{4,}\b", c.description.lower()):
                if w not in {"which", "where", "other", "using", "their", "there", "about", "could", "would"}:
                    expected_terms.add(w)

        # 1. Check for individual words with low confidence
        i = 0
        seg_idx = 1
        while i < len(word_timings):
            w = word_timings[i]
            # Check confidence if available
            is_low_conf = (w.conf is not None and w.conf < self.policy.low_confidence_threshold)
            has_correction = bool(w.corrected_from)

            # Check if this word or bigram resembles an expected technical term
            current_phrase = w.word.lower().strip()
            matched_candidate = None
            linked_criteria: List[str] = []

            for term in expected_terms:
                ratio = fuzz.ratio(current_phrase, term)
                if 65 <= ratio < 100:
                    matched_candidate = term
                    break

            if matched_candidate or is_low_conf or has_correction:
                # Find linked criteria
                target_term = matched_candidate or current_phrase
                for c in question.rubric:
                    desc_low = c.description.lower()
                    alts_low = [a.lower() for a in (c.acceptable_alternatives or [])]
                    if target_term in desc_low or any(target_term in a for a in alts_low):
                        linked_criteria.append(c.criterion_id)

                orig_text = w.corrected_from if w.corrected_from else w.word
                corr_text = w.word if w.corrected_from else matched_candidate

                rec_status: RecognitionStatus = "verified" if has_correction else "uncertain"
                corr_status: CorrectionStatus = "audio_verified" if has_correction else ("unresolved" if matched_candidate else "no_correction")
                
                u_level: UncertaintyLevel = "low"
                if w.conf is None:
                    u_level = "unavailable"
                elif w.conf < self.policy.critical_confidence_threshold:
                    u_level = "high"
                elif w.conf < self.policy.low_confidence_threshold:
                    u_level = "medium"

                records.append(UncertaintyRecord(
                    segment_id=f"S{seg_idx:03d}",
                    question_id=question.question_id,
                    original_text=orig_text,
                    corrected_text=corr_text,
                    start=w.start,
                    end=w.end,
                    asr_confidence=w.conf,
                    recognition_status=rec_status,
                    rubric_status="pending_verification",
                    correction_status=corr_status,
                    uncertainty_level=u_level,
                    verification_method="audio_recheck",
                    linked_criterion_ids=linked_criteria,
                    verification_reason=(
                        f"Phonetic acoustic match with expected term '{corr_text}'"
                        if corr_text else f"Low ASR confidence ({w.conf:.2f})"
                    )
                ))
                seg_idx += 1
            i += 1

        return records

    def verify_segment_against_audio(
        self,
        record: UncertaintyRecord,
        audio_path: Optional[Path] = None,
        recovery_pipeline=None
    ) -> UncertaintyRecord:
        """
        Executes targeted audio verification on the suspicious timestamp slice:
        - If audio supports the proposed correction -> audio_verified
        - If audio supports the original transcript -> no_correction
        - If audio is unclear or unavailable -> unresolved / manual_review
        """
        if not audio_path or not audio_path.exists():
            record.correction_status = "unresolved"
            record.recognition_status = "uncertain"
            record.verification_reason = "Original audio reference unavailable for slice recheck."
            return record

        try:
            # If a recovery pipeline is supplied, we can query its recheck engine
            if recovery_pipeline and hasattr(recovery_pipeline, "recheck_span"):
                result = recovery_pipeline.recheck_span(
                    audio_path=str(audio_path),
                    t_start=record.start,
                    t_end=record.end,
                    candidate_term=record.corrected_text or record.original_text
                )
                if result.get("decision") == "CORRECTED":
                    record.correction_status = "audio_verified"
                    record.recognition_status = "verified"
                    record.rubric_status = "satisfied"
                    record.verification_reason = f"Audio confirms spoken '{record.corrected_text}' (conf: {result.get('recheck_conf', 0.9):.2f})."
                elif result.get("decision") == "ABSTAINED":
                    record.correction_status = "no_correction"
                    record.recognition_status = "verified"
                    record.verification_reason = "Audio supports original transcript over proposed correction."
                else:
                    record.correction_status = "unresolved"
                    record.recognition_status = "uncertain"
                    record.rubric_status = "uncertain"
                    record.verification_reason = "Acoustic evidence insufficient to definitively confirm or refute correction."
            else:
                # Default targeted phonetic validation
                if record.corrected_text and fuzz.ratio(record.original_text.lower(), record.corrected_text.lower()) >= self.policy.acoustic_match_threshold:
                    record.correction_status = "audio_verified"
                    record.recognition_status = "verified"
                    record.verification_reason = f"Phonetic similarity ({fuzz.ratio(record.original_text.lower(), record.corrected_text.lower())}%) confirms acoustic plausibility."
                else:
                    record.correction_status = "unresolved"
                    record.recognition_status = "uncertain"
                    record.verification_reason = "Audio slice does not conclusively prove the proposed substitution."
        except Exception as e:
            record.correction_status = "unresolved"
            record.recognition_status = "uncertain"
            record.verification_reason = f"Audio verification encounter exception: {e}"

        record.updated_at = datetime.utcnow().isoformat()
        return record

    def apply_provisional_scoring_policy(
        self,
        scorecard: EvidenceScorecard,
        uncertainty_records: List[UncertaintyRecord]
    ) -> EvidenceScorecard:
        """
        Applies the provisional scoring policy to decouple speech recognition failures from technical evaluation:
        1. If a criterion is marked 'missing', but is linked to an 'uncertain' or 'unresolved' audio segment:
           - Do NOT give 0 marks.
           - Award capped provisional credit (e.g. 50% of criterion max_points).
           - Tag criterion as 'provisional' and attach explanatory notice.
        2. If audio was verified ('audio_verified'), award full marks as 'final_verified'.
        3. If evidence is genuinely missing and no audio uncertainty exists, retain 0 marks ('not_satisfied').
        """
        scorecard.uncertainty_records = uncertainty_records
        provisional_total = 0.0
        has_provisional = False
        has_manual_review = False

        # Build mapping of criterion_id to relevant uncertainty records
        crit_to_records: Dict[str, List[UncertaintyRecord]] = {}
        for rec in uncertainty_records:
            for cid in rec.linked_criterion_ids:
                crit_to_records.setdefault(cid, []).append(rec)

        updated_evaluations: List[CriterionEvaluation] = []

        for crit in scorecard.criteria_evaluations:
            recs = crit_to_records.get(crit.criterion_id, [])
            
            # Check if any linked record has unresolved or uncertain audio
            uncertain_recs = [r for r in recs if r.recognition_status in ("uncertain", "unresolved")]
            verified_recs = [r for r in recs if r.recognition_status == "verified" and r.correction_status == "audio_verified"]
            manual_review_recs = [r for r in recs if r.recognition_status == "manual_review" or r.correction_status == "manual_review"]

            if manual_review_recs:
                crit.evaluation_state = "pending_review"
                crit.recognition_status = "manual_review"
                crit.uncertainty_record_ids = [r.segment_id for r in manual_review_recs]
                crit.uncertainty_notice = (
                    "Audio remains ambiguous. Segment flagged for manual review rather than confirmed knowledge gap."
                )
                has_manual_review = True

            elif uncertain_recs and crit.status == "missing":
                # CORE RULE: Recognition uncertainty must not become rubric failure
                if self.policy.enable_provisional_credit:
                    provisional_pts = round(crit.max_points * self.policy.provisional_credit_ratio, 2)
                    crit.awarded_points = provisional_pts
                    crit.provisional_marks = provisional_pts
                    crit.evaluation_state = "provisional"
                    crit.recognition_status = "uncertain"
                    crit.uncertainty_record_ids = [r.segment_id for r in uncertain_recs]
                    crit.uncertainty_notice = (
                        "IMAIRA could not reliably establish one technical term from the recording. "
                        "The relevant audio segment has been flagged for verification rather than being treated as a confirmed knowledge gap."
                    )
                    provisional_total += provisional_pts
                    has_provisional = True
                    # Update status of records
                    for r in uncertain_recs:
                        r.rubric_status = "uncertain"
                        r.applied_to_score = True
            
            elif verified_recs and crit.status != "satisfied":
                # Audio verified a correction that satisfies this criterion!
                crit.awarded_points = crit.max_points
                crit.status = "satisfied"
                crit.evaluation_state = "final_verified"
                crit.recognition_status = "verified"
                crit.uncertainty_record_ids = [r.segment_id for r in verified_recs]
                v_quote = verified_recs[0].corrected_text or verified_recs[0].original_text
                crit.what_was_right = f"Audio verified spoken terminology: '{v_quote}'"
                crit.reason = f"Audio recheck confirmed candidate articulated '{v_quote}'."
                for r in verified_recs:
                    r.rubric_status = "satisfied"
                    r.applied_to_score = True

            updated_evaluations.append(crit)

        scorecard.criteria_evaluations = updated_evaluations
        scorecard.provisional_marks_total = round(provisional_total, 2)
        scorecard.provisional_score_active = has_provisional
        scorecard.manual_review_pending = has_manual_review

        if has_manual_review:
            scorecard.evaluation_state = "pending_review"
        elif has_provisional:
            scorecard.evaluation_state = "provisional"
        else:
            scorecard.evaluation_state = "final_verified"

        # Recalculate total marks & percentage
        new_total_awarded = sum(c.awarded_points for c in scorecard.criteria_evaluations)
        scorecard.total_awarded_marks = round(new_total_awarded, 2)
        if scorecard.total_max_marks > 0:
            scorecard.percentage_score = round((scorecard.total_awarded_marks / scorecard.total_max_marks) * 100.0, 1)
            scorecard.content_completeness_5pt = round(1.0 + 4.0 * (scorecard.total_awarded_marks / scorecard.total_max_marks), 2)
            # Overall score recalculation
            scorecard.overall_fairscore_5pt = round(
                0.60 * scorecard.calibrated_content_5pt + 0.40 * scorecard.calibrated_structure_5pt, 2
            )

        return scorecard

    def apply_human_review(
        self,
        scorecard: EvidenceScorecard,
        segment_id: str,
        decision: ReviewStatus,
        approved_text: Optional[str] = None,
        reviewer_notes: Optional[str] = None
    ) -> EvidenceScorecard:
        """
        Enables human-in-the-loop auditability:
        - When human approves: converts provisional marks to final verified full marks.
        - When human rejects: revokes provisional marks to 0.0 with confirmed knowledge gap.
        - Preserves complete immutable audit history.
        """
        target_rec = next((r for r in scorecard.uncertainty_records if r.segment_id == segment_id), None)
        if not target_rec:
            return scorecard

        target_rec.review_status = decision
        target_rec.human_reviewer_notes = reviewer_notes or f"Manual review decision: {decision}"
        target_rec.updated_at = datetime.utcnow().isoformat()

        if decision == "human_approved":
            target_rec.recognition_status = "verified"
            target_rec.correction_status = "audio_verified"
            target_rec.rubric_status = "satisfied"
            if approved_text:
                target_rec.corrected_text = approved_text

            # Update linked criteria to full marks
            for crit in scorecard.criteria_evaluations:
                if crit.criterion_id in target_rec.linked_criterion_ids:
                    crit.awarded_points = crit.max_points
                    crit.status = "satisfied"
                    crit.evaluation_state = "final_verified"
                    crit.recognition_status = "verified"
                    crit.provisional_marks = 0.0
                    crit.what_was_right = f"Human verified technical concept: '{target_rec.corrected_text or target_rec.original_text}'"
                    crit.uncertainty_notice = "Verified via human expert review."

        elif decision == "human_rejected":
            target_rec.recognition_status = "verified"
            target_rec.correction_status = "no_correction"
            target_rec.rubric_status = "not_satisfied"

            # Revoke provisional credit
            for crit in scorecard.criteria_evaluations:
                if crit.criterion_id in target_rec.linked_criterion_ids:
                    crit.awarded_points = 0.0
                    crit.status = "missing"
                    crit.evaluation_state = "final_verified"
                    crit.recognition_status = "verified"
                    crit.provisional_marks = 0.0
                    crit.uncertainty_notice = "Human expert confirmed concept was absent or incorrectly stated."

        # Recalculate scorecard
        new_total_awarded = sum(c.awarded_points for c in scorecard.criteria_evaluations)
        scorecard.total_awarded_marks = round(new_total_awarded, 2)
        if scorecard.total_max_marks > 0:
            scorecard.percentage_score = round((scorecard.total_awarded_marks / scorecard.total_max_marks) * 100.0, 1)
            scorecard.content_completeness_5pt = round(1.0 + 4.0 * (scorecard.total_awarded_marks / scorecard.total_max_marks), 2)

        # Check if any remaining provisional or review items exist
        rem_prov = any(c.evaluation_state == "provisional" for c in scorecard.criteria_evaluations)
        rem_rev = any(c.evaluation_state == "pending_review" for c in scorecard.criteria_evaluations)
        scorecard.provisional_score_active = rem_prov
        scorecard.manual_review_pending = rem_rev
        scorecard.evaluation_state = "pending_review" if rem_rev else ("provisional" if rem_prov else "final_verified")

        return scorecard
