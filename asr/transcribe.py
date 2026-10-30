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
import wave
import json
import logging
from typing import List, Optional, Dict, Any, Union
from pathlib import Path

# Optional torch import for CUDA check
try:
    import torch
except ImportError:
    torch = None

try:
    from faster_whisper import WhisperModel
    HAS_FASTER_WHISPER = True
except ImportError:
    WhisperModel = None
    HAS_FASTER_WHISPER = False
from contracts.transcript import WordTiming, PassResult, TwoPassTranscription

logger = logging.getLogger("imaira_asr.transcribe")
if not logger.handlers:
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(logging.Formatter("[%(asctime)s] [%(levelname)s] %(message)s", datefmt="%H:%M:%S"))
    logger.addHandler(handler)
    logger.setLevel(logging.INFO)

def get_audio_duration_sec(audio_path: str) -> float:
    """Read duration directly from WAV header; falls back to soundfile/wave."""
    try:
        with wave.open(audio_path, "rb") as wf:
            frames = wf.getnframes()
            rate = wf.getframerate()
            return frames / float(rate)
    except Exception:
        # Fallback if audio is not WAV
        import av
        with av.open(audio_path) as container:
            stream = container.streams.audio[0]
            if stream.duration and stream.time_base:
                return float(stream.duration * stream.time_base)
            elif container.duration:
                return float(container.duration / av.time.AV_TIME_BASE)
    return 0.0

def load_glossary_terms(glossary_source: Union[str, List[str], Path]) -> List[str]:
    """Load terms from a list, json file, or plain text file."""
    if isinstance(glossary_source, list):
        return [str(t).strip() for t in glossary_source if str(t).strip()]
    path = Path(glossary_source)
    if not path.is_file():
        return []
    if path.suffix.lower() == ".json":
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
            if isinstance(data, list):
                return [str(t).strip() for t in data if str(t).strip()]
            elif isinstance(data, dict):
                # could be {"terms": [...]} or dictionary mapping
                terms = data.get("terms", list(data.keys()))
                return [str(t).strip() for t in terms if str(t).strip()]
    else:
        with open(path, "r", encoding="utf-8") as f:
            return [line.strip() for line in f if line.strip() and not line.startswith("#")]
    return []

class TwoPassTranscriber:
    """
    Two-pass ASR Transcriber conforming to the IMAIRA FairScore architecture:
    - Pass A: Domain-biased decode using question domain terms as hotwords.
    - Pass B: Unbiased baseline decode without hotwords or prompt hints.
    - Extracts word timestamps and confidence scores for every word.
    - Identifies candidate domain terms across both passes.
    """

    def __init__(
        self,
        model_size_or_path: str = "large-v3",
        device: str = "cuda",
        compute_type: str = "float16",
        download_root: Optional[str] = None
    ):
        self.model_size = model_size_or_path
        self.device = device
        self.compute_type = compute_type
        self.download_root = download_root

        logger.info(f"Initializing WhisperModel ({model_size_or_path}) on device='{device}', compute_type='{compute_type}'...")
        t0 = time.perf_counter()
        try:
            self.model = WhisperModel(
                model_size_or_path,
                device=device,
                compute_type=compute_type,
                download_root=download_root
            )
        except Exception as e:
            if device == "cuda" and compute_type == "float16":
                logger.warning(f"Failed to load on CUDA float16: {e}. Retrying with int8_float16...")
                self.compute_type = "int8_float16"
                self.model = WhisperModel(
                    model_size_or_path,
                    device="cuda",
                    compute_type="int8_float16",
                    download_root=download_root
                )
            else:
                raise
        load_time = time.perf_counter() - t0
        logger.info(f"WhisperModel loaded successfully in {load_time:.2f}s.")

    def _execute_pass(
        self,
        audio_path: str,
        hotwords: Optional[str] = None,
        initial_prompt: Optional[str] = None,
        pass_name: str = "pass"
    ) -> PassResult:
        """Execute a single transcription pass with word-level timestamps and confidence."""
        t0 = time.perf_counter()

        segments_gen, info = self.model.transcribe(
            audio_path,
            word_timestamps=True,
            hotwords=hotwords if hotwords else None,
            initial_prompt=initial_prompt if initial_prompt else None
        )

        words: List[WordTiming] = []
        text_segments: List[str] = []

        for seg in segments_gen:
            if seg.text:
                text_segments.append(seg.text.strip())
            if seg.words:
                for w in seg.words:
                    word_clean = w.word.strip()
                    if word_clean:
                        conf = float(w.probability) if hasattr(w, "probability") and w.probability is not None else 0.0
                        words.append(WordTiming(
                            word=word_clean,
                            start=round(float(w.start), 2),
                            end=round(float(w.end), 2),
                            conf=round(conf, 4),
                            corrected_from=None
                        ))

        latency = time.perf_counter() - t0
        full_text = " ".join(text_segments).strip()

        return PassResult(
            pass_name=pass_name,
            text=full_text,
            words=words,
            latency_sec=round(latency, 3),
            hotwords_used=hotwords
        )

    def extract_candidates(self, pass_a_text: str, pass_b_text: str, glossary: List[str]) -> List[str]:
        """Find any glossary domain term present in either Pass A or Pass B text."""
        import re
        candidates = set()
        a_norm = " " + " ".join(re.sub(r"[^\w\s]", " ", pass_a_text.lower()).split()) + " "
        b_norm = " " + " ".join(re.sub(r"[^\w\s]", " ", pass_b_text.lower()).split()) + " "

        for term in glossary:
            term_clean = term.strip()
            if not term_clean:
                continue
            t_norm = " " + " ".join(re.sub(r"[^\w\s]", " ", term_clean.lower()).split()) + " "
            if t_norm in a_norm or t_norm in b_norm:
                candidates.add(term_clean)

        return sorted(list(candidates))

    def transcribe(
        self,
        audio_path: str,
        domain_terms: Optional[List[str]] = None,
        question_text: Optional[str] = None,
        glossary: Optional[List[str]] = None,
        max_hotwords: int = 250
    ) -> TwoPassTranscription:
        """
        Run two-pass ASR decoding on the target audio.
        - Pass A uses limited domain terms for the question.
        - Pass B has no hotwords (unbiased baseline).
        - Both passes extract word timestamps and confidence scores.
        """
        if not os.path.exists(audio_path):
            raise FileNotFoundError(f"Audio file not found: {audio_path}")

        duration = get_audio_duration_sec(audio_path)
        logger.info(f"Transcribing '{audio_path}' (duration: {duration:.2f}s)...")

        # Prepare hotwords string for Pass A (limited to max_hotwords relevant domain terms)
        hotwords_str = None
        terms_to_use = []
        if domain_terms:
            terms_to_use.extend(domain_terms)
        if glossary and not domain_terms:
            terms_to_use.extend(glossary[:max_hotwords])
        if terms_to_use:
            # Join relevant unique terms
            seen = set()
            unique_terms = []
            for t in terms_to_use:
                t_str = str(t).strip()
                if t_str and t_str.lower() not in seen:
                    seen.add(t_str.lower())
                    unique_terms.append(t_str)
            hotwords_str = " ".join(unique_terms[:max_hotwords])

        # Pass A: Domain-aware decode
        logger.info(f"Running Pass A (hotwords: {len(unique_terms) if terms_to_use else 0} terms)...")
        pass_a = self._execute_pass(
            audio_path=audio_path,
            hotwords=hotwords_str,
            initial_prompt=question_text,
            pass_name="pass_a"
        )
        logger.info(f"Pass A finished in {pass_a.latency_sec}s: {len(pass_a.words)} words extracted.")

        # Pass B: Unbiased baseline decode
        logger.info("Running Pass B (unbiased, no hotwords)...")
        pass_b = self._execute_pass(
            audio_path=audio_path,
            hotwords=None,
            initial_prompt=None,
            pass_name="pass_b"
        )
        logger.info(f"Pass B finished in {pass_b.latency_sec}s: {len(pass_b.words)} words extracted.")

        # Candidate terms found in either pass
        all_glossary = terms_to_use if terms_to_use else (glossary if glossary else [])
        candidate_terms = self.extract_candidates(pass_a.text, pass_b.text, all_glossary)
        logger.info(f"Identified {len(candidate_terms)} candidate terms across passes: {candidate_terms}")

        total_latency = pass_a.latency_sec + pass_b.latency_sec
        rtf = total_latency / duration if duration > 0 else 0.0

        # Primary baseline transcript conforms to the hours 0-4 contract:
        # Default to Pass B words (unbiased) so that suspicious span detection in recover.py
        # detects anomalies compared to Pass A and recovers them with evidence.
        return TwoPassTranscription(
            transcript=pass_b.words,
            text=pass_b.text,
            pass_a=pass_a,
            pass_b=pass_b,
            candidate_terms=candidate_terms,
            audio_duration_sec=round(duration, 3),
            language="en",
            language_probability=1.0,
            rtf=round(rtf, 4),
            metadata={
                "model_size": self.model_size,
                "device": self.device,
                "compute_type": self.compute_type,
                "pass_a_latency_sec": pass_a.latency_sec,
                "pass_b_latency_sec": pass_b.latency_sec,
                "total_inference_sec": round(total_latency, 3),
                "hotwords_count": len(unique_terms) if terms_to_use else 0
            }
        )

# Module-level singleton instance for zero-overhead imports
_DEFAULT_TRANSCRIBER: Optional[TwoPassTranscriber] = None

def get_transcriber(
    model_size_or_path: str = "large-v3",
    device: str = "cuda",
    compute_type: str = "float16"
) -> TwoPassTranscriber:
    global _DEFAULT_TRANSCRIBER
    if _DEFAULT_TRANSCRIBER is None:
        _DEFAULT_TRANSCRIBER = TwoPassTranscriber(
            model_size_or_path=model_size_or_path,
            device=device,
            compute_type=compute_type
        )
    return _DEFAULT_TRANSCRIBER

def transcribe_audio(
    audio_path: str,
    domain_terms: Optional[List[str]] = None,
    question_text: Optional[str] = None,
    glossary: Optional[List[str]] = None,
    compute_type: str = "float16"
) -> TwoPassTranscription:
    """Convenience function running two-pass transcription with singleton model reuse."""
    transcriber = get_transcriber(compute_type=compute_type)
    return transcriber.transcribe(
        audio_path=audio_path,
        domain_terms=domain_terms,
        question_text=question_text,
        glossary=glossary
    )

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="IMAIRA FairScore Two-Pass ASR Transcriber")
    parser.add_argument("audio", help="Path to audio file")
    parser.add_argument("--hotwords", nargs="+", help="Relevant domain terms / hotwords for Pass A", default=[])
    parser.add_argument("--question", type=str, help="Question text prompt", default=None)
    parser.add_argument("--compute_type", type=str, default="float16", choices=["float16", "int8_float16"])
    parser.add_argument("--out", type=str, help="Output JSON path", default=None)
    args = parser.parse_args()

    res = transcribe_audio(
        audio_path=args.audio,
        domain_terms=args.hotwords,
        question_text=args.question,
        compute_type=args.compute_type
    )

    print("\n" + "=" * 60)
    print("TWO-PASS ASR TRANSCRIPTION RESULT")
    print("=" * 60)
    print(f"Audio Duration: {res.audio_duration_sec}s | RTF (Two-Pass): {res.rtf:.4f}")
    print(f"Pass A Latency: {res.pass_a.latency_sec}s | Words: {len(res.pass_a.words)}")
    print(f"Pass B Latency: {res.pass_b.latency_sec}s | Words: {len(res.pass_b.words)}")
    print(f"Candidates Found: {res.candidate_terms}")
    print("\n--- Pass A Text (Biased) ---")
    print(res.pass_a.text)
    print("\n--- Pass B Text (Unbiased Baseline) ---")
    print(res.pass_b.text)
    print("\n--- First 5 Word Timings with Confidence ---")
    for w in res.transcript[:5]:
        print(f"  [{w.start:.2f}s - {w.end:.2f}s] '{w.word}' (conf: {w.conf:.4f})")

    if args.out:
        with open(args.out, "w", encoding="utf-8") as f:
            json.dump(res.to_contract_dict(), f, indent=2)
        print(f"\nSaved contract JSON to {args.out}")
