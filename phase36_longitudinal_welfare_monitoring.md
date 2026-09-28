# PHASE 36: Longitudinal Welfare Monitoring & Risk Trend Intelligence

## 1. Architecture
The longitudinal welfare monitoring system introduces an authoritative backend service `LongitudinalAnalyticsService` that calculates trend intelligence based on the existing Phase 34/35 `StressAssessment` records.

## 2. Data Flow
- Clients invoke `GET /personnel/{personnel_id}/trend`.
- The `api/routes/assessment.py` endpoint retrieves historical assessments from the database in descending order.
- The `LongitudinalAnalyticsService` securely consumes this chronological history, cleansing invalid data.
- The derived welfare trend response is returned to the client and integrated into the Commander Dashboard.

## 3. Trend Calculation
- The trend is calculated using the difference between the most recent risk score and the immediately preceding assessment.
- Thresholds:
  - **WORSENING**: Score increase $\ge$ 5.0 points.
  - **IMPROVING**: Score decrease $\le$ -5.0 points.
  - **STABLE**: Score change within (-5.0, 5.0).
  - **INSUFFICIENT_DATA**: Fewer than 2 valid assessments.

## 4. Trend Thresholds
The 5.0-point threshold maps directly to the continuous 0–100 Phase 34 V2 risk scale, providing a reasonable filter for short-term statistical noise while catching meaningful welfare developments.

## 5. Persistence Definition
- Elevated risk is considered **persistent** if the personnel receives $\ge$ 3 consecutive elevated, high, or critical assessments (Score $\ge$ 55.0).

## 6. Personal Baseline Calculation
- A person-specific historical baseline is established by aggregating all valid historical scores.
- Output metrics include historical mean, median, standard deviation, and the latest assessment's deviation from the historical mean.

## 7. Repeated-Factor Calculation
- Key factors and protective factors (extracted natively by the V2 model) are aggregated.
- Any factor occurring $\ge$ 2 times across the individual's history is flagged as a repeated factor to inform long-term monitoring.

## 8. Acceleration Calculation
- Trend acceleration is measured by splitting the history (if $\ge$ 4 assessments) into older and recent halves.
- The linear regression slope is derived for each half. If the recent slope exceeds the older slope by > 3.0 points per interval, the trend is **INCREASING** (accelerating).

## 9. Data Sufficiency Rules
- **0-1 assessments**: `INSUFFICIENT_DATA` (no trend logic generated)
- **2 assessments**: `LIMITED_HISTORY` (trend direction/slope possible)
- **3+ assessments**: `SUFFICIENT_HISTORY` (full baseline and persistence analysis)

## 10. API Contract
**Endpoint:** `GET /personnel/{personnel_id}/trend`
**Response:** `LongitudinalTrendResponse` matching existing Pydantic models with non-diagnostic metadata.

## 11. Dashboard Behavior
- The Commander Dashboard displays a dedicated `Longitudinal Welfare Trend Intelligence` panel providing risk direction, persistence, baseline deviations, and repeated factors using welfare-oriented language.

## 12. Privacy Considerations
- Access is strictly governed by the existing Role-Based Access Control (RBAC) ensuring commanders only monitor personnel within their designated battalion/location scope.
- Repeated factors and signals do NOT contain personally identifiable information out of context.

## 13. Limitations
- The accuracy of trend insights is highly contingent on the frequency of data submission.
- Simple linear regression for slope calculation is robust but may be overly sensitive to outlier spikes if history is very short.

## 14. Test Results
- All Phase 36 longitudinal welfare tests have successfully passed.
- All Phase 34/35 regression validations remain intact.

> Longitudinal analytics are administrative welfare-monitoring signals and are not clinical diagnoses or causal conclusions.
