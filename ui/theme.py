"""IMAIRA FairScore — Design System & Professional Theme Styling."""

import streamlit as st

def apply_professional_theme():
    st.markdown("""
    <style>
        /* Import Modern Tech Typography */
        @import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@300;400;500;600;700;800&family=JetBrains+Mono:wght@400;500;600&display=swap');

        /* Root CSS Variables */
        :root {
            --bg-base: #07090e;
            --bg-surface: #0e131f;
            --bg-card: rgba(17, 24, 39, 0.7);
            --border-subtle: rgba(255, 255, 255, 0.08);
            --border-accent: rgba(59, 130, 246, 0.3);
            --text-primary: #f8fafc;
            --text-secondary: #94a3b8;
            --text-muted: #64748b;
            --accent-blue: #38bdf8;
            --accent-indigo: #6366f1;
            --accent-purple: #a855f7;
            --accent-emerald: #10b981;
            --accent-amber: #f59e0b;
            --accent-rose: #f43f5e;
        }

        html, body, [class*="css"] {
            font-family: 'Plus Jakarta Sans', -apple-system, BlinkMacSystemFont, sans-serif;
            color: var(--text-primary);
        }

        code, pre, .font-mono {
            font-family: 'JetBrains Mono', monospace !important;
        }

        /* Top Navigation Header Pill */
        .nav-pill-container {
            display: flex;
            align-items: center;
            justify-content: space-between;
            padding: 12px 24px;
            background: linear-gradient(180deg, rgba(15, 23, 42, 0.9) 0%, rgba(15, 23, 42, 0.6) 100%);
            border: 1px solid var(--border-subtle);
            border-radius: 16px;
            backdrop-filter: blur(16px);
            margin-bottom: 24px;
        }

        .brand-badge {
            display: inline-flex;
            align-items: center;
            gap: 10px;
            font-weight: 700;
            font-size: 1.15rem;
            letter-spacing: -0.02em;
            background: linear-gradient(135deg, #60a5fa 0%, #c084fc 100%);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
        }

        /* Hero Banner Container */
        .hero-container {
            position: relative;
            background: radial-gradient(circle at 50% -20%, rgba(99, 102, 241, 0.18) 0%, rgba(14, 19, 31, 0.8) 70%);
            border: 1px solid var(--border-subtle);
            border-radius: 20px;
            padding: 48px 36px 36px 36px;
            margin-bottom: 32px;
            text-align: center;
            overflow: hidden;
            box-shadow: 0 20px 40px -15px rgba(0, 0, 0, 0.5);
        }

        .hero-eyebrow {
            display: inline-block;
            font-size: 0.78rem;
            font-weight: 700;
            text-transform: uppercase;
            letter-spacing: 0.12em;
            padding: 4px 14px;
            border-radius: 9999px;
            background: rgba(56, 189, 248, 0.12);
            color: #38bdf8;
            border: 1px solid rgba(56, 189, 248, 0.25);
            margin-bottom: 16px;
        }

        .hero-title {
            font-size: 2.75rem;
            font-weight: 800;
            line-height: 1.15;
            letter-spacing: -0.03em;
            margin-bottom: 16px;
            background: linear-gradient(135deg, #ffffff 0%, #cbd5e1 50%, #94a3b8 100%);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
        }

        .hero-subtitle {
            font-size: 1.15rem;
            color: #94a3b8;
            max-width: 680px;
            margin: 0 auto 28px auto;
            line-height: 1.6;
        }

        /* Stat Grid */
        .stat-grid {
            display: grid;
            grid-template-columns: repeat(4, 1fr);
            gap: 16px;
            margin-bottom: 36px;
        }

        .stat-card {
            background: rgba(15, 23, 42, 0.65);
            border: 1px solid var(--border-subtle);
            border-radius: 14px;
            padding: 20px;
            text-align: center;
            backdrop-filter: blur(10px);
            transition: all 0.2s ease;
        }

        .stat-card:hover {
            border-color: rgba(99, 102, 241, 0.4);
            transform: translateY(-2px);
        }

        .stat-value {
            font-size: 1.85rem;
            font-weight: 800;
            letter-spacing: -0.02em;
            margin-bottom: 4px;
        }

        .stat-label {
            font-size: 0.8rem;
            font-weight: 600;
            color: #64748b;
            text-transform: uppercase;
            letter-spacing: 0.05em;
        }

        /* Feature Cards Grid */
        .feature-grid {
            display: grid;
            grid-template-columns: repeat(3, 1fr);
            gap: 20px;
            margin-bottom: 36px;
        }

        .feature-card {
            background: linear-gradient(180deg, rgba(30, 41, 59, 0.4) 0%, rgba(15, 23, 42, 0.6) 100%);
            border: 1px solid var(--border-subtle);
            border-radius: 16px;
            padding: 24px;
            backdrop-filter: blur(12px);
            transition: all 0.2s ease-in-out;
            position: relative;
        }

        .feature-card:hover {
            border-color: var(--border-accent);
            box-shadow: 0 12px 24px -10px rgba(59, 130, 246, 0.15);
            transform: translateY(-2px);
        }

        .feature-icon {
            font-size: 1.75rem;
            margin-bottom: 12px;
            display: inline-block;
        }

        .feature-heading {
            font-size: 1.1rem;
            font-weight: 700;
            color: #f1f5f9;
            margin-bottom: 8px;
        }

        .feature-desc {
            font-size: 0.88rem;
            color: #94a3b8;
            line-height: 1.55;
            margin: 0;
        }

        /* Metric Score Cards for Interviewer */
        .metric-card {
            background: linear-gradient(180deg, rgba(30, 41, 59, 0.5) 0%, rgba(15, 23, 42, 0.8) 100%);
            border: 1px solid var(--border-subtle);
            border-radius: 14px;
            padding: 20px;
            text-align: center;
            box-shadow: 0 8px 16px -6px rgba(0, 0, 0, 0.3);
            transition: transform 0.2s ease;
        }

        .metric-card:hover {
            transform: translateY(-2px);
        }

        /* Rubric Badges */
        .badge-covered {
            background: rgba(16, 185, 129, 0.15);
            color: #34d399;
            border: 1px solid rgba(16, 185, 129, 0.3);
            padding: 4px 10px;
            border-radius: 9999px;
            font-weight: 600;
            font-size: 0.8rem;
            letter-spacing: 0.04em;
        }

        .badge-partial {
            background: rgba(245, 158, 11, 0.15);
            color: #fbbf24;
            border: 1px solid rgba(245, 158, 11, 0.3);
            padding: 4px 10px;
            border-radius: 9999px;
            font-weight: 600;
            font-size: 0.8rem;
            letter-spacing: 0.04em;
        }

        .badge-missing {
            background: rgba(239, 68, 68, 0.15);
            color: #f87171;
            border: 1px solid rgba(239, 68, 68, 0.3);
            padding: 4px 10px;
            border-radius: 9999px;
            font-weight: 600;
            font-size: 0.8rem;
            letter-spacing: 0.04em;
        }

        /* Feedback Box */
        .feedback-box {
            background: rgba(15, 23, 42, 0.7);
            border: 1px solid var(--border-subtle);
            border-left: 4px solid #38bdf8;
            padding: 16px 20px;
            margin-bottom: 14px;
            border-radius: 10px;
            backdrop-filter: blur(8px);
        }

        /* Process Steps Container */
        .process-grid {
            display: grid;
            grid-template-columns: repeat(4, 1fr);
            gap: 16px;
            margin: 28px 0;
        }

        .process-step {
            background: rgba(15, 23, 42, 0.5);
            border: 1px solid var(--border-subtle);
            border-radius: 12px;
            padding: 18px;
            position: relative;
        }

        .step-number {
            font-size: 0.75rem;
            font-weight: 800;
            color: #6366f1;
            background: rgba(99, 102, 241, 0.1);
            padding: 3px 8px;
            border-radius: 6px;
            display: inline-block;
            margin-bottom: 10px;
        }

        .step-title {
            font-size: 0.95rem;
            font-weight: 700;
            color: #f8fafc;
            margin-bottom: 6px;
        }

        .step-desc {
            font-size: 0.82rem;
            color: #94a3b8;
            line-height: 1.45;
            margin: 0;
        }
    </style>
    """, unsafe_allow_html=True)

def render_landing_hero():
    """Renders the high-impact enterprise landing page hero & metrics."""
    st.markdown("""
    <div class="hero-container">
        <span class="hero-eyebrow">Enterprise Candidate Assessment Platform</span>
        <h1 class="hero-title">IMAIRA FairScore</h1>
        <p class="hero-subtitle">
            Next-generation AI mock interviewer with accent-neutral speech acoustics, 120 standardized technical rubrics, and real-time interactive re-answering.
        </p>
    </div>
    """, unsafe_allow_html=True)

    # Key Statistics Grid
    st.markdown("""
    <div class="stat-grid">
        <div class="stat-card">
            <div class="stat-value" style="color: #38bdf8;">120</div>
            <div class="stat-label">Standardized Rubrics</div>
        </div>
        <div class="stat-card">
            <div class="stat-value" style="color: #34d399;">100%</div>
            <div class="stat-label">Accent-Fair ASR Recovery</div>
        </div>
        <div class="stat-card">
            <div class="stat-value" style="color: #a78bfa;">3-Pass</div>
            <div class="stat-label">Temperature Mode Voting</div>
        </div>
        <div class="stat-card">
            <div class="stat-value" style="color: #f472b6;">Isotonic</div>
            <div class="stat-label">Score Calibration</div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # Core Value Pillars Grid
    st.markdown("### 🏛️ Architectural Pillars")
    st.markdown("""
    <div class="feature-grid">
        <div class="feature-card">
            <div class="feature-icon">🎙️</div>
            <div class="feature-heading">Neural Voice Interviewer</div>
            <p class="feature-desc">Edge-TTS neural voices deliver natural, spoken interview questions across US and Indian accents with zero robotic artifacts.</p>
        </div>
        <div class="feature-card">
            <div class="feature-icon">🎧</div>
            <div class="feature-heading">Two-Pass Acoustic Recovery</div>
            <p class="feature-desc">Domain-biased decoding and acoustic slice recovery eliminate accent discrimination, correcting phonetic speech mistranscriptions.</p>
        </div>
        <div class="feature-card">
            <div class="feature-icon">🧠</div>
            <div class="feature-heading">Grounded Semantic Judge</div>
            <p class="feature-desc">Grades conceptual understanding and cause-effect reasoning against formal Q&A rubrics—never penalizing L2 grammar or code-mixing.</p>
        </div>
        <div class="feature-card">
            <div class="feature-icon">⚖️</div>
            <div class="feature-heading">Decoupled Dimensions</div>
            <p class="feature-desc">Separates technical content mastery from communication pacing and structural framing, preventing stylistic grading bias.</p>
        </div>
        <div class="feature-card">
            <div class="feature-icon">⏱️</div>
            <div class="feature-heading">Time-Linked Feedback</div>
            <p class="feature-desc">Surfaces top-3 high-leverage improvement areas with exact audio timestamps, verbatim quotes, and ready-to-say ≤30-word fixes.</p>
        </div>
        <div class="feature-card">
            <div class="feature-icon">🔄</div>
            <div class="feature-heading">Interactive Re-Answer Loop</div>
            <p class="feature-desc">Empowers candidates to re-record specific flagged points and witness real-time score gains and feedback updates immediately.</p>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # Step-by-Step Candidate Journey
    st.markdown("### 🗺️ Candidate Evaluation Journey")
    st.markdown("""
    <div class="process-grid">
        <div class="process-step">
            <span class="step-number">STEP 01</span>
            <div class="step-title">AI Speaks Question</div>
            <p class="step-desc">Select from Computer Science categories; neural voice speaks the challenge aloud with domain hotword hints.</p>
        </div>
        <div class="process-step">
            <span class="step-number">STEP 02</span>
            <div class="step-title">Audio Capture</div>
            <p class="step-desc">Record your spoken response or upload an audio file; normalized to 16kHz mono with privacy-preserving cleanup.</p>
        </div>
        <div class="process-step">
            <span class="step-number">STEP 03</span>
            <div class="step-title">Evidence-Based Scoring</div>
            <p class="step-desc">Content coverage, structural organization, and speaking pacing are scored independently with rubric status tracking.</p>
        </div>
        <div class="process-step">
            <span class="step-number">STEP 04</span>
            <div class="step-title">Targeted Re-Answer</div>
            <p class="step-desc">Select any missing or partial rubric point to re-answer; watch your Content Score recover in real time.</p>
        </div>
    </div>
    """, unsafe_allow_html=True)

def render_architecture_page():
    """Renders the comprehensive system architecture documentation tab."""
    st.markdown("## 🔬 Technical Architecture & Methodology")
    st.caption("How IMAIRA FairScore achieves accent neutrality, statistical calibration, and LLM reasoning consistency.")

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("""
        #### 1. Two-Pass Speech Ingestion & Acoustic Recovery
        - **Pass A (Domain-Biased)**: Faster-Whisper decodes audio conditioned on question-specific glossary hotwords (`B-tree`, `WAL`, `MVCC`).
        - **Pass B (Unbiased Baseline)**: Decodes without conditioning to detect acoustic anomalies.
        - **Phonetic Slice Recovery**: Identifies candidate domain terms and corrects acoustic confusion without altering candidate intent.
        """)

        st.markdown("""
        #### 2. Grounded Semantic Proposition Evaluation
        - **120-Rubric Knowledge Base**: Built from `data/rubrics_120.json` and grounded in `data/QandA.json`.
        - **3-Run Temperature Mode-Voting**: Eliminates LLM jitter by executing 3 deterministic runs at `temperature=0` with median score tie-breaking.
        - **Decoupled Structural Scoring**: Evaluates framing, logical coherence, and closure independently from technical correctness.
        """)

    with col2:
        st.markdown("""
        #### 3. Isotonic Calibration & Metric Normalization
        - **Human Panel Alignment**: Maps raw LLM rubric coverage scores to true calibrated human scores using monotonic regression.
        - **Pre-trained Artifacts**: Leverages isotonic model artifacts (`artifacts/calibrator_content.pkl`, `artifacts/calibrator_structure.pkl`) to guarantee bounded error margins.
        - **Deterministic Uncertainty Rule**: Triggers human flag if 3-way score range exceeds 1.0 or if knife-edge evidence cutpoints are met.
        """)

        st.markdown("""
        #### 4. Re-Answer Loop Delta Engine
        - **Targeted Rescore**: Candidate provides supplementary clarification exclusively targeting unmet rubric criteria.
        - **Score Gain Calculation**: Computes mathematically verified score delta $\\Delta = \\text{Score}_{\\text{after}} - \\text{Score}_{\\text{before}}$ while preserving unchanged rubric scores.
        """)

    st.divider()
    st.info("IMAIRA FairScore strictly preserves candidate privacy: audio files are automatically purged from local memory immediately following transcription.")
