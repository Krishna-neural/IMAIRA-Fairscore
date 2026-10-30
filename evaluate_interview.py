"""
IMAIRA FairScore — Unified End-to-End Evaluation & Scoring System
=================================================================
Single-command system to evaluate technical interview audio recordings:
1. Ingests all audio recordings from a drop folder (data/recordings/ or asr/).
2. Performs Two-Pass ASR transcription with word-level timestamps.
3. Fixes accent & speech recognition errors via acoustic slice recovery.
4. Auto-identifies the interview question from the 120-question rubric database.
5. Employs Gemini LLM Reasoning Engine (grounded in data/QandA.json and rubrics)
   for precision error detection, misconception diagnosis, and actionable feedback.
6. Scores Content Completeness, Content Correctness, and Answer Structure.
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
from score.rubrics import load_rubrics, QuestionRubric, SemanticRubricIdea
from score.calibrate import (
    IsotonicScoreCalibrator,
    BaseCalibrator,
    RidgeScoreCalibrator,
    IdentityCalibrator
)
from score.llm_judge import LLMEvaluationEngine
from score.evidence_models import (
    load_evidence_question_bank,
    question_rubric_to_evidence_question,
    EvidenceScorecard,
    MisconceptionItem
)
from score.evidence_scorer import DeterministicEvidenceScorer

# Ensure unpickling works seamlessly across all modules and scripts
import score.calibrate
for attr in ["IsotonicScoreCalibrator", "BaseCalibrator", "RidgeScoreCalibrator", "IdentityCalibrator"]:
    if hasattr(score.calibrate, attr):
        setattr(sys.modules["__main__"], attr, getattr(score.calibrate, attr))


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

            # Boost if exact domain terms match
            if "process" in norm_t and "thread" in norm_t and item["question_id"] == "Q084":
                score += 0.50
            elif "dependency injection" in norm_t and item["question_id"] == "Q120":
                score += 0.50
            elif "continuous integration" in norm_t and item["question_id"] == "Q109":
                score += 0.50
            elif "stack" in norm_t and item["question_id"] in {"Q035", "Q054"}:
                score += 0.50
            elif "hash map" in norm_t and item["question_id"] == "Q032":
                score += 0.50
            elif "encrypt" in norm_t and item["question_id"] == "ENG121":
                score += 0.60
            elif "symmetric" in norm_t and item["question_id"] == "ENG121":
                score += 0.60

            if score > best_score:
                best_score = score
                best_item = item

        confidence = min(1.0, max(0.1, best_score))
        return best_item["rubric"], confidence


class InterviewEvaluator:
    """Master evaluator orchestrating ASR, recovery, question matching, and LLM-grounded scoring."""

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
        print("[INIT] Loading 120 Semantic Rubrics & 120 Q&A Ground-Truth Models...")
        self.rubrics = load_rubrics(REPO_ROOT / "data" / "rubrics_120.json")
        qanda_path = REPO_ROOT / "data" / "QandA.json"
        if qanda_path.exists():
            try:
                with open(qanda_path, "r", encoding="utf-8") as f:
                    qa_list = json.load(f)
                for item in qa_list:
                    qid = item.get("id")
                    if qid and qid not in self.rubrics:
                        ideas = []
                        for idx, idea_data in enumerate(item.get("semantic_rubric_ideas", [])):
                            statement = idea_data.get("semantic_statement", "").strip()
                            if len(statement.split()) < 5:
                                statement = f"Explains the core technical architecture and mechanisms of {item.get('question')}."
                            ideas.append(
                                SemanticRubricIdea(
                                    idea_id=idea_data.get("idea_id", f"{qid}_IDEA_{idx+1}"),
                                    semantic_statement=statement,
                                    required=idea_data.get("required", True),
                                    weight=float(idea_data.get("weight", 1.0)),
                                    acceptable_paraphrase_guidance=idea_data.get("acceptable_paraphrase_guidance", "Accepts standard technical descriptions and valid engineering implementations.")
                                )
                            )
                        if not ideas:
                            ideas.append(
                                SemanticRubricIdea(
                                    idea_id=f"{qid}_IDEA_1",
                                    semantic_statement=f"Explains {item.get('question')} accurately covering key concepts: {', '.join(item.get('key_concepts', []))}.",
                                    required=True,
                                    weight=1.0,
                                    acceptable_paraphrase_guidance="Candidate explains core mechanisms and architectural principles."
                                )
                            )
                        self.rubrics[qid] = QuestionRubric(
                            question_id=qid,
                            question_prompt=item.get("question", ""),
                            domain=item.get("subcategory", item.get("category", "Software Engineering")),
                            semantic_rubric_ideas=ideas
                        )
            except Exception as e:
                print(f"[WARN] Error loading QandA into rubrics: {e}")

        # Load evidence question bank for structured rubrics
        try:
            ev_bank = load_evidence_question_bank()
            for qid, qdef in ev_bank.items():
                if qid not in self.rubrics:
                    ideas = [
                        SemanticRubricIdea(
                            idea_id=c.criterion_id,
                            semantic_statement=c.description,
                            required=True,
                            weight=c.max_points,
                            acceptable_paraphrase_guidance=", ".join(c.acceptable_alternatives or ["Standard technical terminology"])
                        )
                        for c in qdef.rubric
                    ]
                    self.rubrics[qid] = QuestionRubric(
                        question_id=qid,
                        question_prompt=qdef.question,
                        domain=qdef.domain,
                        semantic_rubric_ideas=ideas
                    )
        except Exception as e:
            print(f"[WARN] Error loading evidence question bank: {e}")

        print(f"[INIT] Total Knowledge Bank: {len(self.rubrics)} questions indexed.")
        self.matcher = QuestionMatcher(self.rubrics, qanda_path)
        
        print("[INIT] Loading Isotonic Score Calibrators...")
        with open(REPO_ROOT / "artifacts" / "calibrator_content.pkl", "rb") as f:
            self.calibrator_content = pickle.load(f)
        with open(REPO_ROOT / "artifacts" / "calibrator_structure.pkl", "rb") as f:
            self.calibrator_structure = pickle.load(f)

        print("[INIT] Initializing Evidence-Grounded Gemini LLM Reasoning Engine...")
        self.llm_engine = LLMEvaluationEngine()
        self.evidence_scorer = DeterministicEvidenceScorer()
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

        # Step 3: LLM Reasoning & Grounded Evaluation (Powered by Gemini + QandA.json)
        llm_res = self.llm_engine.evaluate(
            question=question,
            raw_transcript=raw_transcript,
            corrected_transcript=corrected_transcript,
            word_timings=word_timings
        )

        content_completeness = float(llm_res["content_completeness"])
        content_correctness = float(llm_res["content_correctness"])
        raw_structure = float(llm_res["structure_score"])

        # Enforce structure score scaling bounds (1.0 to 5.0)
        if 0.0 < raw_structure <= 1.0:
            raw_structure = 1.0 + 4.0 * raw_structure
        elif raw_structure <= 0.0:
            raw_structure = 1.0
        raw_structure = max(1.0, min(5.0, raw_structure))

        # Build QuestionDefinition and EvidenceScorecard
        q_def = question_rubric_to_evidence_question(question)
        raw_evals = []
        for idea_res in llm_res.get("rubric_idea_breakdown", []):
            v = idea_res["verdict"].lower()
            if v == "covered":
                st = "satisfied"
            elif v == "partial":
                st = "partially_satisfied"
            else:
                st = "missing"
            raw_evals.append({
                "criterion_id": idea_res["idea_id"],
                "status": st,
                "evidence": [{"text": idea_res.get("evidence_quote", ""), "source_start": 0, "source_end": len(idea_res.get("evidence_quote", ""))}] if idea_res.get("evidence_quote") else [],
                "reason": idea_res.get("reasoning", "")
            })

        misc_items = [
            MisconceptionItem(
                concept=m.get("concept", "Concept"),
                severity=m.get("severity", "MODERATE"),
                error_explanation=m.get("error", ""),
                candidate_quote=m.get("candidate_quote")
            )
            for m in llm_res.get("where_got_wrong", [])
        ]

        scorecard = self.evidence_scorer.calculate_scorecard(
            question=q_def,
            raw_evidence_evaluations=raw_evals,
            misconceptions=misc_items,
            transcript_text=corrected_transcript,
            raw_structure_scores=llm_res.get("structure_subcomponents", {}),
            calibrator_content=self.calibrator_content,
            calibrator_structure=self.calibrator_structure
        )

        cal_content = scorecard.calibrated_content_5pt
        cal_structure = scorecard.calibrated_structure_5pt
        overall_fairscore = scorecard.overall_fairscore_5pt

        # Step 6: Build Timestamped Diagnostics
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

        total_latency = round(time.perf_counter() - t_start, 2)

        return {
            "filename": audio_path.name,
            "audio_duration_sec": round(recovery_res.audio_duration_sec, 2),
            "total_latency_sec": total_latency,
            "model_used": llm_res.get("model_used", "gemini-3.8-flash"),
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
                "calibrated_content": round(cal_content, 2),
                "answer_structure": raw_structure,
                "calibrated_structure": round(cal_structure, 2),
                "structure_subcomponents": llm_res["structure_subcomponents"],
                "overall_fairscore": overall_fairscore
            },
            "where_got_wrong": llm_res["where_got_wrong"],
            "rubric_idea_breakdown": llm_res["rubric_idea_breakdown"],
            "actionable_feedback": llm_res.get("actionable_feedback", []),
            "corrections_made": corrections_applied,
            "evidence_scorecard": scorecard.model_dump()
        }


def format_terminal_output(res: Dict[str, Any]):
    """Print an executive, human-readable terminal report."""
    print("=" * 100)
    print(f"EVALUATION RESULT: {res['filename']} (Duration: {res['audio_duration_sec']}s | Evaluated in {res['total_latency_sec']}s)")
    print(f"REASONING ENGINE: Gemini LLM [{res.get('model_used', 'gemini-3.8-flash')}] grounded in QandA.json")
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
            if m.get("candidate_quote"):
                print(f"    Your Quote: \"{m['candidate_quote']}\"")
    else:
        print("  (No conceptual errors detected: Excellent technical accuracy!)\n")

    if res.get("actionable_feedback"):
        print("\n" + "-" * 100)
        print("4. TOP ACTIONABLE IMPROVEMENT RECOMMENDATIONS")
        print("-" * 100)
        for fb in res["actionable_feedback"]:
            ts_str = f" at [{fb['timestamp']}]" if fb.get("timestamp") else ""
            print(f"  [Priority {fb['priority']}]{ts_str} {fb['issue']}")
            print(f"    Why it matters: {fb['why_it_matters']}")
            print(f"    Concrete Action: {fb['improvement_action']}")
            if fb.get("example_sentence"):
                print(f"    Example to adapt: \"{fb['example_sentence']}\"")
            print()

    print("\n" + "-" * 100)
    print("5. RUBRIC IDEA-BY-IDEA EVALUATION & TIMESTAMPS")
    print("-" * 100)
    for r in res["rubric_idea_breakdown"]:
        print(f"  [{r['verdict']}] ({r['points_awarded']} pts) Idea {r['idea_id']}:")
        print(f"      Criterion: {r['criterion']}")
        if r.get('reasoning'):
            print(f"      Reasoning: {r['reasoning']}")
        if r.get('evidence_quote'):
            print(f"      Matched Quote at [{r['timestamp']}]: \"{r['evidence_quote']}\"")

    print("\n" + "=" * 100)
    print("6. FINAL OFFICIAL SCORECARD")
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

    AUDIO_EXTENSIONS = {".wav", ".m4a", ".mp3", ".ogg", ".flac", ".aac", ".webm", ".wma"}

    # Determine input directory or file
    if args.input_path:
        target = Path(args.input_path)
        scan_source_name = f"user path: {target}"
    else:
        # PRIORITY 1: Always scan the asr/ folder first where recordings are dumped
        asr_folder = REPO_ROOT / "asr"
        files_in_asr = [f for f in asr_folder.iterdir() if f.is_file() and f.suffix.lower() in AUDIO_EXTENSIONS] if asr_folder.exists() else []

        if files_in_asr:
            target = asr_folder
            scan_source_name = f"primary ASR drop folder: {asr_folder}"
        else:
            # Fallback to data/recordings/
            drop_folder = REPO_ROOT / "data" / "recordings"
            drop_folder.mkdir(parents=True, exist_ok=True)
            target = drop_folder
            scan_source_name = f"fallback recordings folder: {drop_folder}"

    audio_files = []
    if target.is_file():
        if target.suffix.lower() in AUDIO_EXTENSIONS:
            audio_files = [target]
    elif target.is_dir():
        for f in target.iterdir():
            if f.is_file() and f.suffix.lower() in AUDIO_EXTENSIONS:
                audio_files.append(f)
        audio_files = sorted(audio_files, key=lambda p: p.name.lower())

    print("=" * 100)
    print("IMAIRA FAIRSCORE — AUDIO RECORDING SCANNER")
    print("=" * 100)
    print(f"Target Directory: {target.resolve()}")
    print(f"Source:           {scan_source_name}")
    print(f"Total Found:      {len(audio_files)} recording(s)")
    print("=" * 100)

    if not audio_files:
        print(f"\n[ERROR] No supported audio files found in '{target}'. Please dump your recordings there.")
        print(f"Supported formats: {', '.join(sorted(AUDIO_EXTENSIONS))}")
        sys.exit(1)

    for idx, a in enumerate(audio_files, start=1):
        size_mb = a.stat().st_size / (1024 * 1024)
        print(f"  [{idx:02d}/{len(audio_files):02d}] {a.name:<40} ({size_mb:.2f} MB)")
    print("=" * 100 + "\n")

    evaluator = InterviewEvaluator(compute_type="float16")
    all_results = []
    total_count = len(audio_files)

    for idx, a in enumerate(audio_files, start=1):
        print("\n" + "#" * 100)
        print(f"# >>> [RECORDING {idx}/{total_count}] Starting evaluation: {a.name}")
        print("#" * 100 + "\n")
        try:
            res = evaluator.evaluate_file(a, forced_qid=args.qid)
            format_terminal_output(res)
            all_results.append(res)
        except Exception as ex:
            print(f"\n[ERROR] Failed to evaluate '{a.name}': {ex}")
            import traceback
            traceback.print_exc()
            continue

    print("\n" + "=" * 100)
    print(f"BATCH EVALUATION COMPLETED: {len(all_results)} of {total_count} RECORDINGS SUCCESSFULLY EVALUATED")
    print("=" * 100)
    print(f"{'File':<35} | {'Question':<8} | {'Completeness':<12} | {'Correctness':<11} | {'Structure':<10} | {'Overall FairScore'}")
    print("-" * 100)
    for r in all_results:
        s = r["scores"]
        print(f"{r['filename']:<35} | {r['matched_question']['question_id']:<8} | {s['content_completeness']:<12.2f} | {s['content_correctness']:<11.2f} | {s['answer_structure']:<10.2f} | {s['overall_fairscore']:.2f} / 5.0")
    print("=" * 100 + "\n")

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
                f.write(f"- **Reasoning Engine:** Gemini LLM (`{r.get('model_used', 'gemini-3.8-flash')}`) grounded in `QandA.json`\n")
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
                        quote_part = f" (Your quote: *\"{m['candidate_quote']}\"*)" if m.get("candidate_quote") else ""
                        f.write(f"- **[{m['severity']}] {m['concept']}:** {m['error']}{quote_part}\n")
                    f.write("\n")

                if r.get("actionable_feedback"):
                    f.write("### Top Actionable Improvement Recommendations\n")
                    for fb in r["actionable_feedback"]:
                        ts_str = f" *(at {fb['timestamp']})*" if fb.get("timestamp") else ""
                        f.write(f"- **[Priority {fb['priority']}]{ts_str} {fb['issue']}**\n")
                        f.write(f"  - **Why it matters:** {fb['why_it_matters']}\n")
                        f.write(f"  - **Action:** {fb['improvement_action']}\n")
                        if fb.get("example_sentence"):
                            f.write(f"  - **Example to adapt:** *\"{fb['example_sentence']}\"*\n")
                    f.write("\n")

                f.write("### Rubric Idea Breakdown\n")
                for item in r["rubric_idea_breakdown"]:
                    f.write(f"- **[{item['verdict']}] ({item['points_awarded']} pts) {item['idea_id']}:** {item['criterion']}\n")
                    if item.get("reasoning"):
                        f.write(f"  - *Reasoning:* {item['reasoning']}\n")
                    if item.get("evidence_quote"):
                        f.write(f"  - *Evidence Quote at [{item['timestamp']}]:* \"{item['evidence_quote']}\"\n")
                f.write("\n---\n\n")

        print(f"\n[DONE] Saved evaluation reports to:")
        print(f"  - Markdown: {md_out}")
        print(f"  - JSON:     {json_out}")


if __name__ == "__main__":
    main()
