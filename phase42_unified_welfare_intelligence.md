# PHASE 42: UNIFIED WELFARE INTELLIGENCE & DECISION-SUPPORT LAYER

## 1. Executive Summary & Objective

Phase 42 establishes the **Unified Welfare Intelligence & Decision-Support Layer** for ManoBal / PS 26186. Operating directly above the foundational intelligence systems validated across Phases 34–41, Phase 42 aggregates, synthesizes, and visualizes longitudinal telemetry, risk classifications, early-warning signals, support workflows, and outcome observations into a single, coherent, privacy-preserving interface for authorized commanders and welfare officers.

Phase 42 answers the core command question:
> *"What is happening with welfare across the unit, what signals are changing, what support is currently active, and where should a human reviewer look more closely?"*

---

## 2. Fundamental Architectural Guardrails & Guarantees

Phase 42 is strictly designed as an **intelligence aggregation and human decision-support layer**, NOT a new risk engine, prediction engine, or scoring algorithm.

1. **NO Composite or Hidden Numerical Scores**:
   - Strictly prohibits `unified_risk_score`, `overall_welfare_score`, `commander_score`, or any combination of Phase 34 risk with Phase 39 anomaly severity or Phase 40 recommendation priority into a synthetic index.
   - Each authoritative signal retains its independent mathematical and operational meaning.

2. **NO Personnel Ranking or Sorting by Severity**:
   - Zero "Top 10 highest risk personnel", "Worst personnel", or "Most problematic" lists.
   - Personnel rosters are strictly unranked (ordered deterministically by personnel identifier/code), ensuring non-punitive welfare monitoring.

3. **NO Automated Decision-Making or Personnel Actions**:
   - Phase 42 NEVER alters duty rosters, reassigns personnel, initiates disciplinary actions, enforces medical treatments, or automatically accepts/closes alerts or recommendations.
   - All outcomes, recommendations, and anomaly notifications remain assistive decision-support tools for authorized human review.

4. **Clear Semantic Independence**:
   - **Phase 34 Risk Category**: Authoritative baseline calibrated stress risk (`Low`, `Medium`, `High`).
   - **Phase 36 Trend Direction**: Longitudinal trajectory over time (`Improving`, `Stable`, `Worsening`, `Insufficient Data`).
   - **Phase 37 Alert Status**: Operational alert lifecycle (`OPEN`, `ACKNOWLEDGED`, `UNDER_REVIEW`, `INTERVENTION_PLANNED`, `CLOSED`).
   - **Phase 39 Anomaly Severity**: Statistical anomaly outlier flag (`ATTENTION`, `ELEVATED`, `URGENT_REVIEW`).
   - **Phase 40 Recommendation Priority**: Suggested intervention urgency (`ROUTINE`, `MEDIUM`, `HIGH`, `URGENT`).
   - **Phase 41 Outcome Observation**: Empirical post-intervention observation (`IMPROVED`, `STABLE`, `PERSISTENT_CONCERN`, `WORSENING`, `INSUFFICIENT_DATA`).
   - **Data Sufficiency vs Low Risk**: Insufficient data is explicitly distinguished from low risk; missing assessments never default to low risk.

---

## 3. End-to-End System Architecture

```text
                 ┌─────────────────────────────────┐
                 │ Phase 34: Authoritative Risk    │
                 └────────────────┬────────────────┘
                                  │
                 ┌────────────────▼────────────────┐
                 │ Phase 36: Longitudinal Trends   │
                 └────────────────┬────────────────┘
                                  │
          ┌───────────────────────┼───────────────────────┐
          ▼                       ▼                       ▼
     Phase 37: Alerts        Phase 39: Anomalies    Phase 40: Recommendations
          │                       │                       │
          └───────────────────────┼───────────────────────┘
                                  ▼
                         Human Decision
                                  │
                                  ▼
                      Phase 37: Intervention
                                  │
                                  ▼
                       Phase 41: Follow-up
                                  │
                                  ▼
                         Outcome Observation
                                  │
                                  ▼
                 ┌─────────────────────────────────┐
                 │           PHASE 42              │
                 │   Unified Welfare Intelligence  │
                 │     & Decision-Support Layer    │
                 └────────────────┬────────────────┘
                                  │
                                  ▼
                       Authorized Human Review
                     (Commanders / Welfare Officers)
```

---

## 4. Authoritative Data Sources

| Phase | System / Component | Authoritative Role | Schema / Entity Consumed |
|---|---|---|---|
| **Phase 34** | Authoritative Risk Engine V2 | Sole authority for risk score and stress classification | `StressAssessment` (risk_score, stress_level, risk_priority, key_factors) |
| **Phase 36** | Longitudinal Trend Intelligence | Directional trajectory, baseline mean, slope, persistence | `LongitudinalAnalyticsService` (direction, slope, persistence, baseline) |
| **Phase 37** | Welfare Alerts & Interventions | Operational alert lifecycle & intervention planning | `WelfareAlert`, `WelfareIntervention` |
| **Phase 38** | Commander Analytics | Organizational boundaries & small-group k-anonymity privacy | `ANALYTICS_MIN_GROUP_SIZE = 5` |
| **Phase 39** | Early Warning / Anomaly Detection | Statistical anomaly flags & severity | `WelfareAnomaly` (anomaly_type, severity, evidence_json) |
| **Phase 40** | Support Recommendations | Non-binding guidance suggestions & review windows | `WelfareRecommendation` (recommendation_type, priority, reason) |
| **Phase 41** | Follow-up & Outcome Tracking | Check-in schedules, overdue detection, observed outcomes | `WelfareFollowup` (followup_type, status, outcome_status, due_date) |

---

## 5. API Endpoints

### 5.1 Unit-Level Welfare Intelligence
- **Endpoint**: `GET /api/analytics/welfare-intelligence/unit`
- **Access Control**: Authorized Commanders, Welfare Officers, Administrators.
- **Parameters**: `battalion` (optional), `location` (optional), `time_filter` (`7d`, `30d`, `90d`).

### 5.2 Personnel Welfare Snapshot & Unified Timeline
- **Endpoint**: `GET /api/analytics/welfare-intelligence/personnel/{personnel_id}`
- **Access Control**: Enforces strict RBAC and Anti-IDOR (Jawans see only their own record; Officers restricted to their assigned battalion/location; Administrators full access).

---

## 6. Privacy & Security Safeguards

1. **Small-Group Privacy ($k < 5$)**:
   - Whenever the filtered population size is below 5, aggregate distributions are replaced with 0/null and `personnel_cards` is emptied.
   - Indirect re-identification through percentage ratios or category filters is strictly prevented.
2. **Anti-IDOR Boundaries**:
   - Personnel attempting to request peer records receive HTTP 403 Forbidden.
   - Officers attempting to query across battalion or location lines receive HTTP 403 Forbidden with security audit logging.

---

## 7. Performance & Query Optimization

- **Zero N+1 Database Queries**: Unit aggregation executes in $O(1)$ batched database roundtrips using `personnel_id.in_(p_ids)` for assessments, alerts, anomalies, recommendations, interventions, and follow-ups.
- **Deterministic Response**: Repeated invocations with identical underlying telemetry yield identical payloads in $< 100\text{ ms}$ for standard unit battalions.

---

## 8. Frontend Implementation

- **Component**: [`PS 26186/components/dashboard/UnifiedWelfareIntelligence.tsx`](file:///c:/Users/SAI%20SUSOVAN%20DASH/Desktop/ManoBal/ManoBal/PS%2026186/components/dashboard/UnifiedWelfareIntelligence.tsx)
- **Client Service**: [`PS 26186/lib/unified_intelligence.ts`](file:///c:/Users/SAI%20SUSOVAN%20DASH/Desktop/ManoBal/ManoBal/PS%2026186/lib/unified_intelligence.ts)
- **Mount Point**: Prominently displayed atop [`PS 26186/app/dashboard/page.tsx`](file:///c:/Users/SAI%20SUSOVAN%20DASH/Desktop/ManoBal/ManoBal/PS%2026186/app/dashboard/page.tsx) with interactive search, category filters, and modal drilldown.
