# IMAIRA FairScore — Testing & Quality Assurance Report

## 1. Automated Test Suite Summary

- **Test Framework:** `pytest 9.2.0` (Python 3.14 / AnyIO / Pluggy)
- **Total Test Cases Collected:** 50
- **Total Tests Passed:** **45**
- **Total Tests Skipped (GPU-only hardware tests):** 5
- **Total Tests Failed:** **0 (100% Pass Rate)**
- **Total Test Execution Duration:** 3.55 seconds

```
collected 50 items

tests/test_api_endpoints.py .........                                    [ 18%]
tests/test_cpu1_pipeline.py ..............                               [ 46%]
tests/test_frontend.py .....                                             [ 56%]
tests/test_qanda_integration.py ..........                               [ 76%]
tests/test_recover.py sss                                                [ 82%]
tests/test_span_detector.py .....                                        [ 92%]
tests/test_transcribe.py s.s.                                            [100%]

======================== 45 passed, 5 skipped in 3.55s ========================
```

---

## 2. Interactive Testing Lab Results (18 Core Categories)

All 18 automated tests can be executed interactively by judges directly from the **Judge Console > 5. Testing Lab** tab or via `GET /test/all`.

| Test ID | Category | Test Name | Target Expectation | Actual Outcome | Measured Latency | Status |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| `test_audio_capture` | Audio Ingestion | Audio Buffer & Chunk Ingestion | 250ms PCM audio buffer parsed, latency < 50ms | Duration: 250.0ms, Ingestion: 0.01ms | 0.01 ms | **PASS** |
| `test_live_transcription` | Live ASR | Provisional Live Transcription | Status 'provisional', word_count: 9, non-blocking | Status: provisional, words: 9 | 5.36 ms | **PASS** |
| `test_partial_transcript_updates` | Live ASR | Incremental Hypothesis Updating | Monotonically increasing word count, prefix preserved | Chunk 1: 3 words $\to$ Chunk 2: 7 words | 0.02 ms | **PASS** |
| `test_final_transcript_generation` | ASR Finalization | Final Utterance Finalization | Verified transcript emitted with full audit trail | Verified text: 'polymorphism allows objects...' | 0.16 ms | **PASS** |
| `test_transcript_reconciliation` | ASR Finalization | Transcript Reconciliation | Zero duplicated boundary words across chunks | 'An AVL tree maintains strict balance of one' | 0.01 ms | **PASS** |
| `test_technical_terminology` | Terminology | Technical Terminology Recognition | 5 engineering terms indexed in glossary.csv | All 5 terms present and indexed | 5.08 ms | **PASS** |
| `test_hotword_vs_baseline` | Two-Pass ASR | Pass A Hotword vs Pass B Baseline | Candidate terms extracted across dual passes | Extracted: ['backpropagation', 'gradient descent'] | 5.31 ms | **PASS** |
| `test_suspect_span_detection` | Span Detection | Acoustic Confusion & Alias Detection | Detect 'has map' at low confidence $\to$ 'hash map' | Detected span: candidate 'hash map' | 0.71 ms | **PASS** |
| `test_acoustic_verification` | Verification | Evidence-Checked Span Verification | Correction accepted to 'hash map' with CORRECTED | Status: CORRECTED (fuzzy_score: 95.0) | 0.11 ms | **PASS** |
| `test_abstention` | Abstention | Conservative Abstention Policy | Original word preserved when evidence missing | 'testing' preserved; abstain from 'A/B testing' | 0.07 ms | **PASS** |
| `test_rubric_tagging` | Rubrics | Semantic Proposition Tagging (≥5 words) | $\ge 2$ propositions, each $\ge 5$ words | 2 ideas, lengths: 22 and 24 words | 1.75 ms | **PASS** |
| `test_content_scoring` | Evaluation | Content Scoring (CPU 1 Concept Engine) | Content score $\ge 70\%$, calibrated score present | Content score: 92%, Calibrated: 4.68/5.0 | 33.55 ms | **PASS** |
| `test_structure_scoring` | Evaluation | Structure Scoring (Framing, Coherence, Closure) | Structure score $\ge 60\%$, subscores present | Structure score: 88%, Calibrated: 4.52/5.0 | 3.88 ms | **PASS** |
| `test_communication_scoring` | Evaluation | Communication Fluency Rubric | Score $\ge 80\%$, WPM $\sim 130$–150, 0% fillers | Score: 85%, Pace: 132 WPM, 0% fillers | 0.05 ms | **PASS** |
| `test_prompt_injection` | Security | Prompt Injection & Role Override Defense | Intercept 3 adversarial injection vectors | Flagged 3/3 attacks; role firmly maintained | 0.22 ms | **PASS** |
| `test_camera_permissions` | Privacy | Camera Permission Handling & Isolation | Identical Content score with camera on vs off | Camera on: 92% == Camera off: 92% | 7.18 ms | **PASS** |
| `test_api_resilience` | Resilience | Offline Fallback & Graceful Degradation | Deterministic offline evaluator executes cleanly | Overall score produced: 89.4%, status: completed | 3.50 ms | **PASS** |
| `test_fairness_invariance` | Fairness | Accent Invariance Stress Test (\|$\Delta$\| $\le 5$) | Content delta across 20% WER perturbation $\le 5$ pts | Clean: 92%, Perturbed: 92%, Delta: 0.0 pts | 7.29 ms | **PASS** |

---

## 3. How to Execute Tests

Judges can reproduce the test results locally using any of the following methods:

### Method A: Execute Pytest Command Line
```bash
python -m pytest
```

### Method B: Execute Python Runner Script
```bash
python -c "from tests.judge_lab import run_all_lab_tests; res = run_all_lab_tests(); print('All passed:', all(r['passed'] for r in res))"
```

### Method C: Execute from the Web Application
1. Start the platform: `python -m api.main`
2. Navigate to `http://localhost:8002/#judge`
3. Click tab **5. Testing Lab (18 Tests)**
4. Click **🔄 Re-run All Tests** to view live execution in real time.
