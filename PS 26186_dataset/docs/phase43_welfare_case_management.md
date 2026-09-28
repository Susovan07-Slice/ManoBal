# PHASE 43: WELFARE CASE MANAGEMENT & HUMAN REVIEW WORKSPACE

## 1. Executive Summary & Objective

Phase 43 establishes the **Welfare Case Management & Human Review Workspace** for ManoBal / PS 26186. Operating directly above the unified welfare signals synthesized across Phases 34–42, Phase 43 provides an organized, traceable workflow layer for authorized human reviewers (Commanders, Welfare Officers, Administrators) to manage welfare cases.

The core goal of Phase 43 is:
> **Convert existing welfare signals into a structured, traceable human-review workflow without creating another risk or prediction engine.**

Phase 43 strictly adheres to core safety principles:
- **Does NOT replace Phases 34–42.**
- **Does NOT create another risk score, priority score, or composite index.**
- **Does NOT automatically make personnel decisions.**
- **Does NOT make clinical or disciplinary determinations.**
- **Does NOT rank personnel or produce 'worst cases' lists.**
- **Does NOT automatically close cases without explicit human action.**

---

## 2. Architectural Positioning

```text
                 Assessment
                     ↓
              Phase 34 Risk
                     ↓
             Phase 36 Trends
                     ↓
        ┌────────────┼────────────┐
        ↓            ↓            ↓
     Phase 37     Phase 39     Phase 40
      Alerts      Anomalies   Recommendations
        │            │            │
        └────────────┼────────────┘
                     ↓
              Human Decision
                     ↓
              Intervention
                     ↓
              Phase 41 Follow-up
                     ↓
                  Outcome
                     ↓
              Phase 42 Unified
                 Intelligence
                     ↓
              PHASE 43 CASE
               MANAGEMENT
                     ↓
              Human Review
                     ↓
          Decision / Support / Follow-up
```

Phase 43 is a **workflow and case-management layer**, not another intelligence engine. It consumes context from Phase 42 and gives the human reviewer a structured workspace with an immutable audit trail.

---

## 3. Core Entities & Data Architecture

### 3.1 `WelfareCase`
The primary operational case record:
- `id`: Unique primary key.
- `personnel_id`: Foreign key referencing target personnel (`personnel.id`).
- `case_reference`: Unique human-readable identifier (e.g. `WC-2026-0001`).
- `title`: Descriptive case title.
- `case_type`: Structured reason for opening the case (`CURRENT_RISK_REVIEW`, `WORSENING_TREND`, `ACTIVE_ALERT`, `ANOMALY_REVIEW`, `SUPPORT_FOLLOW_UP`, `REPEATED_WELFARE_CONCERN`, `OTHER`).
- `status`: Controlled lifecycle state (`OPEN`, `UNDER_REVIEW`, `SUPPORT_IN_PROGRESS`, `AWAITING_FOLLOW_UP`, `MONITORING`, `RESOLVED`, `CLOSED`).
- `trigger_source`: Signal source triggering human review (`PHASE_34_RISK`, `PHASE_36_TREND`, `PHASE_37_ALERT`, `PHASE_39_ANOMALY`, `PHASE_40_RECOMMENDATION`, `PHASE_41_FOLLOWUP`, `PHASE_42_INTELLIGENCE`, `MANUAL_REVIEW`).
- **Linked Authoritative Foreign Keys**:
  - `assessment_id`: Reference to Phase 34 `stress_assessments.id`
  - `alert_id`: Reference to Phase 37 `welfare_alerts.id`
  - `anomaly_id`: Reference to Phase 39 `welfare_anomalies.id`
  - `recommendation_id`: Reference to Phase 40 `welfare_recommendations.id`
  - `intervention_id`: Reference to Phase 37 `welfare_interventions.id`
  - `followup_id`: Reference to Phase 41 `welfare_followups.id`
- **Lifecycle & Actor Tracking**:
  - `opened_at`, `opened_by`
  - `last_reviewed_at`, `last_reviewed_by`
  - `closed_at`, `closed_by`, `closure_reason`, `closure_notes`
  - `reopened_at`, `reopened_by`, `reopen_reason`
  - `summary`: Human-entered contextual explanation

### 3.2 `WelfareCaseReview`
Structured record of an explicit human review:
- `id`: Primary key.
- `case_id`: Foreign key referencing parent case.
- `reviewer_id`: Foreign key referencing reviewer user.
- `reviewed_at`: Timestamp of review completion.
- `review_type`: `INITIAL_TRIAGE`, `PROGRESS_EVALUATION`, `INTERVENTION_REVIEW`, `FOLLOWUP_ASSESSMENT`, `CLOSURE_REVIEW`, `ROUTINE_MONITORING`.
- `observations`: Narrative observations from review/interview.
- `decision`: Explicit human workflow decision (`CONTINUE_MONITORING`, `CONTACT_PERSONNEL`, `REVIEW_DUTY_SUPPORT`, `OFFER_SUPPORT_RESOURCE`, `SCHEDULE_FOLLOW_UP`, `CONTINUE_EXISTING_INTERVENTION`, `CLOSE_CASE`, `REFER_TO_AUTHORIZED_SUPPORT`, `OTHER`).
- `next_step`: Specific action plan.
- `review_window`: Expected timeframe for next review (e.g. `Within 14 days`).
- `notes`: Additional reviewer commentary.

### 3.3 `WelfareCaseNote`
Immutable notes appended by authorized reviewers:
- `id`: Primary key.
- `case_id`: Foreign key referencing parent case.
- `author_id`: Foreign key referencing author user.
- `created_at`: Creation timestamp (immutable).
- `note_type`: `REVIEW_NOTE`, `SUPPORT_NOTE`, `FOLLOW_UP_NOTE`, `OUTCOME_NOTE`, `CLOSURE_NOTE`, `GENERAL_NOTE`, `OTHER`.
- `content`: Text content. Never overwritten or deleted.

### 3.4 `WelfareCaseAudit`
Append-only audit trail guaranteeing non-repudiation:
- `id`: Primary key.
- `case_id`: Foreign key referencing parent case.
- `action`: `CASE_CREATED`, `CASE_OPENED`, `CASE_REVIEWED`, `STATUS_CHANGED`, `NOTE_ADDED`, `SIGNALS_LINKED`, `CASE_CLOSED`, `CASE_REOPENED`.
- `actor_id`: Foreign key referencing initiating user.
- `previous_status`, `new_status`: Status transition bounds.
- `timestamp`: UTC timestamp.
- `metadata_json`: Structured context parameters.

---

## 4. Controlled Case Lifecycle & State Machine

Arbitrary status hops are strictly forbidden. The state machine enforces permitted transitions:

```text
          OPEN
         ↙    ↘
 UNDER_REVIEW   CLOSED (terminal without reopen)
   ↙    ↓    ↘     ↑
SUPPORT AWAITING  MONITORING
 IN_PROG FOLLOWUP  ↙     ↘
   ↘    ↓    ↙  RESOLVED  UNDER_REVIEW
      RESOLVED ───→ CLOSED
                    ↓ (Explicit Reopen Action)
                   OPEN
```

### Permitted Transitions:
| From State | Permitted Next States |
|---|---|
| **OPEN** | `UNDER_REVIEW`, `MONITORING`, `CLOSED` |
| **UNDER_REVIEW** | `SUPPORT_IN_PROGRESS`, `AWAITING_FOLLOW_UP`, `MONITORING`, `RESOLVED`, `CLOSED` |
| **SUPPORT_IN_PROGRESS** | `AWAITING_FOLLOW_UP`, `MONITORING`, `RESOLVED`, `CLOSED` |
| **AWAITING_FOLLOW_UP** | `MONITORING`, `SUPPORT_IN_PROGRESS`, `RESOLVED`, `CLOSED` |
| **MONITORING** | `UNDER_REVIEW`, `SUPPORT_IN_PROGRESS`, `AWAITING_FOLLOW_UP`, `RESOLVED`, `CLOSED` |
| **RESOLVED** | `CLOSED`, `MONITORING`, `UNDER_REVIEW` |
| **CLOSED** | `OPEN` (Only through explicit reopen action with recorded justification) |

---

## 5. Security, RBAC & Anti-IDOR Protections

1. **Authentication**: All endpoints require a valid JWT Bearer token.
2. **Jawan Role (Personnel)**:
   - Read-only access to own linked cases ONLY.
   - Cannot view cases belonging to peer personnel (Anti-IDOR HTTP 403).
   - Cannot create cases, record reviews, add notes, or change statuses (HTTP 403).
3. **Officer & Welfare Roles**:
   - Strictly bounded by assigned `battalion` (and `location` if assigned).
   - Cross-battalion access returns HTTP 403 Forbidden.
4. **Admin Role**:
   - Broad organizational access across all units.

---

## 6. Small-Group Privacy Protection (k >= 5)

Aggregate unit-level statistics enforce $k \ge 5$ privacy protection:
- `ANALYTICS_MIN_GROUP_SIZE = 5`
- If total cases in monitored scope are between 1 and 4, case breakdown distributions are suppressed (`data_suppressed = True`).
- Prevents re-identification of individuals in small cohorts.

---

## 7. Performance & Batched Loading (Zero N+1)

To prevent query storms on large rosters:
- Case list query eager-loads `Personnel`, `Opener`, `Reviewer`, and `Closer` with `joinedload`.
- Related signals (latest assessment, active alerts, anomalies, recommendations, interventions, followups) are batch-queried across all personnel IDs in the page using SQL `IN (...)` operators.
- Assembles summaries in $O(N)$ with zero subqueries per row.

---

## 8. API Specification

| Method | Endpoint | Description | Auth Roles |
|---|---|---|---|
| `GET` | `/api/welfare-cases` | List authorized welfare cases (unranked, stable sort) | All authenticated |
| `POST` | `/api/welfare-cases` | Open a new welfare case | Officer, Welfare, Admin |
| `GET` | `/api/welfare-cases/summary-stats` | Get unit aggregate case metrics (k >= 5 privacy) | Officer, Welfare, Admin |
| `GET` | `/api/welfare-cases/{case_id}` | Get case detail & authoritative evidence | Scoped access |
| `POST` | `/api/welfare-cases/{case_id}/review` | Record human review and decision | Officer, Welfare, Admin |
| `POST` | `/api/welfare-cases/{case_id}/notes` | Append immutable case note | Officer, Welfare, Admin |
| `POST` | `/api/welfare-cases/{case_id}/status` | Controlled lifecycle transition | Officer, Welfare, Admin |
| `POST` | `/api/welfare-cases/{case_id}/close` | Explicit human case closure | Officer, Welfare, Admin |
| `POST` | `/api/welfare-cases/{case_id}/reopen` | Reopen closed case (CLOSED -> OPEN) | Officer, Welfare, Admin |
| `POST` | `/api/welfare-cases/{case_id}/link-signal` | Associate authoritative signal IDs | Officer, Welfare, Admin |
| `GET` | `/api/welfare-cases/{case_id}/timeline` | Unified chronological event timeline | Scoped access |
| `GET` | `/api/welfare-cases/{case_id}/audits` | Append-only audit history | Scoped access |

---

## 9. Frontend Integration

1. **Dashboard Workspace** (`components/dashboard/WelfareCaseManagement.tsx`):
   - Unranked case roster with multi-attribute filtering (Status, Type, Search).
   - Comprehensive detail modal with 5 tabbed views: Evidence, Reviews, Notes, Timeline, Audits.
   - Interactive review, note, closure, and reopen dialogs.
2. **Phase 42 Drilldown Integration** (`components/dashboard/UnifiedWelfareIntelligence.tsx`):
   - "Open Welfare Case" button embedded directly in the Personnel Snapshot drilldown modal and roster cards.
   - Smoothly dispatches custom event and focuses the case management workspace.
3. **API Client** (`lib/welfareCases.ts`):
   - Fully typed TypeScript client with zero external dependencies.
