# IMAIRA FairScore — Placement Officer Institutional Intelligence Report
**Report ID:** `REP_POI_20261030_055921` | **Generated:** 2026-10-30T05:59:21.334427
**Authorized Officer:** `lead_placement_officer`

---
## 1. Cohort Performance Overview & Statistical KPIs

- **Total Students Evaluated:** 2
- **Total Interviews Conducted:** 8
- **Average Verified Content Score:** `50.0 / 100`
- **Average Provisional Score:** `14.3`
- **Median Score:** `50.0` | **Std Dev:** `0.0`
- **Evaluations Requiring Review:** `100.0%` (0 unresolved)

### Score Distribution
- 80–100 (Exemplary): 0
- 60–79 (Proficient): 0
- 40–59 (Developing): 0
- 0–39 (Needs Attention): 8

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
- Provisional evaluations active: `8`
- Evaluations pending human review: `0`
- Marks protected/affected by uncertainty: `40.1 pts`

### Category 4: Human-versus-System Disagreement
- Human-reviewed benchmark recordings: `11`
- Mean Absolute Error (MAE): `47.63` pts
- Disagreements exceeding 15 points: `3`

---
## 4. Evaluation Quality Alerts & Management

### [HIGH] High Volume of Provisional Evaluations (`ALT_QUAL_002`)
- **Category:** `high_provisional_rate` | **Status:** `ACTIVE`
- **Description:** 8 interviews (100.0%) received provisional credit due to speech recognition ambiguity.
- **Recommended Action:** Review acoustic environments and headset microphone configurations to reduce speech recognition uncertainty.

### [MEDIUM] Unresolved ASR Spans in Cohort (`ALT_ASR_003`)
- **Category:** `asr_recognition_problem` | **Status:** `ACTIVE`
- **Description:** 237 suspicious audio segments remain unresolved after acoustic slice rechecking.
- **Recommended Action:** Utilize the Human Expert Review Portal to verify spoken terminology against audio.

### [HIGH] Significant AI-Human Scoring Disparity (`ALT_HUM_004`)
- **Category:** `human_score_disagreement` | **Status:** `ACTIVE`
- **Description:** Automated evaluation diverges from gold-standard human targets with MAE = 47.6 points.
- **Recommended Action:** Recalibrate rubric weights and benchmark criteria against faculty assessment guidelines.
