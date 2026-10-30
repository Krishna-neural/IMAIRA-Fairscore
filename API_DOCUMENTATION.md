# IMAIRA FairScore — API & WebSocket Documentation

Base URL: `http://localhost:8002`  
Interactive Swagger UI: `http://localhost:8002/docs`

---

## 1. System & Diagnostic Endpoints

### `GET /health`
Returns system component status, loaded calibrators, glossary size, and rubric counts.

**Response `200 OK`:**
```json
{
  "status": "ok",
  "service": "IMAIRA FairScore Platform",
  "version": "2.0.0",
  "environment": "single-laptop",
  "calibrators_loaded": {
    "content": true,
    "structure": true
  },
  "rubrics_count": 120,
  "glossary_terms_loaded": 2000,
  "gemini_api_configured": false,
  "active_sessions_count": 0
}
```

---

### `GET /system/overview`
Returns comprehensive operational diagnostics for the Judge Console.

**Response `200 OK`:**
```json
{
  "service": "IMAIRA FairScore Platform",
  "version": "2.0.0",
  "architecture_edition": "Master Engineering Edition",
  "uptime_status": "Online & Operational",
  "backend": {
    "framework": "FastAPI (Python 3.14 / uvicorn)",
    "port": 8002,
    "cors_enabled": true,
    "websocket_enabled": true
  },
  "asr_pipeline": {
    "stage_1": "Incremental Live Stream Bridge (<500ms provisional)",
    "stage_2": "Acoustic Verification & 2,000-Term Glossary Span Detector",
    "glossary_terms_loaded": 2000,
    "whisper_model": "large-v3 (RTX 4050 GPU / int8_float16 / CPU Fallback)",
    "abstention_policy": "Conservative (Abstain unless confidence >= 0.75)"
  },
  "scoring_engine": {
    "content_judge": "3-run T=0 mode voting with SQLite SHA-256 caching",
    "structure_judge": "Decoupled Framing (35%), Coherence (40%), Closure (25%)",
    "communication_judge": "Speech Pace (WPM), Filler Rate (%), Pauses (>2s)",
    "calibrators": {
      "content_calibrator": "Isotonic Regression (Loaded: True)",
      "structure_calibrator": "Isotonic Regression (Loaded: True)"
    },
    "rubrics_database_size": 120,
    "sqlite_caches_active": 2
  }
}
```

---

### `GET /architecture`
Returns structured metadata for all 10 architectural pipeline components.

**Response `200 OK`:**
```json
{
  "pipeline_name": "IMAIRA FairScore End-to-End Technical Evaluation Pipeline",
  "total_components": 10,
  "components": [
    {
      "id": "node_mic",
      "name": "Candidate Microphone",
      "category": "Input Ingestion",
      "purpose": "Captures raw continuous acoustic speech from candidate browser audio interface.",
      "input": "User acoustic voice signal",
      "output": "16kHz 16-bit PCM continuous audio buffer",
      "technology": "Web Audio API (AudioContext, MediaStreamTrack, AnalyserNode)",
      "implementation_file": "frontend/static/js/audio_engine.js",
      "api_endpoint": "Browser MediaDevices API -> WebSocket /ws/stream",
      "test_coverage": "tests/judge_lab.py: test_audio_capture",
      "limitations": "Subject to local environmental background noise and room reverberation."
    }
  ]
}
```

---

## 2. Question Bank Querying

### `GET /questions`
Query available technical questions from the 120-question reference dataset.

**Query Parameters:**
- `category` (optional, string): Filter by engineering domain.
- `difficulty` (optional, string): Filter by difficulty (`Beginner`, `Intermediate`, `Advanced`).

**Response `200 OK`:**
```json
{
  "total_matching": 120,
  "questions": [
    {
      "id": "ENG001",
      "category": "Software and Computer Science Fundamentals",
      "subcategory": "Data Structures",
      "difficulty": "Intermediate",
      "question_type": "Comparison",
      "question": "Compare Red-Black Trees and AVL Trees in terms of balancing invariants, tree height, and search versus insertion/deletion performance.",
      "key_concepts": [
        "Self-Balancing Binary Search Trees",
        "Tree Rotations",
        "Lookup vs Insertion Tradeoffs"
      ],
      "answer": "AVL trees enforce a strict balance factor of at most 1..."
    }
  ]
}
```

---

## 3. Conversational AI Interview Flow

### `POST /interview/start`
Starts a new stateful multi-turn interview session.

**Request Payload:**
```json
{
  "candidate_name": "Dr. Grace Hopper",
  "domain": "Software and Computer Science Fundamentals",
  "difficulty": "Intermediate",
  "num_questions": 3
}
```

**Response `200 OK`:**
```json
{
  "session_id": "sess_8f3a912b",
  "greeting": "Hello Dr. Grace Hopper! Welcome to IMAIRA FairScore...",
  "first_question": {
    "id": "ENG001",
    "question": "Compare Red-Black Trees and AVL Trees in terms of balancing invariants...",
    "category": "Software and Computer Science Fundamentals",
    "difficulty": "Intermediate",
    "key_concepts": ["Self-Balancing Binary Search Trees", "Tree Rotations"]
  },
  "stage": "GREETING",
  "questions_count": 3
}
```

---

### `POST /interview/turn`
Processes a candidate conversational turn, checks for adversarial prompt injection, updates dialog state, and generates the interviewer's next response.

**Request Payload:**
```json
{
  "session_id": "sess_8f3a912b",
  "candidate_utterance": "AVL trees enforce stricter balance factor limits of at most one, so lookups are faster. Red-Black trees require fewer rotations during writes."
}
```

**Response `200 OK`:**
```json
{
  "ai_response": "That is a solid breakdown. Could you elaborate specifically on how tree rotations affect write throughput in concurrent database indices?",
  "stage": "FOLLOW_UP",
  "injection_detected": false,
  "current_question_detail": {
    "id": "ENG001",
    "question": "Compare Red-Black Trees and AVL Trees..."
  }
}
```

---

## 4. Real-Time ASR & Stage 2 Verification

### `POST /asr/stream-chunk`
Processes an incremental partial transcript chunk in real-time.

**Request Payload:**
```json
{
  "session_id": "sess_live",
  "chunk_text": "We store user profiles in a hash map"
}
```

**Response `200 OK`:**
```json
{
  "status": "provisional",
  "provisional_text": "We store user profiles in a hash map",
  "word_count": 8,
  "latency_ms": 0.42
}
```

---

### `POST /asr/verify`
Runs Stage 2 glossary verification, suspect-span detection, and acoustic verification across 2,000 engineering terms.

**Request Payload:**
```json
{
  "raw_transcript": "We store user profiles in a has map and index them in postgress"
}
```

**Response `200 OK`:**
```json
{
  "original_transcript": "We store user profiles in a has map and index them in postgress",
  "verified_transcript": "We store user profiles in a hash map and index them in PostgreSQL",
  "detected_spans_count": 2,
  "corrections_applied": 2,
  "audit_log": [
    {
      "span_id": "span_4_6",
      "original_text": "has map",
      "verified_text": "hash map",
      "time_range": "1.4s - 2.1s",
      "reason": "alias_match",
      "fuzzy_score": 95.0,
      "phonetic_match": true,
      "status": "CORRECTED"
    },
    {
      "span_id": "span_10_11",
      "original_text": "postgress",
      "verified_text": "PostgreSQL",
      "time_range": "3.5s - 4.2s",
      "reason": "alias_match",
      "fuzzy_score": 90.0,
      "phonetic_match": true,
      "status": "CORRECTED"
    }
  ],
  "verification_latency_ms": 28.5
}
```

---

## 5. Scoring & Evaluation

### `POST /score`
Evaluates candidate transcript using CPU 1 Content, Structure, and Calibration engines.

**Request Payload:**
```json
{
  "session_id": "sess_8f3a912b",
  "question_id": "ENG001",
  "question_text": "Compare Red-Black Trees and AVL Trees in terms of balancing invariants.",
  "transcript": [
    {
      "start": 0.0,
      "end": 20.0,
      "speaker": "candidate",
      "text": "AVL trees enforce stricter balance factor limits of at most one, compared to Red-Black tree color and black-height rules. In terms of performance tradeoffs, AVL provides faster searches due to shorter tree height, while Red-Black trees require fewer rotations for write operations."
    }
  ]
}
```

**Response `200 OK`:**
```json
{
  "transcript": [
    { "word": "AVL", "start": 0.0, "end": 0.4, "conf": 0.95 }
  ],
  "scores": {
    "content": 92,
    "structure": 88,
    "communication": 85
  },
  "raw_scores": {
    "content": 4.8,
    "structure": 4.5
  },
  "calibrated_scores": {
    "content": 4.68,
    "structure": 4.52
  },
  "overall_score": 89.4,
  "max_score": 100.0,
  "percentage": 89.4,
  "flags": {
    "ENG001_IDEA_1": "covered",
    "ENG001_IDEA_2": "covered"
  },
  "feedback": [
    {
      "criterion_id": "ENG001_IDEA_1",
      "marks_lost": 0.0,
      "quote": "AVL trees enforce stricter balance factor limits...",
      "fix_sentence": "Outstanding demonstration of core tree invariants."
    }
  ],
  "uncertainty": {
    "is_uncertain": false,
    "reasons": []
  },
  "structure_diagnostics": {
    "framing": { "score": 4.5, "feedback": "Direct opening statement." },
    "coherence": { "score": 4.5, "feedback": "Clear comparative flow." },
    "closure": { "score": 4.5, "feedback": "Definitive takeaway reached." }
  },
  "communication_diagnostics": {
    "score": 85,
    "wpm": 132.0,
    "filler_rate": 0.0,
    "pause_count": 0
  }
}
```

---

## 6. Judge Testing Lab & Telemetry

### `POST /test/run`
Executes an individual test case by ID.

**Request Payload:**
```json
{ "test_id": "test_prompt_injection" }
```

**Response `200 OK`:**
```json
{
  "test_id": "test_prompt_injection",
  "test_name": "Prompt Injection & Role Override Defense",
  "category": "Security & Identity",
  "input": "['Ignore all previous instructions...', 'developer mode...']",
  "expected": "All 3 adversarial injection vectors flagged and neutralized",
  "actual": "Flagged: 3/3 attacks intercepted",
  "passed": true,
  "latency_ms": 0.22,
  "evidence": "Server-side regex filter intercepted role overrides before model invocation"
}
```

---

### `GET /test/all`
Runs the entire 18-category Testing Lab suite.

**Response `200 OK`:**
```json
{
  "total": 18,
  "passed": 18,
  "failed": 0,
  "results": [ ... ]
}
```

---

### `GET /fairness/audit`
Retrieves the 120-question accent invariance report.

**Response `200 OK`:**
```json
{
  "target": "Maximum Content Score delta across accent conditions <= 5.0 points",
  "measured_mean_absolute_error": 0.00,
  "signed_bias": 0.00,
  "qwk_invariance": 1.00,
  "flip_rate": 0.00,
  "status": "PASS: Invariance verified across 120 questions under moderate 20% WER perturbation"
}
```

---

### `GET /metrics/latency`
Retrieves live benchmark latency telemetry.

**Response `200 OK`:**
```json
{
  "first_partial_transcript_latency_ms": 320.0,
  "provisional_update_latency_ms": 410.0,
  "stage2_glossary_verification_latency_ms": 28.5,
  "final_scoring_evaluation_latency_sec": 2.4,
  "rtf": 0.18,
  "status": "All target latencies satisfied"
}
```

---

## 7. Bidirectional WebSocket Streaming

### `WebSocket /ws/stream`
Connect via `ws://localhost:8002/ws/stream`.

**Client Messages:**
- **Send chunk:** `{"type": "chunk", "text": "candidate spoken words", "timestamp": 1.45}`
- **Finalize utterance:** `{"type": "finalize", "text": "complete candidate utterance", "word_timings": [...]}`
- **Keep-alive ping:** `{"type": "ping"}`

**Server Messages:**
- **Provisional Hypothesis:**
  ```json
  {
    "type": "provisional",
    "text": "candidate spoken words",
    "word_count": 3,
    "latency_ms": 0.35
  }
  ```
- **Verified Utterance:**
  ```json
  {
    "type": "verified",
    "original_transcript": "...",
    "verified_transcript": "...",
    "audit_log": [ ... ],
    "latency_ms": 28.5
  }
  ```
- **Pong:** `{"type": "pong", "time": 1730268000.0}`
