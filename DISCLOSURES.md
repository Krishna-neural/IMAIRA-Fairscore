# IMAIRA FairScore — Technology, Model & Ethical Disclosures

Conforming to Section 15I of the Master Engineering Specification, this document provides complete, transparent disclosure of all pretrained models, external services, datasets, and ethical invariants.

---

## 1. Pretrained Models & Model Weights

| Model | Provider / Architecture | License | Parameter Size / Precision | Role in IMAIRA FairScore |
| :--- | :--- | :--- | :--- | :--- |
| **Faster-Whisper `large-v3`** | OpenAI / SYSTRAN (CTranslate2) | MIT License | 1,550M parameters (int8_float16 / float16) | Offline two-pass speech recognition and acoustic slice re-decoding on CUDA. |
| **Gemini 2.5 Flash** | Google DeepMind | Commercial API | Cloud Generative LLM | Semantic rubric proposition tagging and structural coherence analysis at $T=0.0$. |
| **Isotonic Calibrator Models** | Scikit-Learn IsotonicRegression | BSD 3-Clause | Custom trained on 5-fold CV human ratings | Maps raw Content & Structure scores to calibrated percentage benchmarks. |

*(Note: In offline environments where API keys or GPU weights are unavailable, IMAIRA FairScore executes its deterministic offline concept evaluator with zero crashes).*

---

## 2. Open-Source Libraries & Frameworks

- **Backend ASGI:** `fastapi` (0.162.0), `uvicorn` (0.54.0), `starlette` (1.10.0), `pydantic` (2.14.1)
- **Acoustic & Phonetic Verification:** `rapidfuzz` (3.14.6), `jellyfish` (1.3.0)
- **Machine Learning & Calibration:** `scikit-learn` (1.9.1), `numpy` (2.5.4), `scipy` (1.18.1), `pandas` (3.1.0)
- **Audio Processing:** `wave`, `soundfile`, `librosa`
- **Testing:** `pytest` (9.2.0), `anyio` (4.15.1)
- **Frontend Technologies:** HTML5, CSS3, JavaScript (ES2022 Modules), Web Audio API, Web Speech API, WebRTC MediaDevices.

---

## 3. Datasets & Reference Corpora

1. **120-Question Technical Reference Dataset (`data/QandA.json`):**
   - 120 validated engineering questions spanning 9 disciplines.
   - Conforms strictly to the Proposition Standard (all semantic rubric propositions $\ge 5$ words).
2. **2,000-Term Technical Engineering Glossary (`data/glossary.csv`):**
   - Curated taxonomy of core computer science, systems, and algorithms terminology.
3. **Robustness & Calibration Reports (`reports/`):**
   - Human-annotated baseline and 20% WER perturbed benchmark dataset verifying accent invariance.

---

## 4. Ethical Commitments & Data Privacy Standards

1. **Zero Biometric Retention:**
   - Candidate webcam feeds are processed entirely in local browser memory.
   - Zero video frames, audio recordings, or facial embeddings are persisted to disk or sent to external cloud servers.
2. **No Pseudoscientific Emotional Inference:**
   - The platform strictly rejects claims that facial expressions, micro-movements, or pupil dilations measure intelligence, honesty, or technical competence.
   - Camera preview is provided solely for interview realism and has **0% influence on Content scores**.
3. **Accent Neutrality Mandate:**
   - Content evaluation explicitly penalizes zero points for non-native pronunciation, regional English accents, or code-mixed colloquial fillers.
4. **No Hidden Prompt Leaks:**
   - System prompts and secret keys are guarded server-side and never exposed to the client interface.
