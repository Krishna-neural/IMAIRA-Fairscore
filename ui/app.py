import json
import os
import sys
import tempfile
from pathlib import Path
import streamlit as st

BASE_DIR = Path(__file__).resolve().parent.parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from interviewer.questions import load_questions, get_question_by_id, get_categories
from interviewer.tts import get_question_audio, get_voice_options
from interviewer.session import InterviewSession
from interviewer.rescore import rescore_segment
from interviewer.pipeline import run_fairscore_pipeline
from ui.theme import apply_professional_theme, render_landing_hero, render_architecture_page

# Page Configuration
st.set_page_config(
    page_title="IMAIRA FairScore | AI Mock Interviewer & Fair Accent Scoring",
    page_icon="🎙️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Apply Corporate Design System & Dark Theme CSS
apply_professional_theme()

# Session State Initialization
if "active_nav" not in st.session_state:
    st.session_state.active_nav = "🏠 Platform Overview"
if "evaluation" not in st.session_state:
    st.session_state.evaluation = None
if "current_q_id" not in st.session_state:
    st.session_state.current_q_id = "q_db_01"
if "transcript" not in st.session_state:
    st.session_state.transcript = ""
if "rescore_history" not in st.session_state:
    st.session_state.rescore_history = []

# Top Modern Navigation Bar
col_brand, col_nav = st.columns([1, 2])
with col_brand:
    st.markdown("""
    <div style="padding: 6px 0;">
        <span class="brand-badge">🎙️ IMAIRA FairScore</span>
        <span style="font-size: 0.75rem; color: #64748b; margin-left: 8px;">v1.0 • Accent-Fair Engine</span>
    </div>
    """, unsafe_allow_html=True)

with col_nav:
    nav_selection = st.radio(
        "Navigation",
        options=["🏠 Platform Overview", "🎙️ Live Mock Interview", "🔬 System Architecture"],
        horizontal=True,
        label_visibility="collapsed",
        key="active_nav"
    )

st.divider()

# ==============================================================================
# TAB 1: ENTERPRISE LANDING PAGE
# ==============================================================================
if nav_selection == "🏠 Platform Overview":
    render_landing_hero()

    st.write("")
    cta_col1, cta_col2, _ = st.columns([2, 2, 3])
    with cta_col1:
        if st.button("🚀 Launch Live Mock Interview", type="primary", use_container_width=True):
            st.session_state.active_nav = "🎙️ Live Mock Interview"
            st.rerun()
    with cta_col2:
        if st.button("🔬 Explore Technical Architecture", type="secondary", use_container_width=True):
            st.session_state.active_nav = "🔬 System Architecture"
            st.rerun()

# ==============================================================================
# TAB 2: LIVE AI MOCK INTERVIEWER
# ==============================================================================
elif nav_selection == "🎙️ Live Mock Interview":
    # Sidebar Controls
    st.sidebar.title("🎙️ Interview Controls")
    categories = get_categories()
    selected_cat = st.sidebar.selectbox("Technical Domain", categories)

    all_questions = load_questions()
    cat_questions = [q for q in all_questions if q.get("category") == selected_cat]
    q_titles = {q["id"]: q["display_title"] for q in cat_questions}
    selected_q_id = st.sidebar.selectbox("Select Question", list(q_titles.keys()), format_func=lambda x: q_titles[x])
    st.session_state.current_q_id = selected_q_id

    voice_options = get_voice_options()
    selected_voice_name = st.sidebar.selectbox("Neural Voice Accent", list(voice_options.keys()))
    selected_voice = voice_options[selected_voice_name]

    st.sidebar.divider()
    st.sidebar.markdown("""
    <div style="font-size: 0.82rem; color: #94a3b8; background: rgba(15, 23, 42, 0.6); padding: 12px; border-radius: 8px; border: 1px solid rgba(255,255,255,0.06);">
        <strong>🔒 Privacy Guarantee</strong><br>
        Candidate audio is stored strictly in ephemeral memory and auto-purged immediately following ASR transcription.
    </div>
    """, unsafe_allow_html=True)

    current_q = get_question_by_id(selected_q_id)
    if not current_q:
        st.error("Question not found.")
        st.stop()

    # Step 1: AI Mock Interviewer Speaks
    st.markdown(f"### 1. Spoken Technical Challenge: `{current_q['display_title']}`")
    col_audio, col_meta = st.columns([2, 1])

    with col_audio:
        with st.spinner("Synthesizing neural voice question..."):
            audio_file_path = get_question_audio(selected_q_id, voice=selected_voice)
        
        if os.path.exists(audio_file_path):
            with open(audio_file_path, "rb") as f:
                st.audio(f.read(), format="audio/mp3", autoplay=False)
        
        st.markdown(f"""
        <div style="background: rgba(15, 23, 42, 0.6); border-left: 3px solid #6366f1; padding: 14px 18px; border-radius: 6px; font-style: italic; color: #cbd5e1; margin-top: 8px;">
            "{current_q.get('spoken_question')}"
        </div>
        """, unsafe_allow_html=True)

    with col_meta:
        st.markdown("**Domain Term Hints:**")
        st.write(" ".join([f"`{term}`" for term in current_q.get("domain_terms", [])]))
        st.markdown(f"**Difficulty Level:** `{current_q.get('difficulty', 'Medium')}`")

    st.divider()

    # Step 2: Candidate Spoken Answer
    st.markdown("### 2. Candidate Spoken Response")
    rec_col, sample_col = st.columns([3, 2])

    with rec_col:
        audio_input = st.audio_input("🎙️ Record your voice response via microphone:")
        uploaded_file = st.file_uploader("Or upload candidate audio (.wav, .mp3, .m4a)", type=["wav", "mp3", "m4a", "webm"])

    with sample_col:
        st.markdown("**Fast Demonstration Mode:**")
        use_sample = st.checkbox("Load benchmark sample answer (Instant Evaluation)", value=False)
        if use_sample:
            st.info("Pre-recorded response loaded covering B-tree logarithmic traversal, secondary index write amplification, and VACUUM dead tuple maintenance.")

    submit_clicked = st.button("🚀 Submit to IMAIRA FairScore Engine", type="primary", use_container_width=True)

    if submit_clicked:
        with st.spinner("Processing speech via Faster-Whisper & Evaluating via FairScore..."):
            session = InterviewSession(question_id=selected_q_id)
            target_audio = None
            temp_file = None

            if uploaded_file is not None:
                suffix = Path(uploaded_file.name).suffix or ".wav"
                temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=suffix)
                temp_file.write(uploaded_file.read())
                temp_file.close()
                target_audio = temp_file.name
            elif audio_input is not None:
                temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".wav")
                temp_file.write(audio_input.read())
                temp_file.close()
                target_audio = temp_file.name
            elif not use_sample:
                st.warning("Please record your voice, upload an audio file, or enable fast test mode.")
                st.stop()

            # Run ASR & Ingestion
            asr_result = session.process_applicant_audio(raw_audio_path=target_audio)
            st.session_state.transcript = asr_result["transcript_text"]

            if temp_file and os.path.exists(temp_file.name):
                try:
                    os.remove(temp_file.name)
                except Exception:
                    pass

            # Run FairScore Evaluation Pipeline
            eval_result = run_fairscore_pipeline(
                transcript_text=asr_result["transcript_text"],
                word_tokens=asr_result["word_tokens"],
                rubric_points=current_q.get("rubric", []),
                question_text=current_q.get("spoken_question", ""),
                duration_sec=asr_result["audio_duration"]
            )

            st.session_state.evaluation = eval_result
            st.session_state.rescore_history = []

    # Step 3: Evaluation Breakdown Display
    if st.session_state.evaluation:
        st.divider()
        st.markdown("### 3. IMAIRA FairScore Assessment Scorecard")

        eval_res = st.session_state.evaluation
        scores = eval_res.get("scores", {})
        flags = eval_res.get("flags", {})
        feedback = eval_res.get("feedback", [])

        m1, m2, m3 = st.columns(3)
        with m1:
            st.markdown(f"""
            <div class="metric-card">
                <h4 style="margin:0; color:#38bdf8;">🧠 Content Score</h4>
                <h1 style="margin:8px 0; color:#60a5fa;">{scores.get('content', 0)} / 100</h1>
                <p style="margin:0; font-size:0.8rem; color:#94a3b8;">Semantic coverage of technical rubrics</p>
            </div>
            """, unsafe_allow_html=True)
        with m2:
            st.markdown(f"""
            <div class="metric-card">
                <h4 style="margin:0; color:#a78bfa;">🏗️ Structure Score</h4>
                <h1 style="margin:8px 0; color:#c084fc;">{scores.get('structure', 0)} / 100</h1>
                <p style="margin:0; font-size:0.8rem; color:#94a3b8;">Logical order, reasoning & conclusion</p>
            </div>
            """, unsafe_allow_html=True)
        with m3:
            st.markdown(f"""
            <div class="metric-card">
                <h4 style="margin:0; color:#10b981;">🗣️ Communication Score</h4>
                <h1 style="margin:8px 0; color:#34d399;">{scores.get('communication', 0)} / 100</h1>
                <p style="margin:0; font-size:0.8rem; color:#94a3b8;">WPM pace & pauses (accent-neutral)</p>
            </div>
            """, unsafe_allow_html=True)

        st.write("")

        # Candidate Transcript View
        with st.expander("📝 View Spoken Transcript (Acoustic Evidence Base)", expanded=False):
            st.write(st.session_state.transcript)

        # Rubric Points Checklist
        st.markdown("#### 📋 Rubric Concept Breakdown")
        for r in current_q.get("rubric", []):
            p_id = r["id"]
            status_flag = flags.get(p_id, "missing")
            badge_class = f"badge-{status_flag}"
            badge_text = status_flag.upper()
            
            st.markdown(f"""
            <div style="padding: 10px 14px; margin-bottom: 8px; background: rgba(15, 23, 42, 0.7); border: 1px solid rgba(255,255,255,0.06); border-radius: 8px; display: flex; justify-content: space-between; align-items: center;">
                <div>
                    <strong style="color: #60a5fa;">{p_id.upper()}</strong>: {r['text']}
                </div>
                <div>
                    <span class="{badge_class}">{badge_text}</span>
                </div>
            </div>
            """, unsafe_allow_html=True)

        # Step 4: Top-3 Actionable Feedback
        st.markdown("#### 💡 Top Missed Points & Actionable Fixes")
        if not feedback:
            st.success("🎉 Outstanding answer! You covered all key rubric points.")
        else:
            for idx, fb in enumerate(feedback, 1):
                st.markdown(f"""
                <div class="feedback-box">
                    <div style="display:flex; justify-content:space-between;">
                        <strong>Point {idx}</strong> (Marks Lost: <span style="color:#f87171; font-weight:bold;">-{fb.get('marks_lost', 0)}</span>)
                        <span style="font-size:0.82rem; color:#94a3b8;">⏱️ Timestamp: {fb.get('t_start', 0.0)}s - {fb.get('t_end', 0.0)}s</span>
                    </div>
                    <p style="margin: 6px 0; font-style: italic; color:#cbd5e1;">"{fb.get('quote', '')}"</p>
                    <p style="margin: 4px 0; color:#f87171;"><strong>Diagnostic Gap:</strong> {fb.get('issue', '')}</p>
                    <p style="margin: 4px 0; color:#38bdf8;"><strong>Ready-to-Say Fix (≤30 words):</strong> {fb.get('fix_sentence', '')}</p>
                </div>
                """, unsafe_allow_html=True)

        st.divider()

        # Step 5: Interactive Re-Answer Loop
        st.markdown("### 4. 🔄 Interactive Re-Answer Loop")
        st.caption("Target a specific missed rubric point by re-recording or typing your explanation. Watch your Content Score improve in real time!")
        
        flagged_points = [p["id"] for p in current_q.get("rubric", []) if flags.get(p["id"]) in ("missing", "partial")]
        
        if not flagged_points:
            st.info("All rubric points covered! No flagged segments need re-answering.")
        else:
            re_col1, re_col2 = st.columns([1, 2])
            with re_col1:
                target_p = st.selectbox("Select Flagged Concept to Re-Answer", flagged_points)
                p_desc = next((p["text"] for p in current_q["rubric"] if p["id"] == target_p), "")
                st.markdown(f"**Target Concept**: *{p_desc}*")

            with re_col2:
                reanswer_text = st.text_area(
                    "Your Targeted Re-Answer Explanation:",
                    placeholder="Address the missing concept directly with technical precision..."
                )
                re_submit = st.button("⚡ Rescore Targeted Segment", type="secondary")

            if re_submit and reanswer_text:
                with st.spinner("Rescoring segment via Re-Answer Loop Engine..."):
                    rescore_result = rescore_segment(
                        original_evaluation=eval_res,
                        target_point_id=target_p,
                        reanswer_text=reanswer_text,
                        question_id=selected_q_id
                    )
                    
                    st.session_state.evaluation["scores"] = rescore_result["updated_scores"]
                    st.session_state.evaluation["flags"] = rescore_result["updated_flags"]
                    st.session_state.evaluation["feedback"] = rescore_result["updated_feedback"]
                    
                    b_score = rescore_result["before"]["content_score"]
                    a_score = rescore_result["after"]["content_score"]
                    gain = rescore_result["score_gain"]

                    st.success(f"🎉 **Score Recovery Achieved!** Content Score improved from **{b_score}** to **{a_score}** (+{gain} points)")
                    st.rerun()

# ==============================================================================
# TAB 3: TECHNICAL ARCHITECTURE & BENCHMARKS
# ==============================================================================
elif nav_selection == "🔬 System Architecture":
    render_architecture_page()
