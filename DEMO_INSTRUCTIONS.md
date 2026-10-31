# IMAIRA FairScore — Judge Demonstration & Evaluation Instructions

This guide provides step-by-step instructions for judges, evaluators, and engineers conducting the technical evaluation of **IMAIRA FairScore: Evidence-Driven, Confidence-Aware, and Accent-Fair AI Interview Platform**.

---

## ⚡ Quick Start: One-Command End-to-End CLI Demo

To immediately verify the full multi-turn interview lifecycle, speech recognition with accent recovery, background scoring, dual diagnosis, SQLite persistence, and cohort intelligence without opening a browser:

```bash
python scripts/demo_e2e_interview.py
```

### What this automated demo script executes:
1. **Engine Pre-Flight:** Verifies Isotonic Content/Structure calibrators, 2,000-term glossary, and 120-question bank.
2. **Session Initialization:** Starts an interactive multi-turn session for candidate *"Rupesh Kumar"* in *"Systems & Database Architecture"*.
3. **Conversational Greeting:** Candidate responds to interviewer greeting; state transitions smoothly to technical questioning.
4. **Question 1 with Non-Native Phonetic Slips:** Candidate answers with common accent confusions (*"semfor"*, *"cubernetes"*). The Two-Pass ASR Bridge detects and recovers them (*"semaphore"*, *"Kubernetes"*) in real-time ($< 35\text{ms}$).
5. **Question 2 with Caching Confusions:** Candidate discusses distributed systems using *"reddis"* and *"has map"*. The system recovers *"Redis"* and *"hash map"*, while accurately distinguishing technical phrase discussion from knowledge gaps.
6. **Session Conclusion & FairScore Aggregation:** Computes the verified FairScore using:
   $$\text{FairScore} = 0.60 \times \text{Calibrated Content} + 0.40 \times \text{Calibrated Structure}$$
7. **Dual Diagnosis Compilation:**
   - **Technical Knowledge Gaps (Score Impacting):** Identifies missing concepts, marks lost, and actionable model sentences.
   - **Pronunciation & Articulation Improvements (Zero Deduction):** Displays recovered terms, coaching tips, and verifies **0.0 marks deducted**.
8. **ACID SQLite Persistence:** Verifies that all turns, audio paths, recovery logs, and scorecards are stored in `artifacts/sessions.db`.
9. **Fairness Invariance Audit Check:** Confirms $\le 5.0\text{ pt}$ cross-speaker invariance under phonetic perturbations.
10. **Cohort Placement Officer Intelligence:** Aggregates student KPIs and skill gaps under RBAC security.

---

## 🚀 Interactive Full-Stack Virtual Human Demonstration

### 1. Launch the Backend FastAPI Service
Open a terminal in the project root:
```bash
python -m api.main
```
Or with Uvicorn:
```bash
uvicorn api.main:app --host 0.0.0.0 --port 8000 --reload
```
You will observe:
```
[INFO] SuspiciousSpanDetector initialized with 2000 terms (conf_thresh=0.85, sim_thresh=75.0)
INFO: Uvicorn running on http://0.0.0.0:8000 (Press CTRL+C to quit)
```

### 2. Launch the React Virtual Human Avatar Frontend
In a second terminal:
```bash
cd frontend_prototype
npm install
npm run dev
```
Open your browser and navigate to:
**`http://localhost:5173/`** (or the port displayed by Vite).

---

## 🎙️ Conducting a Live Candidate Interview

### Step 1: Pre-Flight Configuration
1. Click **`🚀 START LIVE INTERVIEW`**.
2. Configure candidate details:
   - Candidate Name: Enter your name (e.g., *"Judge Evaluator"* or *"Rupesh"*).
   - Domain: Select *"Systems & Database Architecture"* or *"Software & Computer Science Fundamentals"*.
   - Difficulty: Select *"Intermediate"*.
   - Question Count: Select *"2"* or *"3"*.
3. Test your Microphone:
   - Click **`Test Microphone 🎤`** $\to$ speak $\to$ observe the animated audio waveform respond in real time.
4. Click **`🚀 Begin Technical Interview`**.

### Step 2: Interactive Voice Conversation & Real-Time Live ASR
1. **AI Greeting:** The Virtual Human Interviewer enters the animated **Speaking** state and speaks its greeting aloud via Text-to-Speech (TTS).
2. **Candidate Speaking:** When the AI finishes speaking, the avatar automatically switches to the **Listening** state.
3. **Real-Time Live Transcription:**
   - Speak your answer into the microphone. Words stream live onto the screen with provisional styling.
4. **Accent & Regional Articulation Recovery:**
   - Say a technical phrase with non-native articulation (e.g., *"We lock threads using a semfor and orchestrate containers on cubernetes"*).
   - Click **`⚡ Submit Answer`** (or pause).
   - **Observe:** The system detects the suspect spans against the 2,000-term glossary, recovers them to *"semaphore"* and *"Kubernetes"*, and attaches the recovery telemetry transparently.
5. **Silent Evaluation:** The backend evaluates Content and Structure silently without interrupting the conversational flow.

### Step 3: Conclude Interview & Inspect Dual Diagnosis Dashboard
1. Complete the questions or click **`🚪 Conclude & Evaluate`**.
2. Inspect the **Verified Evaluation Scorecard**:
   - **Overall FairScore:** $60\%$ Calibrated Content $+ 40\%$ Calibrated Structure (0–100% and 0.0–5.0 scales).
   - **Accent Invariance Guarantee Active:** Banner certifying that full credit was awarded for acoustically verified terms.
3. Inspect the **Dual Diagnosis Panel**:
   - **Technical Knowledge Gaps:** Conceptual omissions, marks lost, and recommended model response.
   - **Pronunciation & Articulation Improvements:** Recovered terms, phonetic coaching tips, and an explicit **0.0 marks deducted** guarantee.
4. Expand **Turn-by-Turn Transcript & Recovery Deep-Dive**:
   - Inspect verbatim raw speech vs. recovered technical transcripts for each turn.

---

## ⚖️ Inspecting the Judge Technical Console

Click **`⚖️ Judge Console`** in the top navigation bar to access institutional diagnostics:

- **System Overview:** Engine status, active calibrators, glossary count (2,000 terms), and question count (120 rubrics).
- **Interactive Architecture Diagram:** Browse all pipeline components with inputs, outputs, file references, and line numbers.
- **Automated Testing Lab (18 Categories):** Click **`🔄 Re-run All Tests`** to execute all 18 test categories live against the backend in $< 3\text{ seconds}$.
- **Fairness Audit Dashboard:** Inspect the 120-question stress testing results proving an MAE of **0.00 points** (Target: $\le 5.0$ points) and zero systematic bias across accents.

---

## 🛠️ Running Automated Test Suites

All tests can be executed directly from the terminal:

```bash
# 1. Full Backend Test Suite (144 passed across all 5 engines)
python -m pytest tests/ -v

# 2. Automated Testing Lab (18 passed in ~2.8s)
python tests/judge_lab.py

# 3. Stage 5 Integration Suite
python -m pytest tests/test_stage5_frontend_integration.py -v

# 4. Frontend Prototype Unit Tests (8 passed)
cd frontend_prototype && npm test -- --watchAll=false

# 5. Frontend Production Bundle Build
cd frontend_prototype && npm run build
```

---

## 🛡️ Privacy & Offline Resilience

- **Privacy Invariant:** Zero facial or appearance features are stored or processed during evaluation. Video frames are analyzed locally in browser memory strictly for presence detection.
- **100% Offline Capability:** IMAIRA FairScore includes local semantic rubric matchers and pre-trained Isotonic calibrators. The platform operates completely offline without external network dependencies.
