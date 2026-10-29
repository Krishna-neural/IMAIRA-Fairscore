#!/usr/bin/env python3
"""Phase 5: Scorer-Only Accent-Error Robustness Stress Suite across all 120 questions.

Evaluates clean vs. accent-perturbed transcripts without invoking ASR models or UI components.
"""

import argparse
import json
import logging
import random
import re
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union

# Ensure repository root is on sys.path
REPO_ROOT = Path(__file__).resolve().parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

import numpy as np

from eval.agreement import bootstrap_metric_ci, safe_pearsonr, safe_qwk
from score.rubrics import load_rubrics, QuestionRubric
from score.content import ContentJudge
from score.structure import StructureJudge

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

# Phonetic / homophone technical substitutions common in Indian-English and L2 ASR
PHONETIC_TECHNICAL_SUBS = [
    ("gradient descent", "greatient decent"),
    ("gradient", "greatient"),
    ("hyperparameter", "piper parameter"),
    ("hyper parameter", "piper parameter"),
    ("eigenvalue", "iron value"),
    ("eigenvalues", "iron values"),
    ("eigenvector", "iron vector"),
    ("eigenvectors", "iron vectors"),
    ("backpropagation", "back propogation"),
    ("polymorphism", "poly morphism"),
    ("o(n log n)", "oh n log n"),
    ("o(1)", "oh one"),
    ("o(n)", "oh n"),
    ("o(v + e)", "oh v plus e"),
    ("sql", "sequel"),
    ("nosql", "no sequel"),
    ("cache", "cash"),
    ("caching", "cashing"),
    ("queue", "cue"),
    ("queues", "cues"),
    ("thread", "tred"),
    ("threads", "treds"),
    ("throughput", "trough put"),
    ("asynchronous", "async ronus"),
    ("synchronous", "sync ronus"),
    ("regularization", "regularization na"),
    ("overfitting", "over fitting"),
    ("underfitting", "under fitting"),
]

# Character & cluster level shifts (v/w, th/d, retroflex)
CONSONANT_VOWEL_SHIFTS = [
    (r"\bvery\b", "wery"),
    (r"\bvector\b", "wector"),
    (r"\bvectors\b", "wectors"),
    (r"\bvariable\b", "wariable"),
    (r"\bvalue\b", "walue"),
    (r"\bthe\b", "de"),
    (r"\bthis\b", "dis"),
    (r"\bthat\b", "dat"),
    (r"\bthese\b", "dese"),
    (r"\bthose\b", "dose"),
    (r"\bwith\b", "wid"),
    (r"\bthink\b", "tink"),
    (r"\bthree\b", "tree"),
    (r"\bthrough\b", "trough"),
]

DISCOURSE_FILLERS = [
    "basically ya",
    "actually na",
    "matlab",
    "toh",
    "like you know",
    "honestly speaking",
    "as such"
]

class AccentPerturbationEngine:
    """Deterministic phonetic and ASR error generator for Indian-English / L2 speech."""

    def __init__(self, seed: int = 42):
        self.rng = random.Random(seed)

    def perturb(self, text: str, severity: str = "moderate_20pct_wer") -> str:
        """Apply phonetic, phonological, and discourse perturbations based on severity."""
        if severity == "clean":
            return text

        severity_probs = {
            "mild_10pct_wer": {"phonetic": 0.35, "shifts": 0.25, "filler": 0.20},
            "moderate_20pct_wer": {"phonetic": 0.60, "shifts": 0.45, "filler": 0.40},
            "severe_30pct_wer": {"phonetic": 0.85, "shifts": 0.70, "filler": 0.65}
        }
        probs = severity_probs.get(severity, severity_probs["moderate_20pct_wer"])

        perturbed = text

        # 1. Phonetic technical substitutions
        for orig, sub in PHONETIC_TECHNICAL_SUBS:
            if orig in perturbed.lower() and self.rng.random() < probs["phonetic"]:
                # Case-insensitive replacement
                pattern = re.compile(re.escape(orig), re.IGNORECASE)
                perturbed = pattern.sub(sub, perturbed)

        # 2. Consonant/vowel shifts
        for pat, repl in CONSONANT_VOWEL_SHIFTS:
            if re.search(pat, perturbed, flags=re.IGNORECASE) and self.rng.random() < probs["shifts"]:
                perturbed = re.sub(pat, repl, perturbed, flags=re.IGNORECASE)

        # 3. Code-mixed discourse markers insertion
        words = perturbed.split()
        if len(words) > 8 and self.rng.random() < probs["filler"]:
            insert_pos = self.rng.randint(2, len(words) - 2)
            filler = self.rng.choice(DISCOURSE_FILLERS)
            words.insert(insert_pos, filler)
            perturbed = " ".join(words)

        return perturbed

def generate_reference_response_for_question(q: QuestionRubric) -> str:
    """Generate a high-quality reference transcript demonstrating all semantic rubric ideas."""
    ideas = q.semantic_rubric_ideas
    parts = [f"To address {q.question_prompt}, the core principle is that {ideas[0].semantic_statement}."]
    if len(ideas) > 1:
        parts.append(f"Furthermore, {ideas[1].semantic_statement}.")
    if len(ideas) > 2:
        parts.append(f"In addition, {ideas[2].semantic_statement}.")
    parts.append("This guarantees optimal performance and correctness in production.")
    return " ".join(parts)

def run_scorer_robustness_test(
    rubrics_path: str = "data/rubrics_120.json",
    severity: str = "moderate_20pct_wer",
    n_bootstraps: int = 1000,
    seed: int = 42
) -> Dict[str, Any]:
    """Run scorer-only accent error robustness stress tests across all 120 questions."""
    rubrics = load_rubrics(rubrics_path)
    assert len(rubrics) == 120, f"Expected 120 questions, got {len(rubrics)}"

    engine = AccentPerturbationEngine(seed=seed)
    content_judge = ContentJudge()
    structure_judge = StructureJudge()

    clean_content_scores = []
    accent_content_scores = []
    clean_structure_scores = []
    accent_structure_scores = []
    clean_overall_scores = []
    accent_overall_scores = []

    flips_under_perturbation = 0
    uncertain_count_clean = 0
    uncertain_count_accent = 0

    per_question_results = []

    logger.info(f"Evaluating all 120 questions in scorer-only mode under severity='{severity}'...")
    for q_id, q in rubrics.items():
        clean_text = generate_reference_response_for_question(q)
        accent_text = engine.perturb(clean_text, severity=severity)

        # Evaluate Clean
        clean_c = content_judge.evaluate(q, clean_text)
        clean_s = structure_judge.evaluate(q.question_id, q.question_prompt, clean_text)
        c_score_clean = float(clean_c["raw_content_score"])
        s_score_clean = float(clean_s["raw_structure_score"])
        o_score_clean = 0.6 * c_score_clean + 0.4 * s_score_clean

        # Evaluate Accent-Perturbed
        accent_c = content_judge.evaluate(q, accent_text)
        accent_s = structure_judge.evaluate(q.question_id, q.question_prompt, accent_text)
        c_score_accent = float(accent_c["raw_content_score"])
        s_score_accent = float(accent_s["raw_structure_score"])
        o_score_accent = 0.6 * c_score_accent + 0.4 * s_score_accent

        clean_content_scores.append(c_score_clean)
        accent_content_scores.append(c_score_accent)
        clean_structure_scores.append(s_score_clean)
        accent_structure_scores.append(s_score_accent)
        clean_overall_scores.append(o_score_clean)
        accent_overall_scores.append(o_score_accent)

        if abs(o_score_accent - o_score_clean) > 0.5:
            flips_under_perturbation += 1

        if clean_c["is_uncertain"] or clean_s["is_uncertain"]:
            uncertain_count_clean += 1
        if accent_c["is_uncertain"] or accent_s["is_uncertain"]:
            uncertain_count_accent += 1

        per_question_results.append({
            "question_id": q_id,
            "domain": q.domain,
            "clean_scores": {"content": c_score_clean, "structure": s_score_clean, "overall": round(o_score_clean, 2)},
            "accent_scores": {"content": c_score_accent, "structure": s_score_accent, "overall": round(o_score_accent, 2)},
            "score_diff_overall": round(o_score_accent - o_score_clean, 2),
            "clean_transcript_snippet": clean_text[:80] + "...",
            "accent_transcript_snippet": accent_text[:80] + "..."
        })

    # Convert to numpy arrays
    c_clean = np.array(clean_content_scores)
    c_accent = np.array(accent_content_scores)
    s_clean = np.array(clean_structure_scores)
    s_accent = np.array(accent_structure_scores)
    o_clean = np.array(clean_overall_scores)
    o_accent = np.array(accent_overall_scores)

    # Invariance Metrics computation helper
    def compute_invariance_metrics(clean_arr: np.ndarray, accent_arr: np.ndarray) -> Dict[str, Any]:
        data_pairs = [(clean_arr, accent_arr)]
        mae_ci = bootstrap_metric_ci(data_pairs, lambda a, b: float(np.mean(np.abs(a - b))), n_bootstraps=n_bootstraps, seed=seed)
        signed_drift_ci = bootstrap_metric_ci(data_pairs, lambda a, b: float(np.mean(b - a)), n_bootstraps=n_bootstraps, seed=seed)
        qwk_ci = bootstrap_metric_ci(data_pairs, safe_qwk, n_bootstraps=n_bootstraps, seed=seed)
        pearson_ci = bootstrap_metric_ci(data_pairs, safe_pearsonr, n_bootstraps=n_bootstraps, seed=seed)
        return {
            "score_invariance_mae": mae_ci,
            "signed_score_bias": signed_drift_ci,
            "clean_vs_perturbed_qwk": qwk_ci,
            "clean_vs_perturbed_pearson_r": pearson_ci
        }

    results = {
        "severity": severity,
        "num_questions": len(rubrics),
        "dimensions": {
            "content": compute_invariance_metrics(c_clean, c_accent),
            "structure": compute_invariance_metrics(s_clean, s_accent),
            "overall": compute_invariance_metrics(o_clean, o_accent)
        },
        "robustness_summary": {
            "overall_drift_mae": round(float(np.mean(np.abs(o_accent - o_clean))), 4),
            "overall_signed_bias": round(float(np.mean(o_accent - o_clean)), 4),
            "flip_rate_under_perturbation": round(flips_under_perturbation / len(rubrics), 4),
            "uncertainty_rate_clean": round(uncertain_count_clean / len(rubrics), 4),
            "uncertainty_rate_accent": round(uncertain_count_accent / len(rubrics), 4)
        },
        "sample_questions": per_question_results[:5]
    }

    return results

def main():
    parser = argparse.ArgumentParser(description="Scorer-Only Accent Robustness Stress Suite across 120 questions.")
    parser.add_argument("--rubrics-path", type=str, default="data/rubrics_120.json")
    parser.add_argument("--output-report", type=str, default="reports/scorer_robustness_report.json")
    parser.add_argument("--severity", type=str, default="moderate_20pct_wer",
                        choices=["clean", "mild_10pct_wer", "moderate_20pct_wer", "severe_30pct_wer"])
    parser.add_argument("--bootstraps", type=int, default=1000)
    parser.add_argument("--seed", type=int, default=42)
    args = parser.parse_args()

    results = run_scorer_robustness_test(
        rubrics_path=args.rubrics_path,
        severity=args.severity,
        n_bootstraps=args.bootstraps,
        seed=args.seed
    )

    out_p = Path(args.output_report)
    out_p.parent.mkdir(parents=True, exist_ok=True)
    with open(out_p, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2)
    logger.info(f"Saved robustness report to {out_p}")

    # Display summary
    print(f"\n=== SCORER-ONLY ACCENT ROBUSTNESS STRESS TEST ({args.severity}) ===")
    for dim, met in results["dimensions"].items():
        mae = met["score_invariance_mae"]
        bias = met["signed_score_bias"]
        r = met["clean_vs_perturbed_pearson_r"]
        qwk = met["clean_vs_perturbed_qwk"]
        print(f"Dimension: {dim:<10} | Invariance MAE: {mae['point']:.3f} [{mae['ci_lower']:.3f}, {mae['ci_upper']:.3f}] | "
              f"Signed Bias: {bias['point']:+.3f} [{bias['ci_lower']:+.3f}, {bias['ci_upper']:+.3f}] | "
              f"QWK: {qwk['point']:.3f} | Pearson r: {r['point']:.3f}")
    sum_stat = results["robustness_summary"]
    print(f"Flip Rate Under Perturbation: {sum_stat['flip_rate_under_perturbation']*100:.1f}%")
    print(f"Uncertainty Rate (Clean vs Accent): {sum_stat['uncertainty_rate_clean']*100:.1f}% vs {sum_stat['uncertainty_rate_accent']*100:.1f}%\n")

if __name__ == "__main__":
    main()
