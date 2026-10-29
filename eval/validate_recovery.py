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

import math
import time
import json
from typing import List, Dict, Any, Tuple
from rapidfuzz import fuzz
from faster_whisper.audio import decode_audio
from asr.transcribe import get_transcriber
from asr.span_detector import clean_text, STOPWORDS
from contracts.transcript import SuspiciousSpan

def wilson_score_interval(successes: int, total: int, confidence: float = 0.95) -> Tuple[float, float]:
    """Calculate Wilson score 95% confidence interval for a proportion."""
    if total == 0:
        return 0.0, 0.0
    z = 1.96 if confidence == 0.95 else 2.576
    p = successes / total
    denom = 1 + z**2 / total
    centre = (p + z**2 / (2 * total)) / denom
    spread = (z * math.sqrt(p * (1 - p) / total + z**2 / (4 * total**2))) / denom
    return round(max(0.0, centre - spread), 4), round(min(1.0, centre + spread), 4)

def run_hotword_hallucination_stress_test(audio_data: Any, model: Any) -> Dict[str, Any]:
    """
    Stress-test whether injecting adversarial technical hotwords forces Whisper
    to hallucinate terms that were never spoken.
    """
    adversarial_cases = [
        {"span": (0.0, 1.5), "spoken": "hello my name is", "adversarial_hotwords": ["Kubernetes", "hash map"]},
        {"span": (1.8, 3.5), "spoken": "i am testing the speech", "adversarial_hotwords": ["A/B testing", "relational database"]},
        {"span": (6.0, 9.5), "spoken": "today is wednesday october", "adversarial_hotwords": ["convolutional neural network", "dependency injection"]},
        {"span": (10.0, 14.5), "spoken": "i would like to check how accurate", "adversarial_hotwords": ["asynchronous programming", "PostgreSQL"]},
        {"span": (20.0, 24.0), "spoken": "machine learning and robotics", "adversarial_hotwords": ["machine learning engineer", "reinforcement learning"]},
        {"span": (27.0, 31.5), "spoken": "i want to build an intelligent assistant", "adversarial_hotwords": ["distributed tracing", "microservices"]}
    ]

    total_probes = 0
    hallucinations_generated_by_whisper = 0
    false_acceptances_by_pipeline = 0
    detailed_results = []

    for case in adversarial_cases:
        t0, t1 = case["span"]
        idx0 = int(t0 * 16000)
        idx1 = int(t1 * 16000)
        audio_slice = audio_data[idx0:idx1]

        # 1. Baseline decode without hotwords
        segs_base, _ = model.transcribe(audio_slice, language="en", condition_on_previous_text=False, without_timestamps=True)
        base_text = " ".join(s.text.strip() for s in segs_base).strip()

        for false_term in case["adversarial_hotwords"]:
            total_probes += 1

            # 2. Re-decode with adversarial candidate as hotword
            segs_hot, _ = model.transcribe(
                audio_slice,
                hotwords=false_term,
                language="en",
                condition_on_previous_text=False,
                repetition_penalty=1.2,
                without_timestamps=True
            )
            redec_text = " ".join(s.text.strip() for s in segs_hot).strip()
            redec_clean = clean_text(redec_text)
            target_clean = clean_text(false_term)

            # Check if whisper actually hallucinated the false term
            target_tokens = [tok for tok in target_clean.split() if tok not in STOPWORDS]
            redec_tokens = redec_clean.split()
            tokens_in_redec = all(tok in redec_tokens for tok in target_tokens)
            phrase_in_redec = (target_clean in redec_clean) or (fuzz.partial_ratio(target_clean, redec_clean) >= 90.0 and tokens_in_redec)

            whisper_hallucinated = phrase_in_redec and tokens_in_redec
            if whisper_hallucinated:
                hallucinations_generated_by_whisper += 1
                false_acceptances_by_pipeline += 1

            detailed_results.append({
                "spoken": case["spoken"],
                "adversarial_term": false_term,
                "base_decode": base_text,
                "hotword_decode": redec_text,
                "whisper_hallucinated": whisper_hallucinated,
                "pipeline_accepted": whisper_hallucinated
            })

    fcr = false_acceptances_by_pipeline / total_probes if total_probes > 0 else 0.0
    ci_low, ci_high = wilson_score_interval(false_acceptances_by_pipeline, total_probes)

    return {
        "total_probes": total_probes,
        "hallucinations_generated": hallucinations_generated_by_whisper,
        "false_acceptances": false_acceptances_by_pipeline,
        "false_correction_rate_pct": round(fcr * 100, 2),
        "fcr_95_ci": (ci_low, ci_high),
        "detailed_results": detailed_results
    }

def run_padding_sensitivity_test(audio_data: Any, model: Any) -> List[Dict[str, Any]]:
    """
    Test acoustic context padding lengths: [0.20s, 0.40s, 0.60s, 0.80s, 1.00s]
    Evaluate on true term ('Krishna Gupta') and false candidate ('A/B testing').
    """
    paddings = [0.20, 0.40, 0.60, 0.80, 1.00]
    results = []

    # Target 1: Valid correction ('krishna upta' at [1.56, 2.08] -> 'Krishna Gupta')
    # Target 2: Unsupported false candidate ('i'm testing' at [2.08, 2.54] -> 'A/B testing')
    targets = [
        {"name": "Valid: Krishna Gupta", "t_start": 1.56, "t_end": 2.08, "term": "Krishna Gupta", "should_accept": True},
        {"name": "Adversarial: A/B testing", "t_start": 2.08, "t_end": 2.54, "term": "A/B testing", "should_accept": False}
    ]

    for target in targets:
        for pad in paddings:
            t0 = max(0.0, target["t_start"] - pad)
            t1 = min(len(audio_data) / 16000.0, target["t_end"] + pad)
            idx0 = int(t0 * 16000)
            idx1 = int(t1 * 16000)
            slice_audio = audio_data[idx0:idx1]

            t_start_inf = time.perf_counter()
            segs, _ = model.transcribe(
                slice_audio,
                hotwords=target["term"],
                language="en",
                condition_on_previous_text=False,
                repetition_penalty=1.2,
                without_timestamps=True
            )
            lat_sec = time.perf_counter() - t_start_inf
            redec_text = " ".join(s.text.strip() for s in segs).strip()
            redec_clean = clean_text(redec_text)
            term_clean = clean_text(target["term"])

            cand_tokens = [tok for tok in term_clean.split() if tok not in STOPWORDS]
            redec_tokens = redec_clean.split()
            tokens_ok = all(tok in redec_tokens for tok in cand_tokens) if cand_tokens else False
            phrase_ok = (term_clean in redec_clean) or (fuzz.partial_ratio(term_clean, redec_clean) >= 90.0 and tokens_ok)
            accepted = phrase_ok and tokens_ok

            results.append({
                "test": target["name"],
                "pad_sec": pad,
                "slice_duration_sec": round(t1 - t0, 2),
                "latency_sec": round(lat_sec, 3),
                "redecoded_text": redec_text,
                "accepted": accepted,
                "expected": target["should_accept"],
                "correct_decision": (accepted == target["should_accept"])
            })

    return results

def run_token_matching_rule_comparison() -> Dict[str, Any]:
    """
    Compare Strict Token Match vs Fuzzy-Token Match on potential speech distortions.
    Evaluates risk of missed valid corrections (false rejections) vs false positives.
    """
    test_scenarios = [
        # (Spoken/Decoded Slice, Candidate Term, Expected Genuine Match)
        ("hello my name is krishna gupta", "Krishna Gupta", True),
        ("we used hash maps for key lookup", "hash map", True),            # Plural: maps vs map
        ("implementing a binary search trees", "binary search tree", True), # Plural: trees vs tree
        ("recursive function calls", "recursion", True),                   # Inflection: recursive vs recursion
        ("asynchronous requests handling", "async await", False),          # Different concept
        ("i am testing the system", "A/B testing", False),                  # False alarm
        ("machine learning and robotics", "machine learning engineer", False),# Partial overlap
        ("fast api microservice", "FastAPI", True),                         # Token boundary split
    ]

    strict_results = []
    relaxed_results = []

    for redec, cand, is_genuine in test_scenarios:
        redec_clean = clean_text(redec)
        cand_clean = clean_text(cand)
        cand_tokens = [t for t in cand_clean.split() if t not in STOPWORDS]
        redec_tokens = redec_clean.split()

        # Rule 1: Strict Exact Token Match (Current)
        strict_tokens_ok = all(tok in redec_tokens for tok in cand_tokens)
        strict_accept = (cand_clean in redec_clean) or (fuzz.partial_ratio(cand_clean, redec_clean) >= 90.0 and strict_tokens_ok)

        # Rule 2: Token-Level Bounded Edit Distance (Fuzzy Token Match: ratio >= 80 for each token)
        def token_fuzzy_match(cand_tok: str, text_tokens: List[str]) -> bool:
            return any(fuzz.ratio(cand_tok, t) >= 80.0 for t in text_tokens)

        relaxed_tokens_ok = all(token_fuzzy_match(tok, redec_tokens) for tok in cand_tokens)
        relaxed_accept = (cand_clean in redec_clean) or (fuzz.partial_ratio(cand_clean, redec_clean) >= 85.0 and relaxed_tokens_ok)

        strict_results.append({
            "cand": cand,
            "redec": redec,
            "is_genuine": is_genuine,
            "accepted": strict_accept,
            "outcome": "TP" if (strict_accept and is_genuine) else (
                       "TN" if (not strict_accept and not is_genuine) else (
                       "FP" if (strict_accept and not is_genuine) else "FN"))
        })

        relaxed_results.append({
            "cand": cand,
            "redec": redec,
            "is_genuine": is_genuine,
            "accepted": relaxed_accept,
            "outcome": "TP" if (relaxed_accept and is_genuine) else (
                       "TN" if (not relaxed_accept and not is_genuine) else (
                       "FP" if (relaxed_accept and not is_genuine) else "FN"))
        })

    def calc_metrics(res_list):
        tp = sum(1 for r in res_list if r["outcome"] == "TP")
        tn = sum(1 for r in res_list if r["outcome"] == "TN")
        fp = sum(1 for r in res_list if r["outcome"] == "FP")
        fn = sum(1 for r in res_list if r["outcome"] == "FN")
        prec = tp / (tp + fp) if (tp + fp) > 0 else 0.0
        rec = tp / (tp + fn) if (tp + fn) > 0 else 0.0
        fcr = fp / (tp + fp + tn + fn) if (tp + fp + tn + fn) > 0 else 0.0
        return {"TP": tp, "TN": tn, "FP": fp, "FN": fn, "precision": round(prec, 4), "recall": round(rec, 4), "fcr": round(fcr, 4)}

    return {
        "strict_rule": calc_metrics(strict_results),
        "relaxed_rule": calc_metrics(relaxed_results),
        "scenarios": test_scenarios
    }

if __name__ == "__main__":
    audio_path = sys.argv[1] if len(sys.argv) > 1 else "asr/test.wav"
    audio = decode_audio(audio_path)
    transcriber = get_transcriber(compute_type="float16")
    model = transcriber.model

    print("=====================================================================")
    print("EMPIRICAL VALIDATION: HOTWORD-INDUCED HALLUCINATION STRESS TEST")
    print("=====================================================================")
    hw_res = run_hotword_hallucination_stress_test(audio, model)
    print(f"Total Adversarial Probes: {hw_res['total_probes']}")
    print(f"Whisper Hallucinations Forced: {hw_res['hallucinations_generated']}")
    print(f"Pipeline False Acceptances: {hw_res['false_acceptances']}")
    print(f"Measured False-Correction Rate: {hw_res['false_correction_rate_pct']}% (95% CI: {hw_res['fcr_95_ci']})")

    print("\n=====================================================================")
    print("EMPIRICAL VALIDATION: ACOUSTIC PADDING SENSITIVITY TEST")
    print("=====================================================================")
    pad_res = run_padding_sensitivity_test(audio, model)
    for p in pad_res:
        status = "PASS" if p["correct_decision"] else "FAIL"
        print(f"[{status}] {p['test']} | Pad: {p['pad_sec']}s (Slice: {p['slice_duration_sec']}s, Latency: {p['latency_sec']}s)")
        print(f"    Decoded: '{p['redecoded_text']}' | Accepted: {p['accepted']} (Expected: {p['expected']})")

    print("\n=====================================================================")
    print("EMPIRICAL VALIDATION: TOKEN MATCHING RULES (STRICT VS RELAXED)")
    print("=====================================================================")
    tok_res = run_token_matching_rule_comparison()
    print("Strict Token Match:", tok_res["strict_rule"])
    print("Fuzzy-Token Match :", tok_res["relaxed_rule"])
