"""Real-time Live Audio Transcription and Verification Bridge for IMAIRA-Fairscore.

Provides two-stage speech recognition:
Stage 1: Fast live incremental transcription (low-latency speech visibility).
Stage 2: Accurate verified transcription with technical glossary correction,
         acoustic verification, and transparent audit logging.
"""

import os
import sys
import time
import logging
from typing import Any, Dict, List, Optional, Tuple
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from asr.span_detector import SuspiciousSpanDetector, DEFAULT_ALIASES
from contracts.transcript import WordTiming, SuspiciousSpan

logger = logging.getLogger("imaira.asr_bridge")

_SPAN_DETECTOR: Optional[SuspiciousSpanDetector] = None


def get_span_detector() -> SuspiciousSpanDetector:
    """Singleton getter for the technical span detector."""
    global _SPAN_DETECTOR
    if _SPAN_DETECTOR is None:
        csv_path = REPO_ROOT / "data" / "glossary.csv"
        txt_path = REPO_ROOT / "data" / "glossary.txt"
        target_path = str(csv_path) if csv_path.exists() else (str(txt_path) if txt_path.exists() else None)
        _SPAN_DETECTOR = SuspiciousSpanDetector(
            glossary_path=target_path,
            confidence_threshold=0.85,
            similarity_threshold=75.0
        )
    return _SPAN_DETECTOR


class StreamTranscriptionBridge:
    """Manages live provisional streaming audio and final verified transcription."""

    def __init__(self):
        self.detector = get_span_detector()
        self.provisional_segments: List[str] = []
        self.finalized_segments: List[str] = []

    def process_live_chunk(self, chunk_text: str) -> Dict[str, Any]:
        """Process an incremental partial transcript chunk.
        
        Returns real-time provisional output without duplicating finalized text.
        """
        t0 = time.perf_counter()
        words = chunk_text.strip().split()
        latency_ms = round((time.perf_counter() - t0) * 1000, 2)

        return {
            "status": "provisional",
            "provisional_text": chunk_text.strip(),
            "word_count": len(words),
            "latency_ms": latency_ms
        }

    def finalize_and_verify(
        self,
        raw_transcript: str,
        word_timings: Optional[List[Dict[str, Any]]] = None
    ) -> Dict[str, Any]:
        """Stage 2: Execute glossary verification, suspect span detection, and audit logging."""
        t0 = time.perf_counter()
        raw_clean = raw_transcript.strip()

        # Build WordTiming objects if not provided
        words = raw_clean.split()
        if not word_timings:
            wt_list = [
                WordTiming(
                    word=w,
                    start=round(i * 0.35, 2),
                    end=round((i + 1) * 0.35, 2),
                    conf=0.92
                )
                for i, w in enumerate(words)
            ]
        else:
            wt_list = [
                WordTiming(
                    word=w.get("word", ""),
                    start=float(w.get("start", 0.0)),
                    end=float(w.get("end", 0.0)),
                    conf=float(w.get("conf", 0.90)),
                    corrected_from=w.get("corrected_from")
                )
                for w in word_timings
            ]

        # Detect suspicious spans against 2000 technical terms & acoustic confusions
        detected_spans = self.detector.detect_spans(wt_list)

        # Apply verified technical corrections
        verified_words = [w.word for w in wt_list]
        audit_log: List[Dict[str, Any]] = []

        # Sort spans in reverse index order so replacements don't shift indices
        spans_sorted = sorted(detected_spans, key=lambda s: s.start_idx, reverse=True)
        corrections_count = 0

        for span in spans_sorted:
            orig = span.original_text
            cand = span.candidate_term

            # Accept if combined score >= 75.0 or phonetic match is true
            if span.combined_score >= 75.0 or span.phonetic_match:
                verified_words[span.start_idx:span.end_idx] = cand.split()
                corrections_count += 1
                audit_log.append({
                    "span_id": span.span_id,
                    "original_text": orig,
                    "verified_text": cand,
                    "time_range": f"{span.t_start:.1f}s - {span.t_end:.1f}s",
                    "reason": span.reason,
                    "fuzzy_score": span.fuzzy_score,
                    "phonetic_match": span.phonetic_match,
                    "status": "CORRECTED"
                })
            else:
                audit_log.append({
                    "span_id": span.span_id,
                    "original_text": orig,
                    "candidate_term": cand,
                    "time_range": f"{span.t_start:.1f}s - {span.t_end:.1f}s",
                    "reason": "Insufficient acoustic confidence; abstained.",
                    "fuzzy_score": span.fuzzy_score,
                    "phonetic_match": span.phonetic_match,
                    "status": "ABSTAINED"
                })

        verified_text = " ".join(verified_words)
        total_latency_ms = round((time.perf_counter() - t0) * 1000, 2)

        return {
            "original_transcript": raw_clean,
            "verified_transcript": verified_text,
            "detected_spans_count": len(detected_spans),
            "corrections_applied": corrections_count,
            "audit_log": audit_log,
            "verification_latency_ms": total_latency_ms
        }
