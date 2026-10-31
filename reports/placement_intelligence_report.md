# IMAIRA FairScore — Placement Officer Institutional Intelligence Report
**Report ID:** `REP_POI_20261030_064352` | **Generated:** 2026-10-30T06:43:52.696830
**Authorized Officer:** `lead_placement_officer`

---
## 1. Cohort Performance Overview & Statistical KPIs

- **Total Students Evaluated:** 2
- **Total Interviews Conducted:** 8
- **Average Verified Content Score:** `73.4 / 100`
- **Average Provisional Score:** `55.5`
- **Median Score:** `79.8` | **Std Dev:** `9.1`
- **Evaluations Requiring Review:** `62.5%` (0 unresolved)

### Score Distribution
- 80–100 (Exemplary): 0
- 60–79 (Proficient): 6
- 40–59 (Developing): 2
- 0–39 (Needs Attention): 0

---
## 2. Student Skill Gap Analytics

The following technical concepts had the highest marks lost across the cohort:

| Concept | Domain | Assessed | Fail Rate | Avg Marks Lost | Status |
|---|---|---:|---:|---:|---:|

---
## 3. Evaluation Quality Monitoring (The 4 Independent Dimensions)

### Category 1: Student Skill Gaps (Confirmed Technical Deficiencies)
- Total confirmed conceptual weaknesses: `0`

### Category 2: ASR Recognition Problems
- Suspicious transcript segments flagged: `279`
- Audio-verified acoustic slice corrections applied: `24`
- Unresolved ASR segments: `237`
- Interviews with speech recognition incidents: `8`

### Category 3: Uncertain Evaluation Decisions
- Provisional evaluations active: `5`
- Evaluations pending human review: `0`
- Marks protected/affected by uncertainty: `10.0 pts`

### Category 4: Human-versus-System Disagreement
- Human-reviewed benchmark recordings: `6`
- Mean Absolute Error (MAE): `23.13` pts
- Disagreements exceeding 15 points: `2`

---
## 4. Evaluation Quality Alerts & Management

### [CRITICAL] Fairness Tolerance Violation Detected (`ALT_FAIR_001`)
- **Category:** `fairness_audit_failure` | **Status:** `ACTIVE`
- **Description:** Equivalent answers exceeded the 5.0-point tolerance threshold (Max range: 10.0 pts, Pass rate: 66.7%).
- **Recommended Action:** Inspect the Placement Officer Fairness Audit Lab to identify acoustic calibration or rubric drift.

### [HIGH] High Volume of Provisional Evaluations (`ALT_QUAL_002`)
- **Category:** `high_provisional_rate` | **Status:** `ACTIVE`
- **Description:** 5 interviews (62.5%) received provisional credit due to speech recognition ambiguity.
- **Recommended Action:** Review acoustic environments and headset microphone configurations to reduce speech recognition uncertainty.

### [MEDIUM] Unresolved ASR Spans in Cohort (`ALT_ASR_003`)
- **Category:** `asr_recognition_problem` | **Status:** `ACTIVE`
- **Description:** 237 suspicious audio segments remain unresolved after acoustic slice rechecking.
- **Recommended Action:** Utilize the Human Expert Review Portal to verify spoken terminology against audio.
