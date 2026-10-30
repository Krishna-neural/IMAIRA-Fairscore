# IMAIRA FairScore — Cross-Speaker Fairness & Consistency Audit Report
**Experiment ID:** `EXP_FAIRNESS_2026_01` | **Date:** 2026-10-30T06:43:52.655093
**Tolerance Benchmark:** `Score Range <= 5.0 points (0-100 scale)`
**Overall Compliance Verdict:** **NON_COMPLIANT_INVESTIGATION_REQUIRED**

---
## 1. Executive Summary & Key Performance Indicators

- **Total Answer Groups Audited:** 3
- **Valid Groups Evaluated:** 3
- **Groups Passing 5-Point Tolerance:** 2 / 3 (66.7%)
- **Average Cross-Speaker Score Range:** `3.33 points`
- **Maximum Observed Disparity:** `10.0 points`

---
## 2. Group-by-Group Statistical Consistency

| Group ID | Question | N Recs | Min Score | Max Score | Range | Mean ± Std | Status |
|---|---|---:|---:|---:|---:|---:|---:|
| `FAIR_001` | `Q084` | 2 | 68.4 | 68.4 | **0.0** | 68.4 ± 0.0 | ✅ PASS |
| `FAIR_002` | `Q120` | 2 | 83.8 | 83.8 | **0.0** | 83.8 ± 0.0 | ✅ PASS |
| `FAIR_003` | `Q109` | 2 | 58.4 | 68.4 | **10.0** | 63.4 ± 5.0 | ❌ FAIL |

---
## 3. Diagnostic Breakdown & Attribution

The Fairness Audit Lab analyzes whether score differences originated from genuine technical differences, speech recognition errors, or evidence extraction drift:

### Group FAIR_001 (Q084)
- **Technical-Term Recall:** `12.5%`
- **Provisional Safeguards Triggered:** `2` recordings protected
- **Human Reference Agreement (MAE):** `26.60 points`
- **Criterion Score Ranges:** Q084_IDEA_1: 0.0, Q084_IDEA_2: 0.0, Q084_IDEA_3: 0.0
- **Primary Diagnostic Attribution:** `consistent_scoring`

### Group FAIR_002 (Q120)
- **Technical-Term Recall:** `25.0%`
- **Provisional Safeguards Triggered:** `0` recordings protected
- **Human Reference Agreement (MAE):** `14.20 points`
- **Criterion Score Ranges:** Q120_IDEA_1: 0.0, Q120_IDEA_2: 0.0, Q120_IDEA_3: 0.0
- **Primary Diagnostic Attribution:** `consistent_scoring`

### Group FAIR_003 (Q109)
- **Technical-Term Recall:** `0.0%`
- **Provisional Safeguards Triggered:** `2` recordings protected
- **Human Reference Agreement (MAE):** `28.60 points`
- **Criterion Score Ranges:** Q109_IDEA_1: 0.0, Q109_IDEA_2: 0.0, Q109_IDEA_3: 0.5
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