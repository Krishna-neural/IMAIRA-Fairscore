"""
IMAIRA FairScore — Cohort Intelligence & Evaluation Quality Engine
==================================================================
Reusable institutional analytics service implementing:
1. Multi-dimensional cohort performance intelligence (verified vs provisional scoring)
2. True student skill gap discovery (distinguishing genuine knowledge deficits from ASR noise)
3. 4-Category Evaluation Quality Monitoring (Skill Gaps, ASR Issues, Uncertainties, Human Disagreement)
4. Deterministic, rule-based institutional evaluation health alerts
5. RBAC security enforcement and audit-grade report exports
"""

import json
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime
import numpy as np

from analytics.cohort_models import (
    AuthContext,
    CohortFilter,
    CohortOverviewKPIs,
    SkillGapItem,
    EvaluationQualityBreakdown,
    EvaluationAlert,
    PlacementIntelligenceReport,
    AlertSeverity
)
from eval.fairness_audit import FairnessAuditLab

logger = logging.getLogger(__name__)
REPO_ROOT = Path(__file__).resolve().parent.parent


class CohortIntelligenceEngine:
    """
    Core institutional analytics engine powering the Placement Officer Dashboard.
    Operates strictly deterministically from stored evaluation records.
    """

    def __init__(
        self,
        evaluation_data_path: Optional[Path] = None,
        fairness_report_path: Optional[Path] = None,
        feedback_report_path: Optional[Path] = None
    ):
        self.eval_path = evaluation_data_path or (REPO_ROOT / "reports" / "interview_evaluation_report.json")
        self.fairness_path = fairness_report_path or (REPO_ROOT / "reports" / "fairness_audit_report.json")
        self.feedback_path = feedback_report_path or (REPO_ROOT / "reports" / "feedback_report.json")
        
        self.raw_records: List[Dict[str, Any]] = self._load_records()
        self.alert_registry: Dict[str, EvaluationAlert] = {}

    def _load_records(self) -> List[Dict[str, Any]]:
        """Load stored candidate evaluation records from disk."""
        if self.eval_path.exists():
            try:
                with open(self.eval_path, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception as e:
                logger.warning("Could not read interview evaluations: %s", e)
        return []

    def enforce_auth(self, auth: Optional[AuthContext]) -> None:
        """
        Enforce Role-Based Access Control (RBAC).
        Students are strictly prohibited from viewing cohort-level institutional intelligence.
        """
        if auth and not auth.is_authorized():
            raise PermissionError(
                f"Access denied: User '{auth.user_id}' with role '{auth.role}' is not authorized "
                f"to access placement officer cohort intelligence."
            )

    def filter_records(
        self,
        records: List[Dict[str, Any]],
        c_filter: Optional[CohortFilter] = None
    ) -> List[Dict[str, Any]]:
        """Apply multi-dimensional cohort filters."""
        if not c_filter:
            return records

        filtered = []
        for r in records:
            # 1. Filter by domain
            if c_filter.domain:
                q_domain = r.get("matched_question", {}).get("domain", "")
                if c_filter.domain.lower() not in q_domain.lower():
                    continue

            # 2. Filter by evaluation status
            if c_filter.evaluation_status and c_filter.evaluation_status != "all":
                st = r.get("evaluation_state", "final_verified")
                if st.lower() != c_filter.evaluation_status.lower():
                    continue

            # 3. Filter by content score range (0-100 scale)
            scores = r.get("scores", {})
            cal_cont = scores.get("calibrated_content")
            c_score = round((float(cal_cont) - 1.0) / 4.0 * 100.0, 1) if cal_cont is not None else 50.0

            if c_filter.min_content_score is not None and c_score < c_filter.min_content_score:
                continue
            if c_filter.max_content_score is not None and c_score > c_filter.max_content_score:
                continue

            filtered.append(r)
        return filtered

    def calculate_cohort_kpis(self, records: List[Dict[str, Any]]) -> CohortOverviewKPIs:
        """
        Compute deterministic cohort performance KPIs.
        Crucial requirement: Strictly decouple verified scores from provisional scores.
        """
        if not records:
            return CohortOverviewKPIs()

        # Extract unique student candidates from recording filenames (e.g. Prem, Rupesh, Sukhpreet)
        student_set = set()
        for r in records:
            fn = r.get("filename", "")
            spk = fn.split("_")[0] if "_" in fn else fn.split(".")[0]
            student_set.add(spk)

        verified_scores: List[float] = []
        provisional_scores: List[float] = []
        review_required_count = 0
        unresolved_count = 0
        buckets = {"0-39": 0, "40-59": 0, "60-79": 0, "80-100": 0}

        for r in records:
            state = r.get("evaluation_state", "final_verified")
            sc_data = r.get("evidence_scorecard", {})
            is_provisional = (state == "provisional") or sc_data.get("provisional_score_active", False)
            is_pending = (state == "pending_review") or sc_data.get("manual_review_pending", False)

            if is_pending:
                review_required_count += 1
                unresolved_count += 1
            if is_provisional:
                review_required_count += 1

            # Get Content Score on 0-100 scale
            scores = r.get("scores", {})
            cal_cont = scores.get("calibrated_content")
            if cal_cont is not None:
                s_100 = round((float(cal_cont) - 1.0) / 4.0 * 100.0, 1)
            else:
                s_100 = round((float(scores.get("overall_fairscore", 3.0)) - 1.0) / 4.0 * 100.0, 1)

            # Assign to score distribution bucket
            if s_100 < 40.0:
                buckets["0-39"] += 1
            elif s_100 < 60.0:
                buckets["40-59"] += 1
            elif s_100 < 80.0:
                buckets["60-79"] += 1
            else:
                buckets["80-100"] += 1

            if is_provisional:
                provisional_scores.append(s_100)
            else:
                verified_scores.append(s_100)

        # Statistical calculations on verified scores (primary cohort benchmark)
        arr_verified = np.array(verified_scores if verified_scores else [50.0])
        avg_verified = round(float(np.mean(arr_verified)), 1)
        med_verified = round(float(np.median(arr_verified)), 1)
        std_dev = round(float(np.std(arr_verified, ddof=0)), 1)

        avg_provisional = round(float(np.mean(provisional_scores)), 1) if provisional_scores else None
        review_pct = round((review_required_count / len(records)) * 100.0, 1)

        return CohortOverviewKPIs(
            total_students_enrolled=len(student_set),
            total_interviews_conducted=len(records),
            completed_evaluations_count=len(records) - unresolved_count,
            average_verified_content_score=avg_verified,
            average_provisional_content_score=avg_provisional,
            median_content_score=med_verified,
            content_score_std_dev=std_dev,
            evaluations_requiring_review_pct=review_pct,
            unresolved_evaluations_count=unresolved_count,
            score_distribution_buckets=buckets
        )

    def analyze_skill_gaps(self, records: List[Dict[str, Any]], top_n: int = 5) -> List[SkillGapItem]:
        """
        Aggregate criterion-level performance to uncover true cohort skill deficiencies.
        Filters out pseudo-gaps caused primarily by ASR confusion.
        """
        criteria_stats: Dict[str, Dict[str, Any]] = {}

        for r in records:
            ideas = r.get("rubric_idea_breakdown", [])
            domain = r.get("matched_question", {}).get("domain", "General Engineering")
            corrections = r.get("corrections_made", [])
            has_asr_correction = len(corrections) > 0

            for idea in ideas:
                cid = idea.get("idea_id", "C1")
                desc = idea.get("criterion", "Concept Requirement")
                verdict = idea.get("verdict", "COVERED").upper()
                pts_awarded = float(idea.get("points_awarded", 1.0))
                max_pts = float(idea.get("max_points", 1.0))
                marks_lost = max(0.0, max_pts - pts_awarded)

                if cid not in criteria_stats:
                    criteria_stats[cid] = {
                        "concept": desc,
                        "domain": domain,
                        "times_assessed": 0,
                        "times_missing": 0,
                        "total_marks_lost": 0.0,
                        "max_pts": max_pts,
                        "asr_incident_count": 0
                    }

                criteria_stats[cid]["times_assessed"] += 1
                criteria_stats[cid]["total_marks_lost"] += marks_lost
                if verdict in {"MISSING", "PARTIAL"}:
                    criteria_stats[cid]["times_missing"] += 1
                    if has_asr_correction:
                        criteria_stats[cid]["asr_incident_count"] += 1

        skill_gaps: List[SkillGapItem] = []
        for cid, st in criteria_stats.items():
            assessed = st["times_assessed"]
            if assessed == 0:
                continue
            missed = st["times_missing"]
            if missed == 0:
                # Criteria with 100% mastery across cohort are not skill gaps
                continue
            fail_rate = round((missed / assessed) * 100.0, 1)
            avg_lost = round(st["total_marks_lost"] / assessed, 2)
            asr_pct = round((st["asr_incident_count"] / max(1, missed)) * 100.0, 1)
            is_confirmed = (asr_pct < 40.0)  # If >=40% failures had ASR issues, flag as confounded

            training_topic = f"Revision Workshop: {st['concept'][:40]} in {st['domain']}"

            skill_gaps.append(
                SkillGapItem(
                    concept_name=st["concept"],
                    criterion_id=cid,
                    domain=st["domain"],
                    students_assessed_count=assessed,
                    students_missing_count=missed,
                    failure_rate_pct=fail_rate,
                    average_marks_lost=avg_lost,
                    max_possible_marks=st["max_pts"],
                    is_confirmed_skill_gap=is_confirmed,
                    asr_uncertainty_impact_pct=asr_pct,
                    recommended_training_topic=training_topic
                )
            )

        # Deterministic ranking: Confirmed skill gaps first, then highest average marks lost, then failure rate
        skill_gaps.sort(key=lambda x: (x.is_confirmed_skill_gap, x.average_marks_lost, x.failure_rate_pct), reverse=True)
        return skill_gaps[:top_n]

    def build_quality_breakdown(
        self,
        records: List[Dict[str, Any]],
        skill_gaps: List[SkillGapItem]
    ) -> EvaluationQualityBreakdown:
        """
        Build the 4-Category Evaluation Quality Monitoring breakdown:
        Category 1: Student Skill Gaps
        Category 2: ASR Recognition Problems
        Category 3: Uncertain Decisions
        Category 4: Human vs System Disagreements
        """
        # Category 1: Confirmed Skill Gaps
        confirmed_gaps = [g for g in skill_gaps if g.is_confirmed_skill_gap and g.students_missing_count > 0]

        # Category 2: ASR Recognition Problems
        total_suspicious = 0
        total_audio_verified = 0
        total_unresolved_asr = 0
        interviews_with_asr = 0

        for r in records:
            corrs = r.get("corrections_made", [])
            u_recs = r.get("uncertainty_records", [])
            if corrs or u_recs:
                interviews_with_asr += 1
            total_audio_verified += len(corrs)
            for u in u_recs:
                total_suspicious += 1
                if u.get("recognition_status") in {"uncertain", "unresolved"}:
                    total_unresolved_asr += 1

        # Category 3: Uncertain Decisions
        provisional_count = 0
        pending_review_count = 0
        marks_at_risk = 0.0

        for r in records:
            state = r.get("evaluation_state", "final_verified")
            sc_data = r.get("evidence_scorecard", {})
            if state == "provisional" or sc_data.get("provisional_score_active"):
                provisional_count += 1
                marks_at_risk += float(sc_data.get("provisional_marks_total", 1.5))
            if state == "pending_review" or sc_data.get("manual_review_pending"):
                pending_review_count += 1

        # Category 4: Human-vs-System Disagreement (from Fairness Audit Lab if available)
        human_reviewed = 0
        mae_val = None
        sig_diff = 0

        if self.fairness_path.exists():
            try:
                with open(self.fairness_path, "r", encoding="utf-8") as f:
                    fair_data = json.load(f)
                    mae_list = []
                    for gm in fair_data.get("group_metrics", []):
                        if gm.get("human_agreement_mae") is not None:
                            human_reviewed += gm.get("valid_recordings", 0)
                            mae_list.append(gm["human_agreement_mae"])
                    if mae_list:
                        mae_val = round(float(np.mean(mae_list)), 2)
                        sig_diff = sum(1 for m in mae_list if m > 15.0)
            except Exception:
                pass

        return EvaluationQualityBreakdown(
            confirmed_skill_gaps_count=len(confirmed_gaps),
            top_skill_gaps=confirmed_gaps[:5],
            asr_problems_count=total_suspicious + total_audio_verified,
            suspicious_segments_count=total_suspicious,
            audio_verified_corrections_count=total_audio_verified,
            unresolved_asr_segments_count=total_unresolved_asr,
            interviews_with_asr_issues=interviews_with_asr,
            uncertain_evaluations_count=provisional_count + pending_review_count,
            provisional_evaluations_count=provisional_count,
            pending_human_reviews_count=pending_review_count,
            marks_affected_by_uncertainty=round(marks_at_risk, 1),
            human_reviewed_count=human_reviewed,
            human_system_mae=mae_val,
            significant_disagreements_count=sig_diff
        )

    def generate_alerts(
        self,
        kpis: CohortOverviewKPIs,
        quality: EvaluationQualityBreakdown,
        fairness_summary: Optional[Dict[str, Any]] = None
    ) -> List[EvaluationAlert]:
        """
        Generate deterministic evaluation quality alerts using explicit threshold rules.
        """
        alerts: List[EvaluationAlert] = []

        # 1. Fairness Audit Compliance Alert
        if fairness_summary:
            pass_rate = fairness_summary.get("fairness_pass_rate_pct", 100.0)
            max_range = fairness_summary.get("max_observed_score_range", 0.0)
            if pass_rate < 80.0 or max_range > 5.0:
                alerts.append(
                    EvaluationAlert(
                        alert_id="ALT_FAIR_001",
                        category="fairness_audit_failure",
                        severity="critical",
                        title="Fairness Tolerance Violation Detected",
                        description=f"Equivalent answers exceeded the 5.0-point tolerance threshold (Max range: {max_range} pts, Pass rate: {pass_rate}%).",
                        affected_interview_count=fairness_summary.get("failed_groups", 1),
                        recommended_action="Inspect the Placement Officer Fairness Audit Lab to identify acoustic calibration or rubric drift."
                    )
                )

        # 2. High Provisional Evaluation Rate Alert
        if kpis.total_interviews_conducted > 0:
            prov_pct = (quality.provisional_evaluations_count / kpis.total_interviews_conducted) * 100.0
            if prov_pct > 15.0:
                alerts.append(
                    EvaluationAlert(
                        alert_id="ALT_QUAL_002",
                        category="high_provisional_rate",
                        severity="high",
                        title="High Volume of Provisional Evaluations",
                        description=f"{quality.provisional_evaluations_count} interviews ({prov_pct:.1f}%) received provisional credit due to speech recognition ambiguity.",
                        affected_interview_count=quality.provisional_evaluations_count,
                        recommended_action="Review acoustic environments and headset microphone configurations to reduce speech recognition uncertainty."
                    )
                )

        # 3. Unresolved ASR Segments Alert
        if quality.unresolved_asr_segments_count > 0:
            alerts.append(
                EvaluationAlert(
                    alert_id="ALT_ASR_003",
                    category="asr_recognition_problem",
                    severity="medium",
                    title="Unresolved ASR Spans in Cohort",
                    description=f"{quality.unresolved_asr_segments_count} suspicious audio segments remain unresolved after acoustic slice rechecking.",
                    affected_interview_count=quality.interviews_with_asr_issues,
                    recommended_action="Utilize the Human Expert Review Portal to verify spoken terminology against audio."
                )
            )

        # 4. Human-System Disagreement Alert
        if quality.human_system_mae is not None and quality.human_system_mae > 25.0:
            alerts.append(
                EvaluationAlert(
                    alert_id="ALT_HUM_004",
                    category="human_score_disagreement",
                    severity="high",
                    title="Significant AI-Human Scoring Disparity",
                    description=f"Automated evaluation diverges from gold-standard human targets with MAE = {quality.human_system_mae:.1f} points.",
                    affected_interview_count=quality.human_reviewed_count,
                    recommended_action="Recalibrate rubric weights and benchmark criteria against faculty assessment guidelines."
                )
            )

        # Informational alert if zero issues detected
        if not alerts:
            alerts.append(
                EvaluationAlert(
                    alert_id="ALT_INFO_000",
                    category="student_skill_gap",
                    severity="informational",
                    title="Evaluation Pipeline Operating Nominally",
                    description="All automated assessments satisfy confidence, calibration, and fairness benchmarks.",
                    affected_interview_count=0,
                    recommended_action="Continue regular placement interview monitoring."
                )
            )

        # Register alerts
        for a in alerts:
            self.alert_registry[a.alert_id] = a

        return alerts

    def update_alert_status(
        self,
        alert_id: str,
        new_status: str,
        reviewer_notes: Optional[str] = None
    ) -> Optional[EvaluationAlert]:
        """Update review status of an evaluation alert."""
        if alert_id in self.alert_registry:
            alt = self.alert_registry[alert_id]
            alt.status = new_status
            if reviewer_notes:
                alt.reviewer_notes = reviewer_notes
            return alt
        return None

    def generate_report(
        self,
        auth: Optional[AuthContext] = None,
        c_filter: Optional[CohortFilter] = None
    ) -> PlacementIntelligenceReport:
        """
        Generate complete, auditable placement officer intelligence report.
        Enforces RBAC authorization before data retrieval.
        """
        self.enforce_auth(auth)
        filtered = self.filter_records(self.raw_records, c_filter)

        kpis = self.calculate_cohort_kpis(filtered)
        skill_gaps = self.analyze_skill_gaps(filtered, top_n=6)
        quality = self.build_quality_breakdown(filtered, skill_gaps)

        # Load Fairness Audit Summary
        fairness_summary = None
        if self.fairness_path.exists():
            try:
                with open(self.fairness_path, "r", encoding="utf-8") as f:
                    fairness_summary = json.load(f)
            except Exception:
                pass

        alerts = self.generate_alerts(kpis, quality, fairness_summary)

        # Domain breakdown
        domain_perf = {}
        for r in filtered:
            dom = r.get("matched_question", {}).get("domain", "General")
            cal_cont = r.get("scores", {}).get("calibrated_content")
            s = round((float(cal_cont) - 1.0) / 4.0 * 100.0, 1) if cal_cont is not None else 50.0
            domain_perf.setdefault(dom, []).append(s)

        domain_avg = {d: round(float(np.mean(vals)), 1) for d, vals in domain_perf.items()}

        report_id = f"REP_POI_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}"

        return PlacementIntelligenceReport(
            report_id=report_id,
            auth_user=auth.user_id if auth else "SYSTEM_ADMIN",
            cohort_filter=c_filter or CohortFilter(),
            kpis=kpis,
            quality_breakdown=quality,
            alerts=alerts,
            fairness_summary=fairness_summary,
            domain_performance=domain_avg
        )

    def export_dashboard_reports(
        self,
        report: PlacementIntelligenceReport,
        output_dir: Optional[Path] = None
    ) -> Tuple[Path, Path]:
        """Save institutional placement intelligence package as JSON and Markdown."""
        out_dir = output_dir or (REPO_ROOT / "reports")
        out_dir.mkdir(parents=True, exist_ok=True)

        json_path = out_dir / "placement_intelligence_report.json"
        md_path = out_dir / "placement_intelligence_report.md"

        # 1. Save JSON
        with open(json_path, "w", encoding="utf-8") as f:
            json.dump(report.model_dump(), f, indent=2)

        # 2. Save Markdown
        lines = [
            "# IMAIRA FairScore — Placement Officer Institutional Intelligence Report",
            f"**Report ID:** `{report.report_id}` | **Generated:** {report.generated_at}",
            f"**Authorized Officer:** `{report.auth_user}`",
            "",
            "---",
            "## 1. Cohort Performance Overview & Statistical KPIs",
            "",
            f"- **Total Students Evaluated:** {report.kpis.total_students_enrolled}",
            f"- **Total Interviews Conducted:** {report.kpis.total_interviews_conducted}",
            f"- **Average Verified Content Score:** `{report.kpis.average_verified_content_score} / 100`",
            f"- **Average Provisional Score:** `{report.kpis.average_provisional_content_score or 'None active'}`",
            f"- **Median Score:** `{report.kpis.median_content_score}` | **Std Dev:** `{report.kpis.content_score_std_dev}`",
            f"- **Evaluations Requiring Review:** `{report.kpis.evaluations_requiring_review_pct}%` ({report.kpis.unresolved_evaluations_count} unresolved)",
            "",
            "### Score Distribution",
            f"- 80–100 (Exemplary): {report.kpis.score_distribution_buckets.get('80-100', 0)}",
            f"- 60–79 (Proficient): {report.kpis.score_distribution_buckets.get('60-79', 0)}",
            f"- 40–59 (Developing): {report.kpis.score_distribution_buckets.get('40-59', 0)}",
            f"- 0–39 (Needs Attention): {report.kpis.score_distribution_buckets.get('0-39', 0)}",
            "",
            "---",
            "## 2. Student Skill Gap Analytics",
            "",
            "The following technical concepts had the highest marks lost across the cohort:",
            "",
            "| Concept | Domain | Assessed | Fail Rate | Avg Marks Lost | Status |",
            "|---|---|---:|---:|---:|---:|"
        ]

        for g in report.quality_breakdown.top_skill_gaps:
            status_tag = "✅ Confirmed Gap" if g.is_confirmed_skill_gap else "⚠️ ASR Confounded"
            lines.append(
                f"| {g.concept_name[:40]} | {g.domain[:20]} | {g.students_assessed_count} | "
                f"{g.failure_rate_pct}% | **{g.average_marks_lost:.2f}** | {status_tag} |"
            )

        lines.extend([
            "",
            "---",
            "## 3. Evaluation Quality Monitoring (The 4 Independent Dimensions)",
            "",
            "### Category 1: Student Skill Gaps (Confirmed Technical Deficiencies)",
            f"- Total confirmed conceptual weaknesses: `{report.quality_breakdown.confirmed_skill_gaps_count}`",
            "",
            "### Category 2: ASR Recognition Problems",
            f"- Suspicious transcript segments flagged: `{report.quality_breakdown.suspicious_segments_count}`",
            f"- Audio-verified acoustic slice corrections applied: `{report.quality_breakdown.audio_verified_corrections_count}`",
            f"- Unresolved ASR segments: `{report.quality_breakdown.unresolved_asr_segments_count}`",
            f"- Interviews with speech recognition incidents: `{report.quality_breakdown.interviews_with_asr_issues}`",
            "",
            "### Category 3: Uncertain Evaluation Decisions",
            f"- Provisional evaluations active: `{report.quality_breakdown.provisional_evaluations_count}`",
            f"- Evaluations pending human review: `{report.quality_breakdown.pending_human_reviews_count}`",
            f"- Marks protected/affected by uncertainty: `{report.quality_breakdown.marks_affected_by_uncertainty:.1f} pts`",
            "",
            "### Category 4: Human-versus-System Disagreement",
            f"- Human-reviewed benchmark recordings: `{report.quality_breakdown.human_reviewed_count}`",
            f"- Mean Absolute Error (MAE): `{report.quality_breakdown.human_system_mae or 'N/A'}` pts",
            f"- Disagreements exceeding 15 points: `{report.quality_breakdown.significant_disagreements_count}`",
            "",
            "---",
            "## 4. Evaluation Quality Alerts & Management",
            ""
        ])

        for a in report.alerts:
            sev_badge = f"[{a.severity.upper()}]"
            lines.append(f"### {sev_badge} {a.title} (`{a.alert_id}`)")
            lines.append(f"- **Category:** `{a.category}` | **Status:** `{a.status.upper()}`")
            lines.append(f"- **Description:** {a.description}")
            lines.append(f"- **Recommended Action:** {a.recommended_action}")
            if a.reviewer_notes:
                lines.append(f"- **Reviewer Notes:** {a.reviewer_notes}")
            lines.append("")

        with open(md_path, "w", encoding="utf-8") as f:
            f.write("\n".join(lines))

        return json_path, md_path
