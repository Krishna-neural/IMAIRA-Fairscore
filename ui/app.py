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

# Page Configuration & Styling
st.set_page_config(
    page_title="IMAIRA FairScore | AI Mock Interviewer",
    page_icon="🎙️",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.markdown("""
<style>
    .metric-card {
        background: #1e2430;
        border: 1px solid #2d3748;
        border-radius: 10px;
        padding: 16px;
        text-align: center;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
    }
    .badge-covered { background-color: #10b981; color: white; padding: 3px 8px; border-radius: 6px; font-weight: 600; font-size: 0.85rem; }
    .badge-partial { background-color: #f59e0b; color: white; padding: 3px 8px; border-radius: 6px; font-weight: 600; font-size: 0.85rem; }
    .badge-missing { background-color: #ef4444; color: white; padding: 3px 8px; border-radius: 6px; font-weight: 600; font-size: 0.85rem; }
    .feedback-box {
        background: #131b26;
        border-left: 4px solid #3b82f6;
        padding: 12px 16px;
        margin-bottom: 12px;
        border-radius: 4px;
    }
</style>
""", unsafe_allow_html=True)

# Session State Initialization
if "evaluation" not in st.session_state:
    st.session_state.evaluation = None
if "current_q_id" not in st.session_state:
    st.session_state.current_q_id = "q_db_01"
if "transcript" not in st.session_state:
    st.session_state.transcript = ""
if "rescore_history" not in st.session_state:
    st.session_state.rescore_history = []

# Sidebar Controls
st.sidebar.title("🎙️ AI Interviewer Setup")
categories = get_categories()
selected_cat = st.sidebar.selectbox("Question Category", categories)

all_questions = load_questions()
cat_questions = [q for q in all_questions if q.get("category") == selected_cat]
q_titles = {q["id"]: q["display_title"] for q in cat_questions}
selected_q_id = st.sidebar.selectbox("Select Question", list(q_titles.keys()), format_func=lambda x: q_titles[x])
st.session_state.current_q_id = selected_q_id

voice_options = get_voice_options()
selected_voice_name = st.sidebar.selectbox("Interviewer Voice", list(voice_options.keys()))
selected_voice = voice_options[selected_voice_name]

st.sidebar.divider()
st.sidebar.info("💡 **Single-Laptop Mode**: All scoring and TTS run locally on `localhost`. Content is judged strictly from transcript; communication is judged strictly from audio timing.")

# Main Header
st.title("IMAIRA FairScore: AI Mock Interviewer")
st.caption("Accent-fair assessment: grades the answer, not the accent. Time-linked feedback with interactive Re-Answer loop.")

current_q = get_question_by_id(selected_q_id)
if not current_q:
    st.error("Question not found.")
    st.stop()

# Step 1: AI Mock Interviewer Speaks
st.subheader("1. AI Interviewer Speaks the Question")
col_audio, col_meta = st.columns([2, 1])

with col_audio:
    st.markdown(f"**Topic**: `{current_q['display_title']}`")
    with st.spinner("Preparing natural voice synthesis..."):
        audio_file_path = get_question_audio(selected_q_id, voice=selected_voice)
    
    if os.path.exists(audio_file_path):
        with open(audio_file_path, "rb") as f:
            audio_bytes = f.read()
        st.audio(audio_bytes, format="audio/mp3", autoplay=False)
    
    st.markdown(f"> *\"{current_q.get('spoken_question')}\"*")

with col_meta:
    st.markdown("**Domain Hotwords:**")
    st.write(" ".join([f"`{term}`" for term in current_q.get("domain_terms", [])]))
    st.markdown(f"**Difficulty:** `{current_q.get('difficulty', 'Medium')}`")

st.divider()

# Step 2: Applicant Answer
st.subheader("2. Record Your Spoken Answer")
record_col, sample_col = st.columns([3, 2])

with record_col:
    audio_input = st.audio_input("🎙️ Speak into your microphone and click Record:")
    uploaded_file = st.file_uploader("Or upload an audio file (.wav, .mp3, .m4a)", type=["wav", "mp3", "m4a", "webm"])

with sample_col:
    use_sample = st.checkbox("Use sample transcript (Fast Test Mode)", value=False)
    if use_sample:
        st.info("Sample answer on B-trees, write amplification, and vacuuming loaded for instant scoring.")

submit_clicked = st.button("🚀 Submit to IMAIRA FairScore for Evaluation", type="primary", use_container_width=True)

if submit_clicked:
    with st.spinner("Processing speech via Faster-Whisper & Evaluating via FairScore..."):
        session = InterviewSession(question_id=selected_q_id)
        
        # Handle input modes
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
            st.warning("Please record your voice, upload an audio file, or check 'Use sample transcript'.")
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
    st.subheader("3. IMAIRA FairScore Assessment Breakdown")

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
            <p style="margin:0; font-size:0.8rem; color:#94a3b8;">Order, reasoning, example & conclusion</p>
        </div>
        """, unsafe_allow_html=True)
    with m3:
        st.markdown(f"""
        <div class="metric-card">
            <h4 style="margin:0; color:#10b981;">🗣️ Communication Score</h4>
            <h1 style="margin:8px 0; color:#34d399;">{scores.get('communication', 0)} / 100</h1>
            <p style="margin:0; font-size:0.8rem; color:#94a3b8;">WPM pace & pauses (accent neutral)</p>
        </div>
        """, unsafe_allow_html=True)

    st.write("")
    
    # Candidate Transcript View
    with st.expander("📝 View Spoken Transcript (Evidence Base)", expanded=False):
        st.write(st.session_state.transcript)

    # Rubric Points Checklist
    st.markdown("#### 📋 Rubric Concept Breakdown")
    for r in current_q.get("rubric", []):
        p_id = r["id"]
        status_flag = flags.get(p_id, "missing")
        badge_class = f"badge-{status_flag}"
        badge_text = status_flag.upper()
        
        st.markdown(f"""
        <div style="padding: 8px 12px; margin-bottom: 6px; background: #1a2230; border-radius: 6px; display: flex; justify-content: space-between; align-items: center;">
            <div>
                <strong>{p_id.upper()}</strong>: {r['text']}
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
                    <strong>Point {idx}</strong> (Marks Lost: <span style="color:#ef4444; font-weight:bold;">-{fb.get('marks_lost', 0)}</span>)
                    <span style="font-size:0.85rem; color:#94a3b8;">⏱️ {fb.get('t_start', 0.0)}s - {fb.get('t_end', 0.0)}s</span>
                </div>
                <p style="margin: 6px 0; font-style: italic; color:#cbd5e1;">"{fb.get('quote', '')}"</p>
                <p style="margin: 4px 0; color:#f87171;"><strong>Issue:</strong> {fb.get('issue', '')}</p>
                <p style="margin: 4px 0; color:#38bdf8;"><strong>Ready-to-Say Fix (≤30 words):</strong> {fb.get('fix_sentence', '')}</p>
            </div>
            """, unsafe_allow_html=True)

    st.divider()

    # Step 5: Interactive Re-Answer Loop (PDF Page 11 Feature)
    st.subheader("4. 🔄 Re-Answer Loop (Rescore Flagged Segment)")
    st.caption("Address one flagged point by re-recording your response. Watch your Content Score improve in real time!")
    
    flagged_points = [p["id"] for p in current_q.get("rubric", []) if flags.get(p["id"]) in ("missing", "partial")]
    
    if not flagged_points:
        st.info("All rubric points covered! No flagged segments need re-answering.")
    else:
        re_col1, re_col2 = st.columns([1, 2])
        with re_col1:
            target_p = st.selectbox("Select Flagged Point to Re-Answer", flagged_points)
            p_desc = next((p["text"] for p in current_q["rubric"] if p["id"] == target_p), "")
            st.markdown(f"**Target Concept**: *{p_desc}*")

        with re_col2:
            reanswer_text = st.text_area(
                "Your Targeted Re-Answer (Speak or type your updated explanation):",
                placeholder="Address the missing concept directly..."
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
                
                # Update session state evaluation
                st.session_state.evaluation["scores"] = rescore_result["updated_scores"]
                st.session_state.evaluation["flags"] = rescore_result["updated_flags"]
                st.session_state.evaluation["feedback"] = rescore_result["updated_feedback"]
                
                # Show before vs after comparison
                b_score = rescore_result["before"]["content_score"]
                a_score = rescore_result["after"]["content_score"]
                gain = rescore_result["score_gain"]

                st.success(f"🎉 **Score Improvement!** Content Score changed from **{b_score}** to **{a_score}** (+{gain} points)")
                st.rerun()
