# IMAIRA FairScore — System Setup Guide

Complete installation, dependency configuration, and startup instructions for the IMAIRA FairScore platform.

---

## 1. System Requirements

- **Operating System:** Windows 10/11, macOS (12+), or Linux (Ubuntu 20.04+)
- **Python:** Version 3.10 to 3.14
- **Browser:** Google Chrome (recommended for Web Audio and SpeechRecognition), Microsoft Edge, Mozilla Firefox, or Safari
- **Microphone:** Any standard internal or USB microphone
- **Webcam:** Any standard internal or USB webcam (optional)
- **GPU (Optional):** NVIDIA RTX GPU with CUDA 12+ for Faster-Whisper `float16` acceleration

---

## 2. Environment Setup

### Step A: Clone the Repository
```bash
git clone https://github.com/Krishna-neural/IMAIRA-Fairscore.git
cd IMAIRA-Fairscore
```

### Step B: Create a Python Virtual Environment (Recommended)
```bash
python -m venv venv

# On Windows:
venv\Scripts\activate

# On Linux/macOS:
source venv/bin/activate
```

### Step C: Install Dependencies
```bash
pip install -r requirements.txt
```

*(Optional: For GPU-accelerated local Whisper decoding on CUDA):*
```bash
pip install -r requirements-gpu.txt
```

### Step D: Configure Environment Variables
```bash
cp .env.example .env
```
Open `.env` and set any desired keys. If `GEMINI_API_KEY` is omitted, the platform automatically runs in deterministic offline mode.

---

## 3. Running the Application

### Launch Full-Stack Web Platform (Recommended)
```bash
python -m api.main
```
Open your browser to:
- **Web Application:** `http://localhost:8002/`
- **Judge Technical Console:** `http://localhost:8002/#judge`
- **FastAPI Interactive Docs:** `http://localhost:8002/docs`

### Launch Streamlit Interface (Alternative)
```bash
streamlit run frontend/app.py
```

---

## 4. Running the Test Suite

```bash
# Run complete test suite (45 passed, 5 skipped)
python -m pytest

# Run API endpoint tests
python -m pytest tests/test_api_endpoints.py -v

# Run 18 Judge Testing Lab categories
python -c "from tests.judge_lab import run_all_lab_tests; res = run_all_lab_tests(); print('All passed:', all(r['passed'] for r in res))"
```
