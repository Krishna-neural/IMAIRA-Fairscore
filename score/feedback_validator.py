"""
IMAIRA FairScore — Feedback Validation Engine
=============================================
Enforces rigorous validation rules on all generated candidate feedback:
1. Quote Validation: Every quote must exist in original/verified transcript (no fabricated quotes).
2. Timestamp Validation: Non-negative, start < end, falls within audio duration, no invented timestamps.
3. Rubric Linkage: Target criterion exists and candidate actually lost marks.
4. Uncertainty Integrity: Unresolved ASR cannot be reported as confirmed knowledge failure.
5. Technical Correctness: Suggested answer contains relevant concepts and accurate terminology.
6. Quality & Conciseness: Free from motivational fluff and within word limits.
"""

import re
from typing import List, Dict, Any, Optional, Tuple
from rapidfuzz import fuzz

from score.feedback_models import (
    FeedbackOpportunity,
    FeedbackStatus,
    EvidenceQuote,
    FeedbackCompilerInput
)


MOTIVATIONAL_FLUFF_PATTERNS = [
    r"\bgreat job\b",
    r"\bgood try\b",
    r"\bkeep it up\b",
    r"\bdon't worry\b",
    r"\byou can do it\b",
    r"\bnever give up\b",
    r"\bbest of luck\b",
    r"\bcheer up\b",
    r"\bno problem at all\b"
]


class FeedbackValidationError(ValueError):
    """Raised when feedback violates evidence ground-truth or validation rules."""
    pass


class FeedbackValidator:
    """Validates generated feedback opportunities against evaluation evidence."""

    def __init__(self, fuzzy_quote_threshold: float = 85.0, timestamp_tolerance_sec: float = 1.0):
        self.fuzzy_quote_threshold = fuzzy_quote_threshold
        self.timestamp_tolerance_sec = timestamp_tolerance_sec

    def validate_quote(self, quote: str, transcript: str) -> Tuple[bool, str]:
        """
        Verify that a quote actually appears in the candidate's transcript.
        Rejects fabricated quotes and hallucinated speech.
        """
        if not quote or not quote.strip():
            # An empty quote is acceptable when candidate completely omitted a concept
            return True, "Empty quote (omission)"

        q_clean = quote.strip().lower()
        t_clean = transcript.strip().lower()

        # 1. Exact substring match
        if q_clean in t_clean:
            return True, "Exact quote match"

        # 2. Normalized word sequence match (ignoring punctuation)
        q_words = re.findall(r"\b[a-z0-9]+\b", q_clean)
        t_words = re.findall(r"\b[a-z0-9]+\b", t_clean)

        if not q_words:
            return True, "No alphabetic words in quote"

        q_phrase = " ".join(q_words)
        t_phrase = " ".join(t_words)

        if q_phrase in t_phrase:
            return True, "Normalized phrase match"

        # 3. Fuzzy partial ratio match for minor ASR token variations
        sim = fuzz.partial_ratio(q_phrase, t_phrase)
        if sim >= self.fuzzy_quote_threshold:
            return True, f"Fuzzy quote match ({sim:.1f}%)"

        return False, f"Fabricated quote: '{quote[:40]}...' not found in transcript (similarity: {sim:.1f}%)"

    def validate_timestamp(
        self,
        start: Optional[float],
        end: Optional[float],
        audio_duration_sec: Optional[float] = None
    ) -> Tuple[bool, str]:
        """
        Validate timestamp bounds.
        Missing timestamps are allowed; invalid or invented out-of-bounds timestamps are rejected.
        """
        if start is None and end is None:
            return True, "No timestamp provided (allowed for missing concepts)"

        if start is None or end is None:
            return False, "Malformed timestamp: both start and end must be provided if either is set"

        if start < 0.0 or end < 0.0:
            return False, f"Negative timestamp: start={start}, end={end}"

        if start >= end:
            return False, f"Inverted timestamp interval: start ({start}s) >= end ({end}s)"

        if audio_duration_sec is not None and audio_duration_sec > 0:
            max_allowed = audio_duration_sec + self.timestamp_tolerance_sec
            if end > max_allowed:
                return False, f"Timestamp out of bounds: end={end}s exceeds audio duration ({audio_duration_sec}s)"

        return True, "Valid timestamp"

    def validate_rubric_linkage(
        self,
        criterion_id: str,
        marks_lost: float,
        valid_criteria_ids: Dict[str, float]
    ) -> Tuple[bool, str]:
        """
        Verify that the feedback targets a legitimate criterion where the candidate actually lost marks.
        """
        if criterion_id not in valid_criteria_ids:
            return False, f"Nonexistent criterion ID: '{criterion_id}'"

        actual_lost = valid_criteria_ids[criterion_id]
        if actual_lost <= 0.0:
            return False, f"Invalid feedback: candidate earned full marks on criterion '{criterion_id}'"

        if marks_lost <= 0.0:
            return False, f"Marks lost must be positive for an improvement opportunity, got {marks_lost}"

        return True, "Valid rubric linkage"

    def validate_uncertainty(
        self,
        opportunity: FeedbackOpportunity,
        criterion_evaluation_state: str,
        recognition_status: str
    ) -> Tuple[bool, str]:
        """
        Enforce Confidence-Aware Evaluation principle:
        Unresolved ASR evidence must never be presented as a confirmed knowledge gap.
        """
        is_uncertain_asr = recognition_status in {"uncertain", "unresolved"}
        is_provisional = criterion_evaluation_state == "provisional"

        # Check for harsh, definitive failure assertions when ASR is ambiguous
        text_to_check = (opportunity.issue + " " + opportunity.action).lower()
        punitive_words = ["failed to", "failed to understand", "lacks knowledge", "completely ignorant"]

        if (is_uncertain_asr or is_provisional):
            for pw in punitive_words:
                if pw in text_to_check:
                    return False, f"Punitive statement '{pw}' used despite recognition uncertainty"

            if opportunity.feedback_status not in {"provisional", "pending_verification"}:
                return False, "Feedback status must be 'provisional' or 'pending_verification' for uncertain audio"

            if not opportunity.uncertainty_notice:
                return False, "Uncertainty notice is mandatory for feedback derived from provisional evidence"

        return True, "Uncertainty rules satisfied"

    def validate_technical_suggestion(
        self,
        suggested_answer: str,
        expected_concepts: Optional[List[str]] = None
    ) -> Tuple[bool, str]:
        """
        Validate that the suggested answer is a substantial, technically sound model response.
        """
        if not suggested_answer or not suggested_answer.strip():
            return False, "Suggested answer cannot be empty"

        words = suggested_answer.strip().split()
        if len(words) < 8:
            return False, f"Suggested answer is too brief ({len(words)} words; min 8 words required)"

        if expected_concepts:
            lower_text = suggested_answer.lower()
            matched = any(c.lower() in lower_text for c in expected_concepts)
            if not matched and len(words) < 15:
                return False, "Suggested answer does not reference expected technical concepts"

        return True, "Technical suggestion valid"

    def validate_quality_and_fluff(self, text: str) -> Tuple[bool, str]:
        """
        Ensure feedback is strictly technical and free of unnecessary motivational fluff.
        """
        lower = text.lower()
        for pat in MOTIVATIONAL_FLUFF_PATTERNS:
            if re.search(pat, lower):
                return False, f"Unprofessional motivational fluff detected: match for pattern '{pat}'"
        return True, "Clean technical tone"

    def validate_opportunity(
        self,
        opportunity: FeedbackOpportunity,
        transcript: str,
        valid_criteria_ids: Dict[str, float],
        audio_duration_sec: Optional[float] = None,
        criterion_evaluation_state: str = "final_verified",
        recognition_status: str = "verified",
        expected_concepts: Optional[List[str]] = None
    ) -> Tuple[bool, List[str]]:
        """
        Execute comprehensive validation across all rules.
        Returns (is_valid, list_of_errors).
        """
        errors = []

        # 1. Quote validation
        if opportunity.evidence and opportunity.evidence.quote:
            ok, msg = self.validate_quote(opportunity.evidence.quote, transcript)
            if not ok:
                errors.append(msg)

        # 2. Timestamp validation
        if opportunity.evidence:
            ok, msg = self.validate_timestamp(
                opportunity.evidence.start,
                opportunity.evidence.end,
                audio_duration_sec
            )
            if not ok:
                errors.append(msg)

        # 3. Rubric linkage
        ok, msg = self.validate_rubric_linkage(
            opportunity.criterion_id,
            opportunity.marks_lost,
            valid_criteria_ids
        )
        if not ok:
            errors.append(msg)

        # 4. Uncertainty validation
        ok, msg = self.validate_uncertainty(
            opportunity,
            criterion_evaluation_state,
            recognition_status
        )
        if not ok:
            errors.append(msg)

        # 5. Technical suggestion validation
        ok, msg = self.validate_technical_suggestion(
            opportunity.suggested_answer,
            expected_concepts
        )
        if not ok:
            errors.append(msg)

        # 6. Quality & Fluff
        combined_text = f"{opportunity.title} {opportunity.issue} {opportunity.why_it_matters} {opportunity.action}"
        ok, msg = self.validate_quality_and_fluff(combined_text)
        if not ok:
            errors.append(msg)

        # Action word limit check (<= 45 words)
        action_words = len(opportunity.action.split())
        if action_words > 45:
            errors.append(f"Action advice exceeds limit: {action_words} words (max 45)")

        return (len(errors) == 0), errors
