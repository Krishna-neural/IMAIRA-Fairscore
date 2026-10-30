"""IMAIRA-Fairscore — AI Mock Interviewer Frontend.

Professional, bias-resilient interview evaluation interface separating
content mastery from structural organization and communication fluency.
"""

import os
import sys
from pathlib import Path
from typing import Dict, List
import streamlit as st

# Ensure repository root is in sys.path
REPO_ROOT = Path(__file__).resolve().parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from score.qanda import QnARecord
from frontend.styles import CUSTOM_CSS
from frontend.session import (
    STATE_SETUP,
    STATE_INTERVIEWING,
    STATE_FEEDBACK,
    STATE_COMPLETED,
    init_session_state,
    load_dataset_cached,
    start_interview,
    record_evaluation,
    advance_question,
    reset_interview,
)
from frontend.api_client import (
    check_fairscore_health,
    check_asr_health,
    submit_answer_to_backend,
    transcribe_audio_file,
)

# Page configuration
st.set_page_config(
    page_title="IMAIRA FairScore — AI Mock Interviewer",
    page_icon="🎙️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Inject custom styling
st.markdown(CUSTOM_CSS, unsafe_allow_html=True)

# Initialize state
init_session_state()

# Load question dataset
questions_data = load_dataset_cached("data/QandA.json")


# ==============================================================================
# Sidebar: System Status & Diagnostic Overview
# ==============================================================================

with st.sidebar:
    st.markdown("### ⚙️ System Architecture")
    fairscore_status = check_fairscore_health()
    asr_status = check_asr_health()

    if fairscore_status.get("online"):
        st.markdown(
            f'<span class="badge badge-online">● Backend Online</span> '
            f'<small style="color:#64748b;">(Port 8002)</small>',
            unsafe_allow_html=True
        )
    else:
        st.markdown(
            '<span class="badge badge-direct">⚡ Direct Pipeline</span> '
            '<small style="color:#64748b;">(Standalone)</small>',
            unsafe_allow_html=True
        )

    if asr_status.get("online"):
        st.markdown(
            f'<span class="badge badge-online">● ASR Worker Online</span> '
            f'<small style="color:#64748b;">(Port 8001)</small>',
            unsafe_allow_html=True
        )
    else:
        st.markdown(
            '<span class="badge" style="background-color:#94a3b8;color:#fff;">○ ASR Offline</span> '
            '<small style="color:#64748b;">(Text Mode)</small>',
            unsafe_allow_html=True
        )

    st.markdown("---")
    st.markdown("### 📊 Question Bank Status")
    st.metric("Total Questions", len(questions_data))
    if questions_data:
        categories = sorted(list({q.category for q in questions_data}))
        st.caption(f"**Domains Covered:** {len(categories)} Engineering Disciplines")
        st.caption("**Proposition Standards:** Semantic Rubrics (>=5 words)")
        st.caption("**Calibration:** 5-Fold Cross-Validated Models")

    st.markdown("---")
    st.markdown("### 🛡️ Accent Fairness Invariants")
    st.caption(
        "IMAIRA-Fairscore evaluates technical conceptual depth while remaining "
        "strictly invariant to phonetic STT errors, L2 syntax, and code-mixed fillers."
    )

    if st.session_state.interview_state != STATE_SETUP:
        st.markdown("---")
        if st.button("🚪 Exit Current Interview", use_container_width=True):
            reset_interview()
            st.rerun()


# ==============================================================================
# Header Banner
# ==============================================================================

st.markdown(
    """
    <div class="imaira-header">
        <h1>🎙️ IMAIRA FairScore — AI Mock Technical Interviewer</h1>
        <p>Bias-resilient evaluation separating content mastery from structure and speech fluency.</p>
    </div>
    """,
    unsafe_allow_html=True
)

if st.session_state.error_message:
    st.error(st.session_state.error_message)


# ==============================================================================
# Screen 1: Interview Setup
# ==============================================================================

if st.session_state.interview_state == STATE_SETUP:
    st.markdown("## 🎯 Configure Your Mock Interview")
    st.markdown("Select your target engineering domain, difficulty level, and session length.")

    if not questions_data:
        st.error("No questions could be loaded from `data/QandA.json`. Please verify dataset integrity.")
        st.stop()

    available_categories = ["All Categories"] + sorted(list({q.category for q in questions_data}))
    available_difficulties = ["All Difficulties", "Intermediate", "Advanced", "Expert"]

    col1, col2, col3 = st.columns([2, 1.5, 1.5])
    with col1:
        cat_choice = st.selectbox(
            "Select Engineering Category / Domain:",
            options=available_categories,
            index=0
        )
    with col2:
        diff_choice = st.selectbox(
            "Select Difficulty Rating:",
            options=available_difficulties,
            index=0
        )
    with col3:
        num_choice = st.slider(
            "Number of Questions:",
            min_value=1,
            max_value=10,
            value=3
        )

    # Preview matching count
    preview_matches = [
        q for q in questions_data
        if (cat_choice == "All Categories" or q.category == cat_choice) and
           (diff_choice == "All Difficulties" or q.difficulty == diff_choice)
    ]

    st.info(f"✨ Found **{len(preview_matches)}** matching technical questions available in the pool.")

    st.markdown("<br>", unsafe_allow_html=True)
    if st.button("🚀 Start Mock Interview", type="primary", use_container_width=True):
        success = start_interview(
            category=cat_choice,
            difficulty=diff_choice,
            num_questions=num_choice,
            records=questions_data
        )
        if success:
            st.rerun()


# ==============================================================================
# Screen 2: Active Interview Room
# ==============================================================================

elif st.session_state.interview_state == STATE_INTERVIEWING:
    questions: List[QnARecord] = st.session_state.selected_questions
    current_idx = st.session_state.current_question_idx
    current_q: QnARecord = questions[current_idx]

    # Progress header
    progress = (current_idx + 1) / len(questions)
    st.progress(progress, text=f"Question {current_idx + 1} of {len(questions)}")

    diff_badge_class = f"badge-{current_q.difficulty.lower()}"
    st.markdown(
        f"""
        <div style="margin-bottom: 0.6rem;">
            <span class="badge badge-category">{current_q.category}</span>
            <span class="badge {diff_badge_class}">{current_q.difficulty}</span>
            <span class="badge" style="background-color:#475569;color:#fff;">{current_q.question_type}</span>
            <span style="color:#64748b; font-size:0.85rem; margin-left:0.5rem;">ID: {current_q.id} • Subtopic: {current_q.subcategory}</span>
        </div>
        """,
        unsafe_allow_html=True
    )

    # Question card
    st.markdown(
        f"""
        <div class="question-card">
            <div style="color:#0284c7; font-weight:700; font-size:0.9rem; text-transform:uppercase;">Interview Question #{current_idx + 1}</div>
            <div class="question-prompt">{current_q.question}</div>
        </div>
        """,
        unsafe_allow_html=True
    )

    st.caption("🔒 *Reference canonical answers are kept strictly hidden during the active interview.*")

    # Key Concepts guidance pill
    if current_q.key_concepts:
        with st.expander("💡 Topic Focus & Concepts Covered (Hints)", expanded=False):
            st.write(", ".join([f"`{c}`" for c in current_q.key_concepts]))

    st.markdown("### ✍️ Your Answer")
    tab_text, tab_audio = st.tabs(["📝 Text Input (Recommended)", "🎤 Audio Upload / Voice"])

    with tab_text:
        candidate_text = st.text_area(
            "Type your technical response in full detail (explain reasoning, mechanisms, and trade-offs):",
            key=f"text_input_{current_q.id}",
            height=180,
            placeholder="Explain the underlying principles, cause-and-effect mechanisms, and tradeoffs..."
        )
        word_count = len(candidate_text.strip().split()) if candidate_text.strip() else 0
        st.caption(f"Word count: **{word_count}** words")

    with tab_audio:
        st.markdown("**Submit Voice Recording:**")
        uploaded_audio = st.file_uploader(
            "Upload candidate audio answer (WAV, MP3, M4A):",
            type=["wav", "mp3", "m4a"],
            key=f"audio_upload_{current_q.id}"
        )
        if uploaded_audio:
            st.audio(uploaded_audio)
            if st.button("Transcribe Audio via ASR Worker"):
                with st.spinner("Transcribing via Whisper worker..."):
                    asr_res = transcribe_audio_file(uploaded_audio.getvalue(), uploaded_audio.name)
                    if asr_res and "transcript" in asr_res:
                        words = [t.get("word", "") for t in asr_res["transcript"]]
                        extracted_text = " ".join(words)
                        st.success(f"Transcribed {len(words)} words!")
                        candidate_text = extracted_text
                    else:
                        st.warning("ASR service is offline or did not return text. Please use text input mode.")

    col_sub, col_gap = st.columns([1, 3])
    with col_sub:
        submit_btn = st.button("⚡ Submit Answer for Evaluation", type="primary", use_container_width=True)

    if submit_btn:
        answer_to_submit = candidate_text.strip()
        if len(answer_to_submit.split()) < 5:
            st.warning("Please provide a more complete answer (at least 5 words) before submitting.")
        else:
            with st.spinner("Evaluating response with 3-run mode voting, structural analysis, and calibration..."):
                eval_res = submit_answer_to_backend(
                    session_id=st.session_state.session_id,
                    question_id=current_q.id,
                    question_text=current_q.question,
                    answer_text=answer_to_submit,
                    duration_sec=60.0
                )
                record_evaluation(current_q.id, answer_to_submit, eval_res)
                st.rerun()


# ==============================================================================
# Screen 3: Question Evaluation & Actionable Feedback
# ==============================================================================

elif st.session_state.interview_state == STATE_FEEDBACK:
    questions = st.session_state.selected_questions
    current_idx = st.session_state.current_question_idx
    current_q: QnARecord = questions[current_idx]
    eval_res = st.session_state.evaluations.get(current_q.id, {})
    candidate_answer = st.session_state.candidate_answers.get(current_q.id, "")

    st.markdown(f"## 📋 Evaluation Results: Question #{current_idx + 1}")
    st.markdown(f"**Question:** {current_q.question}")

    with st.expander("📝 View Your Submitted Transcript", expanded=False):
        st.info(candidate_answer)

    # 1. High-level metric cards
    scores = eval_res.get("scores", {})
    raw_scores = eval_res.get("raw_scores", {})
    calibrated_scores = eval_res.get("calibrated_scores", {})
    overall = eval_res.get("overall_score", 0.0)

    m1, m2, m3, m4 = st.columns(4)
    with m1:
        st.markdown(
            f"""
            <div class="score-metric-box">
                <div class="score-number">{scores.get('content', 0)}%</div>
                <div class="score-label">Content Mastery</div>
                <small style="color:#64748b;">Calibrated: {calibrated_scores.get('content', 0.0)}/5.0</small>
            </div>
            """,
            unsafe_allow_html=True
        )
    with m2:
        st.markdown(
            f"""
            <div class="score-metric-box">
                <div class="score-number">{scores.get('structure', 0)}%</div>
                <div class="score-label">Structure & Coherence</div>
                <small style="color:#64748b;">Calibrated: {calibrated_scores.get('structure', 0.0)}/5.0</small>
            </div>
            """,
            unsafe_allow_html=True
        )
    with m3:
        st.markdown(
            f"""
            <div class="score-metric-box">
                <div class="score-number">{scores.get('communication', 0)}%</div>
                <div class="score-label">Communication Clarity</div>
                <small style="color:#64748b;">Pace & Fluency</small>
            </div>
            """,
            unsafe_allow_html=True
        )
    with m4:
        st.markdown(
            f"""
            <div class="score-metric-box" style="border-left: 3px solid #0284c7;">
                <div class="score-number" style="color:#0369a1;">{overall}%</div>
                <div class="score-label">Overall Weighted</div>
                <small style="color:#0284c7;">50% C • 30% S • 20% Comm</small>
            </div>
            """,
            unsafe_allow_html=True
        )

    # Uncertainty Flag
    uncertainty = eval_res.get("uncertainty", {})
    if uncertainty.get("is_uncertain"):
        st.warning(
            f"⚠️ **Fixed Uncertainty Rule Triggered:** Human verification recommended. "
            f"Reason(s): {', '.join(uncertainty.get('reasons', ['Borderline score spread']))}"
        )

    st.markdown("<br>", unsafe_allow_html=True)
    col_left, col_right = st.columns([1, 1])

    # 2. Semantic Rubric Proposition Breakdown
    with col_left:
        st.markdown("### 🧩 Semantic Idea Coverage")
        st.caption("Conceptual proposition matching invariant to keyword phrasing:")
        flags = eval_res.get("flags", {})

        if current_q.semantic_rubric_ideas:
            for idea in current_q.semantic_rubric_ideas:
                flag = flags.get(idea.idea_id, "missing")
                card_class = f"prop-{flag}"
                icon = "✅" if flag == "covered" else ("⚠️" if flag == "partial" else "❌")

                st.markdown(
                    f"""
                    <div class="proposition-card {card_class}">
                        <div><strong>{icon} {idea.idea_id} ({flag.upper()})</strong></div>
                        <div style="margin-top:0.3rem;">{idea.semantic_statement}</div>
                    </div>
                    """,
                    unsafe_allow_html=True
                )
        else:
            for fid, flag in flags.items():
                card_class = f"prop-{flag}"
                icon = "✅" if flag == "covered" else ("⚠️" if flag == "partial" else "❌")
                st.markdown(
                    f"""
                    <div class="proposition-card {card_class}">
                        <strong>{icon} Criterion: {fid} — {flag.upper()}</strong>
                    </div>
                    """,
                    unsafe_allow_html=True
                )

    # 3. Top-3 Actionable Coaching Feedback (PDF Page 10 spec)
    with col_right:
        st.markdown("### 🎯 Top Actionable Coaching Fixes")
        st.caption("Bespoke coaching recommendations (max 30 words per fix):")
        feedback_items = eval_res.get("feedback", [])

        if feedback_items:
            for rank, item in enumerate(feedback_items, 1):
                quote = item.get("quote", "").strip()
                fix = item.get("fix_sentence", "").strip()
                marks_lost = item.get("marks_lost", 0)
                crit = item.get("criterion_id", f"Point #{rank}")

                st.markdown(
                    f"""
                    <div class="feedback-box">
                        <div style="font-size:0.75rem; text-transform:uppercase; font-weight:700; color:#86198f;">
                            #{rank} Missed Point: {crit} • -{marks_lost} marks
                        </div>
                        {f'<div class="feedback-quote">"{quote}"</div>' if quote else ''}
                        <div class="feedback-fix">👉 {fix}</div>
                    </div>
                    """,
                    unsafe_allow_html=True
                )
        else:
            st.success("🎉 Outstanding response! All required semantic propositions were fully demonstrated.")

    # Structure & Communication Diagnostics
    with st.expander("🔍 Deep Diagnostics (Structure & Communication)", expanded=False):
        struct_diag = eval_res.get("structure_diagnostics", {})
        comm_diag = eval_res.get("communication_diagnostics", {})
        d1, d2 = st.columns(2)
        with d1:
            st.markdown("**Structure Subcomponents (1.0 to 5.0):**")
            for comp_name in ["framing", "coherence", "closure"]:
                comp = struct_diag.get(comp_name, {})
                st.write(f"- **{comp_name.capitalize()}**: `{comp.get('score', 'N/A')}/5.0` — {comp.get('feedback', '')}")
        with d2:
            st.markdown("**Communication Acoustics / Timing:**")
            st.write(f"- Speech Pace: `{comm_diag.get('wpm', 'N/A')} WPM` (Ideal: 110 - 170 WPM)")
            st.write(f"- Filler Rate: `{comm_diag.get('filler_rate', 'N/A')}%`")
            st.write(f"- Prolonged Pauses (>2s): `{comm_diag.get('pause_count', 'N/A')}`")

    st.markdown("<br>", unsafe_allow_html=True)
    is_last = (current_idx + 1 >= len(questions))
    btn_label = "🏆 View Final Interview Summary" if is_last else "➡️ Proceed to Next Question"

    if st.button(btn_label, type="primary", use_container_width=True):
        advance_question()
        st.rerun()


# ==============================================================================
# Screen 4: Interview Summary & Debrief
# ==============================================================================

elif st.session_state.interview_state == STATE_COMPLETED:
    questions = st.session_state.selected_questions
    evaluations = st.session_state.evaluations

    st.markdown("## 🎓 Interview Debrief & Comprehensive Scorecard")
    st.markdown(f"Session completed with **{len(questions)}** questions evaluated.")

    # Calculate session averages
    content_scores = [evaluations[q.id]["scores"]["content"] for q in questions if q.id in evaluations]
    structure_scores = [evaluations[q.id]["scores"]["structure"] for q in questions if q.id in evaluations]
    comm_scores = [evaluations[q.id]["scores"]["communication"] for q in questions if q.id in evaluations]
    overall_scores = [evaluations[q.id]["overall_score"] for q in questions if q.id in evaluations]

    avg_content = round(sum(content_scores) / len(content_scores), 1) if content_scores else 0.0
    avg_structure = round(sum(structure_scores) / len(structure_scores), 1) if structure_scores else 0.0
    avg_comm = round(sum(comm_scores) / len(comm_scores), 1) if comm_scores else 0.0
    avg_overall = round(sum(overall_scores) / len(overall_scores), 1) if overall_scores else 0.0

    s1, s2, s3, s4 = st.columns(4)
    with s1:
        st.metric("Session Overall", f"{avg_overall}%")
    with s2:
        st.metric("Avg Content Mastery", f"{avg_content}%")
    with s3:
        st.metric("Avg Structure", f"{avg_structure}%")
    with s4:
        st.metric("Avg Communication", f"{avg_comm}%")

    st.markdown("---")
    st.markdown("### 📋 Question-by-Question Breakdown")

    summary_rows = []
    for idx, q in enumerate(questions, 1):
        ev = evaluations.get(q.id, {})
        sc = ev.get("scores", {})
        summary_rows.append({
            "#": idx,
            "Question ID": q.id,
            "Category": q.category,
            "Difficulty": q.difficulty,
            "Content Score": f"{sc.get('content', 'N/A')}%",
            "Structure Score": f"{sc.get('structure', 'N/A')}%",
            "Comm Score": f"{sc.get('communication', 'N/A')}%",
            "Overall": f"{ev.get('overall_score', 'N/A')}%"
        })

    st.table(summary_rows)

    # Reference Answer Review (Authorized post-interview flow)
    st.markdown("### 📖 Canonical Answers & Knowledge Base Review")
    st.caption("Compare your submitted responses against canonical reference answers:")

    for idx, q in enumerate(questions, 1):
        with st.expander(f"Question #{idx} ({q.id}): {q.question}"):
            cand_ans = st.session_state.candidate_answers.get(q.id, "No answer recorded.")
            st.markdown(f"**Your Response:**")
            st.info(cand_ans)
            st.markdown(f"**Canonical Technical Reference:**")
            st.success(q.answer)
            if q.glossary_terms_used:
                st.caption(f"Glossary keywords: {', '.join(q.glossary_terms_used)}")

    st.markdown("<br>", unsafe_allow_html=True)
    if st.button("🔄 Start a New Mock Interview", type="primary", use_container_width=True):
        reset_interview()
        st.rerun()
