"""
IMAIRA FairScore — Confidence-Aware & Evidence-First Evaluation Dashboard
========================================================================
Interactive Streamlit application providing:
1. Evidence-First Rubric Traceability: "No evidence, no marks"
2. Confidence-Aware Uncertainty: Decoupling ASR recognition failures from rubric evaluation
3. Progressive Disclosure: Executive summary -> Rubric criteria -> Verbatim evidence -> Human Review
"""

import sys
import os
import json
from pathlib import Path
import streamlit as st

# Ensure repository root is on sys.path
REPO_ROOT = Path(__file__).resolve().parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from score.evidence_models import (
    QuestionDefinition,
    RubricCriterion,
    MisconceptionItem,
    EvidenceScorecard,
    load_evidence_question_bank
)
from score.evidence_scorer import DeterministicEvidenceScorer
from score.uncertainty_models import (
    UncertaintyRecord,
    UncertaintyPolicy,
    RecognitionStatus,
    RubricStatus
)
from score.uncertainty_engine import UncertaintyEngine

# Page Configuration
st.set_page_config(
    page_title="IMAIRA FairScore — Confidence-Aware Evaluation",
    page_icon="⚖️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom Styling
st.markdown("""
<style>
    .main-header {
        font-size: 2.2rem;
        font-weight: 700;
        color: #1E293B;
        margin-bottom: 0.2rem;
    }
    .sub-header {
        font-size: 1.05rem;
        color: #64748B;
        margin-bottom: 1.5rem;
    }
    .metric-card {
        background-color: #F8FAFC;
        border-radius: 10px;
        padding: 1.2rem;
        border: 1px solid #E2E8F0;
        text-align: center;
    }
    .badge-satisfied {
        background-color: #DCFCE7;
        color: #166534;
        padding: 4px 10px;
        border-radius: 6px;
        font-weight: 600;
        font-size: 0.85rem;
    }
    .badge-partial {
        background-color: #FEF9C3;
        color: #854D0E;
        padding: 4px 10px;
        border-radius: 6px;
        font-weight: 600;
        font-size: 0.85rem;
    }
    .badge-missing {
        background-color: #FEE2E2;
        color: #991B1B;
        padding: 4px 10px;
        border-radius: 6px;
        font-weight: 600;
        font-size: 0.85rem;
    }
    .badge-review {
        background-color: #EDE9FE;
        color: #6D28D9;
        padding: 4px 10px;
        border-radius: 6px;
        font-weight: 600;
        font-size: 0.85rem;
    }
    .quote-box {
        background-color: #F1F5F9;
        border-left: 4px solid #3B82F6;
        padding: 10px 14px;
        border-radius: 4px;
        font-family: monospace;
        font-size: 0.92rem;
        margin: 6px 0;
    }
</style>
""", unsafe_allow_html=True)

# Header
st.markdown('<div class="main-header">⚖️ IMAIRA FairScore — Confidence-Aware & Evidence-First Evaluation</div>', unsafe_allow_html=True)
st.markdown('<div class="sub-header">Explainable, fair interview intelligence. Principles: <strong>No evidence, no marks</strong> & <strong>Recognition uncertainty is not rubric failure</strong>.</div>', unsafe_allow_html=True)

# Load Question Bank
question_bank = load_evidence_question_bank()
if not question_bank:
    st.error("Could not find evidence question bank in data/evidence_question_bank.json")
    st.stop()

# Initialize Engines
scorer = DeterministicEvidenceScorer()
uncertainty_engine = UncertaintyEngine()

# Sidebar: File / Question Selection
st.sidebar.header("📁 Evaluation Source")
mode = st.sidebar.radio("Data Source Mode", ["Inspect Batch Results", "Live Interactive Simulator", "Human Review Audit Portal"])

# Load recent evaluation report
report_path = REPO_ROOT / "reports" / "interview_evaluation_report.json"
evaluation_data = []
if report_path.exists():
    try:
        with open(report_path, "r", encoding="utf-8") as f:
            evaluation_data = json.load(f)
    except Exception:
        pass


if mode == "Inspect Batch Results" and evaluation_data:
    filenames = [item["filename"] for item in evaluation_data]
    selected_file = st.sidebar.selectbox("Select Candidate Recording", filenames)
    record = next((item for item in evaluation_data if item["filename"] == selected_file), None)

    if record:
        q_info = record.get("matched_question", {})
        qid = q_info.get("question_id", "Q032")
        question_def = question_bank.get(qid)
        
        # Audio Player if file exists
        audio_file_path = REPO_ROOT / "asr" / selected_file
        if not audio_file_path.exists():
            audio_file_path = REPO_ROOT.parent / "asr" / selected_file
        if audio_file_path.exists():
            st.sidebar.audio(str(audio_file_path))

        # Check if record has evidence_scorecard
        scorecard_data = record.get("evidence_scorecard")
        scorecard = EvidenceScorecard(**scorecard_data) if scorecard_data else None

        # Display Provisional Notice Banner if applicable
        if scorecard and scorecard.provisional_score_active:
            st.info(
                f"ℹ️ **PROVISIONAL EVALUATION ACTIVE ({scorecard.provisional_marks_total:.2f} pts provisional credit):** "
                "One or more rubric criteria are affected by ambiguous speech recognition. "
                "Provisional credit is awarded to protect the candidate against speech recognition failures."
            )
        elif scorecard and scorecard.manual_review_pending:
            st.warning(
                "🔍 **HUMAN REVIEW PENDING:** "
                "Acoustic verification remains inconclusive for one or more technical terms. "
                "This evaluation has been flagged for human expert confirmation."
            )

        # Top Level Summary Metrics
        scores = record.get("scores", {})
        c1, c2, c3, c4 = st.columns(4)
        with c1:
            fairscore_val = scorecard.overall_fairscore_5pt if scorecard else scores.get('overall_fairscore', 0.0)
            state_label = f" ({scorecard.evaluation_state.upper()})" if scorecard else ""
            st.metric(
                label=f"Overall FairScore{state_label}",
                value=f"{fairscore_val:.2f} / 5.0",
                delta=f"{fairscore_val*20:.0f}%"
            )
        with c2:
            comp_val = scorecard.content_completeness_5pt if scorecard else scores.get('content_completeness', 0.0)
            st.metric(
                label="Content Completeness",
                value=f"{comp_val:.2f} / 5.0",
                help="Proportion of rubric criteria demonstrated by verbatim evidence"
            )
        with c3:
            st.metric(
                label="Technical Correctness",
                value=f"{scores.get('content_correctness', 0.0):.2f} / 5.0",
                help="Evaluated against critical technical misconceptions and errors"
            )
        with c4:
            st.metric(
                label="Answer Structure",
                value=f"{scores.get('answer_structure', 0.0):.2f} / 5.0",
                help="Normalized 1.0 - 5.0 structural organization (Framing, Coherence, Closure)"
            )

        st.markdown("---")
        
        # Matched Question Context
        st.subheader(f"📌 Interview Question: {q_info.get('prompt', 'Technical Question')}")
        st.caption(f"Domain: **{q_info.get('domain', 'General')}** | Question ID: **{qid}** | Match Confidence: **{q_info.get('match_confidence', 1.0)*100:.0f}%**")

        # Two Columns: Spoken Transcript & ASR Diagnostics
        col_t1, col_t2 = st.columns([3, 2])
        with col_t1:
            st.markdown("#### 🎙️ Spoken Transcript")
            raw_t = record.get("transcripts", {}).get("raw_spoken", "")
            rec_t = record.get("transcripts", {}).get("corrected", "")
            st.markdown(f"**Recognized Answer:** {rec_t}")
            with st.expander("Show Raw Acoustic Transcript (Pre-Recovery)"):
                st.code(raw_t)

        with col_t2:
            st.markdown("#### 🛠️ Acoustic Recovery Diagnostics")
            corrs = record.get("corrections_made", [])
            if corrs:
                for c in corrs:
                    st.info(f"**[{c.get('timestamp')}]** '{c.get('original_spoken')}' ➔ **'{c.get('corrected_term')}'** ({c.get('reason')})")
            else:
                st.success("No phonetic or glossary discrepancies detected. Transcript is 100% accurate.")

        st.markdown("---")

        # Level 2: Rubric Criterion-by-Criterion Progressive Disclosure
        st.subheader("🔍 Rubric Evidence Trail & Uncertainty Breakdown")
        
        if scorecard:
            for crit in scorecard.criteria_evaluations:
                if crit.evaluation_state == "provisional":
                    badge = '<span class="badge-partial">⚠️ PROVISIONAL CREDIT (UNRESOLVED ASR)</span>'
                elif crit.evaluation_state == "pending_review":
                    badge = '<span class="badge-review">🔍 PENDING HUMAN REVIEW</span>'
                elif crit.status == "satisfied":
                    badge = '<span class="badge-satisfied">✅ FINAL VERIFIED</span>'
                elif crit.status == "partially_satisfied":
                    badge = '<span class="badge-partial">⚠️ PARTIALLY SATISFIED</span>'
                else:
                    badge = '<span class="badge-missing">❌ MISSING KNOWLEDGE</span>'

                with st.expander(f"{crit.criterion_id}: {crit.description} — {crit.awarded_points}/{crit.max_points} pts", expanded=(crit.status != "satisfied")):
                    st.markdown(f"**Status:** {badge} &nbsp;&nbsp;|&nbsp;&nbsp; **Marks Awarded:** `{crit.awarded_points} / {crit.max_points}`", unsafe_allow_html=True)
                    st.markdown(f"**Evaluator Rationale:** {crit.reason}")

                    # Explanatory notice for uncertainty
                    if crit.uncertainty_notice:
                        st.info(f"🛡️ **Fairness Guard:** {crit.uncertainty_notice}")

                    if crit.evidence:
                        st.markdown("**Verbatim Supporting Evidence Spans:**")
                        for ev in crit.evidence:
                            st.markdown(f'<div class="quote-box">"{ev.text}" (offsets: {ev.source_start}-{ev.source_end})</div>', unsafe_allow_html=True)
                    else:
                        st.caption("No verbatim evidence span found in candidate response.")

                    if crit.what_was_right:
                        st.markdown(f"👍 **What was right:** {crit.what_was_right}")
                    if crit.what_was_missing:
                        st.markdown(f"⚠️ **What was missing:** {crit.what_was_missing}")
                    if crit.how_to_improve:
                        st.markdown(f"💡 **How to improve (≤ 30 words):** _{crit.how_to_improve}_")
        else:
            # Fallback to rubric_idea_breakdown
            ideas = record.get("rubric_idea_breakdown", [])
            for r in ideas:
                v = r.get("verdict", "MISSING")
                with st.expander(f"Idea {r.get('idea_id')}: {r.get('criterion')} — {v}"):
                    st.write(f"Points Awarded: {r.get('points_awarded')}")
                    if r.get("evidence_quote"):
                        st.markdown(f'<div class="quote-box">"{r.get("evidence_quote")}"</div>', unsafe_allow_html=True)
                    st.write(f"Reasoning: {r.get('reasoning')}")

        # Uncertainty Records Detail
        uncertainty_recs = record.get("uncertainty_records", [])
        if uncertainty_recs:
            st.markdown("---")
            st.subheader("🛡️ Speech Recognition Uncertainty Records")
            st.caption("Detailed tracking of suspicious speech segments, audio verification methods, and rubric linkages.")
            for rec in uncertainty_recs:
                with st.expander(f"Segment [{rec.get('segment_id')}]: '{rec.get('original_text')}' ➔ '{rec.get('corrected_text') or 'None'}' ({rec.get('recognition_status').upper()})"):
                    st.write(f"- **Timestamp:** {rec.get('start'):.2f}s - {rec.get('end'):.2f}s")
                    st.write(f"- **ASR Confidence:** {rec.get('asr_confidence') if rec.get('asr_confidence') is not None else 'Unavailable'}")
                    st.write(f"- **Recognition Status:** `{rec.get('recognition_status')}`")
                    st.write(f"- **Correction Status:** `{rec.get('correction_status')}`")
                    st.write(f"- **Verification Method:** `{rec.get('verification_method')}`")
                    st.write(f"- **Verification Reason:** {rec.get('verification_reason')}")
                    st.write(f"- **Linked Criteria:** {', '.join(rec.get('linked_criterion_ids', []))}")


elif mode == "Human Review Audit Portal":
    st.subheader("👨‍⚖️ Human Expert Review & Audit Portal")
    st.write("Review flagged ambiguous speech segments, verify candidate recordings, and trigger deterministic re-scoring.")

    if not evaluation_data:
        st.warning("No evaluation data found. Run evaluate_interview.py first.")
        st.stop()

    # Find records with uncertainty or provisional scores
    flagged_files = [
        item["filename"] for item in evaluation_data
        if item.get("evidence_scorecard", {}).get("provisional_score_active")
        or item.get("uncertainty_records")
    ]
    if not flagged_files:
        flagged_files = [item["filename"] for item in evaluation_data]

    sel_file = st.selectbox("Select Interview Recording to Audit", flagged_files)
    rec = next(item for item in evaluation_data if item["filename"] == sel_file)
    scorecard_dict = rec.get("evidence_scorecard")

    if not scorecard_dict:
        st.error("No evidence scorecard available for this file.")
        st.stop()

    sc = EvidenceScorecard(**scorecard_dict)
    st.markdown(f"**Current Overall FairScore:** `{sc.overall_fairscore_5pt:.2f} / 5.0` | **State:** `{sc.evaluation_state.upper()}`")

    if not sc.uncertainty_records:
        st.info("No suspicious or uncertain segments detected in this interview.")
    else:
        for u_rec in sc.uncertainty_records:
            st.markdown("---")
            st.markdown(f"#### Segment [{u_rec.segment_id}]: Spoken '{u_rec.original_text}' (at {u_rec.start:.2f}s - {u_rec.end:.2f}s)")
            st.write(f"- **Proposed Term:** `{u_rec.corrected_text or 'None'}`")
            st.write(f"- **Current Status:** Recognition: `{u_rec.recognition_status}` | Correction: `{u_rec.correction_status}`")
            st.write(f"- **Verification Reason:** {u_rec.verification_reason}")
            st.write(f"- **Linked Criteria:** {', '.join(u_rec.linked_criterion_ids)}")

            col_a, col_b = st.columns(2)
            with col_a:
                if st.button(f"✅ Approve Spoken Concept for [{u_rec.segment_id}]", key=f"app_{u_rec.segment_id}"):
                    updated_sc = uncertainty_engine.apply_human_review(
                        scorecard=sc,
                        segment_id=u_rec.segment_id,
                        decision="human_approved",
                        reviewer_notes="Human expert verified audio recording demonstrates technical concept."
                    )
                    st.success(f"Approved! Rescored Overall FairScore: {updated_sc.overall_fairscore_5pt:.2f} / 5.0 (State: {updated_sc.evaluation_state})")
                    st.rerun()

            with col_b:
                if st.button(f"❌ Confirm Missing Knowledge for [{u_rec.segment_id}]", key=f"rej_{u_rec.segment_id}"):
                    updated_sc = uncertainty_engine.apply_human_review(
                        scorecard=sc,
                        segment_id=u_rec.segment_id,
                        decision="human_rejected",
                        reviewer_notes="Human expert confirmed audio does not articulate the required technical concept."
                    )
                    st.warning(f"Rejected. Rescored Overall FairScore: {updated_sc.overall_fairscore_5pt:.2f} / 5.0 (State: {updated_sc.evaluation_state})")
                    st.rerun()


else:
    # Mode 2: Live Interactive Simulator
    st.subheader("🧪 Live Confidence-Aware Simulator")
    st.write("Test answers against structured rubrics with simulated ASR errors and audio recheck.")

    selected_qid = st.selectbox("Select Question to Simulate", list(question_bank.keys()), format_func=lambda k: f"[{k}] {question_bank[k].question}")
    q_def = question_bank[selected_qid]

    st.markdown(f"**Domain:** `{q_def.domain}` &nbsp;|&nbsp; **Difficulty:** `{q_def.difficulty}` &nbsp;|&nbsp; **Total Marks:** `{q_def.total_marks}`")

    # Display Rubric
    with st.expander("View Question Rubric Criteria"):
        for c in q_def.rubric:
            st.markdown(f"- **{c.criterion_id} ({c.max_points} pts):** {c.description}")

    col_sim1, col_sim2 = st.columns(2)
    with col_sim1:
        candidate_input = st.text_area(
            "Candidate Transcript Response (Simulate with speech recognition typo):",
            value="A has map is a data structure that maps keys to values. Hash collisions occur when two keys share a bucket.",
            height=120
        )
    with col_sim2:
        sim_conf = st.slider("Simulated ASR Confidence for suspicious terms", 0.10, 1.0, 0.45)
        sim_audio_verified = st.checkbox("Audio Slice Verification Confirms Correction ('has map' ➔ 'hash map')", value=True)

    if st.button("Evaluate Transcript (Confidence-Aware Pipeline)", type="primary"):
        norm_text = candidate_input.lower()
        raw_evals = []

        # Check for matches
        for c in q_def.rubric:
            alts = [a.lower() for a in (c.acceptable_alternatives or [])]
            matched_span = None
            for alt in alts:
                if alt in norm_text:
                    matched_span = alt
                    break

            if matched_span:
                raw_evals.append({
                    "criterion_id": c.criterion_id,
                    "status": "satisfied",
                    "evidence": [{"text": matched_span}],
                    "reason": f"Verbatim match for criterion '{c.description[:30]}...'"
                })
            else:
                raw_evals.append({
                    "criterion_id": c.criterion_id,
                    "status": "missing",
                    "evidence": [],
                    "reason": f"No verbatim match found in transcript."
                })

        # Create simulated uncertainty record
        sim_u_recs = [
            UncertaintyRecord(
                segment_id="S001",
                question_id=q_def.question_id,
                original_text="has map",
                corrected_text="hash map" if sim_audio_verified else None,
                start=1.2,
                end=2.4,
                asr_confidence=sim_conf,
                recognition_status="verified" if sim_audio_verified else "uncertain",
                rubric_status="satisfied" if sim_audio_verified else "pending_verification",
                correction_status="audio_verified" if sim_audio_verified else "unresolved",
                uncertainty_level="medium" if sim_conf > 0.35 else "high",
                verification_method="audio_recheck",
                linked_criterion_ids=["R1"],
                verification_reason="Simulated audio verification recheck"
            )
        ]

        scorecard = scorer.calculate_scorecard(
            question=q_def,
            raw_evidence_evaluations=raw_evals,
            misconceptions=[],
            transcript_text=candidate_input,
            raw_structure_scores={"framing": 4.5, "coherence": 4.5, "closure": 4.5},
            uncertainty_records=sim_u_recs,
            uncertainty_engine=uncertainty_engine
        )

        st.success(f"Evaluation Complete! State: **{scorecard.evaluation_state.upper()}**")

        m1, m2, m3, m4 = st.columns(4)
        m1.metric("Total Marks", f"{scorecard.total_awarded_marks} / {scorecard.total_max_marks}")
        m2.metric("Percentage", f"{scorecard.percentage_score}%")
        m3.metric("Completeness (5pt)", f"{scorecard.content_completeness_5pt} / 5.0")
        m4.metric("Calibrated FairScore", f"{scorecard.overall_fairscore_5pt} / 5.0")

        st.markdown("### Criterion Breakdown")
        for ev in scorecard.criteria_evaluations:
            with st.expander(f"{ev.criterion_id}: {ev.description} — {ev.awarded_points}/{ev.max_points} pts", expanded=True):
                st.write(f"State: **{ev.evaluation_state.upper()}** | Recognition: `{ev.recognition_status}`")
                if ev.uncertainty_notice:
                    st.info(f"🛡️ {ev.uncertainty_notice}")
                st.write(f"Evaluator Rationale: {ev.reason}")
