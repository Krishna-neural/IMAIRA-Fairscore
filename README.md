# IMAIRA FairScore — AI Technical Mock Interview Evaluator

IMAIRA FairScore is a high-precision, production-grade technical interview evaluation pipeline designed to assess engineering candidates fairly, objectively, and comprehensively.

The system transcribes spoken technical answers, recovers accent and domain-term misrecognitions, detects conceptual misconceptions, evaluates rubric completeness, scores answer structure, and computes an isotonic calibrated **Overall FairScore ($1.0 - 5.0$)**.

---

## Quick Start (Single-Command Execution)

### Option A: Double-Click (Zero Terminal Setup)
1. Dump your interview audio recordings (`.wav`, `.mp3`, `.m4a`) into:
   ```
   IMAIRA-Fairscore/data/recordings/
   ```
2. Double-click **`RUN_EVALUATION.bat`** (located in `Deviathon2.0/` or `IMAIRA-Fairscore/`).
3. View results in terminal and in [`reports/interview_evaluation_report.md`](reports/interview_evaluation_report.md).

### Option B: Terminal / Command Line
```powershell
# From the IMAIRA-Fairscore directory:
..\torch-env\Scripts\python evaluate_interview.py

# Or evaluate a specific file or folder:
..\torch-env\Scripts\python evaluate_interview.py data/recordings/test_voice_v3.wav
```

---

## System Architecture

```
                    ┌───────────────────────────────────────────────┐
                    │ Spoken Candidate Audio (.wav / .mp3 / .m4a)   │
                    └──────────────────────┬────────────────────────┘
                                           │
                                           ▼
┌───────────────────────────────────────────────────────────────────────────────────┐
│ 1. TWO-PASS ASR & ACCENT RECOVERY (asr/)                                          │
│    • Pass 1: Initial Whisper transcription with word timestamps                   │
│    • Pass 2: Prompt-biased re-decoding & acoustic phonetic discrepancy detection │
│    • Recovery: Acoustic term re-verification against domain glossary              │
└──────────────────────────────────────────┬────────────────────────────────────────┘
                                           │
                                           ▼
┌───────────────────────────────────────────────────────────────────────────────────┐
│ 2. QUESTION MATCHER & RUBRIC ALIGNMENT (score/)                                   │
│    • Matches candidate answer against 120 benchmark questions (data/QandA.json)   │
│    • Loads question-specific criteria & negative constraints                      │
└──────────────────────────────────────────┬────────────────────────────────────────┘
                                           │
                                           ▼
┌───────────────────────────────────────────────────────────────────────────────────┐
│ 3. MULTI-DIMENSIONAL SCORING ENGINE                                               │
│    • Content Completeness (1.0 - 5.0): Rubric idea-by-idea criteria match         │
│    • Content Correctness  (1.0 - 5.0): Factual consistency & misconception check  │
│    • Answer Structure     (1.0 - 5.0): Framing, logical coherence, closure        │
│    • Timestamps [t_start, t_end]: Aligns quotes, corrections & errors to audio    │
└──────────────────────────────────────────┬────────────────────────────────────────┘
                                           │
                                           ▼
┌───────────────────────────────────────────────────────────────────────────────────┐
│ 4. ISOTONIC SCORE CALIBRATION (artifacts/)                                        │
│    • Non-parametric monotonic mapping learned from benchmark evaluations          │
│    • Overall FairScore = 0.60 * Calibrated_Content + 0.40 * Calibrated_Structure  │
└──────────────────────────────────────────┬────────────────────────────────────────┘
                                           │
                                           ▼
┌───────────────────────────────────────────────────────────────────────────────────┐
│ 5. GENERATED REPORTS (reports/)                                                   │
│    • reports/interview_evaluation_report.md  (Executive markdown report)          │
│    • reports/interview_evaluation_report.json (Machine-readable diagnostics)      │
└───────────────────────────────────────────────────────────────────────────────────┘
```

---

## Directory & File Guide

```
Deviathon2.0/
├── RUN_EVALUATION.bat          # Top-level launcher for one-click evaluation
├── torch-env/                  # Python 3.11 environment with PyTorch CUDA & Whisper
└── IMAIRA-Fairscore/           # Core Project Repository
    ├── RUN_EVALUATION.bat      # In-project launcher
    ├── evaluate_interview.py   # Unified evaluation engine (ASR + Rubric + Scores)
    │
    ├── asr/                    # Speech Recognition & Domain Recovery
    │   ├── transcribe.py       # Two-pass Faster-Whisper transcriber
    │   ├── span_detector.py    # Phonetic discrepancy & domain span detector
    │   ├── recover.py          # Acoustic slice recovery for accent errors
    │   └── profile_baseline.py # GPU inference latency & memory profiling
    │
    ├── score/                  # Evaluation & Scoring
    │   ├── content.py          # Content completeness & correctness judge
    │   ├── structure.py        # Answer structure judge (framing, coherence, closure)
    │   ├── calibrate.py        # Isotonic regression calibration models
    │   ├── rubrics.py          # 120-question rubric loader and schemas
    │   ├── qanda.py            # Q&A data parser and validator
    │   └── cache.py            # SQLite cache for score evaluation
    │
    ├── contracts/              # Shared Data Contracts
    │   └── transcript.py       # Pydantic schemas (WordTiming, RecoveryAuditEntry)
    │
    ├── data/                   # Rubrics, Reference Data & Audio Drop-Folder
    │   ├── recordings/         # DROP FOLDER for candidate voice recordings
    │   ├── rubrics_120.json    # 120 standardized interview questions & rubrics
    │   ├── QandA.json          # Technical questions with domain reference answers
    │   ├── glossary.csv/.txt   # Technical terms for accent & domain recovery
    │   ├── dataset_dev_240.json# Calibration development dataset (240 entries)
    │   └── dataset_heldout_60.json # Held-out benchmark dataset (60 entries)
    │
    ├── artifacts/              # Trained Machine Learning Models
    │   ├── calibrator_content.pkl   # Isotonic model for content scoring
    │   ├── calibrator_structure.pkl # Isotonic model for structure scoring
    │   └── calibrator_metadata.json # Calibration training metrics
    │
    ├── reports/                # Evaluation & Benchmark Outputs
    │   ├── interview_evaluation_report.md   # Latest candidate report
    │   └── interview_evaluation_report.json # Detailed timestamped JSON
    │
    ├── eval/                   # Benchmarks & Offline Validation
    │   ├── validate_recovery.py # ASR recovery precision/recall benchmarks
    │   ├── scorer_only.py       # Scorer accent-invariance validation
    │   └── agreement.py         # Human-machine agreement ceiling analysis
    │
    ├── scripts/                # Dataset Utilities
    │   ├── build_datasets.py        # Builds calibration datasets
    │   └── rebuild_qanda_dataset.py # Re-syncs Q&A rubrics
    │
    ├── tests/                  # Automated Test Suite (36/36 Passing)
    │   ├── test_cpu1_pipeline.py    # Calibration, rubrics, & architectural tests
    │   ├── test_qanda_integration.py# Q&A data integrity tests
    │   ├── test_transcribe.py       # ASR transcription tests
    │   ├── test_span_detector.py    # Phonetic span detector tests
    │   └── test_recover.py          # Acoustic term recovery tests
    │
    ├── config.yaml             # Core configuration (models, thresholds, weights)
    ├── requirements.txt        # Base dependencies
    ├── requirements-gpu.txt    # CUDA-accelerated dependencies
    ├── .gitignore              # Clean gitignore excluding audio, cache, & models
    └── .env.example            # Environment variables template
```

---

## What the System Reports for Every Recording

1. **Exact Timestamps $[t_{\text{start}}, t_{\text{end}}]$:** Word-level timestamps for every spoken phrase, correction, and evidence citation.
2. **What Was Corrected:** A complete audit trail of candidate misrecognitions and accent corrections.
3. **Where the Candidate Got Wrong:** Critical misconceptions, conceptual gaps, and missing technical ideas with severity flags (`[CRITICAL]`, `[MODERATE]`, `[MINOR]`).
4. **Official Scores ($1.0 - 5.0$):**
   - **Content Completeness:** Rubric idea coverage ($1.0 - 5.0$).
   - **Content Correctness:** Factual accuracy and absence of technical fallacies ($1.0 - 5.0$).
   - **Answer Structure:** Framing, Coherence, and Closure ($1.0 - 5.0$).
   - **Calibrated Overall FairScore:** Blended score via Isotonic Regression ($1.0 - 5.0$).
