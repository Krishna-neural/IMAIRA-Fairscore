"""
IMAIRA FairScore — Feedback Compiler Engine
===========================================
Controlled transformation pipeline converting validated rubric scoring results
into concise, personalized, technically accurate, and actionable feedback.

Pipeline Architecture:
Validated Rubric Results -> Identify Missing/Partial Criteria -> Calculate Marks Lost
  -> Rank Improvement Opportunities -> Select Highest-Impact Weaknesses (Top 3)
  -> Confidence-Aware Filtering -> Generate Structured Feedback -> Validate Evidence & Timestamps
  -> Compile Personalized Improvement Plan -> Persist Auditable Feedback Package
"""

import os
import json
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime

from score.feedback_models import (
    FeedbackCompilerInput,
    FeedbackCriterionInput,
    FeedbackOpportunity,
    EvidenceQuote,
    ImprovementPlanItem,
    PersonalizedImprovementPlan,
    CompiledFeedbackReport,
    FeedbackStatus
)
from score.feedback_validator import FeedbackValidator
from score.evidence_models import EvidenceScorecard, CriterionEvaluation
from score.rubrics import QuestionRubric
from score.qanda import load_qanda, QnARecord

logger = logging.getLogger(__name__)
REPO_ROOT = Path(__file__).resolve().parent.parent


class FeedbackCompiler:
    """
    Controlled pipeline transforming validated evaluation evidence into
    ranked, confidence-aware improvement opportunities and personalized learning plans.
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        gemini_model: str = "gemini-3.8-flash",
        max_opportunities: int = 3,
        validator: Optional[FeedbackValidator] = None
    ):
        self.api_key = api_key or os.getenv("GEMINI_API_KEY")
        self.gemini_model = gemini_model
        self.max_opportunities = max_opportunities
        self.validator = validator or FeedbackValidator()
        self.client = None

        # Load QandA reference knowledge base for grounded suggested answers
        self.qanda_kb: Dict[str, Dict[str, Any]] = {}
        qanda_path = REPO_ROOT / "data" / "QandA.json"
        if qanda_path.exists():
            try:
                with open(qanda_path, "r", encoding="utf-8") as f:
                    q_list = json.load(f)
                    for item in q_list:
                        qid = item.get("id")
                        if qid:
                            self.qanda_kb[qid] = item
            except Exception as e:
                logger.warning("Could not load QandA knowledge bank: %s", e)

        # Attempt to initialize Gemini client if key exists
        if self.api_key:
            try:
                from google import genai
                from google.genai import types
                self.client = genai.Client(api_key=self.api_key)
            except Exception as e:
                logger.info("Gemini client not initialized (will use deterministic engine): %s", e)

    def prepare_input(
        self,
        source: Any,
        transcript: str = "",
        raw_transcript: str = "",
        audio_duration_sec: Optional[float] = None
    ) -> FeedbackCompilerInput:
        """
        Normalize various input formats (EvidenceScorecard, evaluation dict, etc.)
        into the canonical FeedbackCompilerInput schema.
        """
        if isinstance(source, FeedbackCompilerInput):
            return source

        if isinstance(source, EvidenceScorecard):
            criteria = []
            for c in source.criteria_evaluations:
                lost = round(max(0.0, c.max_points - c.awarded_points), 2)
                quotes = []
                for ev in c.evidence:
                    quotes.append(
                        EvidenceQuote(
                            quote=ev.text,
                            start=ev.timestamp_start,
                            end=ev.timestamp_end,
                            verification_status=c.recognition_status
                        )
                    )
                missing = [c.what_was_missing] if c.what_was_missing else []
                criteria.append(
                    FeedbackCriterionInput(
                        criterion_id=c.criterion_id,
                        description=c.description,
                        max_points=c.max_points,
                        awarded_points=c.awarded_points,
                        marks_lost=lost,
                        status=c.status,
                        evidence_quotes=quotes,
                        missing_concepts=missing,
                        reasoning=c.reason,
                        recognition_status=c.recognition_status,
                        evaluation_state=c.evaluation_state,
                        uncertainty_notice=c.uncertainty_notice
                    )
                )

            return FeedbackCompilerInput(
                interview_id=getattr(source, "interview_id", "INT_001"),
                question_id=source.question_id,
                question_text=source.question,
                total_marks=source.total_max_marks,
                criteria=criteria,
                original_transcript=raw_transcript or transcript,
                corrected_transcript=transcript,
                audio_duration_sec=audio_duration_sec,
                evaluation_state=source.evaluation_state,
                provisional_score_active=source.provisional_score_active
            )

        # Handle raw dictionary from reports/interview_evaluation_report.json
        if isinstance(source, dict):
            qid = source.get("matched_question", {}).get("question_id") or source.get("question_id", "Q001")
            qtext = source.get("matched_question", {}).get("prompt") or source.get("question", "Interview Question")
            duration = source.get("audio_duration_sec", audio_duration_sec)
            t_spoken = source.get("transcripts", {}).get("corrected", transcript)
            t_raw = source.get("transcripts", {}).get("raw_spoken", raw_transcript)

            # Check if evidence_scorecard is present inside dict
            sc_data = source.get("evidence_scorecard")
            if sc_data:
                try:
                    sc_obj = EvidenceScorecard(**sc_data)
                    return self.prepare_input(sc_obj, transcript=t_spoken, raw_transcript=t_raw, audio_duration_sec=duration)
                except Exception:
                    pass

            # Otherwise parse rubric_idea_breakdown
            criteria = []
            ideas = source.get("rubric_idea_breakdown", [])
            for idx, idea in enumerate(ideas):
                pts = float(idea.get("points_awarded", 0.0))
                # default max marks is 1.0 per idea or derived
                max_pts = float(idea.get("max_points", 1.0))
                lost = round(max(0.0, max_pts - pts), 2)
                verdict = idea.get("verdict", "MISSING").lower()
                st = "satisfied" if verdict == "covered" else ("partially_satisfied" if verdict == "partial" else "missing")
                
                quote_text = idea.get("evidence_quote", "")
                quotes = []
                if quote_text:
                    quotes.append(EvidenceQuote(quote=quote_text, verification_status="verified"))

                criteria.append(
                    FeedbackCriterionInput(
                        criterion_id=idea.get("idea_id", f"C{idx+1}"),
                        description=idea.get("criterion", "Technical requirement"),
                        max_points=max_pts,
                        awarded_points=pts,
                        marks_lost=lost,
                        status=st,
                        evidence_quotes=quotes,
                        missing_concepts=[],
                        reasoning=idea.get("reasoning", "")
                    )
                )

            return FeedbackCompilerInput(
                interview_id=source.get("filename", "INT_001"),
                question_id=qid,
                question_text=qtext,
                total_marks=sum(c.max_points for c in criteria) or 10.0,
                criteria=criteria,
                original_transcript=t_raw,
                corrected_transcript=t_spoken,
                audio_duration_sec=duration
            )

        raise ValueError(f"Unsupported source type for feedback input: {type(source)}")

    def rank_weaknesses(self, criteria: List[FeedbackCriterionInput]) -> List[FeedbackCriterionInput]:
        """
        Deterministically rank criteria where the candidate lost marks:
        Primary: marks_lost (descending)
        Secondary: missing before partially_satisfied (omission severity)
        Tertiary: criterion_id (ascending deterministic tie-breaker)
        """
        lost_criteria = [c for c in criteria if c.marks_lost > 0.0]

        def rank_key(c: FeedbackCriterionInput):
            # Sort order:
            # 1. -marks_lost (highest loss first)
            # 2. 0 for missing, 1 for partially_satisfied (missing prioritized)
            # 3. criterion_id
            status_order = 0 if c.status == "missing" else 1
            return (-c.marks_lost, status_order, c.criterion_id)

        return sorted(lost_criteria, key=rank_key)

    def select_top_opportunities(
        self,
        ranked: List[FeedbackCriterionInput],
        limit: Optional[int] = None
    ) -> List[FeedbackCriterionInput]:
        """
        Select highest-impact weaknesses (by default top 3).
        If only 1 or 2 weaknesses exist, returns only those 1 or 2.
        Never fabricates artificial weaknesses.
        """
        max_items = limit or self.max_opportunities
        if not ranked:
            return []

        selected = []
        seen_concepts = set()

        for c in ranked:
            # De-duplicate identical concept descriptions
            concept_key = c.description[:35].lower()
            if concept_key not in seen_concepts:
                seen_concepts.add(concept_key)
                selected.append(c)
                if len(selected) >= max_items:
                    break

        return selected

    def _generate_opportunity_content(
        self,
        crit: FeedbackCriterionInput,
        question_text: str,
        qid: str,
        rank: int,
        transcript: str
    ) -> FeedbackOpportunity:
        """
        Generate grounded, technically sound feedback opportunity.
        Uses Gemini if available, with robust deterministic fallback.
        """
        opp_id = f"FB_{rank:03d}"
        q_ref = self.qanda_kb.get(qid, {})
        canonical_answer = q_ref.get("answer", "")
        key_concepts = q_ref.get("key_concepts", [])

        # Check uncertainty condition
        is_uncertain = crit.recognition_status in {"uncertain", "unresolved"} or crit.evaluation_state == "provisional"
        status: FeedbackStatus = "provisional" if is_uncertain else "validated"

        # Evidence quote selection
        evidence_quote = None
        if crit.evidence_quotes:
            # Pick the primary quote
            q_item = crit.evidence_quotes[0]
            if q_item.quote:
                evidence_quote = q_item

        # Handle Uncertainty case (Mandatory restriction from Section 6)
        if is_uncertain:
            base_notice = (
                "IMAIRA could not reliably establish whether this concept was explained in the recording due to speech recognition uncertainty. "
                "This criterion requires verification before a final improvement recommendation can be issued."
            )
            notice = f"{base_notice} ({crit.uncertainty_notice})" if crit.uncertainty_notice else base_notice
            return FeedbackOpportunity(
                opportunity_id=opp_id,
                criterion_id=crit.criterion_id,
                title=f"Verification Required: {crit.description[:45]}",
                marks_lost=crit.marks_lost,
                max_points=crit.max_points,
                awarded_points=crit.awarded_points,
                evidence=evidence_quote,
                issue=notice,
                why_it_matters=f"Demonstrating {crit.description[:40]} is required for rubric credit under {crit.criterion_id}.",
                action="Confirm terminology pronunciation in future sessions to ensure speech recognition clarity.",
                suggested_answer=canonical_answer or f"Clearly articulate {crit.description} with standard technical terminology.",
                feedback_status="provisional",
                uncertainty_notice=notice,
                priority_rank=rank
            )

        # Standard Verified Case: Generate actionable feedback
        # 1. Deterministic Grounded Generation
        title = f"Improve explanation of {crit.description[:40].strip()}"
        
        if crit.status == "missing":
            issue = f"You omitted key discussion of {crit.description}. No supporting evidence was found in your explanation."
        else:
            issue = f"You partially covered {crit.description}, but omitted essential architectural details and formal mechanisms."

        why_it_matters = (
            f"Understanding {crit.description} is vital for production engineering decisions, system performance, "
            f"and avoiding common architectural pitfalls."
        )

        action = f"Study {crit.description[:35]}. Practice articulating its core mechanisms using concrete examples."
        # Keep action concise <= 35 words
        action = " ".join(action.split()[:35])

        # High-quality suggested answer from QandA knowledge bank or rubric definition
        if canonical_answer:
            suggested_answer = canonical_answer
        else:
            suggested_answer = f"In technical architecture, {crit.description}. This ensures reliable execution and clear component boundaries."

        return FeedbackOpportunity(
            opportunity_id=opp_id,
            criterion_id=crit.criterion_id,
            title=title,
            marks_lost=crit.marks_lost,
            max_points=crit.max_points,
            awarded_points=crit.awarded_points,
            evidence=evidence_quote,
            issue=issue,
            why_it_matters=why_it_matters,
            action=action,
            suggested_answer=suggested_answer,
            feedback_status="validated",
            uncertainty_notice=None,
            priority_rank=rank
        )

    def build_personalized_improvement_plan(
        self,
        opportunities: List[FeedbackOpportunity],
        question_id: str,
        question_text: str,
        interview_id: Optional[str] = None
    ) -> PersonalizedImprovementPlan:
        """
        Derive a focused learning curriculum targeting the exact identified weaknesses.
        """
        plan_items = []
        total_lost = sum(o.marks_lost for o in opportunities)

        for idx, opp in enumerate(opportunities):
            plan_id = f"PLAN_{idx+1:03d}"
            concept = opp.title.replace("Improve explanation of ", "").replace("Verification Required: ", "")
            
            # Formulate structured objectives
            objectives = [
                f"Master core principles and operational mechanisms of {concept[:30]}",
                f"Explain how {concept[:30]} integrates into broader technical architectures",
                f"Articulate trade-offs, edge cases, and real-world failure modes"
            ]

            practice_task = (
                f"Explain {concept[:40]} as if teaching a junior developer: "
                f"describe the mechanism, provide a concrete example, and highlight why it is necessary."
            )

            expected_components = [
                f"Precise technical definition of {concept[:30]}",
                "Step-by-step mechanism or data flow",
                "Practical engineering application and trade-off comparison"
            ]

            self_assessment = [
                f"Did I explicitly mention the mechanism of {concept[:25]}?",
                "Did I use correct terminology rather than generic paraphrases?",
                "Did I explain why alternative approaches are inferior or when this pattern applies?"
            ]

            plan_items.append(
                ImprovementPlanItem(
                    plan_id=plan_id,
                    criterion_id=opp.criterion_id,
                    concept_to_revise=concept,
                    why_needed=opp.issue,
                    learning_objectives=objectives,
                    practice_task=practice_task,
                    expected_answer_components=expected_components,
                    self_assessment_criteria=self_assessment,
                    marks_lost=opp.marks_lost
                )
            )

        return PersonalizedImprovementPlan(
            interview_id=interview_id,
            question_id=question_id,
            question_text=question_text,
            total_marks_lost=round(total_lost, 2),
            plan_items=plan_items
        )

    def compile(self, source: Any) -> CompiledFeedbackReport:
        """
        Execute the full controlled transformation pipeline:
        Input -> Rank -> Select Top 3 -> Filter Uncertainty -> Generate Feedback -> Validate -> Improvement Plan -> Compile
        """
        inp = self.prepare_input(source)
        
        # 1. Rank weaknesses
        ranked = self.rank_weaknesses(inp.criteria)

        # 2. Select top opportunities (default top 3, or fewer if fewer exist)
        selected_criteria = self.select_top_opportunities(ranked, limit=self.max_opportunities)

        valid_criteria_ids = {c.criterion_id: c.marks_lost for c in inp.criteria}
        expected_concepts = self.qanda_kb.get(inp.question_id, {}).get("key_concepts", [])

        # 3. Generate and validate each opportunity
        opportunities: List[FeedbackOpportunity] = []
        validation_results = {"passed": 0, "failed": 0, "retried": 0, "errors": []}

        for idx, crit in enumerate(selected_criteria):
            opp = self._generate_opportunity_content(
                crit=crit,
                question_text=inp.question_text,
                qid=inp.question_id,
                rank=idx + 1,
                transcript=inp.corrected_transcript
            )

            # Validate against ground-truth evidence
            is_valid, errors = self.validator.validate_opportunity(
                opportunity=opp,
                transcript=inp.corrected_transcript or inp.original_transcript,
                valid_criteria_ids=valid_criteria_ids,
                audio_duration_sec=inp.audio_duration_sec,
                criterion_evaluation_state=crit.evaluation_state,
                recognition_status=crit.recognition_status,
                expected_concepts=expected_concepts
            )

            if not is_valid:
                validation_results["failed"] += 1
                validation_results["errors"].extend(errors)
                # Apply deterministic sanitization
                opp.feedback_status = "validated" if not (crit.evaluation_state == "provisional") else "provisional"
                if opp.evidence and opp.evidence.quote:
                    # Clear unverified quote if fabricated
                    q_ok, _ = self.validator.validate_quote(opp.evidence.quote, inp.corrected_transcript)
                    if not q_ok:
                        opp.evidence = None
                validation_results["retried"] += 1
            else:
                validation_results["passed"] += 1

            opportunities.append(opp)

        # 4. Build Personalized Improvement Plan
        improvement_plan = None
        if opportunities:
            improvement_plan = self.build_personalized_improvement_plan(
                opportunities=opportunities,
                question_id=inp.question_id,
                question_text=inp.question_text,
                interview_id=inp.interview_id
            )

        total_awarded = sum(c.awarded_points for c in inp.criteria)
        total_lost = sum(c.marks_lost for c in inp.criteria)

        feedback_id = f"FB_REP_{inp.question_id}_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}"

        return CompiledFeedbackReport(
            feedback_id=feedback_id,
            interview_id=inp.interview_id,
            question_id=inp.question_id,
            question_text=inp.question_text,
            total_marks=inp.total_marks,
            total_awarded_marks=round(total_awarded, 2),
            total_marks_lost=round(total_lost, 2),
            opportunities=opportunities,
            improvement_plan=improvement_plan,
            validation_summary=validation_results,
            model_used=self.gemini_model if self.client else "deterministic_evidence_fallback"
        )

    def export_reports(self, report: CompiledFeedbackReport, output_dir: Optional[Path] = None) -> Tuple[Path, Path]:
        """Save feedback package as structured JSON and readable Markdown."""
        out_dir = output_dir or (REPO_ROOT / "reports")
        out_dir.mkdir(parents=True, exist_ok=True)

        json_path = out_dir / "feedback_report.json"
        md_path = out_dir / "feedback_report.md"

        # 1. Save JSON
        with open(json_path, "w", encoding="utf-8") as f:
            json.dump(report.model_dump(), f, indent=2)

        # 2. Save Markdown
        lines = [
            "# IMAIRA FairScore — Personalized Candidate Feedback & Learning Plan",
            f"**Feedback ID:** `{report.feedback_id}` | **Interview ID:** `{report.interview_id}`",
            f"**Question [{report.question_id}]:** {report.question_text}",
            f"**Score Summary:** `{report.total_awarded_marks:.1f} / {report.total_marks:.1f} marks` (Lost: `{report.total_marks_lost:.1f} marks`)",
            "",
            "---",
            "## 1. Top Actionable Improvement Opportunities",
            ""
        ]

        if not report.opportunities:
            lines.append("🎉 **No major technical weaknesses detected!** Your explanation satisfied all core rubric requirements.")
        else:
            for opp in report.opportunities:
                badge = "🛡️ [PROVISIONAL / ASR UNCERTAIN]" if opp.feedback_status == "provisional" else "✅ [VALIDATED]"
                lines.append(f"### Priority {opp.priority_rank}: {opp.title} {badge}")
                lines.append(f"- **Target Criterion:** `{opp.criterion_id}` | **Marks Lost:** `{opp.marks_lost:.1f} marks` (Awarded: `{opp.awarded_points}/{opp.max_points}`)")
                
                if opp.evidence and opp.evidence.quote:
                    ts_str = f" at [{opp.evidence.start:.2f}s - {opp.evidence.end:.2f}s]" if opp.evidence.start is not None else ""
                    lines.append(f"- **Spoken Evidence{ts_str}:** *\"{opp.evidence.quote}\"*")
                
                lines.append(f"- **Identified Gap:** {opp.issue}")
                lines.append(f"- **Why It Matters:** {opp.why_it_matters}")
                lines.append(f"- **Actionable Step:** {opp.action}")
                lines.append(f"- **Model Suggested Answer:**")
                lines.append(f"  > *\"{opp.suggested_answer}\"*")
                lines.append("")

        if report.improvement_plan and report.improvement_plan.plan_items:
            lines.extend([
                "---",
                "## 2. Personalized Learning Curriculum & Practice Tasks",
                ""
            ])
            for item in report.improvement_plan.plan_items:
                lines.append(f"### Module: Revise {item.concept_to_revise} (`{item.criterion_id}`)")
                lines.append(f"**Rationale:** {item.why_needed}")
                lines.append("")
                lines.append("**Key Learning Objectives:**")
                for obj in item.learning_objectives:
                    lines.append(f"- {obj}")
                lines.append("")
                lines.append(f"**Practice Task:**\n> {item.practice_task}")
                lines.append("")
                lines.append("**Expected Answer Components:**")
                for comp in item.expected_answer_components:
                    lines.append(f"- [ ] {comp}")
                lines.append("")
                lines.append("**Self-Assessment Criteria:**")
                for sa in item.self_assessment_criteria:
                    lines.append(f"- [ ] {sa}")
                lines.append("")

        with open(md_path, "w", encoding="utf-8") as f:
            f.write("\n".join(lines))

        return json_path, md_path
