# Phase 40 — Welfare Recommendation & Support Engine

## 1. Overview & Operational Purpose

Phase 40 introduces the **Welfare Recommendation & Support Engine** for the ManoBal / PS 26186 platform. Its singular mission is to answer:

> **“Given the existing welfare signals, what supportive actions could an authorized human reviewer consider?”**

### Authoritative Architecture & Downstream Pipeline
Phase 40 does **NOT** compute, alter, or replace any risk scores. **Phase 34 remains the authoritative risk engine.**

The architecture adheres strictly to the downstream pipeline:
```
Assessment
    ↓
Phase 34: Authoritative Risk Engine V2 (Continuous 0-100 risk score, 5-tier classification)
    ↓
Phase 36: Longitudinal Monitoring (Trajectory, baseline deviation, velocity & acceleration)
    ↓
Phase 37 / 39: Welfare Alerts & Anomalies (Pattern departures, thresholds, early warning)
    ↓
Phase 40: Welfare Recommendation & Support Engine (Explainable, non-punitive support suggestions)
    ↓
Human Decision (Authorized Commander / Welfare Officer Review)
    ↓
Phase 37: Welfare Intervention (Optional structured action upon explicit human decision)
    ↓
Follow-up Monitoring & Re-evaluation
```

### Strict Non-Negotiable Boundaries
Phase 40 strictly does **NOT**:
1. Calculate a new risk score or create any alternate scoring formula.
2. Override Phase 34 risk scoring, feature semantics, or category thresholds.
3. Automatically execute punitive, disciplinary, or coercive personnel actions.
4. Mandate psychiatric diagnosis, compulsory medical leave, or forced removal from duty.
5. Bypass human decision-making or initiate interventions without explicit human confirmation.

---

## 2. Supported Recommendation Types

The engine generates eight explainable, supportive recommendation types:

| Recommendation Type | Typical Trigger Context | Suggested Review Window | Linked Phase 37 Intervention |
|---|---|---|---|
| **`RECOVERY_REVIEW`** | Consecutive duty days $\ge 12$, extreme duty hours ($\ge 65$h/wk), or sleep deprivation anomaly | Within 48 hours | `MANDATORY_REST_INTERVAL` |
| **`DUTY_SCHEDULE_REVIEW`** | Sustained high duty hours ($\ge 55$h/wk), heavy night shifts ($\ge 8$/mo), or workload anomaly | Within 3–5 days | `DUTY_SCHEDULE_ADJUSTMENT` |
| **`WELFARE_FOLLOW_UP`** | Extended leave gap ($\ge 120$ days), family/financial stress factors, or peer welfare signals | Within 7 days | `WELLNESS_CHECKIN` |
| **`VOLUNTARY_WELLNESS_CHECKIN`** | Moderate/Elevated risk with worsening longitudinal trend or subtle anomaly departure | Within 7 days | `WELLNESS_CHECKIN` |
| **`SUPPORT_RESOURCE_REFERRAL`** | High/Critical risk, severe sleep deficit, or multiple co-occurring stress factors | Within 24–48 hours | `COUNSELING_SESSION` / `PEER_SUPPORT` |
| **`FOLLOW_UP_ASSESSMENT`** | Assessment gap, high uncertainty, or rapid trajectory transition | Within 72 hours | `WELLNESS_CHECKIN` |
| **`CONTINUE_MONITORING`** | Stable low-risk profile, routine check-in without anomalies | Routine (14–30 days) | None |
| **`HUMAN_REVIEW`** | Urgent multi-factor cluster, acute risk surge, or anomalous biometric/telemetry divergence | Immediate (Within 24 hours) | `COUNSELING_SESSION` |

---

## 3. Priority Semantics Independent of Risk Score

Recommendation priority determines **action review urgency**, not medical diagnosis:
- **`CRITICAL`**: Immediate review required (e.g., Critical risk + multi-factor cluster or acute surge). Suggested review: within 24 hours.
- **`HIGH`**: Prioritized review (e.g., High risk or extreme consecutive duty $\ge 14$ days, even with lower current risk score). Suggested review: within 48 hours.
- **`ELEVATED`**: Timely attention (e.g., Elevated risk, continuous workload $\ge 55$h, or accelerating trend). Suggested review: within 3–7 days.
- **`ROUTINE`**: Standard check-in during normal muster cycles. Suggested review: within 14–30 days.

> **Key Decoupling**: A soldier with a Low risk score (e.g., 32.0) who has worked 15 consecutive days without respite will correctly receive a `RECOVERY_REVIEW` recommendation with **HIGH priority**, demonstrating that operational welfare needs are not blinded by raw risk scores alone.

---

## 4. Explainability & Traceability Contract

Every recommendation includes a rich, transparent evidence envelope:
- **`trigger`**: Human-readable trigger explanation (e.g., `"Workload anomaly detected (68.0h/wk) alongside 14 consecutive duty days."`).
- **`evidence_metrics`**: Quantified signals (e.g., `{ duty_hours_per_week: 68.0, consecutive_duty_days: 14, sleep_hours: 4.8, baseline_deviation: -2.2 }`).
- **`reason`**: Clear supportive rationale for the reviewer.
- **`source_signals`**: List of upstream origins (`PHASE_34_RISK_ENGINE`, `PHASE_36_LONGITUDINAL_TREND`, `PHASE_37_ALERT`, `PHASE_39_ANOMALY`, `HRMS_DUTY_ROSTER`, `WEARABLE_TELEMETRY`).
- **`traceability_links`**: Explicit links to `linked_alert_id`, `linked_anomaly_id`, and `linked_intervention_id`.

---

## 5. Deterministic Deduplication Hashing

To prevent recommendation flooding during repeated evaluations on the same day:
$$\text{dedup\_hash} = \text{SHA256}(\text{personnel\_id} \,\|\, \text{recommendation\_type} \,\|\, \text{trigger\_date} \,\|\, \text{evidence\_signature})$$
If an active recommendation matching the hash already exists for the personnel member, the engine returns the existing record without inserting duplicate rows.

---

## 6. Reviewer Lifecycle State Machine & Phase 37 Integration

Recommendations transition through an explicit human review workflow:
```
[SUGGESTED]
    │
    ├─── Acknowledge ───> [ACKNOWLEDGED]
    │                          │
    ├─── Accept ──────────────> [ACCEPTED] ─── (Optional: Create Phase 37 Intervention)
    │                          │
    ├─── Defer ───────────────> [DEFERRED] (Set review window to +7/14/30 days)
    │                          │
    ├─── Dismiss ─────────────> [DISMISSED] (Requires non-punitive rationale)
    │                          │
    └─── Record Action ───────> [ACTIONED] (Supportive action completed)
```

When an authorized reviewer **Accepts** a recommendation:
- The system allows the reviewer to optionally schedule a formal **Phase 37 `WelfareIntervention`** (e.g., `MANDATORY_REST_INTERVAL`, `DUTY_SCHEDULE_ADJUSTMENT`, `WELLNESS_CHECKIN`, `COUNSELING_SESSION`, `PEER_SUPPORT`).
- The resulting intervention's ID is linked directly back to `WelfareRecommendation.linked_intervention_id`, closing the loop between decision support and structured welfare support.

---

## 7. Security, Anti-IDOR & Privacy Governance

1. **Role-Based Access Control (RBAC)**:
   - `personnel`: Authorized **ONLY** to view their own personal welfare recommendations (`Anti-IDOR`).
   - `officer` / `welfare`: Scoped strictly to their matching **Battalion** and **Location**. Cross-battalion or cross-location access returns HTTP 403 Forbidden.
   - `admin`: System-wide authorized access.
2. **Small-Group Privacy Suppression ($k$-Anonymity)**:
   - When unit size is below `ANALYTICS_MIN_GROUP_SIZE = 5`, commander summary responses suppress individual recommendations (`small_group_suppressed: true`) to prevent indirect re-identification.
3. **Auditing**:
   - Every review action records `acknowledged_by`, `acknowledged_at`, `actioned_by`, `actioned_at`, and `action_notes`.

---

## 8. REST API Endpoints

- `GET /api/recommendations/personnel/{personnel_id}`: Retrieve active/historical recommendations for personnel (RBAC/Anti-IDOR enforced).
- `POST /api/recommendations/evaluate/{personnel_id}`: Trigger signal aggregation and generate new recommendations.
- `GET /api/recommendations/commander`: Unit-level recommendations summary with status/priority breakdowns and privacy suppression.
- `POST /api/recommendations/{id}/acknowledge`: Mark recommendation acknowledged by human reviewer.
- `POST /api/recommendations/{id}/accept`: Accept recommendation with optional Phase 37 intervention creation.
- `POST /api/recommendations/{id}/defer`: Defer review window by $N$ days.
- `POST /api/recommendations/{id}/dismiss`: Dismiss recommendation with recorded rationale.
- `POST /api/recommendations/{id}/action`: Complete recommendation with supportive action summary.
