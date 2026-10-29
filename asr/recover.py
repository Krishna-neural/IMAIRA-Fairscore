import os
import sys

# Ensure repository root is on sys.path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

# Ensure Windows discovers CUDA and cuDNN DLLs located in the python environment
scripts_dir = os.path.dirname(sys.executable)
if os.path.isdir(scripts_dir):
    try:
        os.add_dll_directory(scripts_dir)
    except Exception:
        pass
    os.environ["PATH"] = scripts_dir + os.pathsep + os.environ.get("PATH", "")

torch_lib = os.path.join(os.path.dirname(scripts_dir), "Lib", "site-packages", "torch", "lib")
if os.path.isdir(torch_lib):
    try:
        os.add_dll_directory(torch_lib)
    except Exception:
        pass
    os.environ["PATH"] = torch_lib + os.pathsep + os.environ.get("PATH", "")

import time
import copy
import logging
from typing import List, Optional, Dict, Any, Tuple
from pathlib import Path

from rapidfuzz import fuzz
from faster_whisper import WhisperModel
from faster_whisper.audio import decode_audio

from contracts.transcript import (
    WordTiming,
    SuspiciousSpan,
    TwoPassTranscription,
    RecoveryAuditEntry,
    RecoveryResult
)
from asr.transcribe import TwoPassTranscriber, get_transcriber
from asr.span_detector import SuspiciousSpanDetector, clean_text, STOPWORDS

logger = logging.getLogger("imaira_asr.recover")
if not logger.handlers:
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(logging.Formatter("[%(asctime)s] [%(levelname)s] %(message)s", datefmt="%H:%M:%S"))
    logger.addHandler(handler)
    logger.setLevel(logging.INFO)

class AudioRecoveryPipeline:
    """
    Evidence-checked ASR Recovery and Abstention Engine:
    1. Receives word-level transcript and suspicious spans from detector.
    2. Slices exact audio sub-segments in memory.
    3. Re-decodes each span with candidate hotword biasing and repetition penalty.
    4. Evaluates acoustic support:
       - SUPPORTED -> updates transcript, sets 'corrected_from', records audit entry.
       - NOT SUPPORTED -> abstains, flags 'uncertain', leaves original text unchanged.
    5. Preserves full audit trail (original + corrected transcripts stored).
    """

    def __init__(
        self,
        transcriber: Optional[TwoPassTranscriber] = None,
        detector: Optional[SuspiciousSpanDetector] = None,
        compute_type: str = "float16",
        pad_sec: float = 0.60,
        min_recheck_conf: float = 0.35,
        term_match_threshold: float = 88.0
    ):
        self.transcriber = transcriber or get_transcriber(compute_type=compute_type)
        self.model: WhisperModel = self.transcriber.model
        self.detector = detector or SuspiciousSpanDetector()
        self.pad_sec = pad_sec
        self.min_recheck_conf = min_recheck_conf
        self.term_match_threshold = term_match_threshold

    def recheck_span(
        self,
        audio_data: Any,
        duration_sec: float,
        span: SuspiciousSpan
    ) -> Tuple[bool, str, Optional[float], str]:
        """
        Re-decode a single suspicious audio slice and determine if the audio supports the candidate.
        Returns: (supported: bool, redecoded_text: str, recheck_conf: float, reason: str)
        """
        t_start = max(0.0, span.t_start - self.pad_sec)
        t_end = min(duration_sec, span.t_end + self.pad_sec)

        idx_start = int(t_start * 16000)
        idx_end = int(t_end * 16000)
        audio_slice = audio_data[idx_start:idx_end]

        if len(audio_slice) < 1600:
            return False, "", None, "slice_too_short"

        try:
            segments, _ = self.model.transcribe(
                audio_slice,
                hotwords=span.candidate_term,
                language="en",
                condition_on_previous_text=False,
                repetition_penalty=1.2,
                without_timestamps=True
            )
            redec_segments = list(segments)
        except Exception as e:
            logger.warning(f"Error re-decoding slice {span.span_id}: {e}")
            return False, "", None, f"redecode_error: {str(e)}"

        redec_text = " ".join(s.text.strip() for s in redec_segments).strip()
        redec_clean = clean_text(redec_text)
        cand_clean = clean_text(span.candidate_term)

        # Conservative Verification:
        # Check that all non-stopword tokens in candidate are present in the re-decoded slice
        cand_tokens = [tok for tok in cand_clean.split() if tok not in STOPWORDS]
        redec_tokens = redec_clean.split()

        def token_match(c_tok: str, r_toks: List[str]) -> bool:
            c_stem = c_tok.rstrip('s')
            return any(
                t == c_tok or (len(c_stem) > 2 and t.rstrip('s') == c_stem) or fuzz.ratio(c_tok, t) >= 82.0
                for t in r_toks
            )

        tokens_present = all(token_match(tok, redec_tokens) for tok in cand_tokens) if cand_tokens else False
        compound_match = len(cand_clean) > 3 and cand_clean.replace(" ", "") in redec_clean.replace(" ", "")
        phrase_present = compound_match or (cand_clean in redec_clean) or (
            fuzz.partial_ratio(cand_clean, redec_clean) >= self.term_match_threshold and tokens_present
        )

        if phrase_present and (tokens_present or compound_match):
            return True, redec_text, 0.92, "audio_supported"

        return False, redec_text, None, "audio_not_supported"

    def recover(
        self,
        audio_path: str,
        two_pass_result: Optional[TwoPassTranscription] = None,
        spans: Optional[List[SuspiciousSpan]] = None
    ) -> RecoveryResult:
        """
        Execute conservative recovery and abstention over the suspicious spans.
        """
        t0 = time.perf_counter()

        # If two_pass_result not provided, run two-pass transcription
        if two_pass_result is None:
            logger.info(f"Running two-pass ASR for {audio_path}...")
            two_pass_result = self.transcriber.transcribe(audio_path)

        duration = two_pass_result.audio_duration_sec
        audio_data = decode_audio(audio_path)

        # Detect suspicious spans if not pre-computed
        if spans is None:
            spans = self.detector.detect_spans(
                transcript=two_pass_result.transcript,
                pass_a_transcript=two_pass_result.pass_a.words,
                candidate_terms=two_pass_result.candidate_terms
            )

        logger.info(f"Starting audio re-checking for {len(spans)} suspicious spans...")

        # Deep copy original transcript to preserve baseline audit
        original_words: List[WordTiming] = [
            WordTiming(
                word=w.word,
                start=w.start,
                end=w.end,
                conf=w.conf,
                corrected_from=None
            )
            for w in two_pass_result.transcript
        ]
        corrected_words: List[WordTiming] = copy.deepcopy(original_words)

        audit_log: List[RecoveryAuditEntry] = []
        corrected_count = 0
        abstained_count = 0

        # Process spans in REVERSE chronological order to maintain stable indices during replacement
        sorted_spans = sorted(spans, key=lambda s: s.start_idx, reverse=True)

        for span in sorted_spans:
            supported, redec_text, recheck_conf, reason = self.recheck_span(
                audio_data=audio_data,
                duration_sec=duration,
                span=span
            )

            if supported:
                # Conservative Correction
                decision = "CORRECTED"
                corrected_count += 1
                logger.info(f"CORRECTED span [{span.t_start:.2f}s - {span.t_end:.2f}s]: '{span.original_text}' -> '{span.candidate_term}'")

                # Generate replacement WordTiming tokens for the candidate term
                candidate_words = span.candidate_term.split()
                n_new = len(candidate_words)
                time_span = max(0.01, span.t_end - span.t_start)
                step = time_span / n_new

                replacement_tokens = []
                orig_words_list = span.original_text.split()

                for i, cw in enumerate(candidate_words):
                    w_start = round(span.t_start + (i * step), 2)
                    w_end = round(span.t_start + ((i + 1) * step), 2)
                    orig_from = orig_words_list[min(i, len(orig_words_list) - 1)]
                    replacement_tokens.append(WordTiming(
                        word=cw,
                        start=w_start,
                        end=w_end,
                        conf=round(recheck_conf if recheck_conf is not None else span.avg_conf, 4),
                        corrected_from=orig_from
                    ))

                # Splice replacement into corrected_words
                corrected_words[span.start_idx : span.end_idx] = replacement_tokens
                applied = span.candidate_term

            else:
                # Conservative Abstention
                decision = "ABSTAINED"
                abstained_count += 1
                logger.info(f"ABSTAINED span [{span.t_start:.2f}s - {span.t_end:.2f}s]: kept '{span.original_text}' (candidate was '{span.candidate_term}', reason: {reason})")
                applied = None

            audit_log.append(RecoveryAuditEntry(
                span_id=span.span_id,
                t_start=round(span.t_start, 2),
                t_end=round(span.t_end, 2),
                original_text=span.original_text,
                candidate_term=span.candidate_term,
                redecoded_text=redec_text,
                decision=decision,
                reason=reason,
                original_conf=round(span.avg_conf, 4),
                recheck_conf=round(recheck_conf, 4) if recheck_conf is not None else None,
                applied_correction=applied
            ))

        # Re-sort audit log chronologically
        audit_log.sort(key=lambda e: e.t_start)

        orig_text = " ".join(w.word for w in original_words).strip()
        corr_text = " ".join(w.word for w in corrected_words).strip()
        elapsed = time.perf_counter() - t0

        return RecoveryResult(
            original_transcript=original_words,
            corrected_transcript=corrected_words,
            original_text=orig_text,
            corrected_text=corr_text,
            audit_log=audit_log,
            spans_detected=len(spans),
            spans_corrected=corrected_count,
            spans_abstained=abstained_count,
            audio_duration_sec=round(duration, 3),
            recovery_latency_sec=round(elapsed, 3)
        )

# Module-level convenience function
def recover_transcript(
    audio_path: str,
    two_pass_result: Optional[TwoPassTranscription] = None,
    compute_type: str = "float16",
    glossary_path: str = "data/glossary.csv"
) -> RecoveryResult:
    """Convenience functional wrapper for end-to-end evidence-checked recovery."""
    detector = SuspiciousSpanDetector(glossary_path=glossary_path)
    pipeline = AudioRecoveryPipeline(detector=detector, compute_type=compute_type)
    return pipeline.recover(audio_path=audio_path, two_pass_result=two_pass_result)

if __name__ == "__main__":
    import argparse
    import json

    parser = argparse.ArgumentParser(description="IMAIRA FairScore Audio Recovery Pipeline")
    parser.add_argument("audio", help="Path to audio file")
    parser.add_argument("--compute_type", default="float16", choices=["float16", "int8_float16"])
    parser.add_argument("--out", help="Save output JSON result", default=None)
    args = parser.parse_args()

    result = recover_transcript(args.audio, compute_type=args.compute_type)

    print("\n" + "=" * 60)
    print("AUDIO RECOVERY AND ABSTENTION AUDIT REPORT")
    print("=" * 60)
    print(f"Audio Duration: {result.audio_duration_sec}s | Recovery Latency: {result.recovery_latency_sec}s")
    print(f"Spans Evaluated: {result.spans_detected} | Corrected: {result.spans_corrected} | Abstained: {result.spans_abstained}")

    print("\n--- AUDIT LOG ENTRIES ---")
    for entry in result.audit_log:
        status_symbol = "[CORRECTED]" if entry.decision == "CORRECTED" else "[ABSTAINED]"
        print(f"{status_symbol} [{entry.t_start}s - {entry.t_end}s] '{entry.original_text}' -> Candidate: '{entry.candidate_term}'")
        print(f"    Decision: {entry.decision} ({entry.reason}) | Re-decoded Slice: '{entry.redecoded_text}'")

    print("\n--- ORIGINAL TRANSCRIPT ---")
    print(result.original_text)
    print("\n--- CORRECTED TRANSCRIPT ---")
    print(result.corrected_text)

    if args.out:
        with open(args.out, "w", encoding="utf-8") as f:
            json.dump(result.to_contract_dict(), f, indent=2)
        print(f"\nSaved contract JSON to {args.out}")
