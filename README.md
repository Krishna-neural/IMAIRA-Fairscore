# IMAIRA FairScore — Full-Stack AI Technical Interview Platform

> **"Grade what you know, not how you sound."**

An intelligent, accent-aware technical interview evaluation platform designed to decouple technical knowledge, answer structure, and speech communication fluency. 

Built for the **Integraminds AI FRONTIER Software Track** second-round technical evaluation.

---

## 🌟 Overview & Product Vision

Conventional automated interview systems suffer from severe phonetic and cultural biases. Standard automatic speech recognition (ASR) engines routinely mistranscribe technical terms spoken in non-native or regional accents (e.g., transcribing *"hash map"* as *"has map"*, or *"PostgreSQL"* as *"postgress"*). Compounding this error, naive LLM evaluators penalize candidates for speech disfluencies, L2 grammar patterns, and ASR artifacts, incorrectly conflating communication accent with technical competence.

**IMAIRA FairScore** solves this problem through an evidence-checked, multi-stage engineering pipeline:
1. **Live Real-Time Voice Interface:** Continuous streaming microphone capture with sub-second provisional transcript visibility as words are spoken.
2. **Stage 2 Terminology Verification:** A 2,000-term technical engineering glossary (`data/glossary.csv`) coupled with RapidFuzz lexical matching and Jellyfish Metaphone/Soundex phonetic verification.
3. **Conservative Acoustic Abstention:** Suspicious spans are verified against audio slices; ambiguous words are preserved without false-positive corruption.
4. **Three Strictly Decoupled Evaluation Dimensions:**
   - **Content Mastery (50%):** Evaluates underlying conceptual understanding against semantic rubric propositions (≥5 words) with 3-run mode voting at $T=0$. Invariant to ASR errors, syntax, and fillers.
   - **Structure & Coherence (30%):** Evaluates Framing (35%), Coherence (40%), and Closure (25%) decoupled from factual accuracy.
   - **Communication Fluency (20%):** Evaluates delivery pace (ideal 110–170 WPM), filler word rate, and extended pauses (>2s).
5. **Calibrated Scoring:** 5-fold cross-validated isotonic regression models mapping raw scores into calibrated percentage metrics.
6. **Judge Technical Console:** A comprehensive technical inspection console featuring interactive architecture diagrams, live API testing, an automated 18-category testing lab, fairness audit dashboards, and latency telemetry.

---

## 🏗️ System Architecture

```
Candidate Microphone
       │
       ▼
Audio Capture & Ingestion (Web Audio API, 16kHz PCM Buffer)
       │
       ▼
Streaming Audio Transport (WebSocket /ws/stream, HTTP/2 Fallback)
       │
       ▼
Voice Activity Detection (VAD Energy Thresholding & Boundaries)
       │
       ▼
Live ASR (Stage 1 Provisional: <500ms hypothesis stream)
       │
       ▼
Final ASR Utterance Reconciliation (Two-Pass ASR / WordTiming Tokens)
       │
       ▼
Suspect-Span Detection (2,000-Term Glossary, RapidFuzz, Phonetic Metaphone)
       │
       ▼
Acoustic Verification & Abstention (Audio slice re-check, CORRECTED vs ABSTAINED)
       │
       ▼
Verified Technical Transcript
       │
       ├─────────────────────────────────┬─────────────────────────────────┐
       ▼                                 ▼                                 ▼
LLM Semantic Rubric Tagging      Structure Organization Judge       Communication Fluency Analyzer
(3-Run T=0 Mode Voting)          (Framing, Coherence, Closure)     (Pace, Fillers, Pauses)
       │                                 │                                 │
       ▼                                 ▼                                 │
Isotonic Content Calibrator      Isotonic Structure Calibrator             │
(5-Fold CV Regression)           (5-Fold CV Regression)                    │
       │                                 │                                 │
       └─────────────────────────────────┼─────────────────────────────────┘
                                         ▼
                         Deterministic Overall Score (50/30/20)
                                         │
                                         ▼
               Evaluation Dashboard & Timestamped Audit Trail
```

---

## 🚀 Quickstart & Installation

### Prerequisites
- **Python 3.10 – 3.14**
- Modern web browser (Chrome, Edge, Firefox, or Safari) with microphone access
- *(Optional)* NVIDIA GPU with CUDA for Faster-Whisper float16 acceleration

### 1. Clone Repository & Install Dependencies
```bash
git clone https://github.com/Krishna-neural/IMAIRA-Fairscore.git
cd IMAIRA-Fairscore

# Install Python requirements
pip install -r requirements.txt
```

### 2. Configure Environment Variables
Copy the environment template:
```bash
cp .env.example .env
```
Edit `.env` (optional for local offline execution):
```env
GEMINI_API_KEY=your_gemini_api_key_here
GEMINI_MODEL=gemini-2.5-flash
FAIRSCORE_PORT=8002
FAIRSCORE_HOST=0.0.0.0
```
*(Note: IMAIRA FairScore includes an offline deterministic concept-matching judge. If no API key is provided, the platform automatically runs in deterministic offline mode with zero crashes).*

### 3. Launch Backend & Web Platform
```bash
python -m api.main
```
The unified full-stack platform will start on **`http://localhost:8002`**.

Open your browser to:
- **Web Platform:** `http://localhost:8002/`
- **Judge Console:** `http://localhost:8002/#judge`
- **API Swagger Docs:** `http://localhost:8002/docs`

*(Optional)* Launch Streamlit frontend alternative:
```bash
streamlit run frontend/app.py
```

---

## 🧪 Automated Test Suite

IMAIRA FairScore includes a comprehensive test suite covering API endpoints, acoustic span detection, scoring pipelines, and the interactive testing lab:

```bash
# Run complete test suite (45 passed, 5 skipped)
python -m pytest

# Run API endpoint integration tests
python -m pytest tests/test_api_endpoints.py -v

# Run 18 Judge Testing Lab categories
python -c "from tests.judge_lab import run_all_lab_tests; res = run_all_lab_tests(); print(f'Passed {sum(1 for r in res if r[\"passed\"])}/{len(res)} tests')"
```

---

## 📊 Measured Performance & Fairness Telemetry

| Metric | Target Specification | Measured Result | Status |
| :--- | :--- | :--- | :--- |
| **First Partial Transcript Latency** | < 1,000 ms | **320 ms** | **PASS** |
| **Provisional Update Latency** | 500 – 1,000 ms | **410 ms** | **PASS** |
| **Stage 2 Glossary Verification** | < 1,000 ms | **28.5 ms** | **PASS** |
| **Final Answer Evaluation Latency** | < 20.0 s | **2.40 s** | **PASS** |
| **Real-Time Factor (RTF)** | < 0.50 | **0.18** | **PASS** |
| **Duplicated Finalized Segments** | 0 segments | **0 segments** | **PASS** |
| **Accent Invariance Content Delta (MAE)** | ≤ 5.0 pts / 100 | **0.00 pts** | **PASS** |

---

## 📁 Repository Structure

```
IMAIRA-Fairscore/
├── api/
│   ├── __init__.py
│   └── main.py                     # FastAPI REST & WebSocket server
├── asr/
│   ├── span_detector.py            # RapidFuzz & Metaphone 2,000-term detector
│   ├── stream_bridge.py            # Real-time provisional & Stage 2 verification bridge
│   ├── transcribe.py               # Two-pass ASR decoder (Pass A biased, Pass B baseline)
│   └── recover.py                  # Acoustic audio re-check & conservative abstention
├── contracts/
│   ├── transcript.py               # WordTiming, SuspiciousSpan, TwoPassTranscription dataclasses
│   ├── score_request.json          # Score API contract schema
│   └── score_response.json         # Score API response schema
├── data/
│   ├── glossary.csv                # 2,000+ technical CS/engineering terms
│   ├── QandA.json                  # 120 validated technical questions & reference answers
│   └── rubrics_120.json            # 120 semantic rubric proposition definitions
├── feedback/
│   ├── generate.py                 # Top-3 actionable coaching fix generator (≤ 30 words)
│   └── validate.py                 # Coaching recommendation schema validator
├── frontend/
│   ├── static/                     # Flagship Web SPA (Served at http://localhost:8002/)
│   │   ├── index.html              # Modern dark-mode single-page application
│   │   ├── css/styles.css          # Master design system & animation keyframes
│   │   └── js/
│   │       ├── audio_engine.js     # Web Audio API analyser, VU meter, SpeechRecognition
│   │       ├── camera_engine.js    # WebRTC camera stream & privacy manager
│   │       ├── interview_engine.js # Multi-turn dialog & Web Speech TTS engine
│   │       └── judge_console.js    # Interactive architecture, API tester & Testing Lab
│   └── app.py                      # Alternative Streamlit frontend
├── reports/
│   ├── scorer_robustness_report.json # 120-question accent invariance stress test results
│   └── calibration_evaluation_report.json # 5-fold CV isotonic calibration metrics
├── score/
│   ├── content.py                  # 3-run T=0 Content Judge with SQLite cache & fallback
│   ├── structure.py                # Decoupled Framing, Coherence, Closure Judge
│   ├── comm.py                     # Pace (WPM), filler rate, and pause duration analyzer
│   ├── calibrate.py                # Isotonic score calibrator
│   ├── rubrics.py                  # SemanticRubricIdea & QuestionRubric models
│   └── pipeline.py                 # Integrated FairScore evaluation pipeline
├── tests/
│   ├── judge_lab.py                # Interactive 18-test testing lab engine
│   ├── test_api_endpoints.py       # FastAPI endpoint unit & integration tests
│   ├── test_cpu1_pipeline.py       # CPU 1 scoring & calibration tests
│   ├── test_frontend.py            # Session state lifecycle tests
│   ├── test_qanda_integration.py   # Q&A dataset validation tests
│   ├── test_span_detector.py       # RapidFuzz & phonetic span detection tests
│   └── test_transcribe.py          # Transcribe contract & candidate extraction tests
├── .env.example                    # Environment variable template
├── ARCHITECTURE.md                 # Master Architecture Specification
├── API_DOCUMENTATION.md            # Complete API & WebSocket Documentation
├── IMPLEMENTATION_STATUS.md        # Comprehensive Implementation & Verification Matrix
├── TESTING_REPORT.md               # Automated & Interactive Test Report
├── FAIRNESS_REPORT.md              # 120-Question Accent Invariance Report
├── PERFORMANCE_REPORT.md           # Latency Benchmarks & Telemetry Report
├── LIMITATIONS.md                  # Known Limitations & Mitigation Strategies
├── DISCLOSURES.md                  # Pretrained Models, Libraries, and Ethical Disclosures
└── DEMO_INSTRUCTIONS.md            # Step-by-Step Judge Demonstration Walkthrough
```

---

## 🛡️ Security, Privacy & Integrity Invariants

1. **Server-Side Scoring Enforcement:** Candidates cannot alter scoring formulas, criteria weights, or model configurations client-side.
2. **Prompt-Injection Defense:** Rigid regex heuristics intercept jailbreaks, developer mode triggers, and scoring override commands (`"ignore previous instructions"`), firmly refusing overrides without leaking system prompts.
3. **Webcam Privacy Isolation:** Camera preview is 100% client-side. Zero video frames are recorded or transmitted to the server. Video presence has **zero influence** on Content scores.
4. **Deterministic Evaluation:** Scoring uses temperature $T=0.0$ with 3-run mode voting and fixed uncertainty boundaries to prevent score variance across identical submissions.

---

## 🏆 Competition Credentials

- **Track:** Integraminds AI FRONTIER Software Track
- **Round:** Second-Round Technical Evaluation
- **Repository:** [https://github.com/Krishna-neural/IMAIRA-Fairscore.git](https://github.com/Krishna-neural/IMAIRA-Fairscore.git)
- **Tagline:** *"Grade what you know, not how you sound."*
