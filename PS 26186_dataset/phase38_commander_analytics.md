# Phase 38 — Advanced Commander Analytics & Unit-Level Welfare Intelligence

## 1. Overview & Purpose
Phase 38 delivers organizational-level welfare analytics for authorized Commanders, Officers, and Welfare personnel in the ManoBal (`PS 26186`) platform. It answers the operational question:

> *"What is happening across my authorized organizational scope, and are there emerging welfare patterns that require human attention?"*

### Architectural Rule
**Phase 38 does not create or modify the authoritative Phase 34 risk engine.**

Phase 38 is strictly an aggregation, summarization, and decision-support layer built downstream of:
1. **Phase 34**: Authoritative Welfare Risk Engine V2 (Continuous 0–100 risk scoring with 5-tier classification: `Critical`, `High`, `Elevated`, `Moderate`, `Low`).
2. **Phase 36**: Longitudinal Welfare Monitoring Service (Temporal trajectories: `IMPROVING`, `STABLE`, `WORSENING`, `LIMITED_HISTORY`, `INSUFFICIENT_DATA`).
3. **Phase 37**: Welfare Alert & Intervention Management Service (`WelfareAlert` triggers, severity workflows, and follow-ups).

```
Phase 34
Welfare Risk Engine V2
        ↓
Individual Risk Assessment (Authoritative 0-100 & 5-tier scale)
        ↓
Phase 36
Longitudinal Analytics (Temporal trajectory & baseline deviation)
        ↓
Phase 37
Welfare Alerts & Interventions (Rapid escalation, review, follow-up)
        ↓
Phase 38
Commander Analytics Service (Scoped aggregation, privacy k-anonymity, unit intelligence)
```

---

## 2. Core Architectural Components

### A. Centralized Service: `CommanderAnalyticsService`
- Location: `services/commander_analytics_service.py`
- Core Responsibilities:
  1. **Strict Scope Filtering**: Filters `Personnel` records by the authenticated user's `battalion` and `location`. Officer and Welfare accounts cannot access personnel outside their authorized organizational assignment.
  2. **Privacy / Small-Group Protection ($k$-Anonymity)**: Configurable threshold `ANALYTICS_MIN_GROUP_SIZE` (default: 5). If the authorized population in scope is below this threshold, individual risk metrics and category counts are withheld and status `INSUFFICIENT_GROUP_SIZE` is returned.
  3. **Current Risk Distribution**: Computes the distribution of unique personnel across the authoritative Phase 34 V2 5 categories using only the *latest valid assessment* per individual. Historical check-ins do not inflate counts.
  4. **Longitudinal Trends**: Aggregates Phase 36 longitudinal outputs across scoped personnel to compute improving %, stable %, worsening %, and persistent elevated-risk population counts.
  5. **Alert Analytics**: Aggregates Phase 37 alerts (open, under review, resolved) and intervention statuses (planned, completed, follow-ups required).
  6. **Welfare Factors**: Aggregates recurring stressor factors (duty hours, sleep deficits, night shifts, leave gaps) using supportive, non-punitive language.
  7. **Data Quality & Determinism**: Detects missing assessments, unassessed personnel, and malformed inputs without failing or leaking stack traces. Given identical inputs, produces deterministic responses.

---

## 3. API Contract: `GET /api/analytics/commander`

### Parameters
| Query Parameter | Type | Default | Description |
|---|---|---|---|
| `time_filter` | `str` | `"30d"` | `"7d"`, `"30d"`, `"90d"`, `"all"`, or `"custom"` |
| `time_range` | `str` | `None` | Alias for `time_filter` |
| `start_date` | `str` | `None` | ISO timestamp for custom range start |
| `end_date` | `str` | `None` | ISO timestamp for custom range end |
| `reference_time` | `str` | `None` | Optional UTC anchor timestamp for deterministic audits |
| `battalion` | `str` | `None` | Ignored for non-admins; strictly scoped to user token |
| `location` | `str` | `None` | Ignored for non-admins; strictly scoped to user token |

### Security & RBAC Enforcement
- Allowed Roles: `admin`, `officer`, `welfare`.
- Personnel Role (Jawan): Returns `HTTP 403 Forbidden`.
- Anti-IDOR Scope Violation: If an officer assigned to Battalion A passes `?battalion=Battalion B`, the API rejects the request immediately with `HTTP 403 Forbidden` (`"Access denied: Cannot query organizational analytics outside your assigned Battalion scope."`).

---

## 4. Privacy & $k$-Anonymity Minimum Group Size
In remote or small tactical detachments (e.g., small hill outposts of 3 or 4 personnel), aggregate risk statistics like *"1 Critical, 0 High, 2 Low"* allow deductive re-identification of which specific soldier has high stress.

To prevent deductive deanonymization:
```json
{
  "status": "INSUFFICIENT_GROUP_SIZE",
  "message": "Aggregate analytics are unavailable for this population size. A minimum group size of 5 authorized personnel is required to protect individual privacy and prevent deductive re-identification.",
  "scope": {
    "role": "officer",
    "battalion": "Small Outpost",
    "location": "Remote Hill",
    "total_authorized_personnel": 3,
    "min_group_size_threshold": 5
  },
  "summary": null,
  "risk_distribution": null,
  "trend": null,
  "alerts": null,
  "welfare_factors": null,
  "interventions": null,
  "data_quality": {
    "records_analyzed": 0,
    "personnel_count": 3,
    "latest_assessment_date": null,
    "date_range": { "filter_type": "30d" },
    "insufficient_data": true,
    "notes": ["Population below privacy threshold. Individual risk metrics withheld."]
  }
}
```

---

## 5. Non-Punitive Terminology & Ethical Safeguards
In compliance with military welfare governance:
- **No Individual Ranking**: No "top 10 riskiest soldiers" or "worst units" endpoints exist.
- **Supportive Factor Naming**:
  - *"Elevated operational duty workload (> 50 hrs/week)"*
  - *"Restorative sleep deficit (< 5.5 hrs/night)"*
  - *"Frequent night-shift roster assignments"*
  - *"Prolonged duration without respite/leave"*
  - *"Continuous duty period without rest interval"*
- Disciplinary, punitive, or derogatory terms are strictly forbidden. Analytics serve strictly as human decision-support for commanders to schedule relief, respite, and supportive check-ins.
