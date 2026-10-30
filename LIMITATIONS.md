# IMAIRA FairScore — Engineering Limitations & Failure Cases

Honest, transparent engineering requires identifying where a system's current boundaries lie, detailing active mitigations, and documenting the future development roadmap.

---

## 1. Limitation & Failure Mode Matrix

| Failure Mode / Boundary | Failure Mechanism | Observed Impact | Current Active Mitigation | Future Engineering Roadmap |
| :--- | :--- | :--- | :--- | :--- |
| **1. Extreme Ambient Noise** | Background construction, multi-speaker crosstalk, or low-cost laptop mic distortion. | Drops raw acoustic confidence below threshold ($< 0.60$). | Browser Web Audio noise suppression + conservative abstention policy. | Multi-microphone beamforming and spectral subtraction filter. |
| **2. Un-Enunciated Slurred Speech** | Candidate mumbles rapidly ($> 220$ WPM) without articulatory separation. | Acoustic phonetic slice cannot isolate syllables for Metaphone match. | Low-confidence flag logged; original words preserved; Communication score flags excessive pace. | Personalized acoustic enrollment and speaker adaptation. |
| **3. Emerging Brand & Library Names** | Novel open-source packages released after glossary compilation (not in 2,000 terms). | Span detector cannot match against static dictionary. | RapidFuzz fuzzy ratio fallback with confidence gating; question key concepts dynamically added. | Dynamic glossary extraction from target job description or GitHub repo. |
| **4. Long Thinking Pauses (>3.0s)** | Candidate pauses mid-sentence to formulate a complex algorithmic proof. | Voice Activity Detection (VAD) energy threshold may misinterpret pause as completion. | Generous 2.5s silence threshold + manual "Submit Answer" button so candidate controls turn end. | Multimodal gaze tracking and prosodic pitch trajectory end-of-thought detection. |
| **5. External LLM Rate Limits (429)** | Cloud provider throttling or intermittent network disconnection. | Model evaluation API returns 429 or timeout. | Exponential backoff with jitter + deterministic offline concept-matching judge fallback. | Local ONNX/quantized LLM running locally on device via llama.cpp. |
| **6. Camera Permission Denied** | Candidate denies browser webcam permission or has no camera hardware. | Video feed unavailable in candidate preview panel. | Camera is strictly optional; scoring continues with 100% functionality and 0% penalty. | Audio-only avatar layout mode that reclaims camera screen space. |
| **7. Multi-Lingual Code-Switching** | Candidate speaks full sentences in Hindi/Spanish interspersed with English. | ASR English acoustic model experiences token insertion/deletion errors. | Content Judge is instructed to tolerate code-mixed discourse markers; evaluates technical English tokens. | Multilingual multilingual Whisper models with automatic language identification. |
| **8. Browser SpeechSynthesis Variance** | Operating systems provide different installed TTS voices (e.g. robotic voices on older Linux). | AI Interviewer voice quality differs depending on client OS. | Voice selection heuristic prioritizes Natural/Google/Samantha voices; falls back to text interaction. | Neural server-side streaming TTS (e.g. Piper, ElevenLabs, or Kokoro). |

---

## 2. Abstention Philosophy

IMAIRA FairScore strictly follows a **"Do No Harm"** abstention philosophy:

> *When speech-to-text evidence is acoustically ambiguous, it is far safer for an interview platform to leave an imperfect word unchanged than to hallucinate a false correction.*

Every glossary recovery requires:
1. Lexical or phonetic similarity $\ge 75.0$ points.
2. Acoustic re-check confirming candidate tokens in the target slice.
3. If criteria are unmet, the system logs an explicit `ABSTAINED` entry in the audit trail, protecting candidate integrity.
