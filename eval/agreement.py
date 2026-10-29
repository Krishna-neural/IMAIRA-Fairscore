#!/usr/bin/env python3
"""Phase 0: Human Inter-Interviewer Agreement Ceiling & Contested Answer Identification."""

import argparse
import json
import logging
import sys
import warnings
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union

# Ensure repository root is on sys.path
REPO_ROOT = Path(__file__).resolve().parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

import numpy as np
from scipy import stats
from sklearn.metrics import cohen_kappa_score

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

DEFAULT_DIMENSIONS = ["content", "structure", "overall"]

def safe_pearsonr(x: np.ndarray, y: np.ndarray) -> float:
    """Compute Pearson r handling zero variance gracefully."""
    if len(x) < 2:
        return 0.0
    if np.all(x == x[0]) or np.all(y == y[0]):
        return 1.0 if np.all(x == y) else 0.0
    try:
        r, _ = stats.pearsonr(x, y)
        if np.isnan(r):
            return 0.0
        return float(r)
    except Exception:
        return 0.0

def safe_qwk(x: np.ndarray, y: np.ndarray, min_rating: int = 1, max_rating: int = 5) -> float:
    """Compute Quadratic Weighted Kappa with integer-rounded ratings and explicit scale labels."""
    labels = list(range(min_rating, max_rating + 1))
    x_disc = np.clip(np.round(x).astype(int), min_rating, max_rating)
    y_disc = np.clip(np.round(y).astype(int), min_rating, max_rating)
    try:
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            score = cohen_kappa_score(x_disc, y_disc, weights="quadratic", labels=labels)
        if np.isnan(score):
            return 1.0 if np.all(x_disc == y_disc) else 0.0
        return float(score)
    except Exception:
        return 1.0 if np.all(x_disc == y_disc) else 0.0

def compute_pairwise_metrics(
    y_a: np.ndarray,
    y_b: np.ndarray,
    min_rating: int = 1,
    max_rating: int = 5
) -> Dict[str, float]:
    """Compute QWK, Pearson r, and MAE for a pair of raters or rater vs consensus."""
    qwk = safe_qwk(y_a, y_b, min_rating=min_rating, max_rating=max_rating)
    r = safe_pearsonr(y_a, y_b)
    mae = float(np.mean(np.abs(y_a - y_b)))
    return {"qwk": qwk, "pearson_r": r, "mae": mae}

def bootstrap_metric_ci(
    data_pairs: List[Tuple[np.ndarray, np.ndarray]],
    metric_func,
    n_bootstraps: int = 2000,
    seed: int = 42,
    alpha: float = 0.05
) -> Dict[str, float]:
    """Perform candidate-level paired non-parametric bootstrap resampling."""
    n_samples = len(data_pairs[0][0])
    rng = np.random.default_rng(seed)
    
    # Point estimate on entire dataset
    point_estimates = [metric_func(a, b) for a, b in data_pairs]
    point_est = float(np.mean(point_estimates))
    
    bootstrap_vals = []
    for _ in range(n_bootstraps):
        boot_idx = rng.integers(0, n_samples, size=n_samples)
        pair_scores = []
        for a, b in data_pairs:
            pair_scores.append(metric_func(a[boot_idx], b[boot_idx]))
        bootstrap_vals.append(float(np.mean(pair_scores)))
        
    bootstrap_vals = np.array(bootstrap_vals)
    ci_lower = float(np.percentile(bootstrap_vals, 100 * (alpha / 2)))
    ci_upper = float(np.percentile(bootstrap_vals, 100 * (1 - alpha / 2)))
    std_err = float(np.std(bootstrap_vals))
    
    return {
        "point": round(point_est, 4),
        "ci_lower": round(ci_lower, 4),
        "ci_upper": round(ci_upper, 4),
        "std_err": round(std_err, 4)
    }

def compute_inter_interviewer_agreement(
    examples: List[Dict[str, Any]],
    dimensions: Optional[List[str]] = None,
    n_bootstraps: int = 2000,
    seed: int = 42,
    min_rating: int = 1,
    max_rating: int = 5
) -> Dict[str, Any]:
    """Compute human agreement ceiling across raters for all dimensions."""
    if dimensions is None:
        dimensions = DEFAULT_DIMENSIONS
        
    num_examples = len(examples)
    if num_examples == 0:
        raise ValueError("Cannot compute agreement on empty example set.")
        
    results: Dict[str, Any] = {
        "num_examples": num_examples,
        "n_bootstraps": n_bootstraps,
        "seed": seed,
        "dimensions": {}
    }
    
    # Extract ratings
    for dim in dimensions:
        # Check available raters
        sample = examples[0].get("human_scores", {})
        rater_keys = [k for k in sample.keys() if k.startswith("rater_")]
        if not rater_keys:
            # Fallback to direct keys
            rater_keys = ["rater_1", "rater_2"]
            
        rater_data = {r: [] for r in rater_keys}
        consensus_data = []
        
        for ex in examples:
            hs = ex.get("human_scores", {})
            for r in rater_keys:
                score = hs.get(r, {}).get(dim, hs.get(r, 0.0))
                rater_data[r].append(float(score))
            c_score = hs.get("consensus_score", {}).get(dim, None)
            if c_score is None:
                # Average of available raters
                c_score = np.mean([rater_data[r][-1] for r in rater_keys])
            consensus_data.append(float(c_score))
            
        for r in rater_keys:
            rater_data[r] = np.array(rater_data[r])
        consensus_arr = np.array(consensus_data)
        
        # Build pairwise pairs
        pairs = []
        for i in range(len(rater_keys)):
            for j in range(i + 1, len(rater_keys)):
                r_a, r_b = rater_keys[i], rater_keys[j]
                pairs.append((rater_data[r_a], rater_data[r_b]))
                
        # Also build rater-vs-consensus pairs
        rater_vs_consensus_pairs = [(rater_data[r], consensus_arr) for r in rater_keys]
        
        # Compute bootstrap CIs
        qwk_ci = bootstrap_metric_ci(
            pairs,
            lambda a, b: safe_qwk(a, b, min_rating=min_rating, max_rating=max_rating),
            n_bootstraps=n_bootstraps,
            seed=seed
        )
        pearson_ci = bootstrap_metric_ci(
            pairs,
            safe_pearsonr,
            n_bootstraps=n_bootstraps,
            seed=seed
        )
        mae_ci = bootstrap_metric_ci(
            pairs,
            lambda a, b: float(np.mean(np.abs(a - b))),
            n_bootstraps=n_bootstraps,
            seed=seed
        )
        
        # Rater vs Consensus metrics
        consensus_qwk_ci = bootstrap_metric_ci(
            rater_vs_consensus_pairs,
            lambda a, b: safe_qwk(a, b, min_rating=min_rating, max_rating=max_rating),
            n_bootstraps=n_bootstraps,
            seed=seed
        )
        consensus_pearson_ci = bootstrap_metric_ci(
            rater_vs_consensus_pairs,
            safe_pearsonr,
            n_bootstraps=n_bootstraps,
            seed=seed
        )
        consensus_mae_ci = bootstrap_metric_ci(
            rater_vs_consensus_pairs,
            lambda a, b: float(np.mean(np.abs(a - b))),
            n_bootstraps=n_bootstraps,
            seed=seed
        )
        
        results["dimensions"][dim] = {
            "inter_rater_pairwise": {
                "qwk": qwk_ci,
                "pearson_r": pearson_ci,
                "mae": mae_ci
            },
            "rater_vs_consensus": {
                "qwk": consensus_qwk_ci,
                "pearson_r": consensus_pearson_ci,
                "mae": consensus_mae_ci
            }
        }
        
    return results

def identify_contested_answers(
    examples: List[Dict[str, Any]],
    spread_threshold: float = 1.0,
    dimensions: Optional[List[str]] = None
) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
    """Flag contested answers where human raters disagree beyond spread threshold."""
    if dimensions is None:
        dimensions = DEFAULT_DIMENSIONS

    annotated = []
    contested_count = 0
    dim_contested_counts = {d: 0 for d in dimensions}

    for ex in examples:
        item = dict(ex)
        hs = item.get("human_scores", {})
        rater_keys = [k for k in hs.keys() if k.startswith("rater_")]
        
        spreads = {}
        consensus = {}
        is_contested = False
        reasons = []

        for dim in dimensions:
            scores = [float(hs[r].get(dim, hs[r])) for r in rater_keys if r in hs]
            if scores:
                spread = round(float(np.ptp(scores)), 2)
                mean_val = round(float(np.mean(scores)), 2)
            else:
                spread = 0.0
                mean_val = 0.0

            spreads[dim] = spread
            consensus[dim] = mean_val

            if spread > spread_threshold:
                is_contested = True
                dim_contested_counts[dim] += 1
                reasons.append(f"{dim} spread ({spread}) > {spread_threshold}")

        item["is_contested"] = is_contested
        item["inter_rater_spread"] = spreads
        item["consensus_score"] = consensus
        item["contested_reasons"] = reasons

        if is_contested:
            contested_count += 1

        annotated.append(item)

    summary = {
        "total_examples": len(examples),
        "contested_count": contested_count,
        "contested_fraction": round(contested_count / len(examples), 4) if examples else 0.0,
        "spread_threshold": spread_threshold,
        "per_dimension_contested": dim_contested_counts
    }
    return annotated, summary

def main():
    parser = argparse.ArgumentParser(description="Compute Phase 0 Human Inter-Interviewer Agreement Ceiling & Mark Contested Answers.")
    parser.add_argument("--data-path", type=str, default="data/dataset_dev_240.json", help="Path to input examples JSON")
    parser.add_argument("--output-report", type=str, default="reports/phase0_agreement_ceiling.json", help="Path for agreement report")
    parser.add_argument("--output-manifest", type=str, default="reports/annotated_manifest.json", help="Path for annotated manifest")
    parser.add_argument("--spread-threshold", type=float, default=1.0, help="Threshold for marking contested items")
    parser.add_argument("--bootstraps", type=int, default=2000, help="Number of bootstrap iterations")
    parser.add_argument("--seed", type=int, default=42, help="Random seed")
    args = parser.parse_args()

    data_path = Path(args.data_path)
    if not data_path.exists():
        logger.error(f"Data file not found: {data_path}")
        return

    with open(data_path, "r", encoding="utf-8") as f:
        examples = json.load(f)

    logger.info(f"Loaded {len(examples)} examples from {data_path}")
    
    # 1. Agreement Ceiling
    logger.info(f"Computing agreement ceiling with B={args.bootstraps} bootstraps (seed={args.seed})...")
    ceiling_results = compute_inter_interviewer_agreement(
        examples,
        n_bootstraps=args.bootstraps,
        seed=args.seed
    )

    # 2. Contested Answer Identification
    annotated_examples, contested_summary = identify_contested_answers(
        examples,
        spread_threshold=args.spread_threshold
    )
    ceiling_results["contested_summary"] = contested_summary

    # Save outputs
    out_rep = Path(args.output_report)
    out_rep.parent.mkdir(parents=True, exist_ok=True)
    with open(out_rep, "w", encoding="utf-8") as f:
        json.dump(ceiling_results, f, indent=2)
    logger.info(f"Saved agreement report to {out_rep}")

    out_man = Path(args.output_manifest)
    out_man.parent.mkdir(parents=True, exist_ok=True)
    with open(out_man, "w", encoding="utf-8") as f:
        json.dump(annotated_examples, f, indent=2)
    logger.info(f"Saved annotated manifest to {out_man}")

    # Print summary
    print("\n=== PHASE 0 HUMAN AGREEMENT CEILING SUMMARY ===")
    for dim, met in ceiling_results["dimensions"].items():
        pw = met["inter_rater_pairwise"]
        print(f"Dimension: {dim:<10} | QWK: {pw['qwk']['point']:.3f} [{pw['qwk']['ci_lower']:.3f}, {pw['qwk']['ci_upper']:.3f}] | "
              f"Pearson r: {pw['pearson_r']['point']:.3f} [{pw['pearson_r']['ci_lower']:.3f}, {pw['pearson_r']['ci_upper']:.3f}] | "
              f"MAE: {pw['mae']['point']:.3f} [{pw['mae']['ci_lower']:.3f}, {pw['mae']['ci_upper']:.3f}]")
    print(f"Contested Items: {contested_summary['contested_count']} / {contested_summary['total_examples']} "
          f"({contested_summary['contested_fraction']*100:.1f}%) with spread > {args.spread_threshold}\n")

if __name__ == "__main__":
    main()
