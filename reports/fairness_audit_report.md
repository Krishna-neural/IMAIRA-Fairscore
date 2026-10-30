# IMAIRA FairScore — Cross-Speaker Fairness & Consistency Audit Report
**Experiment ID:** `EXP_FAIRNESS_2026_01` | **Date:** 2026-10-30T05:59:53.833631
**Tolerance Benchmark:** `Score Range <= 5.0 points (0-100 scale)`
**Overall Compliance Verdict:** **COMPLIANT**

---
## 1. Executive Summary & Key Performance Indicators

- **Total Answer Groups Audited:** 3
- **Valid Groups Evaluated:** 3
- **Groups Passing 5-Point Tolerance:** 3 / 3 (100.0%)
- **Average Cross-Speaker Score Range:** `0.0 points`
- **Maximum Observed Disparity:** `0.0 points`

---
## 2. Group-by-Group Statistical Consistency

| Group ID | Question | N Recs | Min Score | Max Score | Range | Mean ± Std | Status |
|---|---|---:|---:|---:|---:|---:|---:|
| `FAIR_001` | `Q084` | 2 | 14.3 | 14.3 | **0.0** | 14.3 ± 0.0 | ✅ PASS |
| `FAIR_002` | `Q120` | 2 | 14.3 | 14.3 | **0.0** | 14.3 ± 0.0 | ✅ PASS |
| `FAIR_003` | `Q109` | 2 | 14.3 | 14.3 | **0.0** | 14.3 ± 0.0 | ✅ PASS |

---
## 3. Diagnostic Breakdown & Attribution

The Fairness Audit Lab analyzes whether score differences originated from genuine technical differences, speech recognition errors, or evidence extraction drift:

### Group FAIR_001 (Q084)
- **Technical-Term Recall:** `12.5%`
- **Provisional Safeguards Triggered:** `2` recordings protected
- **Human Reference Agreement (MAE):** `80.70 points`
- **Criterion Score Ranges:** Q084_IDEA_1: 0.5, Q084_IDEA_2: 0.0, Q084_IDEA_3: 0.5
- **Primary Diagnostic Attribution:** `consistent_scoring`

### Group FAIR_002 (Q120)
- **Technical-Term Recall:** `25.0%`
- **Provisional Safeguards Triggered:** `2` recordings protected
- **Human Reference Agreement (MAE):** `83.70 points`
- **Criterion Score Ranges:** Q120_IDEA_1: 0.0, Q120_IDEA_2: 0.0, Q120_IDEA_3: 0.0
- **Primary Diagnostic Attribution:** `consistent_scoring`

### Group FAIR_003 (Q109)
- **Technical-Term Recall:** `0.0%`
- **Provisional Safeguards Triggered:** `2` recordings protected
- **Human Reference Agreement (MAE):** `77.70 points`
- **Criterion Score Ranges:** Q109_IDEA_1: 0.5, Q109_IDEA_2: 0.0, Q109_IDEA_3: 0.0
- **Primary Diagnostic Attribution:** `consistent_scoring`

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