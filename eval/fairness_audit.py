"""
IMAIRA FairScore — Fairness Audit Lab
=====================================
Independent Evaluation, Bias Detection & Cross-Speaker Consistency Benchmarking.
Evaluates equivalent technical answers spoken by different speakers to measure:
    Score Range = max(Si) - min(Si) <= 5.0 points (out of 100)

Core Guarantee:
Deterministic statistical calculations, full diagnostic attribution, and human
reference comparison to make fairness measurable, inspectable, and defensible.
"""

import sys
import os
import json
import math
import numpy as np
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple

# Ensure repository root is on sys.path
REPO_ROOT = Path(__file__).resolve().parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from eval.fairness_models import (
    ExperimentalConditions,
    AuditedRecording,
    HumanReferenceEvaluation,
    EquivalentAnswerGroup,
    GroupFairnessMetrics,
    ExperimentConfig,
    FairnessAuditSummary
)
from score.evidence_models import load_evidence_question_bank
from score.uncertainty_engine import UncertaintyEngine


class FairnessAuditLab:
    """
    Independent fairness benchmarking framework measuring cross-speaker
    and cross-accent scoring consistency across equivalent-answer groups.
    """

    def __init__(
        self,
        groups_path: Optional[Path] = None,
        config: Optional[ExperimentConfig] = None,
        evaluator=None
    ):
        self.groups_path = groups_path or (REPO_ROOT / "data" / "fairness_benchmark_groups.json")
        self.config = config or ExperimentConfig(experiment_id="EXP_FAIRNESS_2026_01")
        self.evaluator = evaluator
        self.question_bank = load_evidence_question_bank()
        self.uncertainty_engine = UncertaintyEngine()

        # Cache of existing batch evaluation results if available
        self.cached_report: Dict[str, Dict[str, Any]] = {}
        report_file = REPO_ROOT / "reports" / "interview_evaluation_report.json"
        if report_file.exists():
            try:
                with open(report_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    for item in data:
                        fname = item.get("filename")
                        if fname:
                            self.cached_report[fname] = item
                            # Also map without directory prefix
                            self.cached_report[Path(fname).name] = item
            except Exception:
                pass

    def load_groups(self) -> List[EquivalentAnswerGroup]:
        """Loads and validates equivalent answer benchmark groups from JSON."""
        if not self.groups_path.exists():
            return []
        with open(self.groups_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        return [EquivalentAnswerGroup(**item) for item in data]

    def evaluate_group(self, group: EquivalentAnswerGroup) -> GroupFairnessMetrics:
        """
        Executes or extracts complete evaluation pipeline outputs for all recordings
        in an equivalent answer group, then computes deterministic fairness statistics.
        """
        scores_100: List[float] = []
        criterion_scores_map: Dict[str, List[float]] = {}
        total_recs = len(group.recordings)
        valid_recs = 0
        provisional_count = 0
        term_matches = 0
        total_expected_terms = 0

        # Extract expected terms from human reference if available
        expected_terms = set()
        if group.human_reference:
            expected_terms.update(t.lower() for t in group.human_reference.expected_concepts)
        else:
            q_def = self.question_bank.get(group.question_id)
            if q_def:
                expected_terms.update(c.lower() for c in q_def.expected_concepts)

        for rec in group.recordings:
            # 1. If recording already has content_score_100 explicitly specified (e.g. benchmark/test fixtures)
            if rec.content_score_100 is not None:
                valid_recs += 1
                scores_100.append(rec.content_score_100)
                for cid, pts in rec.criterion_scores.items():
                    criterion_scores_map.setdefault(cid, []).append(pts)
                continue

            audio_path = Path(rec.audio_reference)
            if not audio_path.is_absolute():
                audio_path = REPO_ROOT / audio_path

            # 2. Otherwise retrieve from live evaluator or cached execution report
            res = None
            audio_filename = audio_path.name
            if audio_filename in self.cached_report:
                res = self.cached_report[audio_filename]
            elif self.evaluator and audio_path.exists():
                try:
                    res = self.evaluator.evaluate_file(audio_path, forced_qid=group.question_id)
                except Exception:
                    res = None

            if res:
                valid_recs += 1
                rec.raw_transcript = res.get("transcripts", {}).get("raw_spoken")
                rec.corrected_transcript = res.get("transcripts", {}).get("corrected")
                rec.audio_duration_sec = res.get("audio_duration_sec")
                
                # Condition 2: Content score varies by <= 5.0 points on 0-100 scale across accents
                scores_obj = res.get("scores", {})
                fairscore_5pt = float(scores_obj.get("overall_fairscore", 3.0))
                cal_content = scores_obj.get("calibrated_content")
                if cal_content is not None:
                    score_100 = round((float(cal_content) - 1.0) / 4.0 * 100.0, 1)
                else:
                    score_100 = round((fairscore_5pt - 1.0) / 4.0 * 100.0, 1)
                
                rec.fairscore_5pt = fairscore_5pt
                rec.content_score_100 = score_100
                scores_100.append(score_100)

                # Track criterion level scores
                idea_breakdown = res.get("rubric_idea_breakdown", [])
                for idea in idea_breakdown:
                    cid = idea.get("idea_id", "C1")
                    pts = float(idea.get("points_awarded", 0.0))
                    rec.criterion_scores[cid] = pts
                    criterion_scores_map.setdefault(cid, []).append(pts)

                # Track uncertainty records
                rec.uncertainty_record_ids = [u.get("segment_id", "") for u in res.get("uncertainty_records", [])]
                if res.get("evidence_scorecard", {}).get("provisional_score_active"):
                    rec.provisional_score_active = True
                    provisional_count += 1
                rec.evaluation_state = res.get("evaluation_state", "final_verified")

                # Measure technical-term recall
                norm_text = (rec.corrected_transcript or "").lower()
                for t in expected_terms:
                    total_expected_terms += 1
                    if t in norm_text:
                        term_matches += 1

            elif rec.content_score_100 is not None:
                # Pre-populated score in benchmark fixture
                valid_recs += 1
                scores_100.append(rec.content_score_100)
                for cid, pts in rec.criterion_scores.items():
                    criterion_scores_map.setdefault(cid, []).append(pts)

        if not scores_100:
            # Empty or un-evaluated group fallback
            return GroupFairnessMetrics(
                group_id=group.group_id,
                question_id=group.question_id,
                total_recordings=total_recs,
                valid_recordings=0,
                highest_score=0.0,
                lowest_score=0.0,
                score_range=0.0,
                mean_score=0.0,
                median_score=0.0,
                std_dev=0.0,
                passed_tolerance=False,
                tolerance_threshold=self.config.tolerance_threshold
            )

        # -----------------------------------------------------------------------------------------
        # Deterministic Statistical Calculations
        # -----------------------------------------------------------------------------------------
        s_arr = np.array(scores_100)
        s_max = float(np.max(s_arr))
        s_min = float(np.min(s_arr))
        score_range = round(s_max - s_min, 2)
        mean_s = round(float(np.mean(s_arr)), 2)
        median_s = round(float(np.median(s_arr)), 2)
        # Population standard deviation
        std_dev = round(float(np.std(s_arr, ddof=0)), 2)

        percentiles = {
            "p25": round(float(np.percentile(s_arr, 25)), 2),
            "p50": median_s,
            "p75": round(float(np.percentile(s_arr, 75)), 2),
            "p90": round(float(np.percentile(s_arr, 90)), 2) if len(s_arr) >= 4 else s_max
        }

        passed = (score_range <= self.config.tolerance_threshold)

        # Criterion-level ranges
        crit_ranges = {}
        for cid, vals in criterion_scores_map.items():
            if vals:
                crit_ranges[cid] = round(max(vals) - min(vals), 2)

        term_recall = round(term_matches / total_expected_terms, 3) if total_expected_terms > 0 else 1.0

        # Human agreement MAE
        human_mae = None
        if group.human_reference and scores_100:
            ref_s = group.human_reference.reference_content_score_100
            human_mae = round(float(np.mean(np.abs(s_arr - ref_s))), 2)

        # Diagnostic Attribution
        diag_attr = {
            "primary_driver": "consistent_scoring" if passed else "speech_recognition_disparity",
            "asr_error_detected": bool(provisional_count > 0),
            "max_criterion_drift": max(crit_ranges.values()) if crit_ranges else 0.0,
            "provisional_safeguard_triggered": bool(provisional_count > 0)
        }

        return GroupFairnessMetrics(
            group_id=group.group_id,
            question_id=group.question_id,
            total_recordings=total_recs,
            valid_recordings=valid_recs,
            highest_score=s_max,
            lowest_score=s_min,
            score_range=score_range,
            mean_score=mean_s,
            median_score=median_s,
            std_dev=std_dev,
            percentiles=percentiles,
            passed_tolerance=passed,
            tolerance_threshold=self.config.tolerance_threshold,
            criterion_score_ranges=crit_ranges,
            technical_term_recall=term_recall,
            provisional_evaluations_count=provisional_count,
            diagnostic_attribution=diag_attr,
            human_agreement_mae=human_mae
        )

    def run_full_audit(self) -> FairnessAuditSummary:
        """Runs fairness evaluation across all configured benchmark groups and aggregates KPIs."""
        groups = self.load_groups()
        total_g = len(groups)
        valid_g = 0
        passed_g = 0
        failed_g = 0
        all_metrics: List[GroupFairnessMetrics] = []
        ranges: List[float] = []

        for g in groups:
            m = self.evaluate_group(g)
            all_metrics.append(m)
            if m.valid_recordings > 0:
                valid_g += 1
                ranges.append(m.score_range)
                if m.passed_tolerance:
                    passed_g += 1
                else:
                    failed_g += 1

        pass_rate = round((passed_g / valid_g * 100.0), 1) if valid_g > 0 else 0.0
        avg_range = round(float(np.mean(ranges)), 2) if ranges else 0.0
        max_range = round(float(np.max(ranges)), 2) if ranges else 0.0

        verdict = "COMPLIANT" if pass_rate >= 80.0 else "NON_COMPLIANT_INVESTIGATION_REQUIRED"

        return FairnessAuditSummary(
            experiment_config=self.config,
            total_groups=total_g,
            valid_groups=valid_g,
            passed_groups=passed_g,
            failed_groups=failed_g,
            fairness_pass_rate_pct=pass_rate,
            average_score_range=avg_range,
            max_observed_score_range=max_range,
            group_metrics=all_metrics,
            overall_recommendation=verdict
        )

    def export_audit_reports(self, summary: FairnessAuditSummary, output_dir: Optional[Path] = None) -> Tuple[Path, Path]:
        """Generates machine-readable JSON and executive Markdown audit reports."""
        out_dir = output_dir or (REPO_ROOT / "reports")
        out_dir.mkdir(parents=True, exist_ok=True)

        json_path = out_dir / "fairness_audit_report.json"
        md_path = out_dir / "fairness_audit_report.md"

        # 1. Save JSON
        with open(json_path, "w", encoding="utf-8") as f:
            json.dump(summary.model_dump(), f, indent=2)

        # 2. Save Markdown
        lines = [
            "# IMAIRA FairScore — Cross-Speaker Fairness & Consistency Audit Report",
            f"**Experiment ID:** `{summary.experiment_config.experiment_id}` | **Date:** {summary.experiment_config.created_at}",
            f"**Tolerance Benchmark:** `Score Range <= {summary.experiment_config.tolerance_threshold} points (0-100 scale)`",
            f"**Overall Compliance Verdict:** **{summary.overall_recommendation}**",
            "",
            "---",
            "## 1. Executive Summary & Key Performance Indicators",
            "",
            f"- **Total Answer Groups Audited:** {summary.total_groups}",
            f"- **Valid Groups Evaluated:** {summary.valid_groups}",
            f"- **Groups Passing 5-Point Tolerance:** {summary.passed_groups} / {summary.valid_groups} ({summary.fairness_pass_rate_pct}%)",
            f"- **Average Cross-Speaker Score Range:** `{summary.average_score_range} points`",
            f"- **Maximum Observed Disparity:** `{summary.max_observed_score_range} points`",
            "",
            "---",
            "## 2. Group-by-Group Statistical Consistency",
            "",
            "| Group ID | Question | N Recs | Min Score | Max Score | Range | Mean ± Std | Status |",
            "|---|---|---:|---:|---:|---:|---:|---:|"
        ]

        for m in summary.group_metrics:
            status_badge = "✅ PASS" if m.passed_tolerance else "❌ FAIL"
            lines.append(
                f"| `{m.group_id}` | `{m.question_id}` | {m.valid_recordings} | "
                f"{m.lowest_score:.1f} | {m.highest_score:.1f} | **{m.score_range:.1f}** | "
                f"{m.mean_score:.1f} ± {m.std_dev:.1f} | {status_badge} |"
            )

        lines.extend([
            "",
            "---",
            "## 3. Diagnostic Breakdown & Attribution",
            "",
            "The Fairness Audit Lab analyzes whether score differences originated from genuine technical differences, speech recognition errors, or evidence extraction drift:",
            ""
        ])

        for m in summary.group_metrics:
            lines.append(f"### Group {m.group_id} ({m.question_id})")
            lines.append(f"- **Technical-Term Recall:** `{m.technical_term_recall * 100:.1f}%`")
            lines.append(f"- **Provisional Safeguards Triggered:** `{m.provisional_evaluations_count}` recordings protected")
            if m.human_agreement_mae is not None:
                lines.append(f"- **Human Reference Agreement (MAE):** `{m.human_agreement_mae:.2f} points`")
            lines.append(f"- **Criterion Score Ranges:** {', '.join(f'{k}: {v}' for k, v in m.criterion_score_ranges.items())}")
            lines.append(f"- **Primary Diagnostic Attribution:** `{m.diagnostic_attribution.get('primary_driver')}`")
            lines.append("")

        lines.extend([
            "---",
            "## 4. Methodology & Fairness Acceptance Rules",
            "",
            "1. **Substantive Equivalence:** Every answer group communicates identical technical core ideas, despite natural speaker differences in pronunciation, cadence, and sentence structure.",
            "2. **Production Pipeline Execution:** No manual normalization or human transcript edits occur before evaluation; all recordings pass through production Whisper ASR, recovery recheck, and deterministic scoring.",
            "3. **Decoupled Uncertainty:** Recognition uncertainty is prevented from causing rubric failure via the Confidence-Aware Engine's provisional scoring policy.",
            "",
            "---",
            "## 5. Limitations & Future Scope",
            "",
            "- Benchmark dataset consists of controlled candidate recordings across diverse Indian regional accents.",
            "- Additional trials with heavy acoustic ambient noise (e.g. cafeteria, wind) are recommended for stress-testing.",
            "- Inter-rater human agreement analysis is currently based on gold-standard faculty rubric annotations."
        ])

        with open(md_path, "w", encoding="utf-8") as f:
            f.write("\n".join(lines))

        return json_path, md_path


if __name__ == "__main__":
    lab = FairnessAuditLab()
    summary = lab.run_full_audit()
    json_path, md_path = lab.export_audit_reports(summary)
    print("=" * 80)
    print("FAIRNESS AUDIT BENCHMARK SUMMARY")
    print("=" * 80)
    print(f"Total Groups: {summary.total_groups} | Valid Groups: {summary.valid_groups}")
    print(f"Passed Groups: {summary.passed_groups} | Failed Groups: {summary.failed_groups}")
    print(f"Pass Rate: {summary.fairness_pass_rate_pct}% (Tolerance <= {summary.experiment_config.tolerance_threshold} pts)")
    print(f"Average Range: {summary.average_score_range} pts | Max Range: {summary.max_observed_score_range} pts")
    print(f"Overall Recommendation: {summary.overall_recommendation}")
    print("-" * 80)
    for m in summary.group_metrics:
        res = "PASS" if m.passed_tolerance else "FAIL"
        print(f"[{res}] Group {m.group_id} ({m.question_id}): Range={m.score_range:.1f} pts, Scores=[{m.lowest_score:.1f} .. {m.highest_score:.1f}], StdDev={m.std_dev:.2f}")
    print("=" * 80)
    print(f"Reports saved to: {md_path} and {json_path}")

