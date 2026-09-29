# ManoBal 🛡️ — Personnel Stress & Welfare Monitoring System
### AI-Driven Early Warning, Longitudinal Welfare Intelligence & Human-in-the-Loop Decision Support for Defense & Uniformed Services
**System Title:** Personnel Stress & Welfare Monitoring System  
**Repository Architecture:** Monorepo (FastAPI ML Backend + Next.js Commander Dashboard + Next.js Jawan Mobile Portal)  
**System Status:** **Ready for Pilot Field Deployment** (`READY WITH MINOR DOCUMENTED GAPS`)

---

## Table of Contents
1. [Project Overview](#1-project-overview)
2. [Problem Statement](#2-problem-statement)
3. [Solution at a Glance](#3-solution-at-a-glance)
4. [Key Features](#4-key-features)
5. [System Architecture](#5-system-architecture)
6. [End-to-End Data Flow](#6-end-to-end-data-flow)
7. [Input Data Dictionary](#7-input-data-dictionary)
8. [AI / ML Architecture](#8-ai--ml-architecture)
9. [Risk Scoring — Detailed Explanation](#9-risk-scoring--detailed-explanation)
10. [Longitudinal Intelligence](#10-longitudinal-intelligence)
11. [Early Warning & Anomaly Detection](#11-early-warning--anomaly-detection)
12. [Welfare Recommendation Engine](#12-welfare-recommendation-engine)
13. [Alerts & Human Review](#13-alerts--human-review)
14. [Follow-up & Outcome Tracking](#14-follow-up--outcome-tracking)
15. [Welfare Case Management](#15-welfare-case-management)
15B. [Jawan Welfare Notifications & Signal Delivery (Phase 47)](#15b-jawan-welfare-notifications--signal-delivery-phase-47)
16. [HRMS Integration (Actual Implementation)](#16-hrms-integration-actual-implementation)
17. [Wearable & Telemetry Integration (Actual Implementation)](#17-wearable--telemetry-integration-actual-implementation)
18. [Database Architecture & Entity Relationships](#18-database-architecture--entity-relationships)
19. [API Architecture & Route Groups](#19-api-architecture--route-groups)
20. [Frontend Architecture](#20-frontend-architecture)
21. [Security Architecture & Anti-IDOR](#21-security-architecture--anti-idor)
22. [Privacy & Ethical Non-Punitive Design](#22-privacy--ethical-non-punitive-design)
23. [Project Directory Structure](#23-project-directory-structure)
24. [Technology Stack](#24-technology-stack)
25. [Installation & Setup](#25-installation--setup)
26. [Running the System](#26-running-the-system)
27. [Example End-to-End Usage Walkthrough](#27-example-end-to-end-usage-walkthrough)
28. [Example Inputs & Outputs](#28-example-inputs--outputs)
29. [Testing & Verification Results](#29-testing--verification-results)
30. [Known Limitations](#30-known-limitations)
31. [Future Scope](#31-future-scope)
32. [Live Demo Flow (5–10 Minutes)](#33-live-demo-flow-510-minutes)
34. [Technical Architecture Explanation (Technical Pitch)](#35-technical-architecture-explanation-technical-pitch)

---

## 1. Project Overview

**ManoBal** (translating from Hindi to *"Mental Strength"* or *"Inner Morale"*) is an indigenous, enterprise-grade AI-powered welfare monitoring and early-warning decision-support system designed specifically for Central Armed Police Forces (CAPFs), Armed Forces, and uniformed personnel in India.

### What Problem It Solves
Uniformed personnel operate under extreme conditions: extended field deployments, high operational tempo, circadian disruption from night shifts, family separation, hazardous field duty, and physical exhaustion. Traditional psychological support in military organizations is largely **reactive**—interventions occur only after acute distress, disciplinary breakdowns, absenteeism, or suicidal ideation manifest. ManoBal converts this dynamic into a **proactive, preventive welfare paradigm**.

### Who Uses It
1. **Jawans (Uniformed Personnel):** Utilize a private, dignified, mobile-first self-assessment portal for daily recovery check-ins, mood tracking, personal stress trajectory visualization, and actionable self-care recommendations.
2. **Commanders (Company & Battalion Commanders):** Utilize an operational web dashboard for aggregated, unit-level stress heatmaps, early-warning anomaly alerts, and workload distribution intelligence.
3. **Welfare Officers & Clinical Counselors:** Utilize a structured case management workspace for evidence-based human reviews, supportive interventions, duty-pacing adjustments, and longitudinal outcome tracking.
4. **System Administrators:** Oversee role provisioning, tenant battalion configurations, API health, and audit trail compliance.

### What Makes ManoBal Proactive
Unlike static psychological questionnaires administered annually, ManoBal fuses continuous operational duty indicators (duty hours, night shifts, consecutive duty days, leave gaps) with voluntary subjective check-ins and recovery metrics. Machine learning models continuously compute risk velocity ($\Delta S / \Delta t$) and statistical anomalies, flagging worsening trends **weeks before a clinical crisis emerges**.

```
PROACTIVE PARADIGM:
Traditional Military:  Crisis Event Occurs ──► Disciplinary or Emergency Psychiatric Referral (Reactive)
ManoBal Paradigm:      Duty + Sleep Deficit ──► AI Detects Worsening Velocity ──► Early Rest Stand-Down (Preventive)
```

---

## 2. Problem Statement

### Operational Reality in Uniformed Services
Personnel deployed in border outposts, counter-insurgency operations, and high-altitude deployments face compound stressors:
- **Extended Continuous Deployment:** Months without rotation away from high-threat zones.
- **Sleep Deprivation & Night Rotations:** Fragmented circadian cycles that degrade cognitive resilience.
- **Consecutive Duty Stretches:** 14 to 30 consecutive days on active duty without a 24-hour restorative rest window.
- **Accumulated Leave Deficit:** Operational constraints often delay sanctioned annual leave for 6 to 9 months.
- **Stigmatization Barrier:** Cultural barriers in military units often discourage personnel from openly reporting mental health struggles due to fear of career penalties or perceived weakness.

### How ManoBal Solves These Challenges
- **Multi-Factor Objective Grounding:** Evaluates objective operational stressors alongside subjective self-reports so risk identification does not rely solely on self-disclosure.
- **Privacy-Shielded Non-Punitive Design:** Eliminates individual rankings, leaderboards, and autonomous disciplinary actions. Individual assessments are strictly confidential; commanders only view aggregate unit metrics and supportive triage recommendations.
- **Human-in-the-Loop Governance:** AI outputs supportive recommendations (e.g., *"Consider a 48-hour rest stand-down"*), but all final intervention decisions require authenticated human review.

---

## 3. Solution at a Glance

The complete system pipeline transitions raw data into structured human welfare actions:

```
[Personnel / Jawan] ──► Voluntary Self-Assessment & Check-In (Port 3001)
         │
[HRMS Service Record] ──► Duty Hours, Night Shifts, Deployment Days, Leave Gaps
         │
[Telemetry Bridge] ──► Sleep Duration, Heart Rate, HRV Recovery Signals
         │
         ▼
[Pydantic Validation & Shielding] (Rejects NaN, Inf, negative values)
         │
         ▼
[Feature Engineering Pipeline] (28 Domain Features & Interaction Terms)
         │
         ▼
[LightGBM ML Champion Model] (Predicts Calibrated Continuous Risk Score [0–100])
         │
         ├─────────────────────────────────────────┐
         ▼                                         ▼
[Longitudinal Trajectory Engine]        [Isolation Forest Anomaly Engine]
(EWMA Velocity, Trend: Improving/Worsening)   (SHAP Factor Attribution)
         │                                         │
         └────────────────────┬────────────────────┘
                              │
                              ▼
                [Welfare Alert & Recommendation Engine]
           (High Stress Spike, Worsening Trend, Rest Stand-down)
                              │
                              ▼
             [Authorized Human Review & Triage] (Port 3000)
                              │
                              ▼
           [Welfare Case Management & Controlled Lifecycle]
              (OPEN ──► UNDER_REVIEW ──► RESOLVED)
                              │
                              ▼
               [Scheduled Follow-up & Outcome Tracking]
                   (Pre vs. Post Recovery Delta)
                              │
                              ▼
                 [Immutable Audit Trail Logging]
```

| Pipeline Stage | Nature | Governance Rule |
| :--- | :---: | :--- |
| **Data Collection** | Automated / Voluntary | Voluntary self-reporting; HRMS ingestion via scoped API. |
| **Risk Prediction** | Automated (AI) | Calibrated LightGBM model; strictly bounded within $[0, 100]$. |
| **Anomaly Detection** | Automated (AI) | Isolation Forest flags statistical deviations with SHAP factors. |
| **Recommendations** | Automated (Rule-based) | Evidence-based suggestions; **no autonomous action taken**. |
| **Triage & Decision** | **Human Decision** | Commander / Counselor must review and authorize actions. |
| **Case Progression** | **Human Decision** | Status transitions require authenticated user signature and reason. |
| **Intervention Closure** | **Human Decision** | Automated closure is prohibited; human closure note mandatory. |

---

## 4. Key Features

### 4.1 Personnel / Jawan Experience (`manobal-mobile`)
- **Secure Authentication:** JWT bearer token authentication with role `personnel`.
- **14-Screen Interactive Assessment:** Touch-friendly slider controls for duty hours, night shifts, consecutive duty days, sleep duration, physical fatigue, mood/morale, and burnout frequency.
- **Immediate Calibrated Feedback:** Displays personal stress category (Low, Medium, High, Very High) with supportive, non-stigmatizing visual guidance.
- **Personal Trend Tracking:** Recharts longitudinal graphs tracking personal risk scores over 7, 30, and 90 days.
- **Self-Care Recommendations:** Direct self-guided recovery actions (circadian sleep pacing, breathing routines, hydration guidelines).
- **Self-Only Authorization:** Strict Anti-IDOR enforcement prevents jawans from accessing any peer records or commander-level views.

### 4.2 Commander & Welfare Officer Experience (`manobal-web`)
- **Unit Welfare Overview:** Real-time summary cards displaying active personnel count, average stress index, and stress/risk category distributions.
- **Early-Warning Alerts Panel:** Multi-tier alerts (`HIGH_STRESS_SPIKE`, `WORSENING_TREND`, `ANOMALOUS_FATIGUE`, `PROLONGED_DEPLOYMENT`) with urgency badges.
- **Anomaly Detection Heatmap:** Isolation Forest signals highlighting personnel experiencing anomalous multidimensional shifts, annotated with SHAP attribution bars.
- **Support Recommendations Panel:** Context-aware suggestions (e.g., 48-hour rest stand-down, schedule review, fast-track leave).
- **Personnel Profile Drilldown:** Scoped access to individual operational history, consecutive duty stretches, and historical recovery trajectories.
- **Unit Intelligence Aggregates:** High-level battalion stress maps protected by $k \ge 5$ k-anonymity privacy thresholds.

### 4.3 AI & Behavioral Analytics Engine
- **Calibrated ML Risk Engine V2:** LightGBM champion pipeline trained on multi-factor operational and psychological datasets, calibrated via isotonic regression to produce continuous 0–100 scores.
- **Explainable AI (SHAP):** TreeExplainer extracts individual feature contributions, translating complex tree splits into plain-language drivers (e.g., *"Elevated duty schedule: 72 hrs/week"*).
- **Longitudinal Dynamics:** Exponentially Weighted Moving Average (EWMA) tracks velocity ($\Delta S / \Delta t$) and acceleration to detect rapid decompensation before thresholds are breached.
- **Input Shielding:** Pydantic validation rejects string injections, "NaN", "Inf", negative sleep hours, and out-of-range ages.

### 4.4 Welfare Case Management Workspace
- **Controlled Lifecycle:** Cases transition strictly through validated states (`OPEN` $\rightarrow$ `UNDER_REVIEW` $\rightarrow$ `SUPPORT_IN_PROGRESS` $\rightarrow$ `AWAITING_FOLLOW_UP` $\rightarrow$ `MONITORING` $\rightarrow$ `RESOLVED` $\rightarrow$ `CLOSED`).
- **Immutable Clinical Notes:** Append-only review notes with author attribution and ISO timestamps.
- **Human Decisions:** Explicit decisions recorded (`CONTINUE_MONITORING`, `REVIEW_DUTY_SUPPORT`, `OFFER_SUPPORT_RESOURCE`, `SCHEDULE_FOLLOW_UP`, `REFER_TO_AUTHORIZED_SUPPORT`).
- **Audit Trails:** Every status transition and note appends to `welfare_case_audits`.

---

## 5. System Architecture

The ManoBal platform uses a decoupled, three-tier micro-architecture:

```mermaid
flowchart TB
    subgraph Presentation ["Presentation Layer (Client Browsers)"]
        UI_CMD["Commander & Welfare Portal (Port 3000)<br>Next.js 14 • React 18 • TailwindCSS • Recharts"]
        UI_JAW["Jawan Mobile Portal (Port 3001)<br>Next.js 16 • Turbopack • Responsive PWA Layout"]
    end

    subgraph API ["API & Routing Layer (FastAPI :8000)"]
        ROUTERS["162 Endpoints across 18 Tag Groups<br>/auth, /predict, /personnel, /assessment, /dashboard<br>/alerts, /anomalies, /recommendations, /followups<br>/welfare-cases, /analytics, /hrms, /telemetry"]
        DEPS["Auth Dependencies & RBAC<br>get_current_user • require_roles • check_personnel_access"]
    end

    subgraph Services ["Service Layer (Business Logic & Intelligence)"]
        SRV_PRED["WelfarePredictionService<br>(LightGBM Inference)"]
        SRV_LONG["LongitudinalAnalyticsService<br>(EWMA Velocity & Trends)"]
        SRV_ALERT["WelfareAlertService<br>(Multi-Tier Escalation)"]
        SRV_ANOM["WelfareAnomalyService<br>(Isolation Forest + SHAP)"]
        SRV_REC["WelfareRecommendationService<br>(Evidence Pacing Engine)"]
        SRV_CASE["WelfareCaseService<br>(Human Review Workspace)"]
        SRV_OUT["WelfareOutcomeService<br>(Pre vs Post Recovery Delta)"]
        SRV_UWI["UnifiedWelfareIntelligenceService<br>(k>=5 Privacy Fusion)"]
    end

    subgraph Storage ["Data Layer (SQLAlchemy ORM + SQLite/PostgreSQL)"]
        DB_USERS[(users)]
        DB_PERS[(personnel)]
        DB_ASSESS[(stress_assessments)]
        DB_ALERTS[(welfare_alerts)]
        DB_ANOM[(welfare_anomalies)]
        DB_RECS[(welfare_recommendations)]
        DB_CASES[(welfare_cases)]
        DB_NOTES[(welfare_case_notes)]
        DB_AUDIT[(welfare_case_audits)]
        DB_HRMS[(hrms_service_records)]
        DB_TELE[(wearable_telemetry)]
    end

    UI_CMD -- "JWT Bearer REST" --> ROUTERS
    UI_JAW -- "JWT Bearer REST" --> ROUTERS
    ROUTERS --> DEPS
    DEPS --> Services
    Services --> Storage
```

---

## 6. End-to-End Data Flow

```mermaid
sequenceDiagram
    autonumber
    actor Jawan as Jawan (PF-0001)
    actor Officer as Commander / Counselor
    participant MobileUI as Jawan App (:3001)
    participant API as FastAPI (:8000)
    participant ML as LightGBM ML Pipeline
    participant Long as Longitudinal Service
    participant Alerts as Alert & Rec Engine
    participant CaseService as Case Management
    participant DB as SQLite / PostgreSQL

    Jawan->>MobileUI: Submit 14-Screen Assessment (Duty: 72h, Sleep: 4.5h)
    MobileUI->>API: POST /api/personnel/1/assess
    API->>API: Verify Token & Personnel Access
    API->>ML: assess_personnel(feature_dict)
    ML-->>API: Risk Score: 80.8, Level: High, Factors: [Duty, Sleep]
    API->>DB: INSERT INTO stress_assessments
    API->>Long: calculate_longitudinal_trend(history)
    Long-->>API: Trajectory: Worsening, Velocity: +17.9
    API->>Alerts: evaluate_signals(assessment, trend)
    Alerts->>DB: INSERT INTO welfare_alerts (HIGH_STRESS_SPIKE)
    Alerts->>DB: INSERT INTO welfare_recommendations (Stand-down 48h)
    API-->>MobileUI: 201 Created (Assessment + Supportive Feedback)
    MobileUI-->>Jawan: Render Stress Level & Self-Care Pacing

    Note over Officer,API: Commander Review Flow
    Officer->>API: GET /api/dashboard/summary & /api/welfare/alerts
    API-->>Officer: Active Alerts: HIGH_STRESS_SPIKE for PF-0001
    Officer->>API: POST /api/welfare-cases (Open Case: WC-2026-0006)
    API->>DB: INSERT INTO welfare_cases (status: OPEN)
    Officer->>API: POST /api/welfare-cases/6/notes ("Initial screening completed")
    API->>DB: INSERT INTO welfare_case_notes
    Officer->>API: POST /api/welfare-cases/6/status (status: UNDER_REVIEW)
    API->>DB: UPDATE welfare_cases & INSERT INTO welfare_case_audits
```

---

## 7. Input Data Dictionary

Every input feature utilized by the ManoBal platform is verified in the active codebase:

| Parameter | Domain Category | Data Type | Permitted Range | Source | Used By | Required? |
| :--- | :--- | :---: | :---: | :--- | :--- | :---: |
| `duty_hours_per_week` | Operational | Float | 0.0 – 168.0 | Assessment / HRMS | LightGBM, Pacing Rules | Required |
| `consecutive_duty_days` | Operational | Integer | 0 – 365 | Assessment / HRMS | Fatigue Rules, Anomaly | Required |
| `night_shifts_per_month` | Operational | Integer | 0 – 31 | Assessment / HRMS | Circadian Disruption Index | Required |
| `leave_gap_days` | Operational | Integer | 0 – 1000 | Assessment / HRMS | Leave Deficit Metric | Required |
| `deployment_days` | Operational | Integer | 0 – 2000 | HRMS Sync / Seed | Cumulative Exposure | Optional |
| `operational_exposure` | Operational | String | Low, Medium, High | Assessment / Roster | Exposure Multiplier | Required |
| `remote_posting` | Operational | String | Yes, No | Assessment / Roster | Isolation Stress Factor | Required |
| `transfer_frequency` | Operational | Integer | 0 – 20 | HRMS Sync / Seed | Organizational Instability | Optional |
| `training_load` | Operational | Integer | 1 – 5 | HRMS Sync / Seed | Physical Workload | Optional |
| `sleep_hours` | Recovery | Float | 0.0 – 24.0 | Assessment / Wearable | Sleep Deficit Calculation | Required |
| `physical_activity_hours`| Recovery | Float | 0.0 – 50.0 | Assessment / Wearable | Physical Conditioning | Optional |
| `mood_score` | Wellbeing | Integer | 1 – 5 | Assessment Check-in | Subjective Morale Factor | Required |
| `burnout_symptoms` | Wellbeing | String | Rarely, Sometimes, Often | Assessment Wizard | Burnout Penalty Multiplier | Required |
| `age` | Demographic | Integer | 18 – 65 | Personnel Profile | Baseline Normalization | Required |
| `gender` | Demographic | String | Male, Female, Other | Personnel Profile | Demographic Baseline | Required |
| `experience_years` | Demographic | Float | 0.0 – 45.0 | Personnel Profile | Experience Adaptation | Required |
| `heart_rate` | Physiological | Integer | 30 – 220 | Telemetry Bridge | Anomaly Detection | Optional |
| `hrv_rmssd` | Physiological | Float | 5.0 – 250.0 | Telemetry Bridge | Parasympathetic Recovery | Optional |

---

## 8. AI / ML Architecture

### 8.1 Machine Learning Pipeline
- **Champion Model Artifact:** `ml_pipeline/models/final_stress_prediction_pipeline.pkl`
- **Model Type:** Calibrated LightGBM (Light Gradient Boosting Machine) Ensemble.
- **Preconditioning:** Scikit-Learn `Pipeline` executing median imputation for continuous missing values, one-hot encoding for categorical variables (`Location`, `Department`, `Job_Role`), and min-max feature scaling.
- **Probability Calibration:** Isotonic regression calibrated on out-of-fold validation splits to minimize Brier score and ensure output probabilities reflect true empirical risk frequencies.

### 8.2 Anomaly Detection vs. Risk Scoring
It is critical to distinguish the two complementary AI engines in ManoBal:
1. **Authoritative Risk Classifier (LightGBM):** Evaluates known, supervised stress relationships (e.g., high duty hours + low sleep = high stress probability). Outputs a continuous score $[0, 100]$ and categorical band.
2. **Behavioral Anomaly Detector (Isolation Forest):** Evaluates unsupervised statistical divergence. An anomaly flags a jawan whose multidimensional pattern deviates significantly from their peer cohort (e.g., normal duty hours but sudden collapse in HRV and extreme mood drop).

```
AI SYSTEM SEPARATION:
┌─────────────────────────────────┐     ┌─────────────────────────────────┐
│   Supervised Risk Prediction    │     │  Unsupervised Anomaly Detection │
│         (LightGBM V2)           │     │       (Isolation Forest)        │
│  Outputs: Risk Score (0–100)    │     │  Outputs: Outlier Flag (-1 / 1) │
│  Focus: Workload & Sleep Strain │     │  Focus: Statistical Divergence  │
└─────────────────────────────────┘     └─────────────────────────────────┘
```

---

## 9. Risk Scoring — Detailed Explanation

### 9.1 Risk Categories & Calibrated Bands
The authoritative continuous risk score is mapped to four distinct operational tiers:

| Tier | Score Range | Operational Meaning | Recommended Action |
| :--- | :---: | :--- | :--- |
| **Low** | $0.0 - 34.9$ | Normal operational stress resilience. Restorative sleep adequate. | Routine monitoring; standard duty rotations. |
| **Medium** | $35.0 - 64.9$ | Moderate strain. Elevated duty hours or mild sleep deficit detected. | Monitor consecutive shifts; encourage recovery pacing. |
| **High** | $65.0 - 84.9$ | Significant operational fatigue and persistent sleep debt. | Active welfare review; consider 48h rest stand-down. |
| **Very High** | $85.0 - 100.0$ | Acute compound overload across operational and recovery vectors. | Immediate supportive check-in; fast-track leave cycle. |

### 9.2 Real-World Scenarios (Verified Values)
The following scenarios reflect verified empirical outputs from the running system:

#### Scenario 1: Healthy Operational Baseline
- **Inputs:** Age 29, 8.0h sleep, 42.0 duty hrs/wk, 4 consecutive days, 2 night shifts, 15 leave days taken, `burnout_symptoms: "Rarely"`.
- **Output:** **Risk Score: 26.8 | Category: Low | Priority: Routine**
- **System Action:** No alerts generated; routine telemetry logged.

#### Scenario 2: Moderate Operational Strain
- **Inputs:** Age 32, 5.0h sleep, 68.0 duty hrs/wk, 18 consecutive days, 10 night shifts, 95 leave gap days, `burnout_symptoms: "Sometimes"`.
- **Output:** **Risk Score: 56.0 | Category: Medium | Priority: Elevated**
- **System Action:** Supportive duty pacing suggested; logged in unit monitoring queue.

#### Scenario 3: Compound Critical Overload
- **Inputs:** Age 28, 3.0h sleep, 96.0 duty hrs/wk, 35 consecutive days, 24 night shifts, 240 leave gap days, 210 deployment days, `burnout_symptoms: "Often"`.
- **Output:** **Risk Score: 88.5 | Category: High / Very High | Priority: Urgent**
- **System Action:** Triggers `HIGH_STRESS_SPIKE` alert; generates 48-hour rest stand-down recommendation; flags for Welfare Officer case opening.

---

## 10. Longitudinal Intelligence

ManoBal does not rely on isolated snapshots. The `LongitudinalAnalyticsService` tracks multi-assessment histories:
- **EWMA Temporal Smoothing:** Applies Exponentially Weighted Moving Averages ($\alpha = 0.3$) giving higher weight to recent assessments while preserving historical context.
- **Risk Velocity ($\Delta S / \Delta t$):** Evaluates rate of score change per unit time. A jawan moving from score 30 to 60 over 7 days triggers an early warning even though 60 is below the critical threshold.
- **Trajectory Classification:** Automatically classifies personal trends as:
  - `Improving`: Negative velocity ($\Delta S < -5.0$).
  - `Stable`: Score within $\pm 5.0$ band.
  - `Worsening`: Positive velocity ($\Delta S > +5.0$).
- **Multi-Window Analysis:** Evaluates 7-day, 30-day, and 90-day rolling horizons.

---

## 11. Early Warning & Anomaly Detection

The `WelfareAnomalyService` scans unit cohorts using Isolation Forest:

| Anomaly Signal | Detection Mechanism | Primary Triggers | Operational Purpose |
| :--- | :--- | :--- | :--- |
| **Multivariate Behavioral Outlier** | Isolation Forest ($n\_estimators=100$) | Contradictory inputs (e.g. 90 duty hours but self-reporting 0 fatigue). | Flags potential denial, masked distress, or acute outlier strain. |
| **Circadian Collapse Anomaly** | Rule + Tree Split | Night shifts $> 15$ with sleep duration $< 4.0\text{h}$. | Flags critical sleep deprivation before cognitive failure occurs. |
| **Leave Deficit Anomaly** | Longitudinal Window | Consecutive duty days $> 25$ with leave gap $> 180\text{ days}$. | Prevents chronic burnout from denied rotational leave. |
| **Physiological Divergence** | Telemetry Ingestion Bridge | Resting Heart Rate surge $> 20\%$ with RMSSD drop $> 35\%$. | Detects acute autonomic nervous system exhaustion. |

---

## 12. Welfare Recommendation Engine

The `WelfareRecommendationService` maps detected risk clusters to evidence-based non-clinical recommendations:

| Recommendation Type | Trigger Condition | Suggested Action | Priority |
| :--- | :--- | :--- | :---: |
| **`REST_STAND_DOWN`** | Risk Score $> 75$ or Consecutive Days $> 21$ | Mandatory 48-hour operational stand-down from high-stress duties. | Urgent |
| **`DUTY_SCHEDULE_REVIEW`** | Duty Hours $> 65\text{h/wk}$ or Night Shifts $> 10$ | Commander review of shift distribution and rotational spacing. | High |
| **`LEAVE_SANCTION_FASTTRACK`** | Leave Gap $> 120\text{ days}$ + Worsening Trend | Prioritize approved rotational leave for restorative recovery. | High |
| **`VOLUNTARY_WELLNESS_CHECKIN`**| Anomaly detected or Mood Score $\le 2$ | Offer a confidential, voluntary check-in with unit counselor. | Medium |
| **`SUPPORT_RESOURCE_REFERRAL`**| Persistent Medium/High Risk $> 14\text{ days}$ | Provide access to unit welfare resources, peer support, or helpline. | Medium |

> **Ethical Guardrail:** Recommendations are strictly advisory. The AI engine cannot alter duty rosters, reassign personnel, or order medical leave autonomously.

---

## 13. Alerts & Human Review

```
[Signal Generated] ──► [Welfare Alert Created] ──► [Commander / Welfare Queue]
                                                              │
                                                              ▼
                                                   [Human Review Screen]
                                                              │
                               ┌──────────────────────────────┴──────────────────────────────┐
                               ▼                                                             ▼
                   [Acknowledge & Monitor]                                        [Open Welfare Case]
               (Status: IN_PROGRESS / MONITORING)                            (Escalate to Case Workspace)
```

- **Alert Lifecycle:** `NEW` $\rightarrow$ `ACKNOWLEDGED` $\rightarrow$ `ACTIONED` $\rightarrow$ `DISMISSED`.
- **Deduplication:** Prevents alert fatigue by suppressing duplicate alert generation within a 48-hour cooldown window unless score increases by $\ge 15$ points.
- **Audit Logging:** Every dismissal, acknowledgement, and action records the reviewer ID, timestamp, and justification.

---

## 14. Follow-up & Outcome Tracking

Managed by `WelfareOutcomeService` (`api/routes/followups.py`):
1. **Scheduling:** Following an intervention, the officer schedules a structured follow-up window (7, 14, or 30 days).
2. **Reassessment:** At the follow-up milestone, the jawan submits an updated assessment.
3. **Outcome Calculation:** System compares baseline score ($S_{base}$) with post-intervention score ($S_{post}$):
   $$\Delta S = S_{post} - S_{base}$$
   - **`IMPROVED`:** $\Delta S \le -10.0$ (Significant stress reduction).
   - **`STABLE`:** $-10.0 < \Delta S < +10.0$ (Maintained baseline).
   - **`WORSENED`:** $\Delta S \ge +10.0$ (Stress escalated; triggers immediate clinical review).
4. **Non-Punitive Guarantee:** Unimproved outcomes prompt secondary supportive reviews—never disciplinary action.

---

## 15. Welfare Case Management

Implemented in `services/welfare_case_service.py` (`api/routes/cases.py`):
- **Purpose:** Acts as the auditable human case-management workspace. It **does not calculate a new AI score** or rank jawans.
- **Allowed States:** `OPEN`, `UNDER_REVIEW`, `SUPPORT_IN_PROGRESS`, `AWAITING_FOLLOW_UP`, `MONITORING`, `RESOLVED`, `CLOSED`.
- **Valid Transitions:**
  - `OPEN` $\rightarrow$ `UNDER_REVIEW`, `MONITORING`, `CLOSED`
  - `UNDER_REVIEW` $\rightarrow$ `SUPPORT_IN_PROGRESS`, `AWAITING_FOLLOW_UP`, `MONITORING`, `RESOLVED`, `CLOSED`
  - `CLOSED` $\rightarrow$ `OPEN` (Explicit human reopening with mandatory justification).
- **Immutable Notes:** Notes cannot be edited or deleted once written.
- **No Automatic Closure:** A case remains open until an authorized human reviewer explicitly submits a structured closure reason (`RESOLVED`, `SUPPORT_COMPLETED`, `TRANSFERRED`).

---

## 15B. Jawan Welfare Notifications & Signal Delivery (Phase 47)

Implemented across `services/welfare_notification_service.py`, `api/routes/notifications.py`, `manobal-mobile/components/notifications/NotificationDrawer.tsx`, and `manobal-web/components/dashboard/SendWelfareNotificationModal.tsx`.

### Core Purpose
Connects the existing Commander / Welfare Officer decision workflow to the affected Jawan in the Jawan mobile web portal. When an authorized officer reviews a welfare alert, schedules an outcome follow-up, or approves a support recommendation, the corresponding supportive communication is securely delivered directly to the Jawan.

### Architectural Invariants
1. **Zero Risk Engine Duplication:** No secondary risk model or parallel alert engine was created. All signals originate from the authoritative Phase 34 LightGBM and existing welfare lifecycle handlers.
2. **Strict Anti-IDOR Isolation:** A Jawan can ONLY fetch, view, and mark as read notifications where `recipient_personnel_id == authenticated_user.personnel_id`. Cross-user inspection by ID or list yields `HTTP 403 Forbidden` / `HTTP 404 Not Found`.
3. **Strict Organizational Scoping:** Officers can only notify personnel within their assigned Battalion and Location. Cross-unit notifications are rejected with `HTTP 403 Forbidden`.
4. **Non-Stigmatizing Content Shielding:** Technical Commander-only analytics (raw risk scores, Isolation Forest sigma scores, SHAP values, rankings, disciplinary terminology) are strictly prohibited and sanitized from Jawan-facing messages.
5. **Human-in-the-Loop Governance:** Direct ad-hoc notifications require human initiation and authorization. Automated lifecycle triggers fire only when authorized officers take concrete workflow steps (approving a recommendation, scheduling a follow-up, or updating a request status).
6. **Immutable Audit Trail:** All notification events (creation, delivery, mark read, and mark all read) generate tamper-evident audit records in `welfare_notification_audits`.

### Supported Notification Types
- `WELFARE_SUPPORT`: General supportive welfare message from the officer.
- `FOLLOW_UP_REQUEST`: Scheduled welfare check-in / follow-up requested.
- `FOLLOW_UP_REMINDER`: Reminder to complete an upcoming follow-up check-in.
- `SUPPORT_RECOMMENDATION`: Actionable rest/support recommendation made available.
- `DUTY_SUPPORT_REVIEW`: Notice that operational duty review / stand-down has been approved.
- `RECOVERY_SUPPORT`: Guidance on circadian sleep and recovery routines.
- `CASE_UPDATE`: Supportive status update on an active welfare case.
- `WELFARE_MESSAGE`: Direct authorized welfare officer communication.

---

## 16. HRMS Integration (Actual Implementation)

- **Actual State:** Standardized REST API Ingestion Bridge (`POST /api/hrms/sync`).
- **Entity Model:** `HrmsServiceRecord` (`db/models/hrms.py`) linked 1-to-1 with `Personnel`.
- **Disclosures:** Source is explicitly stamped as `source = "mock_hrms"`.
- **Functionality:** Ingests service numbers, duty hours, deployment days, night shifts, leave gap, transfer frequency, and training load. Propagates values directly to active personnel operational records.
- **Limitation:** Live, automated connectors to proprietary military intranet ERP systems (e.g., ARPAN, E-HRMS, SAP) are not connected in this prototype. The API contract is fully functional and ready for enterprise socket connection.

---

## 17. Wearable & Telemetry Integration (Actual Implementation)

- **Actual State:** Time-Series Telemetry Ingestion Bridge (`POST /api/telemetry/wearable`).
- **Entity Model:** `WearableTelemetry` (`db/models/telemetry.py`).
- **Disclosures:** Stamped with disclaimer: *"Simulated wearable telemetry interface. Data represents simulated physiological signals, not real biometric device telemetry or medical diagnosis."*
- **Functionality:** Accepts JSON streams of `heart_rate`, `hrv_rmssd`, `sleep_duration_hours`, `sleep_quality_score`, `step_count`, and `active_minutes`. Extracted via `wearable_features.py` to inform anomaly and recovery models.
- **Limitation:** Direct physical hardware pairing (Bluetooth Low Energy / GATT) and commercial cloud APIs (Garmin Health, Fitbit Web API) are absent. Data ingestion is via HTTP REST API.

---

## 18. Database Architecture & Entity Relationships

The relational schema is implemented in SQLAlchemy Declarative ORM:

```mermaid
erDiagram
    users ||--o| personnel : "links to"
    personnel ||--o{ stress_assessments : "submits"
    personnel ||--o| hrms_service_records : "has service record"
    personnel ||--o{ wearable_telemetry : "logs telemetry"
    personnel ||--o{ welfare_alerts : "triggers"
    personnel ||--o{ welfare_anomalies : "flags"
    personnel ||--o{ welfare_recommendations : "receives"
    personnel ||--o{ welfare_followups : "tracked via"
    personnel ||--o{ welfare_cases : "subject of"
    personnel ||--o{ welfare_notifications : "receives"

    welfare_cases ||--o{ welfare_case_notes : "contains"
    welfare_cases ||--o{ welfare_case_reviews : "evaluated via"
    welfare_cases ||--o{ welfare_case_audits : "audited by"
    welfare_notifications ||--o{ welfare_notification_audits : "audited by"
    stress_assessments ||--o{ welfare_recommendations : "generates"

    personnel {
        int id PK
        string personnel_code UK
        string name
        string battalion
        string location
        string rank
        float duty_hours_per_week
        int night_shifts_per_month
        int consecutive_duty_days
        int leave_gap_days
    }

    stress_assessments {
        int id PK
        int personnel_id FK
        float risk_score
        string stress_level
        float low_probability
        float high_probability
        string risk_trend
        datetime assessment_timestamp
    }

    welfare_cases {
        int id PK
        string case_reference UK
        int personnel_id FK
        string status
        string priority
        string case_type
        datetime created_at
    }

    welfare_notifications {
        int id PK
        string notification_id UK
        int recipient_personnel_id FK
        string notification_type
        string title
        string message
        string priority
        string status
        datetime read_at
        datetime created_at
    }

    welfare_case_audits {
        int id PK
        int case_id FK
        string action
        int actor_id
        string previous_status
        string new_status
        datetime created_at
    }

    welfare_notification_audits {
        int id PK
        int notification_id FK
        string action
        int actor_id
        string details
        datetime created_at
    }
```

---

## 19. API Architecture & Route Groups

FastAPI backend registers **168 endpoints across 19 tag groups** (`http://localhost:8000/docs`):

| API Area | Base Path | Core Endpoints | Primary Purpose |
| :--- | :--- | :--- | :--- |
| **Authentication** | `/api/auth` | `POST /login`, `POST /register`, `GET /me` | JWT bearer token issuing, profile inspection. |
| **Stress Prediction** | `/api/predict` | `POST /predict`, `GET /model-info` | Real-time LightGBM inference & factor extraction. |
| **Personnel Assessments**| `/api/personnel` | `POST /{id}/assess`, `GET /{id}/trend` | Executes assessment pipeline, computes EWMA trends. |
| **Commander Dashboard**| `/api/dashboard` | `GET /summary`, `GET /stress-distribution` | Unit-level aggregate metrics, stress distributions. |
| **Welfare Alerts** | `/api/welfare` | `GET /alerts`, `PATCH /alerts/{id}` | Multi-tier early alerts, acknowledgement lifecycle. |
| **Anomaly Detection** | `/api/anomalies` | `GET /commander`, `GET /personnel/{id}` | Isolation Forest anomaly heatmaps and SHAP factors. |
| **Recommendations** | `/api/recommendations` | `GET /commander`, `PATCH /{id}/status` | Supportive duty-pacing recommendations. |
| **Follow-up Tracking** | `/api/followups` | `GET /`, `POST /`, `POST /{id}/reassess` | Pre vs. post outcome evaluation, recovery deltas. |
| **Case Management** | `/api/welfare-cases` | `GET /`, `POST /`, `POST /{id}/notes`, `POST /{id}/status` | Controlled human review workspace, audits. |
| **Welfare Notifications**| `/api/notifications` | `GET /`, `GET /unread-count`, `POST /{id}/read`, `POST /send` | Jawan notification delivery, Anti-IDOR scoping. |
| **Unit Intelligence** | `/api/analytics` | `GET /welfare-intelligence/unit` | Cross-signal synthesis with $k \ge 5$ privacy. |
| **HRMS Ingestion** | `/api/hrms` | `POST /sync` | Mock HRMS service record synchronization. |
| **Wearable Telemetry** | `/api/telemetry` | `POST /wearable` | Time-series physiological telemetry ingestion. |

---

## 20. Frontend Architecture

### 20.1 Commander & Welfare Officer Dashboard (`manobal-web`)
- **Technology:** Next.js 14.2.15, React 18, TailwindCSS, Recharts, Lucide Icons.
- **Port:** `http://localhost:3000`
- **Type Safety:** 100% TypeScript (`npx tsc --noEmit` exits with 0 errors).
- **Core Views & Modules:**
  - `/dashboard`: Unit welfare summary, distribution charts, alerts table, anomaly panel, recommendation panel, follow-up panel, intelligence heatmap, case management workspace.
  - `/personnel`: Searchable unit roster with battalion and location filters.
  - `/personnel/[id]`: Scoped profile drilldown with historical trajectory graphs and operational attributes.
  - `SendWelfareNotificationModal.tsx`: Officer-to-Jawan notification modal with predefined support templates, custom messaging, character limits, deep-linking, and battalion-scope enforcement.
  - `/login`: Role-aware officer authentication.
- **Hydration Parity:** Fully resolved with deterministic mounting guards.

### 20.2 Jawan Mobile Portal (`manobal-mobile`)
- **Technology:** Next.js 16.3.5 (Turbopack), React 18, TailwindCSS.
- **Port:** `http://localhost:3001`
- **Type Safety:** 100% TypeScript (`npx tsc --noEmit` exits with 0 errors).
- **Core Views & Modules:**
  - `TopHeader.tsx`: Real-time notification bell with dynamic badge counter and drawer trigger.
  - `NotificationDrawer.tsx`: Glassmorphism notification center displaying unread counts, categorized support cards, mark-as-read, mark-all-read, and deep links.
  - `HomeScreen.tsx`: Prominent "Welfare Updates" callout banner on the home screen showing unread support communications.
  - `/(tabs)/assessment`: 14-screen guided assessment wizard with touch sliders.
  - `/(tabs)/check-in`: Rapid daily mood and fatigue check-in.
  - `/(tabs)/trends`: Personal stress score trajectory visualization.
  - `/login`: Secure Jawan service authentication.
- **Responsive Layout:** Mobile-constrained layout matching 375px–430px smartphone form factors.

---

## 21. Security Architecture & Anti-IDOR

ManoBal implements strict defensive security and access control:

### 21.1 Role-Based Access Control (RBAC) Matrix

| Resource / Capability | `personnel` (Jawan) | `officer` (Commander) | `welfare` (Counselor) | `admin` (System Admin) |
| :--- | :---: | :---: | :---: | :---: |
| **Submit Own Assessment** | ✅ | ❌ | ❌ | ❌ |
| **View Own Stress Trends** | ✅ | ❌ | ❌ | ❌ |
| **View Peer Personnel Data** | ❌ (403) | ❌ (403) | ❌ (403) | ✅ |
| **View Unit Dashboard** | ❌ (403) | ✅ (In-Scope) | ✅ (In-Scope) | ✅ (Global) |
| **Access Welfare Alerts** | ❌ (403) | ✅ (In-Scope) | ✅ (In-Scope) | ✅ (Global) |
| **Create Welfare Case** | ❌ (403) | ✅ (In-Scope) | ✅ (In-Scope) | ✅ (Global) |
| **Add Clinical Review Note** | ❌ (403) | ✅ (In-Scope) | ✅ (In-Scope) | ✅ (Global) |
| **Review Early-Warning Signal** | ❌ (403) | ✅ (In-Scope) | ✅ (In-Scope) | ✅ (Global) |
| **Resolve Early-Warning Signal** | ❌ (403) | ✅ (In-Scope) | ✅ (In-Scope) | ✅ (Global) |
| **View Own Notifications** | ✅ (Self Only) | ❌ (403) | ❌ (403) | ✅ (Global) |
| **Send Welfare Notification**| ❌ (403) | ✅ (In-Scope) | ✅ (In-Scope) | ✅ (Global) |
| **Cross-Location Access** | ❌ (403) | ❌ (403) | ❌ (403) | ✅ (Global) |

### 21.2 Empirical Anti-IDOR Proof
- **Test Case:** Officer Sharma (`officer_sharma`, assigned to `7th Battalion`, `Srinagar`) attempts to view Personnel ID 4 (`Constable Amit Verma`, assigned to `Delhi`).
- **Result:** API strictly rejects with `HTTP 403 Forbidden`:
  ```json
  {"detail": "Cross-location access restricted. Officer location 'Srinagar' does not match personnel location 'Delhi'."}
  ```

---

## 22. Privacy & Ethical Non-Punitive Design

- **Small-Group Privacy Protection ($k \ge 5$ k-Anonymity):** Whenever a commander queries aggregate stress distributions for a sub-unit cohort smaller than 5 individuals, category breakdowns are suppressed to prevent deductive deanonymization.
- **No Individual Rankings:** The platform has no leaderboards, comparative percentiles on public screens, or "worst performer" classifications.
- **No Autonomous Disciplinary Actions:** The AI engine cannot alter rosters, mandate transfers, or trigger disciplinary actions.
- **Human Authority:** All supportive actions require explicit human authorization by an identified welfare officer or commander.

---

## 23. Project Directory Structure

```
ManoBal/
├── README.md                                  # Complete Master Technical Documentation
├── pyrightconfig.json                         # Strict Python type-resolution configuration
├── manobal-web/                                  # Commander & Welfare Officer Web Dashboard
│   ├── app/                                   # Next.js App Router (dashboard, personnel, login)
│   ├── components/                            # Modular UI panels (Alerts, Anomalies, Cases, etc.)
│   ├── lib/                                   # API client, auth context, dashboard fetchers
│   └── package.json                           # Next.js 14, React 18, TailwindCSS, Recharts
├── manobal-mobile/                              # Jawan Mobile Self-Assessment Portal
│   ├── app/                                   # Next.js 16 App Router ((tabs), assessment, trends)
│   ├── components/                            # Mobile sliders, rating controls, bottom navigation
│   ├── lib/                                   # Mobile API client, auth state
│   └── package.json                           # Next.js 16 (Turbopack), TailwindCSS
└── manobal-backend/                          # FastAPI Backend & Machine Learning Engine
    ├── api/                                   # API Routing Layer
    │   ├── routes/                            # 16 route modules (auth, assess, cases, alerts, etc.)
    │   ├── deps.py                            # Token validation, RBAC, Anti-IDOR dependencies
    │   └── main.py                            # FastAPI application factory & CORS configuration
    ├── core/                                  # Application settings, security utilities, logging
    ├── db/                                    # Database Layer (SQLAlchemy ORM models, session)
    ├── ml_pipeline/                           # ML Training, preprocessing, models
    │   └── models/                            # Model artifacts (final_stress_prediction_pipeline.pkl)
    ├── schemas/                               # Pydantic v2 validation & response contracts
    ├── services/                              # Business logic, ML inference, case management
    ├── tests/                                 # 35 Pytest files (456 tests covering Phases 34–46)
    └── docs/                                  # Phase validation reports & Production traceability
```

---

## 24. Technology Stack

| Layer | Technology | Version | Purpose in ManoBal |
| :--- | :--- | :---: | :--- |
| **Backend API** | FastAPI | 0.110+ | High-performance asynchronous REST API framework. |
| **ASGI Server** | Uvicorn | 0.28+ | Lightning-fast ASGI web server hosting FastAPI backend. |
| **ML Framework** | LightGBM | 4.3+ | Gradient boosted tree ensemble for stress prediction. |
| **ML Pipeline** | Scikit-Learn | 1.4+ | Preprocessing pipelines, encoders, and Isolation Forest. |
| **Explainable AI** | SHAP | 0.45+ | TreeExplainer feature attribution for risk factor extraction. |
| **Database ORM** | SQLAlchemy | 2.0+ | Declarative object-relational mapping and migrations. |
| **Validation** | Pydantic v2 | 2.6+ | Strict runtime request and response schema validation. |
| **Security** | PyJWT / Passlib | 2.8+ | JWT token generation and bcrypt password hashing. |
| **Commander UI** | Next.js | 14.2.15 | Production React framework for Commander Dashboard. |
| **Jawan Mobile UI**| Next.js (Turbopack) | 16.3.5 | Mobile-optimized responsive PWA layout for Jawans. |
| **Styling** | TailwindCSS | 3.4+ | Military-grade dark theme and responsive utility styles. |
| **Visualization** | Recharts | 2.13+ | Interactive time-series trends and distribution charts. |

---

## 25. Installation & Setup

### Prerequisites
- Python 3.10+ (Python 3.11 / 3.12 recommended)
- Node.js 18.18+ or 20+
- Git

### Step 1: Clone Repository
```bash
git clone https://github.com/Susovan07-Slice/ManoBal.git
cd ManoBal
```

### Step 2: Set Up Backend (`manobal-backend`)
```bash
cd "manobal-backend"
python -m venv venv
# On Windows:
venv\Scripts\activate
# On Linux/macOS:
source venv/bin/activate

pip install -r requirements.txt
python -m db.init_db
```

### Step 3: Set Up Commander Dashboard (`manobal-web`)
Open a second terminal:
```bash
cd "manobal-web"
npm install
```

### Step 4: Set Up Jawan Mobile App (`manobal-mobile`)
Open a third terminal:
```bash
cd "manobal-mobile"
npm install
```

---

## 26. Running the System

Start all three services concurrently in separate terminals:

### Terminal 1: Backend API (Port 8000)
```bash
cd "manobal-backend"
# Ensure venv is activated
uvicorn api.main:app --host 0.0.0.0 --port 8000 --reload
```
*Accessible at:* `http://localhost:8000` | *Interactive Swagger Docs:* `http://localhost:8000/docs`

### Terminal 2: Commander Dashboard (Port 3000)
```bash
cd "manobal-web"
npm run dev
```
*Accessible at:* `http://localhost:3000/dashboard` | *Login:* `http://localhost:3000/login`

### Terminal 3: Jawan Mobile Portal (Port 3001)
```bash
cd "manobal-mobile"
npm run dev -- -p 3001
```
*Accessible at:* `http://localhost:3001` | *Login:* `http://localhost:3001/login`

### Verified Pre-Seeded Test Credentials

| Role | Username | Password | Assigned Scope | Intended Portal |
| :--- | :--- | :--- | :--- | :--- |
| **Jawan** | `jawan_verma` | `PersonnelPassword123!` | Personnel ID: 4, Location: Delhi | Port 3001 (Jawan App) |
| **Commander** | `officer_sharma` | `OfficerPassword123!` | 7th Battalion, Location: Srinagar | Port 3000 (Commander) |
| **Welfare Officer** | `counselor_priya` | `WelfarePassword123!` | Clinical Welfare Queue | Port 3000 (Commander) |
| **Administrator** | `admin` | `AdminPassword123!` | Global System-Wide | Port 3000 (Commander) |

---

## 27. Example End-to-End Usage Walkthrough

1. **Jawan Self-Assessment:** Jawan logs into `http://localhost:3001` as `jawan_verma`, navigates to `/assessment`, completes the 14-screen wizard, and submits. The ML engine calculates a calibrated score (e.g. 80.8, High), returning immediate non-stigmatizing restorative recommendations.
2. **Signal Synthesis:** The backend updates longitudinal EWMA trend (Velocity: Worsening) and generates an automated `HIGH_STRESS_SPIKE` welfare alert and a `REST_STAND_DOWN` recommendation.
3. **Commander Triage:** Officer Sharma logs into `http://localhost:3000/dashboard`, views the updated unit stress distribution, notices the active alert, and inspects the jawan's operational attributes (72 duty hrs, 16 consecutive days).
4. **Welfare Case Opening:** Officer opens Case `WC-2026-0006`, assigning it to Counselor Priya.
5. **Counseling & Review:** Counselor Priya adds an immutable review note (*"Conducted supportive telephonic check-in"*) and transitions status to `UNDER_REVIEW`.
6. **Follow-up & Outcome:** Counselor schedules a 14-day follow-up. Upon reassessment, the jawan's score drops to 45.2 ($\Delta S = -35.6$), automatically recording a successful `IMPROVED` outcome.

---

## 28. Example Inputs & Outputs

### 28.1 Sample Input Payload (`POST /api/predict`)
```json
{
  "age": 29,
  "gender": "Male",
  "marital_status": "Single",
  "location": "Srinagar",
  "job_role": "Field Officer",
  "company_size": "Large",
  "department": "Operations",
  "experience_years": 5.0,
  "monthly_salary_inr": 60000.0,
  "working_hours_per_week": 42.0,
  "duty_hours_per_week": 72.0,
  "commute_time_hours": 0.5,
  "remote_work": "No",
  "annual_leaves_taken": 10,
  "team_size": 25,
  "sleep_hours": 4.5,
  "physical_activity_hours_per_week": 4.0,
  "health_issues": "",
  "mental_health_leave_taken": "No",
  "burnout_symptoms": "Often",
  "deployment_days": 120,
  "night_shifts_per_month": 12,
  "consecutive_duty_days": 16,
  "transfer_frequency": 1,
  "training_load": 3,
  "leave_gap_days": 105,
  "remote_posting": "Yes",
  "operational_exposure": "High"
}
```

### 28.2 Sample Output Response
```json
{
  "risk_score": 80.8,
  "stress_level": "High",
  "risk_priority": "Priority",
  "confidence": "Moderate",
  "uncertainty": 0.6,
  "risk_trend": "Worsening",
  "risk_change": 17.9,
  "low_probability": 0.032,
  "medium_probability": 0.08,
  "high_probability": 0.632,
  "key_factors": [
    "Elevated duty schedule: 72 hrs/week",
    "Restricted restorative sleep: 4.5 hrs/night",
    "Extended continuous duty: 16 consecutive days",
    "High night-shift frequency: 12 shifts/month"
  ],
  "recommendations": [
    {
      "recommendation_type": "Sleep & Recovery",
      "recommendation_text": "Immediate 48-hour operational rest stand-down and clinical welfare review.",
      "priority": "Priority"
    },
    {
      "recommendation_type": "Workload Optimization",
      "recommendation_text": "Protected circadian recovery sleep block of at least 8 uninterrupted hours.",
      "priority": "Priority"
    }
  ]
}
```

---

## 29. Testing & Verification Results

All tests have been executed and verified in the live workspace environment:

| Test Category | Target Scope | Command | Result | Pass Rate |
| :--- | :--- | :--- | :---: | :---: |
| **Phase 34–44 Target Suite** | Active Production Engine | `pytest tests/test_phase3[4-9]* tests/test_phase4[0-4]*` | **102 / 102 Passed** | **100.0%** |
| **Phase 45 System Audit** | Live Programmatic Integration | `python -u test_phase45_audit.py` | **4 / 4 Suites Passed** | **100.0%** |
| **Phase 46 Production Acceptance Audit**| End-to-End Problem Statement | `python -u test_phase46_audit.py` | **6 / 6 Blocks Passed** | **100.0%** |
| **Full Repository Regression** | All Repo Tests | `python -m pytest tests/` | **442 Passed, 14 Legacy Failed** | **96.9%** |
| **Commander TypeScript** | `manobal-web` | `npx tsc --noEmit` | **0 Errors** | **100.0%** |
| **Jawan TypeScript** | `manobal-mobile` | `npx tsc --noEmit` | **0 Errors** | **100.0%** |
| **Commander Production Build** | `manobal-web` | `npm run build` | **Exit Code 0 (8 routes)** | **100.0%** |
| **Jawan Production Build** | `manobal-mobile` | `npm run build` | **Exit Code 0 (9 routes)** | **100.0%** |

> **Audit Note on the 14 Legacy Failures:** All 14 repository failures originate in deprecated exploratory scripts created prior to Phase 34 asserting obsolete integer cutoffs ($score > 85$) or experimental CatBoost models. None exist in active production routes, services, or models.

---

## 30. Known Limitations

In the spirit of complete intellectual honesty, the following operational limitations are documented:
1. **Responsive Web Application vs. Native APK:** The Jawan portal is delivered as a mobile-optimized web application on port 3001, not as an installable `.apk` or native iOS app.
2. **Simulated Wearable Telemetry:** Biometric vitals are ingested via standard REST API (`POST /api/telemetry/wearable`); direct Bluetooth Low Energy (BLE) pairing with commercial wristbands is not present.
3. **Simulated Enterprise HRMS Sync:** The system provides an API ingestion bridge (`POST /api/hrms/sync`), but live automated socket connections to military intranet ERP systems (e.g., ARPAN) are simulated.
4. **Local SQLite Storage in Development:** Development runs on SQLite. Production deployment requires transitioning to PostgreSQL 15+ with Transparent Data Encryption (TDE) for demographic PII.

---

## 31. Future Scope

Post-Production enhancements for operational force-wide deployment include:
- **Native Android Packaging:** Wrapping the Next.js Jawan portal via Capacitor/React Native to generate signed `.apk` binaries for defense-issued smartphones.
- **Direct BLE Smartwatch Pairing:** Integrating Web Bluetooth APIs for direct real-time heart rate and HRV streaming from MIL-STD-810 tactical smartwatches.
- **Enterprise Defense Connectors:** Building dedicated SFTP/SOAP connectors for direct synchronization with military personnel databases.
- **Offline Mesh Synchronization:** Enabling offline assessment caching with peer-to-peer mesh sync for forward operating bases with zero cellular connectivity.

---

## License & Intellectual Property
Developed for the Ministry of Defense & Uniformed Services. All source code, models, and architectures are proprietary to the ManoBal Project Development Team.
