# Phase 37 — Welfare Alert & Intervention Architecture

## 1. System Architecture & Authoritative Pipeline Hierarchy

The ManoBal Welfare Alert & Intervention Subsystem operates strictly as a downstream consumer of the validated machine learning pipeline. It does **not** compute independent risk scores, invent alternative thresholds, or modify outputs from earlier phases.

```
┌────────────────────────────────────────────────────────┐
│ Phase 34: Welfare Risk Engine V2 (Authoritative ML)   │
│ - Continuous Calibrated Risk Score (0.0 – 100.0)       │
│ - Categorical Mapping: Low, Moderate, Elevated, High,  │
│   Critical                                             │
│ - Evidence & Protective Factor Attribution             │
└───────────────────────────┬────────────────────────────┘
                            │ (risk_score, risk_category, factors)
                            ▼
┌────────────────────────────────────────────────────────┐
│ Phase 36: Longitudinal Welfare Analytics Engine       │
│ - Trend Direction & Velocity (Slope)                   │
│ - Trajectory Persistence (Consecutive Elevated >= 3)   │
│ - Risk Acceleration (Recent vs. Historical Epochs)     │
│ - Repeated Risk & Protective Factors (Frequency >= 2)  │
│ - Personal Baseline Stability & Deviations             │
└───────────────────────────┬────────────────────────────┘
                            │ (trend, history, acceleration, repeated factors)
                            ▼
┌────────────────────────────────────────────────────────┐
│ Phase 37: Welfare Alert & Intervention Management      │
│ - Multi-signal Event Generation                        │
│ - Idempotent Deduplication (Unresolved state matching) │
│ - Finite State Machine (Open -> Acknowledged -> ...)   │
│ - Non-punitive Supportive Intervention Workflow        │
│ - Tamper-evident Audit Logging & RBAC Scope Isolation  │
└────────────────────────────────────────────────────────┘
```

---

## 2. Alert Trigger Specifications

Phase 37 defines five distinct, non-punitive welfare review signals. Each signal derives strictly from upstream authoritative calculations:

| Alert Type | Authoritative Source | Exact Trigger Condition | Default Severity | Deduplication Rule |
| :--- | :--- | :--- | :--- | :--- |
| **`HIGH_CURRENT_RISK`** | Phase 34 V2 Engine | `risk_category == 'Critical'` or `risk_category == 'High'` | `URGENT_REVIEW` (Critical) / `HIGH_PRIORITY` (High) | Suppressed if active alert of same type exists for personnel |
| **`PERSISTENT_ELEVATED_RISK`** | Phase 36 Analytics | `trend_data['history']['persistent_elevated_risk'] == True` (>= 3 consecutive elevated records >= 55.0) | `HIGH_PRIORITY` | Suppressed if active alert of same type exists for personnel |
| **`WORSENING_TREND`** | Phase 36 Analytics | `trend_data['trend']['direction'] == 'WORSENING'` (Meaningful positive slope/delta) | `ATTENTION` | Suppressed if active alert of same type exists for personnel |
| **`RAPID_RISK_INCREASE`** | Phase 36 Analytics | `trend_data['trend']['acceleration'] == 'INCREASING'` (Slope acceleration delta > 3.0) | `ATTENTION` | Suppressed if active alert of same type exists for personnel |
| **`REPEATED_WELFARE_FACTOR`** | Phase 36 Analytics | `repeated_factors` with `type == 'risk'` and `frequency >= 2` | `INFO` | Top recurring factor flagged; suppressed if active alert of same type exists |

---

## 3. Alert Deduplication Engine

To eliminate commander alert fatigue while guaranteeing critical welfare visibility, deduplication adheres to five certified scenarios:

1. **Scenario A (Single Assessment):** An assessment triggering a condition generates exactly one alert.
2. **Scenario B (Repeated Execution):** Re-evaluating the same assessment generates 0 duplicate alerts.
3. **Scenario C (Persistent Condition):** Subsequent assessments reflecting an ongoing condition keep the existing open/active alert intact without creating duplicates.
4. **Scenario D (Re-emergent Condition):** Once an earlier alert reaches a terminal status (`RESOLVED` or `DISMISSED`), a subsequent assessment meeting the trigger condition creates a new, independent alert.
5. **Scenario E (Multi-signal Differentiation):** Assessments exhibiting multiple simultaneous conditions (e.g., `HIGH_CURRENT_RISK` and `PERSISTENT_ELEVATED_RISK`) generate distinct alert instances corresponding to each condition, with zero cross-type collision.

---

## 4. Finite State Machine & Lifecycle Validation

Welfare alerts transition strictly through an authorized, forward-only finite state machine:

```
[ OPEN ]
   │
   ▼
[ ACKNOWLEDGED ]
   │
   ▼
[ UNDER_REVIEW ]
   │
   ▼
[ INTERVENTION_PLANNED ]
   │
   ▼
[ FOLLOW_UP ]
   │
   ▼
[ RESOLVED / DISMISSED ] (Terminal States)
```

### Invalid Transitions (Strictly Rejected with HTTP 400):
- Cannot acknowledge an alert that is not `OPEN`.
- Cannot begin review on an alert that is already `UNDER_REVIEW`, `RESOLVED`, or `DISMISSED`.
- Cannot create interventions or schedule follow-ups on `RESOLVED` or `DISMISSED` alerts.
- Cannot resolve or dismiss an alert that has already reached a terminal state.
- Interventions cannot be cancelled or completed once already marked `COMPLETED` or `CANCELLED`.

---

## 5. Security & Organizational Scope (RBAC / IDOR Protection)

All alert endpoints enforce strict organizational boundaries:
- **`Admin`:** Retains system-wide visibility across all battalions and locations.
- **`Officer` & `Welfare`:** Strict organizational scoping. Queries automatically filter personnel by matching `battalion` and `location`. Direct alert access or manipulation across out-of-scope units is rejected with `HTTP 403 Forbidden`.
- **`Personnel` (Jawan):** Strictly prohibited from accessing commander welfare alert review feeds (`HTTP 403 Forbidden`). Jawans interact solely with their own daily check-ins, assessments, and SOS requests.

---

## 6. Non-Punitive Supportive Language Policy

In alignment with military psychological health best practices, Phase 37 strictly prohibits punitive or disciplinary terminology:
- **Prohibited:** *unfit, dangerous, disciplinary risk, offender, violator, punishment, unreliable person.*
- **Enforced:** *welfare review signal, restorative leave, workload optimization, supportive check-in, peer support stand-down, elevated welfare concern.*
