# IMAIRA FairScore — Placement Officer Institutional Intelligence Report
**Report ID:** `REP_POI_20261030_051643` | **Generated:** 2026-10-30T05:16:43.509143
**Authorized Officer:** `placement_officer_demo`

---
## 1. Cohort Performance Overview & Statistical KPIs

- **Total Students Evaluated:** 5
- **Total Interviews Conducted:** 30
- **Average Verified Content Score:** `43.2 / 100`
- **Average Provisional Score:** `None active`
- **Median Score:** `39.6` | **Std Dev:** `28.3`
- **Evaluations Requiring Review:** `0.0%` (0 unresolved)

### Score Distribution
- 80–100 (Exemplary): 0
- 60–79 (Proficient): 10
- 40–59 (Developing): 5
- 0–39 (Needs Attention): 15

---
## 2. Student Skill Gap Analytics

The following technical concepts had the highest marks lost across the cohort:

| Concept | Domain | Assessed | Fail Rate | Avg Marks Lost | Status |
|---|---|---:|---:|---:|---:|
| Explains that REST is strictly stateless | API Design & Archite | 1 | 100.0% | **1.00** | ✅ Confirmed Gap |
| Contrasts statelessness with stateful se | API Design & Archite | 1 | 100.0% | **1.00** | ✅ Confirmed Gap |

---
## 3. Evaluation Quality Monitoring (The 4 Independent Dimensions)

### Category 1: Student Skill Gaps (Confirmed Technical Deficiencies)
- Total confirmed conceptual weaknesses: `2`

### Category 2: ASR Recognition Problems
- Suspicious transcript segments flagged: `0`
- Audio-verified acoustic slice corrections applied: `59`
- Unresolved ASR segments: `0`
- Interviews with speech recognition incidents: `26`

### Category 3: Uncertain Evaluation Decisions
- Provisional evaluations active: `0`
- Evaluations pending human review: `0`
- Marks protected/affected by uncertainty: `0.0 pts`

### Category 4: Human-versus-System Disagreement
- Human-reviewed benchmark recordings: `11`
- Mean Absolute Error (MAE): `47.63` pts
- Disagreements exceeding 15 points: `3`

---
## 4. Evaluation Quality Alerts & Management

### [HIGH] Significant AI-Human Scoring Disparity (`ALT_HUM_004`)
- **Category:** `human_score_disagreement` | **Status:** `ACTIVE`
- **Description:** Automated evaluation diverges from gold-standard human targets with MAE = 47.6 points.
- **Recommended Action:** Recalibrate rubric weights and benchmark criteria against faculty assessment guidelines.
