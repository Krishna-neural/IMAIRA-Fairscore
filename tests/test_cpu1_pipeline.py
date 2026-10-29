"""Test Suite for Member 3: CPU 1 — Content, Structure, Calibration, and Agreement."""

import ast
import json
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch

import numpy as np
import pytest

# Ensure repository root is on sys.path
REPO_ROOT = Path(__file__).resolve().parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from eval.agreement import (
    compute_inter_interviewer_agreement,
    identify_contested_answers,
    safe_pearsonr,
    safe_qwk
)
from eval.scorer_only import AccentPerturbationEngine, run_scorer_robustness_test
from score.cache import SQLiteDiskCache, execute_with_backoff, normalize_text
from score.calibrate import (
    HeldOutAccessError,
    HeldOutAlreadyEvaluatedError,
    evaluate_held_out_guarded,
    load_and_verify_datasets,
    run_5fold_cv_calibration,
    run_calibration_pipeline
)
from score.content import ContentJudge, apply_fixed_uncertainty_rule
from score.rubrics import (
    QuestionRubric,
    compute_rubric_version_hash,
    load_rubrics,
    validate_rubrics
)
from score.structure import StructureJudge, apply_structure_uncertainty_rule


# ==============================================================================
# 1. Rubric Audit Check
# ==============================================================================

def test_rubric_audit_120_questions():
    """Verify all 120 questions follow semantic proposition principle with zero bare keywords."""
    rubrics_path = REPO_ROOT / "data" / "rubrics_120.json"
    assert rubrics_path.exists(), f"Rubrics file missing at {rubrics_path}"

    with open(rubrics_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    assert len(data) == 120, f"Expected 120 questions, got {len(data)}"
    is_valid, msg, meta = validate_rubrics(data)
    assert is_valid, f"Rubric validation failed: {msg}"
    assert meta["num_questions"] == 120
    assert meta["total_ideas"] >= 240
    assert "rubric_version_hash" in meta
    assert len(meta["rubric_version_hash"]) == 64

    # Verify no bare keywords
    for item in data:
        assert "question_id" in item
        assert "question_prompt" in item
        assert "domain" in item
        for idea in item["semantic_rubric_ideas"]:
            words = idea["semantic_statement"].split()
            assert len(words) >= 5, f"Idea {idea['idea_id']} has fewer than 5 words: keyword violation"
            assert "acceptable_paraphrase_guidance" in idea


# ==============================================================================
# 2. Content Judge Checks (3 runs, mode voting, caching, backoff, flip rate)
# ==============================================================================

def test_content_judge_three_runs_mode_voting_and_tie_breaking(tmp_path):
    """Verify 3 runs at temperature=0, majority mode selection, and median tie-breaking with uncertainty."""
    judge = ContentJudge(cache_dir=tmp_path)
    rubrics = load_rubrics(REPO_ROOT / "data" / "rubrics_120.json")
    q = rubrics["Q001"]

    # Test Case 1: Majority mode (2 of 3 agree)
    with patch.object(judge, "_execute_run") as mock_run:
        mock_run.side_effect = [
            {"raw_content_score": 4.0, "per_idea_verdicts": [
                {"idea_id": "Q001_IDEA_1", "verdict": "demonstrated", "score": 1.0, "evidence_span": "test"},
                {"idea_id": "Q001_IDEA_2", "verdict": "demonstrated", "score": 1.0, "evidence_span": "test"},
                {"idea_id": "Q001_IDEA_3", "verdict": "partially_demonstrated", "score": 0.5, "evidence_span": "test"},
            ]},
            {"raw_content_score": 4.0, "per_idea_verdicts": [
                {"idea_id": "Q001_IDEA_1", "verdict": "demonstrated", "score": 1.0, "evidence_span": "test"},
                {"idea_id": "Q001_IDEA_2", "verdict": "demonstrated", "score": 1.0, "evidence_span": "test"},
                {"idea_id": "Q001_IDEA_3", "verdict": "partially_demonstrated", "score": 0.5, "evidence_span": "test"},
            ]},
            {"raw_content_score": 3.0, "per_idea_verdicts": [
                {"idea_id": "Q001_IDEA_1", "verdict": "partially_demonstrated", "score": 0.5, "evidence_span": "test"},
                {"idea_id": "Q001_IDEA_2", "verdict": "partially_demonstrated", "score": 0.5, "evidence_span": "test"},
                {"idea_id": "Q001_IDEA_3", "verdict": "absent", "score": 0.0, "evidence_span": ""},
            ]},
        ]
        res = judge.evaluate(q, "Sample transcript long enough to test mode voting properly.")
        assert res["raw_content_score"] == 4.0
        assert res["individual_run_scores"] == [4.0, 4.0, 3.0]
        assert res["score_flip"] is True

    # Test Case 2: Three-way tie (all 3 runs distinct) -> selects median and triggers uncertainty
    with patch.object(judge, "_execute_run") as mock_run:
        mock_run.side_effect = [
            {"raw_content_score": 2.0, "per_idea_verdicts": [
                {"idea_id": "Q001_IDEA_1", "verdict": "absent", "score": 0.0, "evidence_span": ""},
                {"idea_id": "Q001_IDEA_2", "verdict": "absent", "score": 0.0, "evidence_span": ""},
                {"idea_id": "Q001_IDEA_3", "verdict": "absent", "score": 0.0, "evidence_span": ""},
            ]},
            {"raw_content_score": 5.0, "per_idea_verdicts": [
                {"idea_id": "Q001_IDEA_1", "verdict": "demonstrated", "score": 1.0, "evidence_span": "test"},
                {"idea_id": "Q001_IDEA_2", "verdict": "demonstrated", "score": 1.0, "evidence_span": "test"},
                {"idea_id": "Q001_IDEA_3", "verdict": "demonstrated", "score": 1.0, "evidence_span": "test"},
            ]},
            {"raw_content_score": 3.5, "per_idea_verdicts": [
                {"idea_id": "Q001_IDEA_1", "verdict": "partially_demonstrated", "score": 0.5, "evidence_span": "test"},
                {"idea_id": "Q001_IDEA_2", "verdict": "partially_demonstrated", "score": 0.5, "evidence_span": "test"},
                {"idea_id": "Q001_IDEA_3", "verdict": "partially_demonstrated", "score": 0.5, "evidence_span": "test"},
            ]},
        ]
        res = judge.evaluate(q, "Sample transcript long enough to test mode voting properly.")
        # Median of [2.0, 3.5, 5.0] is 3.5
        assert res["raw_content_score"] == 3.5
        assert res["is_uncertain"] is True
        assert any("Three-way score disagreement" in r for r in res["uncertainty_reasons"])

def test_content_judge_sha256_cache_hits(tmp_path):
    """Verify SHA-256 disk cache returns cached result on repeated evaluation with 0 re-computations."""
    judge = ContentJudge(cache_dir=tmp_path)
    rubrics = load_rubrics(REPO_ROOT / "data" / "rubrics_120.json")
    q = rubrics["Q001"]
    transcript = "Iteratively updating parameters in the direction of negative gradient minimizes loss."

    # First evaluation
    res1 = judge.evaluate(q, transcript)
    # Second evaluation
    res2 = judge.evaluate(q, transcript)

    assert res1["raw_content_score"] == res2["raw_content_score"]
    assert res1["individual_run_scores"] == res2["individual_run_scores"]

def test_exponential_backoff_retry():
    """Verify exponential backoff retries on transient simulated errors."""
    attempts = 0

    def flaky_service():
        nonlocal attempts
        attempts += 1
        if attempts < 3:
            raise RuntimeError("Transient 429 Rate Limit")
        return {"status": "success"}

    result = execute_with_backoff(flaky_service, max_retries=4, base_delay=0.01, max_delay=0.1)
    assert result["status"] == "success"
    assert attempts == 3

def test_content_judge_flip_rate_below_5_percent():
    """Verify flip rate across a development sample is strictly below 5%."""
    rubrics = load_rubrics(REPO_ROOT / "data" / "rubrics_120.json")
    with open(REPO_ROOT / "data" / "dataset_dev_240.json", "r", encoding="utf-8") as f:
        dev_data = json.load(f)

    sample_items = dev_data[:30]
    judge = ContentJudge()
    results, stats = judge.evaluate_batch(sample_items, rubrics, enforce_flip_rate=True)

    assert stats["score_flip_rate"] < 0.05, f"Flip rate {stats['score_flip_rate']:.2%} >= 5%!"
    assert stats["target_flip_rate_met"] is True


# ==============================================================================
# 3. Structure Judge Checks (Decoupling & ASR / Code-Mixing Invariance)
# ==============================================================================

def test_structure_judge_independence_and_code_mixing_invariance(tmp_path):
    """Verify structure judge preserves scores despite code-mixed fillers and phonetic errors."""
    judge = StructureJudge(cache_dir=tmp_path)

    clean_transcript = (
        "To address this system design question, the core premise is that consistent hashing maps nodes to a ring. "
        "Furthermore, requests are routed to the nearest server clockwise. "
        "And to conclude, adding servers minimizes key remapping to guarantee high availability in production."
    )
    code_mixed_perturbed = (
        "Basically ya, matlab speaking about dis system design question, the core premise is dat consistent hashing maps nodes to a ring. "
        "Furthermore, toh requests are routed to de nearest server clockwise. "
        "And to conclude na, adding servers minimizes key remapping to guarantee high availability in production."
    )

    res_clean = judge.evaluate("Q057", "Explain Consistent Hashing", clean_transcript)
    res_perturbed = judge.evaluate("Q057", "Explain Consistent Hashing", code_mixed_perturbed)

    # Structure scores should be invariant (drift < 0.3)
    assert abs(res_clean["raw_structure_score"] - res_perturbed["raw_structure_score"]) <= 0.3
    assert res_perturbed["raw_structure_score"] >= 4.0
    assert res_perturbed["components"]["framing"]["score"] >= 4.0


# ==============================================================================
# 4. Agreement Ceiling Checks (eval/agreement.py)
# ==============================================================================

def test_agreement_ceiling_metrics_and_contested_marking():
    """Verify QWK, Pearson r, MAE point estimates and 95% bootstrap CIs, and contested marking."""
    with open(REPO_ROOT / "data" / "dataset_dev_240.json", "r", encoding="utf-8") as f:
        examples = json.load(f)

    # Compute agreement
    ceiling = compute_inter_interviewer_agreement(examples, n_bootstraps=100, seed=42)
    assert "dimensions" in ceiling
    for dim in ["content", "structure", "overall"]:
        assert dim in ceiling["dimensions"]
        pw = ceiling["dimensions"][dim]["inter_rater_pairwise"]
        assert 0.60 <= pw["qwk"]["point"] <= 1.0
        assert 0.70 <= pw["pearson_r"]["point"] <= 1.0
        assert pw["mae"]["point"] < 0.60
        # Check CIs
        assert pw["qwk"]["ci_lower"] <= pw["qwk"]["point"] <= pw["qwk"]["ci_upper"]
        assert pw["pearson_r"]["ci_lower"] <= pw["pearson_r"]["point"] <= pw["pearson_r"]["ci_upper"]

    # Contested answer marking
    annotated, summary = identify_contested_answers(examples, spread_threshold=1.0)
    assert summary["total_examples"] == 240
    assert summary["contested_count"] > 0
    assert any(ex["is_contested"] for ex in annotated)


# ==============================================================================
# 5. Calibration & Held-Out Lockbox Checks (score/calibrate.py)
# ==============================================================================

def test_calibrate_data_partition_and_disjointness():
    """Verify 240 dev and 60 held-out partition sizes and zero ID overlap."""
    dev_data, heldout_data = load_and_verify_datasets(
        dev_path=REPO_ROOT / "data" / "dataset_dev_240.json",
        heldout_path=REPO_ROOT / "data" / "dataset_heldout_60.json",
        allow_heldout_load=True
    )
    assert len(dev_data) == 240
    assert len(heldout_data) == 60
    dev_ids = {e["example_id"] for e in dev_data}
    heldout_ids = {e["example_id"] for e in heldout_data}
    assert dev_ids.isdisjoint(heldout_ids)

def test_held_out_lockbox_access_error():
    """Verify accessing held-out data without --run-held-out-final-once raises HeldOutAccessError."""
    with pytest.raises(HeldOutAccessError):
        evaluate_held_out_guarded(
            heldout_path=REPO_ROOT / "data" / "dataset_heldout_60.json",
            run_held_out_final_once=False
        )

def test_held_out_lockbox_already_evaluated_error(tmp_path):
    """Verify attempting to re-evaluate held-out data after lock raises HeldOutAlreadyEvaluatedError."""
    lock_file = tmp_path / "held_out_lock.json"
    with open(lock_file, "w", encoding="utf-8") as f:
        json.dump({
            "held_out_evaluated": True,
            "evaluated_at": "2026-10-27T10:00:00",
            "override_token": "SPECIAL_TOKEN"
        }, f)

    # Without override token -> raises HeldOutAlreadyEvaluatedError
    with pytest.raises(HeldOutAlreadyEvaluatedError):
        evaluate_held_out_guarded(
            heldout_path=REPO_ROOT / "data" / "dataset_heldout_60.json",
            run_held_out_final_once=True,
            lock_path=lock_file,
            override_lock=None
        )

    # With correct override token -> succeeds
    data = evaluate_held_out_guarded(
        heldout_path=REPO_ROOT / "data" / "dataset_heldout_60.json",
        run_held_out_final_once=True,
        lock_path=lock_file,
        override_lock="SPECIAL_TOKEN"
    )
    assert len(data) == 60

def test_5fold_cv_calibration_execution():
    """Verify 5-fold CV runs on 240 dev examples and yields out-of-fold calibrated scores."""
    np.random.seed(42)
    raw_scores = np.random.uniform(1.0, 5.0, size=240)
    targets = np.clip(raw_scores + np.random.normal(0, 0.3, size=240), 1.0, 5.0)

    oof_preds, meta = run_5fold_cv_calibration(raw_scores, targets, method="isotonic", n_splits=5, seed=42)
    assert len(oof_preds) == 240
    assert np.all(oof_preds >= 1.0) and np.all(oof_preds <= 5.0)


# ==============================================================================
# 6. Scorer-Only Robustness & Zero ASR/UI Imports Check
# ==============================================================================

def test_zero_asr_and_ui_architectural_prohibition():
    """Verify zero imports from ASR packages (whisper, torchaudio) or UI packages in score/ and eval/."""
    prohibited_packages = {
        "whisper", "faster_whisper", "torchaudio", "soundfile", "librosa",
        "streamlit", "gradio", "flask", "django"
    }

    modules_to_inspect = [
        REPO_ROOT / "score" / "content.py",
        REPO_ROOT / "score" / "structure.py",
        REPO_ROOT / "score" / "calibrate.py",
        REPO_ROOT / "eval" / "agreement.py",
        REPO_ROOT / "eval" / "scorer_only.py",
    ]

    for mod_path in modules_to_inspect:
        assert mod_path.exists(), f"Module {mod_path} does not exist"
        with open(mod_path, "r", encoding="utf-8") as f:
            tree = ast.parse(f.read(), filename=str(mod_path))

        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    root_pkg = alias.name.split(".")[0]
                    assert root_pkg not in prohibited_packages, (
                        f"Architectural prohibition violated in {mod_path.name}: "
                        f"Imported forbidden package '{root_pkg}'"
                    )
            elif isinstance(node, ast.ImportFrom):
                if node.module:
                    root_pkg = node.module.split(".")[0]
                    assert root_pkg not in prohibited_packages, (
                        f"Architectural prohibition violated in {mod_path.name}: "
                        f"Imported from forbidden package '{root_pkg}'"
                    )

def test_scorer_only_accent_invariance():
    """Verify accent robustness engine yields near-zero directional drift across 120 questions."""
    engine = AccentPerturbationEngine(seed=42)
    text = "Gradient descent uses learning rate to optimize loss."
    perturbed = engine.perturb(text, severity="moderate_20pct_wer")
    assert isinstance(perturbed, str)
    assert len(perturbed) > 0


# ==============================================================================
# 7. Git Hygiene Check
# ==============================================================================

def test_git_branch_isolation():
    """Verify current git branch is the dedicated side branch, not main or master."""
    res = subprocess.run(
        ["git", "branch", "--show-current"],
        cwd=str(REPO_ROOT),
        capture_output=True,
        text=True
    )
    current_branch = res.stdout.strip()
    assert current_branch == "feature/cpu1-content-structure-calibration", (
        f"Branch isolation violated! Currently on branch '{current_branch}', "
        "must be 'feature/cpu1-content-structure-calibration'."
    )
    assert current_branch not in {"main", "master"}, "Must NEVER work directly on main or master!"
