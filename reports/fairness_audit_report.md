# IMAIRA FairScore — Cross-Speaker Fairness & Consistency Audit Report
**Experiment ID:** `EXP_FAIRNESS_2026_01` | **Date:** 2026-10-30T04:39:01.381373
**Tolerance Benchmark:** `Score Range <= 5.0 points (0-100 scale)`
**Overall Compliance Verdict:** **NON_COMPLIANT_INVESTIGATION_REQUIRED**

---
## 1. Executive Summary & Key Performance Indicators

- **Total Answer Groups Audited:** 3
- **Valid Groups Evaluated:** 3
- **Groups Passing 5-Point Tolerance:** 0 / 3 (0.0%)
- **Average Cross-Speaker Score Range:** `18.57 points`
- **Maximum Observed Disparity:** `28.7 points`

---
## 2. Group-by-Group Statistical Consistency

| Group ID | Question | N Recs | Min Score | Max Score | Range | Mean ± Std | Status |
|---|---|---:|---:|---:|---:|---:|---:|
| `FAIR_001` | `Q084` | 4 | 45.0 | 55.0 | **10.0** | 49.6 ± 3.7 | ❌ FAIL |
| `FAIR_002` | `Q120` | 4 | 52.8 | 81.5 | **28.7** | 60.0 ± 12.4 | ❌ FAIL |
| `FAIR_003` | `Q109` | 3 | 13.5 | 30.5 | **17.0** | 24.4 ± 7.7 | ❌ FAIL |

---
## 3. Diagnostic Breakdown & Attribution

The Fairness Audit Lab analyzes whether score differences originated from genuine technical differences, speech recognition errors, or evidence extraction drift:

### Group FAIR_001 (Q084)
- **Technical-Term Recall:** `12.5%`
- **Provisional Safeguards Triggered:** `0` recordings protected
- **Human Reference Agreement (MAE):** `45.42 points`
- **Criterion Score Ranges:** Q084_IDEA_1: 0.0, Q084_IDEA_2: 0.0, Q084_IDEA_3: 0.0
- **Primary Diagnostic Attribution:** `speech_recognition_disparity`

### Group FAIR_002 (Q120)
- **Technical-Term Recall:** `25.0%`
- **Provisional Safeguards Triggered:** `0` recordings protected
- **Human Reference Agreement (MAE):** `38.03 points`
- **Criterion Score Ranges:** Q120_IDEA_1: 0.0, Q120_IDEA_2: 0.0, Q120_IDEA_3: 0.0
- **Primary Diagnostic Attribution:** `speech_recognition_disparity`

### Group FAIR_003 (Q109)
- **Technical-Term Recall:** `0.0%`
- **Provisional Safeguards Triggered:** `0` recordings protected
- **Human Reference Agreement (MAE):** `67.60 points`
- **Criterion Score Ranges:** Q109_IDEA_1: 0.0, Q109_IDEA_2: 0.5, Q109_IDEA_3: 0.0
- **Primary Diagnostic Attribution:** `speech_recognition_disparity`

---
## 4. Methodology & Fairness Acceptance Rules

1. **Substantive Equivalence:** Every answer group communicates identical technical core ideas, despite natural speaker differences in pronunciation, cadence, and sentence structure.
2. **Production Pipeline Execution:** No manual normalization or human transcript edits occur before evaluation; all recordings pass through production Whisper ASR, recovery recheck, and deterministic scoring.
3. **Decoupled Uncertainty:** Recognition uncertainty is prevented from causing rubric failure via the Confidence-Aware Engine's provisional scoring policy.

---
## 5. Limitations & Future Scope

- Benchmark dataset consists of controlled candidate recordings across diverse Indian regional accents.
- Additional trials with heavy acoustic ambient noise (e.g. cafeteria, wind) are recommended for stress-testing.
- Inter-rater human agreement analysis is currently based on gold-standard faculty rubric annotations.