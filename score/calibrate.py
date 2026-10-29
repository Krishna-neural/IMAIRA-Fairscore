"""Per-dimension score calibration, 5-fold cross-validation, and held-out lockbox subsystem."""

import argparse
import datetime
import hashlib
import json
import logging
import os
import pickle
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union

# Ensure repository root is on sys.path
REPO_ROOT = Path(__file__).resolve().parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

import numpy as np
from sklearn.isotonic import IsotonicRegression
from sklearn.linear_model import Ridge
from sklearn.model_selection import StratifiedKFold, KFold

from eval.agreement import bootstrap_metric_ci, safe_pearsonr, safe_qwk
from score.rubrics import load_rubrics
from score.content import ContentJudge
from score.structure import StructureJudge

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

class HeldOutAccessError(PermissionError):
    """Raised when held-out test data is accessed without explicit authorization."""
    pass

class HeldOutAlreadyEvaluatedError(PermissionError):
    """Raised when held-out test data has already been evaluated and is locked."""
    pass

class BaseCalibrator:
    """Base class for score calibrators."""
    def fit(self, X: np.ndarray, y: np.ndarray) -> "BaseCalibrator":
        raise NotImplementedError
    def predict(self, X: np.ndarray) -> np.ndarray:
        raise NotImplementedError

class IdentityCalibrator(BaseCalibrator):
    def fit(self, X: np.ndarray, y: np.ndarray) -> "IdentityCalibrator":
        return self
    def predict(self, X: np.ndarray) -> np.ndarray:
        return np.clip(X.flatten(), 1.0, 5.0)

class IsotonicScoreCalibrator(BaseCalibrator):
    def __init__(self):
        self.model = IsotonicRegression(y_min=1.0, y_max=5.0, out_of_bounds="clip")
    def fit(self, X: np.ndarray, y: np.ndarray) -> "IsotonicScoreCalibrator":
        self.model.fit(X.flatten(), y.flatten())
        return self
    def predict(self, X: np.ndarray) -> np.ndarray:
        return np.clip(self.model.predict(X.flatten()), 1.0, 5.0)

class RidgeScoreCalibrator(BaseCalibrator):
    def __init__(self, alpha: float = 1.0):
        self.model = Ridge(alpha=alpha)
    def fit(self, X: np.ndarray, y: np.ndarray) -> "RidgeScoreCalibrator":
        X_mat = X.reshape(-1, 1) if X.ndim == 1 else X
        self.model.fit(X_mat, y.flatten())
        return self
    def predict(self, X: np.ndarray) -> np.ndarray:
        X_mat = X.reshape(-1, 1) if X.ndim == 1 else X
        preds = self.model.predict(X_mat)
        return np.clip(preds.flatten(), 1.0, 5.0)

def load_and_verify_datasets(
    dev_path: Union[str, Path] = "data/dataset_dev_240.json",
    heldout_path: Union[str, Path] = "data/dataset_heldout_60.json",
    allow_heldout_load: bool = False
) -> Tuple[List[Dict[str, Any]], Optional[List[Dict[str, Any]]]]:
    """Verify exact dataset partition sizes and disjointness."""
    dev_p = Path(dev_path)
    if not dev_p.exists():
        raise FileNotFoundError(f"Dev dataset not found at {dev_p}")
    with open(dev_p, "r", encoding="utf-8") as f:
        dev_data = json.load(f)

    if len(dev_data) != 240:
        raise ValueError(f"Strict requirement violation: dev set must have exactly 240 examples, got {len(dev_data)}")

    dev_ids = {e["example_id"] for e in dev_data}

    heldout_data = None
    if allow_heldout_load:
        heldout_data = evaluate_held_out_guarded(
            heldout_path=heldout_path,
            run_held_out_final_once=allow_heldout_load
        )
        heldout_ids = {e["example_id"] for e in heldout_data}
        if not dev_ids.isdisjoint(heldout_ids):
            overlap = dev_ids.intersection(heldout_ids)
            raise ValueError(f"Data leak: Dev and Held-out sets share overlapping IDs: {overlap}")

    return dev_data, heldout_data

def evaluate_held_out_guarded(
    heldout_path: Union[str, Path] = "data/dataset_heldout_60.json",
    run_held_out_final_once: bool = False,
    lock_path: Union[str, Path] = "reports/held_out_execution_lock.json",
    override_lock: Optional[str] = None
) -> List[Dict[str, Any]]:
    """Guarded loader enforcing the Held-Out Lockbox rule."""
    if not run_held_out_final_once:
        raise HeldOutAccessError(
            "Access to the 60 held-out examples is strictly prohibited without passing --run-held-out-final-once."
        )

    lock_p = Path(lock_path)
    if lock_p.exists():
        with open(lock_p, "r", encoding="utf-8") as f:
            lock_data = json.load(f)
        if lock_data.get("held_out_evaluated", False):
            if not override_lock or override_lock != lock_data.get("override_token", "AUTHORIZED_OVERRIDE_TOKEN"):
                raise HeldOutAlreadyEvaluatedError(
                    f"Held-out test set was already evaluated at {lock_data.get('evaluated_at')}. "
                    "Re-evaluation is locked to prevent test-set overfitting. "
                    "To override, provide valid --override-lock token."
                )

    heldout_p = Path(heldout_path)
    if not heldout_p.exists():
        raise FileNotFoundError(f"Held-out dataset not found at {heldout_p}")
    with open(heldout_p, "r", encoding="utf-8") as f:
        data = json.load(f)

    if len(data) != 60:
        raise ValueError(f"Strict requirement violation: held-out set must have exactly 60 examples, got {len(data)}")

    return data

def get_calibrator(method: str) -> BaseCalibrator:
    m = method.lower()
    if m == "isotonic":
        return IsotonicScoreCalibrator()
    elif m in {"ridge", "linear"}:
        return RidgeScoreCalibrator()
    elif m == "identity":
        return IdentityCalibrator()
    else:
        raise ValueError(f"Unknown calibration method: {method}")

def run_5fold_cv_calibration(
    raw_scores: np.ndarray,
    target_scores: np.ndarray,
    method: str = "isotonic",
    n_splits: int = 5,
    seed: int = 42
) -> Tuple[np.ndarray, Dict[str, Any]]:
    """Run deterministic 5-fold cross-validation on 240 dev examples."""
    assert len(raw_scores) == 240, f"Expected 240 dev examples, got {len(raw_scores)}"
    
    # Discretize target into bins for stratification
    bins = np.clip(np.round(target_scores).astype(int), 1, 5)
    skf = StratifiedKFold(n_splits=n_splits, shuffle=True, random_state=seed)
    
    oof_preds = np.zeros(len(raw_scores))
    fold_models = []

    for fold_idx, (train_idx, val_idx) in enumerate(skf.split(raw_scores, bins)):
        calibrator = get_calibrator(method)
        calibrator.fit(raw_scores[train_idx], target_scores[train_idx])
        oof_preds[val_idx] = calibrator.predict(raw_scores[val_idx])
        fold_models.append(calibrator)

    return oof_preds, {"method": method, "n_splits": n_splits, "seed": seed}

def compute_dimension_metrics(
    predictions: np.ndarray,
    targets: np.ndarray,
    n_bootstraps: int = 2000,
    seed: int = 42
) -> Dict[str, Dict[str, float]]:
    """Compute QWK, Pearson r, and MAE with 95% bootstrap confidence intervals."""
    data_pairs = [(predictions, targets)]
    qwk_ci = bootstrap_metric_ci(data_pairs, safe_qwk, n_bootstraps=n_bootstraps, seed=seed)
    pearson_ci = bootstrap_metric_ci(data_pairs, safe_pearsonr, n_bootstraps=n_bootstraps, seed=seed)
    mae_ci = bootstrap_metric_ci(data_pairs, lambda a, b: float(np.mean(np.abs(a - b))), n_bootstraps=n_bootstraps, seed=seed)
    return {
        "qwk": qwk_ci,
        "pearson_r": pearson_ci,
        "mae": mae_ci
    }

def format_side_by_side_markdown(
    results_summary: Dict[str, Any],
    human_ceiling: Optional[Dict[str, Any]] = None
) -> str:
    """Render side-by-side comparison table of Model vs Human Ceiling with 95% Bootstrap CIs."""
    lines = [
        "| Dimension | Split | Model QWK (95% CI) | Human Ceiling QWK (95% CI) | % of Ceiling | Model Pearson r (95% CI) | Human Pearson r (95% CI) | Model MAE (95% CI) | Human MAE (95% CI) |",
        "|:---|:---|:---|:---|:---|:---|:---|:---|:---|"
    ]

    for dim in ["content", "structure", "overall"]:
        if dim not in results_summary.get("dimensions", {}):
            continue
        dim_data = results_summary["dimensions"][dim]

        # Get human ceiling
        h_qwk_str = "N/A"
        h_r_str = "N/A"
        h_mae_str = "N/A"
        h_qwk_pt = None
        if human_ceiling and "dimensions" in human_ceiling and dim in human_ceiling["dimensions"]:
            h_dim = human_ceiling["dimensions"][dim]["inter_rater_pairwise"]
            h_qwk_str = f"{h_dim['qwk']['point']:.3f} [{h_dim['qwk']['ci_lower']:.3f}, {h_dim['qwk']['ci_upper']:.3f}]"
            h_r_str = f"{h_dim['pearson_r']['point']:.3f} [{h_dim['pearson_r']['ci_lower']:.3f}, {h_dim['pearson_r']['ci_upper']:.3f}]"
            h_mae_str = f"{h_dim['mae']['point']:.3f} [{h_dim['mae']['ci_lower']:.3f}, {h_dim['mae']['ci_upper']:.3f}]"
            h_qwk_pt = h_dim['qwk']['point']

        # Splits: dev_oof_all, dev_oof_non_contested, heldout_final
        splits = [
            ("Dev (5-Fold OOF)", "dev_oof_all"),
            ("Dev Non-Contested", "dev_oof_non_contested")
        ]
        if "heldout_final" in dim_data:
            splits.append(("Held-Out (Final)", "heldout_final"))

        for split_label, split_key in splits:
            if split_key not in dim_data:
                continue
            met = dim_data[split_key]
            m_qwk_str = f"{met['qwk']['point']:.3f} [{met['qwk']['ci_lower']:.3f}, {met['qwk']['ci_upper']:.3f}]"
            m_r_str = f"{met['pearson_r']['point']:.3f} [{met['pearson_r']['ci_lower']:.3f}, {met['pearson_r']['ci_upper']:.3f}]"
            m_mae_str = f"{met['mae']['point']:.3f} [{met['mae']['ci_lower']:.3f}, {met['mae']['ci_upper']:.3f}]"

            pct_ceiling = "N/A"
            if h_qwk_pt and h_qwk_pt > 0:
                pct = (met['qwk']['point'] / h_qwk_pt) * 100
                pct_ceiling = f"{pct:.1f}%"

            lines.append(
                f"| {dim.capitalize()} | {split_label} | {m_qwk_str} | {h_qwk_str} | {pct_ceiling} | {m_r_str} | {h_r_str} | {m_mae_str} | {h_mae_str} |"
            )

    return "\n".join(lines)

def run_calibration_pipeline(
    dev_path: str = "data/dataset_dev_240.json",
    heldout_path: str = "data/dataset_heldout_60.json",
    rubrics_path: str = "data/rubrics_120.json",
    ceiling_report_path: str = "reports/phase0_agreement_ceiling.json",
    lock_path: str = "reports/held_out_execution_lock.json",
    artifacts_dir: str = "artifacts",
    run_held_out: bool = False,
    override_lock: Optional[str] = None,
    calibration_method: str = "isotonic",
    n_bootstraps: int = 2000,
    seed: int = 42
) -> Dict[str, Any]:
    """Execute per-dimension 5-fold CV, fit calibrator, and conditionally execute heldout lockbox."""
    artifacts_p = Path(artifacts_dir)
    artifacts_p.mkdir(parents=True, exist_ok=True)
    lock_p = Path(lock_path)
    lock_p.parent.mkdir(parents=True, exist_ok=True)

    # 1. Held-Out Lockbox Security Check
    if run_held_out:
        if lock_p.exists():
            with open(lock_p, "r", encoding="utf-8") as f:
                lock_data = json.load(f)
            if lock_data.get("held_out_evaluated", False):
                if not override_lock or override_lock != lock_data.get("override_token", "AUTHORIZED_OVERRIDE_TOKEN"):
                    raise HeldOutAlreadyEvaluatedError(
                        f"Held-out test set was already evaluated at {lock_data.get('evaluated_at')}. "
                        "Re-evaluation is locked to prevent test-set overfitting. "
                        "To override, provide valid --override-lock token."
                    )
                logger.warning("Held-out evaluation proceeding under explicit human override token!")
    
    # 2. Load and verify datasets
    dev_data, heldout_data = load_and_verify_datasets(
        dev_path=dev_path,
        heldout_path=heldout_path,
        allow_heldout_load=run_held_out
    )
    logger.info(f"Loaded {len(dev_data)} development examples.")
    if heldout_data:
        logger.info(f"Loaded {len(heldout_data)} held-out examples.")

    # Load rubrics
    rubrics = load_rubrics(rubrics_path)

    # Load human ceiling if available
    human_ceiling = None
    ceil_p = Path(ceiling_report_path)
    if ceil_p.exists():
        with open(ceil_p, "r", encoding="utf-8") as f:
            human_ceiling = json.load(f)

    # Initialize Judges
    content_judge = ContentJudge()
    structure_judge = StructureJudge()

    # 3. Extract or evaluate raw judge scores on Dev Set
    logger.info("Computing raw Content and Structure scores on 240 Dev examples...")
    dev_raw_content = []
    dev_raw_structure = []
    dev_target_content = []
    dev_target_structure = []
    dev_is_contested = []

    for ex in dev_data:
        q = rubrics[ex["question_id"]]
        t = ex["transcript"]
        is_cont = ex.get("is_contested", False)
        
        c_eval = content_judge.evaluate(q, t, is_contested_meta=is_cont)
        s_eval = structure_judge.evaluate(q.question_id, q.question_prompt, t)

        dev_raw_content.append(float(c_eval["raw_content_score"]))
        dev_raw_structure.append(float(s_eval["raw_structure_score"]))
        
        hs = ex["human_scores"]["consensus_score"]
        dev_target_content.append(float(hs["content"]))
        dev_target_structure.append(float(hs["structure"]))
        dev_is_contested.append(bool(is_cont))

    dev_raw_content = np.array(dev_raw_content)
    dev_raw_structure = np.array(dev_raw_structure)
    dev_raw_overall = 0.6 * dev_raw_content + 0.4 * dev_raw_structure

    dev_target_content = np.array(dev_target_content)
    dev_target_structure = np.array(dev_target_structure)
    dev_target_overall = 0.6 * dev_target_content + 0.4 * dev_target_structure
    dev_is_contested = np.array(dev_is_contested)

    # 4. 5-Fold Cross Validation per dimension
    logger.info(f"Running 5-fold cross validation with method='{calibration_method}'...")
    oof_content, _ = run_5fold_cv_calibration(dev_raw_content, dev_target_content, method=calibration_method, seed=seed)
    oof_structure, _ = run_5fold_cv_calibration(dev_raw_structure, dev_target_structure, method=calibration_method, seed=seed)
    oof_overall = 0.6 * oof_content + 0.4 * oof_structure

    # Compute Dev Metrics
    non_cont_mask = ~dev_is_contested

    results = {
        "calibration_method": calibration_method,
        "n_dev_examples": len(dev_data),
        "dimensions": {
            "content": {
                "dev_oof_all": compute_dimension_metrics(oof_content, dev_target_content, n_bootstraps=n_bootstraps, seed=seed),
                "dev_oof_non_contested": compute_dimension_metrics(oof_content[non_cont_mask], dev_target_content[non_cont_mask], n_bootstraps=n_bootstraps, seed=seed)
            },
            "structure": {
                "dev_oof_all": compute_dimension_metrics(oof_structure, dev_target_structure, n_bootstraps=n_bootstraps, seed=seed),
                "dev_oof_non_contested": compute_dimension_metrics(oof_structure[non_cont_mask], dev_target_structure[non_cont_mask], n_bootstraps=n_bootstraps, seed=seed)
            },
            "overall": {
                "dev_oof_all": compute_dimension_metrics(oof_overall, dev_target_overall, n_bootstraps=n_bootstraps, seed=seed),
                "dev_oof_non_contested": compute_dimension_metrics(oof_overall[non_cont_mask], dev_target_overall[non_cont_mask], n_bootstraps=n_bootstraps, seed=seed)
            }
        }
    }

    # 5. Fit Final Calibrators on all 240 Dev examples and serialize
    final_calibrator_content = get_calibrator(calibration_method).fit(dev_raw_content, dev_target_content)
    final_calibrator_structure = get_calibrator(calibration_method).fit(dev_raw_structure, dev_target_structure)

    with open(artifacts_p / "calibrator_content.pkl", "wb") as f:
        pickle.dump(final_calibrator_content, f)
    with open(artifacts_p / "calibrator_structure.pkl", "wb") as f:
        pickle.dump(final_calibrator_structure, f)

    meta_payload = {
        "calibration_method": calibration_method,
        "fit_timestamp": datetime.datetime.now().isoformat(),
        "dev_examples_count": len(dev_data),
        "rubric_version_hash": rubrics[list(rubrics.keys())[0]].question_id
    }
    with open(artifacts_p / "calibrator_metadata.json", "w", encoding="utf-8") as f:
        json.dump(meta_payload, f, indent=2)
    logger.info(f"Saved calibrator models to {artifacts_p}")

    # 6. Held-Out Evaluation (Guarded One-Time-Only)
    if run_held_out and heldout_data:
        logger.info("Evaluating guarded 60 Held-Out examples with frozen calibrators...")
        heldout_raw_c = []
        heldout_raw_s = []
        heldout_tgt_c = []
        heldout_tgt_s = []

        for ex in heldout_data:
            q = rubrics[ex["question_id"]]
            t = ex["transcript"]
            c_res = content_judge.evaluate(q, t, is_contested_meta=ex.get("is_contested", False))
            s_res = structure_judge.evaluate(q.question_id, q.question_prompt, t)
            
            heldout_raw_c.append(float(c_res["raw_content_score"]))
            heldout_raw_s.append(float(s_res["raw_structure_score"]))
            hs = ex["human_scores"]["consensus_score"]
            heldout_tgt_c.append(float(hs["content"]))
            heldout_tgt_s.append(float(hs["structure"]))

        heldout_raw_c = np.array(heldout_raw_c)
        heldout_raw_s = np.array(heldout_raw_s)
        heldout_tgt_c = np.array(heldout_tgt_c)
        heldout_tgt_s = np.array(heldout_tgt_s)

        heldout_cal_c = final_calibrator_content.predict(heldout_raw_c)
        heldout_cal_s = final_calibrator_structure.predict(heldout_raw_s)
        heldout_cal_o = 0.6 * heldout_cal_c + 0.4 * heldout_cal_s
        heldout_tgt_o = 0.6 * heldout_tgt_c + 0.4 * heldout_tgt_s

        results["dimensions"]["content"]["heldout_final"] = compute_dimension_metrics(heldout_cal_c, heldout_tgt_c, n_bootstraps=n_bootstraps, seed=seed)
        results["dimensions"]["structure"]["heldout_final"] = compute_dimension_metrics(heldout_cal_s, heldout_tgt_s, n_bootstraps=n_bootstraps, seed=seed)
        results["dimensions"]["overall"]["heldout_final"] = compute_dimension_metrics(heldout_cal_o, heldout_tgt_o, n_bootstraps=n_bootstraps, seed=seed)

        # Write Held-Out Lock Ledger
        pred_hash = hashlib.sha256(heldout_cal_o.tobytes()).hexdigest()
        lock_entry = {
            "held_out_evaluated": True,
            "evaluated_at": datetime.datetime.now().isoformat(),
            "n_held_out": len(heldout_data),
            "predictions_sha256": pred_hash,
            "override_token": "AUTHORIZED_OVERRIDE_TOKEN"
        }
        with open(lock_p, "w", encoding="utf-8") as f:
            json.dump(lock_entry, f, indent=2)
        logger.info(f"Recorded held-out execution lock in {lock_p}")

    # Generate Markdown side-by-side comparison
    md_table = format_side_by_side_markdown(results, human_ceiling=human_ceiling)
    results["side_by_side_markdown"] = md_table

    report_p = Path("reports/calibration_evaluation_report.json")
    report_p.parent.mkdir(parents=True, exist_ok=True)
    with open(report_p, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2)

    with open("reports/side_by_side_comparison.md", "w", encoding="utf-8") as f:
        f.write("# IMAIRA-Fairscore: Model vs. Human Inter-Interviewer Ceiling\n\n" + md_table + "\n")

    return results

def main():
    parser = argparse.ArgumentParser(description="Per-dimension Score Calibration and Held-Out Lockbox Pipeline.")
    parser.add_argument("--dev-path", type=str, default="data/dataset_dev_240.json")
    parser.add_argument("--heldout-path", type=str, default="data/dataset_heldout_60.json")
    parser.add_argument("--rubrics-path", type=str, default="data/rubrics_120.json")
    parser.add_argument("--method", type=str, default="isotonic", choices=["isotonic", "ridge", "identity"])
    parser.add_argument("--bootstraps", type=int, default=500, help="Bootstrap resampling iterations")
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--run-held-out-final-once", action="store_true", help="Guarded flag to evaluate 60 held-out examples")
    parser.add_argument("--override-lock", type=str, default=None, help="Explicit token to re-evaluate held-out set")
    args = parser.parse_args()

    results = run_calibration_pipeline(
        dev_path=args.dev_path,
        heldout_path=args.heldout_path,
        rubrics_path=args.rubrics_path,
        calibration_method=args.method,
        run_held_out=args.run_held_out_final_once,
        override_lock=args.override_lock,
        n_bootstraps=args.bootstraps,
        seed=args.seed
    )

    print("\n" + results["side_by_side_markdown"] + "\n")

if __name__ == "__main__":
    main()
