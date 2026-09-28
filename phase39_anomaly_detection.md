# Phase 39 — Early-Warning & Welfare Anomaly Detection

## 1. Overview & Purpose
Phase 39 introduces an **Early-Warning & Welfare Anomaly Detection layer** for the ManoBal / PS 26186 platform. Its operational mission is to answer:

> *"Is something changing unusually or unexpectedly across an individual's personal baseline or within a command unit that deserves human welfare attention?"*

### Critical Architectural Rule
**Phase 39 is an early-warning/anomaly detection layer and does not replace or modify the authoritative Phase 34 Welfare Risk Engine V2.**

The system remains structured as a strict downstream pipeline:
```
Phase 34: Authoritative Welfare Risk Engine V2
   Continuous 0-100 scoring & 5-tier classification [Low, Moderate, Elevated, High, Critical]
                 ↓
Phase 36: Longitudinal Monitoring
   Temporal trajectory, baseline deviation, velocity & acceleration
                 ↓
Phase 37: Welfare Alerts & Interventions
   Alert lifecycle, human review workflows, supportive interventions
                 ↓
Phase 38: Commander Analytics
   Organizational aggregations, unit distribution, k-anonymity privacy
                 ↓
Phase 39: Early-Warning & Welfare Anomaly Detection
   Baseline-first departure detection, co-occurring factor clusters, human-in-the-loop signals
```

Phase 39 strictly does **NOT**:
- Modify Phase 34 risk scoring or scoring coefficients.
- Modify Phase 34 risk-category boundaries.
- Create a secondary welfare risk score.
- Automatically diagnose any clinical or psychiatric conditions.
- Automatically trigger disciplinary action or rank personnel.
- Override human welfare officer review.

---

## 2. Anomaly Categories & Detection Logic

| Anomaly Type | Target Scope | Baseline & Trigger Criteria | Severity | Confidence |
|---|---|---|---|---|
| **`RAPID_RISK_CHANGE`** | Individual | Current assessment jumps $\ge 20.0$ points above preceding check-in, or $\ge 2.5\times\sigma$ from personal historical mean. | `ATTENTION` / `URGENT_REVIEW` (if score $\ge 70$) | `HIGH` (if $N \ge 5$) / `MEDIUM` |
| **`RAPID_RISK_ACCELERATION`** | Individual | Phase 36 longitudinal acceleration is `ACCELERATING`, slope $\ge 0.4$ pts/day, and score change $\ge 8.0$ points. | `ATTENTION` | `HIGH` / `MEDIUM` |
| **`WORKLOAD_ANOMALY`** | Individual | Operational duty schedule $\ge 65.0$ hrs/week, representing an acute surge ($+15$ hrs above standard baseline). | `ATTENTION` | `HIGH` |
| **`SLEEP_RECOVERY_ANOMALY`** | Individual | Recent sleep duration is $\ge 2.0$ hrs below historical personal mean, or consecutive duty days $\ge 14$ without respite. | `ATTENTION` | `HIGH` / `MEDIUM` |
| **`NIGHT_SHIFT_PATTERN_CHANGE`** | Individual | Night shift roster allocation $\ge 8$ shifts/month (an increase of $\ge 4$ shifts above baseline). | `WATCH` | `HIGH` |
| **`WELFARE_FACTOR_CLUSTER`** | Individual | $\ge 3$ strain factors co-occurring simultaneously (workload $\ge 55$h + sleep deficit + night shifts/leave gap + worsening trend). | `URGENT_REVIEW` / `ATTENTION` | `HIGH` |
| **`UNIT_LEVEL_ANOMALY`** | Unit | Proportion of High/Critical personnel in unit surges by $\ge 15.0\%$ relative to prior reporting baseline period. | `ATTENTION` / `URGENT_REVIEW` | `HIGH` |

---

## 3. Baseline-First Design & Sufficiency Requirements

Anomaly detection is fundamentally **personalized**, comparing an individual soldier against their own established history rather than an arbitrary global cutoff:
- `MIN_PERSONAL_ASSESSMENTS_FOR_ANOMALY = 3`: If a personnel member has fewer than 3 historical assessments, the system returns `status: "INSUFFICIENT_BASELINE"`. It strictly refuses to invent speculative baselines or generate false-positive alarms.
- `MIN_UNIT_PERIODS_FOR_ANOMALY = 2`: Unit-level baseline comparison requires at least 5 baseline assessments and 3 recent assessments.
- `ANALYTICS_MIN_GROUP_SIZE = 5`: Privacy preservation ($k$-anonymity) for unit-level commander aggregations.

### Anomaly States
- `DETECTED`: One or more genuine baseline departures flagged for review.
- `NO_ANOMALY`: Metrics adhere to expected historical variation.
- `INSUFFICIENT_BASELINE`: Personnel history is too short to establish a reliable baseline.
- `INSUFFICIENT_DATA`: Zero records exist in the database.
- `INSUFFICIENT_GROUP_SIZE`: Unit population is below the privacy threshold ($< 5$).

---

## 4. Anomaly Severity & Confidence Semantics
Anomaly severity is used **strictly for prioritizing human review**, not as a medical or disciplinary label:
- `INFO`: Early subtle variation noted for tracking.
- `WATCH`: Moderate departure from baseline; monitor next check-in.
- `ATTENTION`: Significant departure or co-occurring operational factors; supportive check-in recommended.
- `URGENT_REVIEW`: Severe sudden shift or multi-factor cluster in elevated risk; prioritized officer review required.

---

## 5. Storage, Deduplication & Human Review Lifecycle

### Dedicated Persistence: `WelfareAnomaly`
Location: `db/models/anomaly.py`
Key fields:
- `personnel_id`: Nullable for unit-level anomalies.
- `scope_type`: `INDIVIDUAL` or `UNIT`.
- `anomaly_type`, `severity`, `status`, `confidence`.
- `evidence_json`: Structured explainable details (reason, baseline mean, baseline std, current value, delta, explanation).
- `dedup_hash`: Deterministic hash of `scope_type:personnel_id:scope_battalion:scope_location:anomaly_type:date`.

### Deduplication Guarantee
Evaluating unchanged data multiple times executes an idempotent `UPDATE` of evidence and timestamps rather than inserting duplicate records.

### Human Review Workflow
```
DETECTED
   ↓ (Officer / Welfare acknowledges)
ACKNOWLEDGED
   ↓ (Officer opens formal investigation or check-in)
UNDER_REVIEW
   ↓ (Officer documents supportive action & respite)
RESOLVED
```

---

## 6. Security, RBAC & Anti-IDOR Protection
- **Officer & Welfare Roles**: Scoped strictly to `current_user.battalion` and `current_user.location`. Query parameters attempting to override scope (`?battalion=other`) are rejected with `HTTP 403 Forbidden`.
- **Personnel Role (Jawan)**: Can access their own personal anomalies (`/api/anomalies/personnel/{id}` where `id == current_user.personnel_id`). Accessing other records or commander endpoints returns `HTTP 403 Forbidden`.
- **Small-Group Privacy ($k$-Anonymity)**: Units with $< 5$ personnel return `INSUFFICIENT_GROUP_SIZE`. Individual anomaly counts and evidence are withheld.

---

## 7. API Endpoints
- `GET /api/anomalies/personnel/{personnel_id}` — Get individual early-warning anomaly history.
- `GET /api/anomalies/commander` — Get unit-level early-warning intelligence summary.
- `POST /api/anomalies/{anomaly_id}/acknowledge` — Acknowledge signal.
- `POST /api/anomalies/{anomaly_id}/review` — Mark signal under active review.
- `POST /api/anomalies/{anomaly_id}/resolve` — Resolve signal with mandatory resolution notes.
