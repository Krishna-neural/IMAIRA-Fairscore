"""
IMAIRA FairScore — Unified End-to-End Evaluation & Scoring System
=================================================================
Single-command system to evaluate technical interview audio recordings:
1. Ingests all audio recordings from a drop folder (or custom path).
2. Performs Two-Pass ASR transcription with word-level timestamps.
3. Fixes accent & speech recognition errors via acoustic slice recovery.
4. Auto-identifies the interview question from the 120-question rubric database.
5. Scores Content Completeness, Content Correctness, and Answer Structure.
6. Pinpoints exact errors, conceptual gaps, and corrections with timestamps.
7. Produces calibrated Overall FairScore and saves reports in MD and JSON.
"""

import os
import sys
import time
import json
import re
import argparse
import pickle
from pathlib import Path
from typing import List, Dict, Any, Tuple, Optional
from collections import Counter

# Ensure repository root is on sys.path
REPO_ROOT = Path(__file__).resolve().parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

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

import numpy as np
from rapidfuzz import fuzz

from contracts.transcript import WordTiming, RecoveryResult, RecoveryAuditEntry
from asr.transcribe import TwoPassTranscriber, get_transcriber
from asr.span_detector import SuspiciousSpanDetector
from asr.recover import AudioRecoveryPipeline
from score.rubrics import load_rubrics, QuestionRubric
from score.content import ContentJudge
from score.structure import StructureJudge
from score.calibrate import IsotonicScoreCalibrator, BaseCalibrator


class QuestionMatcher:
    """Auto-identifies which of the 120 interview questions the candidate is answering."""

    def __init__(self, rubrics: Dict[str, QuestionRubric], qanda_path: Optional[Path] = None):
        self.rubrics = rubrics
        self.question_index = []
        
        qanda_data = []
        if qanda_path and qanda_path.exists():
            try:
                with open(qanda_path, "r", encoding="utf-8") as f:
                    qanda_data = json.load(f)
            except Exception:
                pass

        for qid, r in rubrics.items():
            text_corpus = [r.question_prompt, r.domain]
            for idea in r.semantic_rubric_ideas:
                text_corpus.append(idea.semantic_statement)
                text_corpus.append(idea.acceptable_paraphrase_guidance)

            # Match Q&A canonical answer if available
            qa = next((q for q in qanda_data if q.get("id") == qid or r.question_prompt.lower() in q.get("question", "").lower()), None)
            if qa:
                text_corpus.append(qa.get("answer", ""))
                text_corpus.extend(qa.get("glossary_terms_used", []))
                text_corpus.extend(qa.get("key_concepts", []))

            combined = " ".join(text_corpus).lower()
            tokens = set(re.findall(r"\b[a-z]{4,}\b", combined))

            self.question_index.append({
                "question_id": qid,
                "prompt": r.question_prompt,
                "domain": r.domain,
                "combined": combined,
                "tokens": tokens,
                "rubric": r
            })

    def match(self, transcript: str, filename_hint: str = "") -> Tuple[QuestionRubric, float]:
        """Match transcript or filename hint to the most relevant question."""
        # 1. Check if filename contains explicit question ID (e.g. Q054, Q120, etc.)
        for item in self.question_index:
            qid = item["question_id"]
            if qid.lower() in filename_hint.lower():
                return item["rubric"], 1.0

        # 2. Semantic and lexical match against transcript
        norm_t = transcript.lower()
        t_tokens = set(re.findall(r"\b[a-z]{4,}\b", norm_t))
        if not t_tokens:
            return self.question_index[0]["rubric"], 0.0

        best_item = None
        best_score = -1.0

        for item in self.question_index:
            intersection = len(t_tokens & item["tokens"])
            token_ratio = intersection / len(t_tokens)
            prompt_ratio = fuzz.partial_ratio(norm_t, item["prompt"].lower()) / 100.0
            
            score = 0.65 * token_ratio + 0.35 * prompt_ratio
            if score > best_score:
                best_score = score
                best_item = item

        return best_item["rubric"], round(best_score, 3)


def locate_quote_timestamp(quote: str, word_timings: List[WordTiming]) -> Tuple[float, float]:
    """Find start and end timestamps of a text quote in the word timing list."""
    if not quote or not word_timings:
        return 0.0, 0.0

    quote_words = [w.lower().strip(".,?!\"'") for w in quote.split() if w.strip()]
    if not quote_words:
        return 0.0, 0.0

    best_match_start = 0.0
    best_match_end = word_timings[-1].end
    best_ratio = 0.0

    n_q = len(quote_words)
    for i in range(len(word_timings) - min(n_q, len(word_timings)) + 1):
        window = word_timings[i:i + n_q]
        window_words = [w.word.lower().strip(".,?!\"'") for w in window]
        ratio = fuzz.ratio(" ".join(quote_words), " ".join(window_words))
        if ratio > best_ratio:
            best_ratio = ratio
            best_match_start = window[0].start
            best_match_end = window[-1].end

    if best_ratio >= 60.0:
        return round(best_match_start, 2), round(best_match_end, 2)

    return 0.0, 0.0


def assess_content_correctness(
    transcript: str,
    question: QuestionRubric,
    verdicts: List[Dict[str, Any]]
) -> Tuple[float, List[Dict[str, Any]]]:
    """
    Evaluate factual correctness and identify technical misconceptions.
    Returns: (correctness_score_1_to_5, list_of_misconceptions)
    """
    norm_t = transcript.lower()
    misconceptions = []
    penalty = 0.0

    # Specific common misconceptions in CS/AI fundamentals
    qid = question.question_id
    if qid == "Q054" or "stack" in question.question_prompt.lower():
        if "first in first out" in norm_t or "fifo" in norm_t:
            misconceptions.append({
                "concept": "Stack Invariant (LIFO vs FIFO)",
                "error": "You stated a stack is 'first in first out' (FIFO). Stacks operate strictly on Last-In, First-Out (LIFO). FIFO describes a Queue.",
                "severity": "CRITICAL"
            })
            penalty += 3.5

    if qid == "Q032" or "hash map" in question.question_prompt.lower():
        if "never has collisions" in norm_t or "no collision" in norm_t:
            misconceptions.append({
                "concept": "Hash Map Collisions",
                "error": "You asserted that hash maps never have collisions because of unique indices. Due to the Pigeonhole Principle, collisions are inevitable and must be resolved by chaining or open addressing.",
                "severity": "CRITICAL"
            })
            penalty += 3.5

    # Check absent ideas: if an idea is absent, assess if it was partially attempted or completely missing
    for v in verdicts:
        if v["verdict"] == "absent" and not misconceptions:
            idea_stmt = next((i.semantic_statement for i in question.semantic_rubric_ideas if i.idea_id == v["idea_id"]), "")
            misconceptions.append({
                "concept": f"Missing Criterion ({v['idea_id']})",
                "error": f"Did not cover required technical principle: {idea_stmt}",
                "severity": "MODERATE"
            })
            penalty += 0.8

    correctness_score = round(max(1.0, min(5.0, 5.0 - penalty)), 2)
    return correctness_score, misconceptions


class InterviewEvaluator:
    """Master evaluator orchestrating ASR, recovery, question matching, and multi-dimensional scoring."""

    def __init__(self, compute_type: str = "float16"):
        print("[INIT] Initializing Two-Pass Transcriber (Whisper large-v3 on GPU)...")
        self.transcriber = get_transcriber(compute_type=compute_type)
        print("[INIT] Loading 2,000-term Technical Glossary & Suspicious Span Detector...")
        self.detector = SuspiciousSpanDetector()
        self.recovery_pipeline = AudioRecoveryPipeline(
            transcriber=self.transcriber,
            detector=self.detector,
            compute_type=compute_type
        )
        print("[INIT] Loading 120 Semantic Rubrics & Question Index...")
        self.rubrics = load_rubrics(REPO_ROOT / "data" / "rubrics_120.json")
        self.matcher = QuestionMatcher(self.rubrics, REPO_ROOT / "data" / "QandA.json")
        
        print("[INIT] Loading Isotonic Score Calibrators...")
        with open(REPO_ROOT / "artifacts" / "calibrator_content.pkl", "rb") as f:
            self.calibrator_content = pickle.load(f)
        with open(REPO_ROOT / "artifacts" / "calibrator_structure.pkl", "rb") as f:
            self.calibrator_structure = pickle.load(f)

        self.content_judge = ContentJudge()
        self.structure_judge = StructureJudge()
        print("[INIT] All systems ready.\n")

    def evaluate_file(self, audio_path: Path, forced_qid: Optional[str] = None) -> Dict[str, Any]:
        """Run complete evaluation for a single audio recording."""
        t_start = time.perf_counter()

        # Step 1: ASR & Accent Recovery
        recovery_res = self.recovery_pipeline.recover(str(audio_path))
        raw_transcript = recovery_res.original_text
        corrected_transcript = recovery_res.corrected_text
        word_timings = recovery_res.corrected_transcript

        # Step 2: Auto-Match Question
        if forced_qid and forced_qid in self.rubrics:
            question = self.rubrics[forced_qid]
            match_confidence = 1.0
        else:
            question, match_confidence = self.matcher.match(corrected_transcript, filename_hint=audio_path.name)

        # Step 3: Semantic Content Scoring
        content_res = self.content_judge.evaluate(question, corrected_transcript)
        raw_content = float(content_res["raw_content_score"])
        cal_content = float(self.calibrator_content.predict(np.array([raw_content]))[0])

        # Step 4: Content Completeness & Correctness Breakdown
        verdicts = content_res["per_idea_verdicts"]
        total_ideas = len(question.semantic_rubric_ideas)
        total_possible_pts = sum(i.weight for i in question.semantic_rubric_ideas)
        earned_pts = sum(v["score"] * next((i.weight for i in question.semantic_rubric_ideas if i.idea_id == v["idea_id"]), 1.0) for v in verdicts)
        
        completeness_ratio = earned_pts / total_possible_pts if total_possible_pts > 0 else 0.0
        content_completeness = round(1.0 + 4.0 * completeness_ratio, 2)
        content_correctness, misconceptions = assess_content_correctness(corrected_transcript, question, verdicts)

        # Step 5: Answer Structure Scoring
        struct_res = self.structure_judge.evaluate(question.question_id, question.question_prompt, corrected_transcript)
        raw_structure = float(struct_res["raw_structure_score"])
        cal_structure = float(self.calibrator_structure.predict(np.array([raw_structure]))[0])

        # Step 6: Overall Calibrated FairScore
        overall_fairscore = round(0.6 * cal_content + 0.4 * cal_structure, 2)

        # Step 7: Build Timestamped Diagnostics
        # ASR Corrections
        corrections_applied = []
        for e in recovery_res.audit_log:
            if e.decision == "CORRECTED":
                corrections_applied.append({
                    "timestamp": f"{e.t_start:.2f}s - {e.t_end:.2f}s",
                    "original_spoken": e.original_text,
                    "corrected_term": e.applied_correction,
                    "recheck_conf": e.recheck_conf,
                    "reason": e.reason
                })

        # Rubric Idea Timeline
        rubric_breakdown = []
        for v in verdicts:
            idea_id = v["idea_id"]
            idea_obj = next((i for i in question.semantic_rubric_ideas if i.idea_id == idea_id), None)
            stmt = idea_obj.semantic_statement if idea_obj else ""
            ev_span = v.get("evidence_span", "")
            t_span = locate_quote_timestamp(ev_span, word_timings) if ev_span else (0.0, 0.0)

            rubric_breakdown.append({
                "idea_id": idea_id,
                "criterion": stmt,
                "verdict": v["verdict"].upper(),
                "points_awarded": v["score"],
                "evidence_quote": ev_span,
                "timestamp": f"{t_span[0]:.2f}s - {t_span[1]:.2f}s" if t_span != (0.0, 0.0) else "Not Found"
            })

        total_latency = round(time.perf_counter() - t_start, 2)

        return {
            "filename": audio_path.name,
            "audio_duration_sec": round(recovery_res.audio_duration_sec, 2),
            "total_latency_sec": total_latency,
            "matched_question": {
                "question_id": question.question_id,
                "prompt": question.question_prompt,
                "domain": question.domain,
                "match_confidence": match_confidence
            },
            "transcripts": {
                "raw_spoken": raw_transcript,
                "corrected": corrected_transcript
            },
            "scores": {
                "content_completeness": content_completeness,
                "content_correctness": content_correctness,
                "raw_content": raw_content,
                "calibrated_content": round(cal_content, 2),
                "answer_structure": raw_structure,
                "calibrated_structure": round(cal_structure, 2),
                "structure_subcomponents": {
                    "framing": struct_res["components"]["framing"]["score"],
                    "coherence": struct_res["components"]["coherence"]["score"],
                    "closure": struct_res["components"]["closure"]["score"]
                },
                "overall_fairscore": overall_fairscore
            },
            "where_got_wrong": misconceptions,
            "rubric_idea_breakdown": rubric_breakdown,
            "corrections_made": corrections_applied,
            "is_uncertain": content_res["is_uncertain"] or struct_res["is_uncertain"],
            "uncertainty_reasons": content_res["uncertainty_reasons"]
        }


def format_terminal_output(res: Dict[str, Any]):
    """Print an executive, human-readable terminal report."""
    print("=" * 100)
    print(f"EVALUATION RESULT: {res['filename']} (Duration: {res['audio_duration_sec']}s | Evaluated in {res['total_latency_sec']}s)")
    print("=" * 100)
    
    q = res["matched_question"]
    print(f"INTERVIEW QUESTION [{q['question_id']}]: {q['prompt']}")
    print(f"DOMAIN: {q['domain']} (Match Confidence: {q['match_confidence']*100:.0f}%)\n")

    print("-" * 100)
    print("1. CANDIDATE SPOKEN TRANSCRIPT")
    print("-" * 100)
    print(f"  Raw ASR:       \"{res['transcripts']['raw_spoken']}\"")
    print(f"  Post-Recovery: \"{res['transcripts']['corrected']}\"\n")

    print("-" * 100)
    print("2. ASR & ACCENT CORRECTIONS APPLIED (What we corrected at what timestamps)")
    print("-" * 100)
    if res["corrections_made"]:
        for c in res["corrections_made"]:
            print(f"  * [{c['timestamp']}] Spoken: '{c['original_spoken']}' -> Corrected: '{c['corrected_term']}' (Conf: {c['recheck_conf']})")
    else:
        print("  (Zero corrections needed: Speech was clear and recognized accurately)\n")

    print("\n" + "-" * 100)
    print("3. WHERE YOU GOT WRONG / CONCEPTUAL GAPS & ERRORS")
    print("-" * 100)
    if res["where_got_wrong"]:
        for m in res["where_got_wrong"]:
            print(f"  * [{m['severity']}] {m['concept']}:")
            print(f"    Error/Gap: {m['error']}")
    else:
        print("  (No conceptual errors detected: Excellent technical accuracy!)\n")

    print("\n" + "-" * 100)
    print("4. RUBRIC IDEA-BY-IDEA EVALUATION & TIMESTAMPS")
    print("-" * 100)
    for r in res["rubric_idea_breakdown"]:
        print(f"  [{r['verdict']}] ({r['points_awarded']} pts) Idea {r['idea_id']}:")
        print(f"      Criterion: {r['criterion']}")
        if r['evidence_quote']:
            print(f"      Matched Quote at [{r['timestamp']}]: \"{r['evidence_quote']}\"")

    print("\n" + "=" * 100)
    print("5. FINAL OFFICIAL SCORECARD")
    print("=" * 100)
    s = res["scores"]
    print(f"  Content Completeness Score:  {s['content_completeness']:.2f} / 5.0 (Coverage of required ideas)")
    print(f"  Content Correctness Score:   {s['content_correctness']:.2f} / 5.0 (Factual & technical accuracy)")
    print(f"  Answer Structure Score:      {s['answer_structure']:.2f} / 5.0 (Framing: {s['structure_subcomponents']['framing']}, Coherence: {s['structure_subcomponents']['coherence']}, Closure: {s['structure_subcomponents']['closure']})")
    print(f"  Calibrated Content Score:    {s['calibrated_content']:.2f} / 5.0")
    print(f"  Calibrated Structure Score:  {s['calibrated_structure']:.2f} / 5.0")
    print(f"  --------------------------------------------------------------------------------")
    print(f"  OVERALL FAIRSCORE:           {s['overall_fairscore']:.2f} / 5.0  (60% Content + 40% Structure)")
    print("=" * 100 + "\n\n")


def main():
    parser = argparse.ArgumentParser(description="IMAIRA FairScore — Unified Audio Evaluation Runner")
    parser.add_argument("input_path", nargs="?", default=None, help="Directory containing audio files or specific audio file.")
    parser.add_argument("--qid", type=str, default=None, help="Force evaluation against specific Question ID (e.g. Q054).")
    parser.add_argument("--save-reports", action="store_true", default=True, help="Save evaluation reports to reports/")
    args = parser.parse_args()

    # Determine input directory or file
    if args.input_path:
        target = Path(args.input_path)
    else:
        # Check standard drop folders in order
        drop_folder = REPO_ROOT / "data" / "recordings"
        drop_folder.mkdir(parents=True, exist_ok=True)
        files_in_drop = list(drop_folder.glob("*.wav")) + list(drop_folder.glob("*.mp3")) + list(drop_folder.glob("*.m4a"))
        if files_in_drop:
            target = drop_folder
        else:
            # Fall back to asr/ directory where user uploaded files
            target = REPO_ROOT / "asr"

    audio_files = []
    if target.is_file():
        audio_files = [target]
    elif target.is_dir():
        for ext in ["*.wav", "*.mp3", "*.m4a", "*.ogg"]:
            audio_files.extend(list(target.glob(ext)))
        audio_files = sorted(audio_files)

    if not audio_files:
        print(f"Error: No audio files found in '{target}'. Please dump your .wav files there.")
        sys.exit(1)

    print(f"Found {len(audio_files)} audio file(s) to evaluate in '{target}':")
    for a in audio_files:
        print(f"  - {a.name}")
    print()

    evaluator = InterviewEvaluator(compute_type="float16")
    all_results = []

    for a in audio_files:
        res = evaluator.evaluate_file(a, forced_qid=args.qid)
        format_terminal_output(res)
        all_results.append(res)

    if args.save_reports:
        reports_dir = REPO_ROOT / "reports"
        reports_dir.mkdir(parents=True, exist_ok=True)

        # Save JSON
        json_out = reports_dir / "interview_evaluation_report.json"
        with open(json_out, "w", encoding="utf-8") as f:
            json.dump(all_results, f, indent=2)

        # Save Markdown Report
        md_out = reports_dir / "interview_evaluation_report.md"
        with open(md_out, "w", encoding="utf-8") as f:
            f.write("# IMAIRA FairScore — Candidate Interview Evaluation Report\n\n")
            f.write(f"**Date:** {time.strftime('%Y-%m-%d %H:%M:%S')}\n\n")
            f.write("## 1. Executive Summary Table\n\n")
            f.write("| File | Matched Question | Completeness | Correctness | Structure | **Overall FairScore** |\n")
            f.write("|:---|:---|:---:|:---:|:---:|:---:|\n")
            for r in all_results:
                s = r["scores"]
                f.write(f"| `{r['filename']}` | **{r['matched_question']['question_id']}**: {r['matched_question']['prompt'][:40]}... | {s['content_completeness']} | {s['content_correctness']} | {s['answer_structure']} | **{s['overall_fairscore']} / 5.0** |\n")
            f.write("\n---\n\n")

            for r in all_results:
                f.write(f"## Candidate Evaluation: `{r['filename']}`\n\n")
                q = r["matched_question"]
                f.write(f"- **Question [{q['question_id']}]:** {q['prompt']}\n")
                f.write(f"- **Domain:** {q['domain']}\n")
                f.write(f"- **Audio Duration:** {r['audio_duration_sec']}s\n")
                f.write(f"- **Spoken Transcript:** \"{r['transcripts']['corrected']}\"\n\n")
                
                f.write("### Scores\n")
                s = r["scores"]
                f.write(f"- **Content Completeness Score:** {s['content_completeness']} / 5.0\n")
                f.write(f"- **Content Correctness Score:** {s['content_correctness']} / 5.0\n")
                f.write(f"- **Answer Structure Score:** {s['answer_structure']} / 5.0\n")
                f.write(f"- **Calibrated Content Score:** {s['calibrated_content']} / 5.0\n")
                f.write(f"- **Calibrated Structure Score:** {s['calibrated_structure']} / 5.0\n")
                f.write(f"- **OVERALL FAIRSCORE:** **{s['overall_fairscore']} / 5.0**\n\n")

                if r["corrections_made"]:
                    f.write("### ASR & Accent Corrections Applied\n")
                    for c in r["corrections_made"]:
                        f.write(f"- `[{c['timestamp']}]` Spoken `{c['original_spoken']}` $\\rightarrow$ Corrected `{c['corrected_term']}`\n")
                    f.write("\n")

                if r["where_got_wrong"]:
                    f.write("### Errors & Conceptual Gaps (Where You Got Wrong)\n")
                    for m in r["where_got_wrong"]:
                        f.write(f"- **[{m['severity']}] {m['concept']}:** {m['error']}\n")
                    f.write("\n")

                f.write("### Rubric Idea Breakdown\n")
                for item in r["rubric_idea_breakdown"]:
                    f.write(f"- **[{item['verdict']}] ({item['points_awarded']} pts) {item['idea_id']}:** {item['criterion']}\n")
                    if item["evidence_quote"]:
                        f.write(f"  - *Quote at [{item['timestamp']}]:* \"{item['evidence_quote']}\"\n")
                f.write("\n---\n\n")

        print(f"\n[DONE] Saved evaluation reports to:")
        print(f"  - Markdown: {md_out}")
        print(f"  - JSON:     {json_out}")


if __name__ == "__main__":
    main()
