# IMAIRA FairScore — Unified AI Mock Interviewer & Evidence-Driven Evaluation Platform

> **"Grade what you know, not how you sound."**

An enterprise-grade, accent-fair, and evidence-grounded AI technical interview platform designed to decouple technical knowledge from speech communication disfluencies, regional accents, and ASR artifacts.

Built for the **Integraminds AI FRONTIER Software Track** second-round technical evaluation.

---

## 🌟 Overview & Product Vision

Conventional automated interview systems suffer from severe phonetic, accent, and cultural biases. Standard automatic speech recognition (ASR) engines routinely mistranscribe technical domain terms spoken in non-native or regional accents (e.g., transcribing *"hash map"* as *"has map"*, or *"semaphore"* as *"semfor"*). Compounding this error, naive LLM evaluators penalize candidates for speech disfluencies, L2 grammar patterns, and ASR artifacts, incorrectly conflating communication accent with technical competence.

**IMAIRA FairScore** solves this problem through an end-to-end multi-stage pipeline:
1. **Interactive Virtual Human Interviewer:** Real-time interactive conversational interviewer with live audio streaming, webcam integrity monitoring, and realistic turn-taking.
2. **Two-Pass ASR with Real-Time Acoustic Slice Recovery:** A 2,000-term technical engineering glossary (`data/glossary.csv`) coupled with RapidFuzz lexical matching, Jellyfish Metaphone phonetic indexing, and conservative acoustic re-verification.
3. **Decoupled Evidence-First Scoring:**
   - **Content Mastery (60%):** Evaluates underlying conceptual understanding against semantic rubric propositions with 3-run mode voting at $T=0$. Invariant to ASR errors, syntax, and fillers.
   - **Structure & Coherence (40%):** Evaluates Framing (35%), Coherence (40%), and Closure (25%) decoupled from factual accuracy.
4. **Isotonic Score Calibration:** Calibrated against empirical human reference scores via 5-fold cross-validated isotonic regression models.
5. **Confidence-Aware Uncertainty Protection:** Recognizes acoustic ambiguity and awards provisional credit so accent artifacts are never penalized as technical deficiencies.
6. **Actionable Dual Feedback:** Strictly differentiates between *Technical Knowledge Gaps* (missing concepts, marks lost, model sentence fix) and *Pronunciation/Articulation Scopes of Improvement*.
7. **Institutional Placement Intelligence:** Centralized analytics cohort intelligence, skill gap detection, and automated evaluation audit for university placement officers.

---

## 🏗️ System Architecture

```text
                     Candidate Microphone / Audio Input
                                    │
                                    ▼
                 Audio Ingestion & Streaming Transport
                      (Web Audio API / WebSocket)
                                    │
                                    ▼
       ┌────────────────────────────────────────────────────────┐
       │   ASR Pipeline: Two-Pass + Real-Time Slice Recovery    │
       │   • Pass 1: Streaming WordTiming Tokens                │
       │   • Pass 2: 2,000-Term Glossary & Metaphone Matching   │
       │   • Slice Re-Verification: Abstains on Ambiguity       │
       └────────────────────────────┬───────────────────────────┘
                                    │
                                    ▼
                         Verified Technical Transcript
                                    │
         ┌──────────────────────────┴──────────────────────────┐
         ▼                                                     ▼
┌─────────────────────────────────┐           ┌─────────────────────────────────┐
│     Content Evaluation (60%)    │           │    Structure Evaluation (40%)   │
│  • Grounded in QandA.json       │           │  • Framing (35%)                │
│  • 3-Run Mode Voting at T=0     │           │  • Coherence & Flow (40%)       │
│  • Verbatim Evidence Quotes     │           │  • Closure & Summary (25%)      │
└────────────────┬────────────────┘           └────────────────┬────────────────┘
                 │                                             │
                 └──────────────────────┬──────────────────────┘
                                        │
                                        ▼
                      ┌─────────────────────────────────┐
                      │    Isotonic Score Calibration   │
                      │  • Calibrator Content (619 B)   │
                      │  • Calibrator Structure (603 B) │
                      │  • Cumulative FairScore (1.0-5.0)│
                      └─────────────────┬───────────────┘
                                        │
                                        ▼
         ┌──────────────────────────────┴──────────────────────────────┐
         ▼                                                             ▼
┌─────────────────────────────────┐                   ┌─────────────────────────────────┐
│   Implementation 4: Feedback    │                   │   Implementation 5: Placement   │
│   • Technical Knowledge Gaps    │                   │   Officer Cohort Intelligence   │
│   • Pronunciation Scopes        │                   │   • Concept Mastery Heatmaps    │
│   • Max 3 Actionable Fixes      │                   │   • Uncertainty Audit & Drift   │
└─────────────────────────────────┘                   └─────────────────────────────────┘
```

---

## 🚀 Quick Start

### Option 1: Full-Stack Web Platform (Interactive Virtual Human)

Launch the FastAPI backend server:
```powershell
python -m api.main
```
Open your browser to:
- **Interactive Interview:** `http://localhost:8002/`
- **Judge Technical Console:** `http://localhost:8002/#judge`
- **FastAPI OpenAPI Docs:** `http://localhost:8002/docs`

Launch the React + TypeScript frontend prototype:
```powershell
cd frontend_prototype
npm install
npm run dev
```

### Option 2: Single-Command Batch Audio Evaluation

Evaluate pre-recorded audio answers (.wav, .mp3, .m4a) against the 120-question reference dataset:
```powershell
# Run batch evaluation on recordings in data/recordings/
python evaluate_interview.py

# Or evaluate a specific audio file:
python evaluate_interview.py data/recordings/test_voice_v3.wav
```
The final evaluation report will be generated at [`reports/interview_evaluation_report.md`](reports/interview_evaluation_report.md).

---

## 🧪 Comprehensive Verification & Test Suite

Run the full automated test suite (unit tests, scoring contracts, calibration, and git hygiene):
```powershell
python -m pytest tests/ -v
```

Run pre-flight hardware and asset diagnostics:
```powershell
python check_setup.py
```

Run Judge Testing Lab (18 automated stress and invariant tests):
```powershell
python -c "from tests.judge_lab import run_all_lab_tests; res = run_all_lab_tests(); print('All passed:', all(r['passed'] for r in res))"
```

---

## 📁 Repository Structure

```text
IMAIRA-Fairscore/
├── api/
│   ├── main.py                     # FastAPI application & WebSocket /ws/stream server
│   └── __init__.py
├── artifacts/
│   ├── calibrator_content.pkl      # Isotonic content regression model
│   └── calibrator_structure.pkl    # Isotonic structure regression model
├── asr/
│   ├── recover.py                  # Real-time acoustic slice recovery & fuzzy matching
│   ├── span_detector.py            # Suspect span detector with phonetic indexing
│   ├── stream_bridge.py            # Streaming audio transport & buffer bridge
│   ├── transcribe.py               # Two-pass Faster-Whisper transcriber
│   └── vocabulary_extractor.py     # Technical domain vocabulary extractor
├── contracts/
│   ├── score_request.json          # Score API contract schema
│   ├── score_response.json         # Score API response schema
│   └── transcript.py               # WordTiming, SuspiciousSpan, TwoPassTranscription
├── data/
│   ├── glossary.csv                # 2,000+ technical CS/engineering terms
│   ├── QandA.json                  # 120 validated technical questions & reference answers
│   └── rubrics_120.json            # 120 semantic rubric proposition definitions
├── feedback/
│   ├── generate.py                 # Actionable coaching fix generator
│   └── validate.py                 # Coaching recommendation schema validator
├── frontend/
│   ├── static/                     # Embedded Web SPA (Served at http://localhost:8002/)
│   └── app.py                      # Alternative Streamlit frontend
├── frontend_prototype/             # Modern React + Vite + TypeScript Virtual Human UI
│   ├── src/
│   │   ├── components/avatar/      # 3D/Canvas Human Avatar & Lip-Sync
│   │   ├── components/interview/   # Live captions, question card, chat stream
│   │   ├── components/integrity/   # Camera & proctoring integrity monitor
│   │   ├── pages/InterviewPage.tsx # Virtual Human Mock Interviewer experience
│   │   └── pages/EvaluationPage.tsx# Final FairScore scorecard & dual feedback
│   └── package.json
├── interview/
│   └── conversational.py           # Multi-turn dialog state machine & anti-injection
├── reports/
│   ├── scorer_robustness_report.json # 120-question accent invariance stress test results
│   └── calibration_evaluation_report.json # 5-fold CV isotonic calibration metrics
├── score/
│   ├── calibrate.py                # Isotonic score calibrator
│   ├── comm.py                     # Pace (WPM) & fluency analyzer
│   ├── content.py                  # 3-run T=0 Content Judge
│   ├── pipeline.py                 # Unified FairScore evaluation pipeline
│   ├── qanda.py                    # Question & answer dataset loader
│   ├── rubrics.py                  # SemanticRubricIdea & QuestionRubric models
│   └── structure.py                # Decoupled Structure & Coherence Judge
├── tests/
│   ├── judge_lab.py                # Interactive 18-test testing lab engine
│   ├── test_api_endpoints.py       # FastAPI endpoint tests
│   ├── test_cpu1_pipeline.py       # 96 core scoring & calibration tests
│   ├── test_frontend.py            # Session state lifecycle tests
│   ├── test_qanda_integration.py   # Q&A dataset validation tests
│   └── test_recover.py             # Acoustic slice recovery tests
├── check_setup.py                  # System diagnostic checker
├── evaluate_interview.py           # Batch CLI interview evaluator
└── requirements.txt                # Production Python dependencies
```

---

## 🛡️ Security, Privacy & Integrity Invariants

1. **Server-Side Scoring Enforcement:** Candidates cannot alter scoring formulas, criteria weights, or model configurations client-side.
2. **Prompt-Injection Defense:** Strict regex and semantic heuristics intercept jailbreaks, developer mode triggers, and scoring override commands (`"ignore previous instructions"`), firmly refusing overrides without leaking system prompts.
3. **Webcam Privacy Isolation:** Camera preview is 100% client-side. Zero video frames are recorded or transmitted to the server. Video presence has **zero influence** on Content scores.
4. **Deterministic Evaluation:** Scoring uses temperature $T=0.0$ with 3-run mode voting and fixed uncertainty boundaries to prevent score variance across identical submissions.

---

## 🏆 Competition Credentials

- **Track:** Integraminds AI FRONTIER Software Track
- **Round:** Second-Round Technical Evaluation
- **Repository:** [https://github.com/Krishna-neural/IMAIRA-Fairscore.git](https://github.com/Krishna-neural/IMAIRA-Fairscore.git)
- **Tagline:** *"Grade what you know, not how you sound."*
