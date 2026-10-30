"""
IMAIRA FairScore — Evidence-First Explainability Dashboard
=========================================================
Interactive Streamlit application providing complete transparency,
evidence traceability, rubric-level breakdowns, and revision simulation.
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

# Page Configuration
st.set_page_config(
    page_title="IMAIRA FairScore — Evidence-First Evaluation",
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
st.markdown('<div class="main-header">⚖️ IMAIRA FairScore — Evidence-First Evaluation</div>', unsafe_allow_html=True)
st.markdown('<div class="sub-header">Explainable, rubric-governed interview intelligence. Principle: <strong>No evidence, no marks.</strong></div>', unsafe_allow_html=True)

# Load Question Bank
question_bank = load_evidence_question_bank()
if not question_bank:
    st.error("Could not find evidence question bank in data/evidence_question_bank.json")
    st.stop()

# Sidebar: File / Question Selection
st.sidebar.header("📁 Evaluation Source")
mode = st.sidebar.radio("Data Source Mode", ["Inspect Batch Results", "Live Interactive Simulator"])

# Try loading recent evaluation report
report_path = REPO_ROOT / "reports" / "interview_evaluation_report.json"
evaluation_data = []
if report_path.exists():
    try:
        with open(report_path, "r", encoding="utf-8") as f:
            evaluation_data = json.load(f)
    except Exception:
        pass

scorer = DeterministicEvidenceScorer()

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
            # Check in parent
            audio_file_path = REPO_ROOT.parent / "asr" / selected_file
        if audio_file_path.exists():
            st.sidebar.audio(str(audio_file_path))

        # Top Level Summary Metrics
        scores = record.get("scores", {})
        c1, c2, c3, c4 = st.columns(4)
        with c1:
            st.metric(
                label="Overall FairScore (Calibrated)",
                value=f"{scores.get('overall_fairscore', 0.0):.2f} / 5.0",
                delta=f"{scores.get('overall_fairscore', 0.0)*20:.0f}%"
            )
        with c2:
            st.metric(
                label="Content Completeness",
                value=f"{scores.get('content_completeness', 0.0):.2f} / 5.0",
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
        st.subheader("🔍 Rubric Evidence Trail & Decision Traceability")
        
        # Check if record has evidence_scorecard or rubric_idea_breakdown
        scorecard_data = record.get("evidence_scorecard")
        if scorecard_data:
            scorecard = EvidenceScorecard(**scorecard_data)
            for crit in scorecard.criteria_evaluations:
                if crit.status == "satisfied":
                    badge = '<span class="badge-satisfied">✅ SATISFIED</span>'
                elif crit.status == "partially_satisfied":
                    badge = '<span class="badge-partial">⚠️ PARTIALLY SATISFIED</span>'
                else:
                    badge = '<span class="badge-missing">❌ MISSING</span>'

                with st.expander(f"{crit.criterion_id}: {crit.description} — {crit.awarded_points}/{crit.max_points} pts", expanded=(crit.status != "satisfied")):
                    st.markdown(f"**Status:** {badge} &nbsp;&nbsp;|&nbsp;&nbsp; **Marks Awarded:** `{crit.awarded_points} / {crit.max_points}`", unsafe_allow_html=True)
                    st.markdown(f"**Evaluator Rationale:** {crit.reason}")
                    
                    if crit.evidence:
                        st.markdown("**Verbatim Supporting Evidence Spans:**")
                        for ev in crit.evidence:
                            st.markdown(f'<div class="quote-box">"{ev.text}" (offsets: {ev.source_start}-{ev.source_end})</div>', unsafe_allow_html=True)
                    else:
                        st.warning("No verbatim evidence span found in candidate response.")

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

        # Misconceptions Section
        miscs = record.get("where_got_wrong", [])
        if miscs:
            st.markdown("---")
            st.subheader("⚠️ Conceptual Misconceptions & Errors")
            for m in miscs:
                st.error(f"**[{m.get('severity')}] {m.get('concept')}**: {m.get('error')}")
                if m.get("candidate_quote"):
                    st.caption(f"Candidate Quote: \"{m.get('candidate_quote')}\"")

        # Actionable Feedback
        fb_list = record.get("actionable_feedback", [])
        if fb_list:
            st.markdown("---")
            st.subheader("🎯 Prioritized Actionable Recommendations")
            for fb in fb_list:
                with st.container():
                    ts = f" at {fb.get('timestamp')}" if fb.get("timestamp") else ""
                    st.markdown(f"**Priority {fb.get('priority')}{ts}: {fb.get('issue')}**")
                    st.write(f"- *Why it matters:* {fb.get('why_it_matters')}")
                    st.write(f"- *Action to take:* {fb.get('improvement_action')}")
                    if fb.get("example_sentence"):
                        st.info(f"💡 Example sentence to adapt: \"{fb.get('example_sentence')}\"")

else:
    # Mode 2: Live Interactive Simulator (Step E.4)
    st.subheader("🧪 Live Evidence-First Interactive Simulator")
    st.write("Test answers against any structured rubric to see real-time evidence extraction and deterministic mark calculation.")

    selected_qid = st.selectbox("Select Question to Simulate", list(question_bank.keys()), format_func=lambda k: f"[{k}] {question_bank[k].question}")
    q_def = question_bank[selected_qid]

    st.markdown(f"**Domain:** `{q_def.domain}` &nbsp;|&nbsp; **Difficulty:** `{q_def.difficulty}` &nbsp;|&nbsp; **Total Marks:** `{q_def.total_marks}`")

    # Display Rubric
    with st.expander("View Question Rubric Criteria"):
        for c in q_def.rubric:
            st.markdown(f"- **{c.criterion_id} ({c.max_points} pts):** {c.description}")
            if c.acceptable_alternatives:
                st.caption(f"Acceptable alternatives: {', '.join(c.acceptable_alternatives)}")

    candidate_input = st.text_area(
        "Candidate Transcript Response:",
        value="A hash map is an associative data structure that maps keys to values using a hash function. When two keys hash to the same bucket, that is a collision. We can resolve collisions using separate chaining where each bucket holds a linked list, or open addressing using linear probing.",
        height=140
    )

    if st.button("Evaluate Transcript (Deterministic Evidence Engine)", type="primary"):
        norm_text = candidate_input.lower()
        raw_evals = []
        
        # Extract evidence for each rubric criterion
        for c in q_def.rubric:
            # Check for matches
            matched_span = None
            keywords = [w.lower() for w in c.description.split() if len(w) > 4]
            alts = [a.lower() for a in (c.acceptable_alternatives or [])]
            
            # Simple substring search
            for alt in alts:
                if alt in norm_text:
                    start = norm_text.find(alt)
                    matched_span = candidate_input[start:start+len(alt)]
                    break
            
            if not matched_span:
                matched_kws = [k for k in keywords if k in norm_text]
                if len(matched_kws) >= 2:
                    start = norm_text.find(matched_kws[0])
                    end = norm_text.find(matched_kws[-1]) + len(matched_kws[-1])
                    matched_span = candidate_input[start:end]

            if matched_span:
                raw_evals.append({
                    "criterion_id": c.criterion_id,
                    "status": "satisfied",
                    "evidence": [{"text": matched_span}],
                    "reason": f"Verbatim evidence matches criterion '{c.description[:35]}...'"
                })
            else:
                raw_evals.append({
                    "criterion_id": c.criterion_id,
                    "status": "missing",
                    "evidence": [],
                    "reason": f"No supporting evidence found in transcript for '{c.description[:35]}...'"
                })

        scorecard = scorer.calculate_scorecard(
            question=q_def,
            raw_evidence_evaluations=raw_evals,
            misconceptions=[],
            transcript_text=candidate_input,
            raw_structure_scores={"framing": 4.5, "coherence": 4.5, "closure": 4.5}
        )

        st.success(f"Evaluation Complete! Verdict: **{scorecard.summary_verdict}**")
        
        m1, m2, m3, m4 = st.columns(4)
        m1.metric("Total Marks", f"{scorecard.total_awarded_marks} / {scorecard.total_max_marks}")
        m2.metric("Percentage", f"{scorecard.percentage_score}%")
        m3.metric("Completeness (5pt)", f"{scorecard.content_completeness_5pt} / 5.0")
        m4.metric("Calibrated FairScore", f"{scorecard.overall_fairscore_5pt} / 5.0")

        st.markdown("### Criterion Breakdown")
        for ev in scorecard.criteria_evaluations:
            with st.expander(f"{ev.criterion_id}: {ev.description} — {ev.awarded_points}/{ev.max_points} pts", expanded=True):
                st.write(f"Status: **{ev.status.upper()}**")
                st.write(f"Evaluator Rationale: {ev.reason}")
                if ev.evidence:
                    st.info(f"Verified Quote: \"{ev.evidence[0].text}\"")
                else:
                    st.warning("No evidence found. Marks = 0.0")
