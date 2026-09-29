import os
import re
import json
import hashlib
from datetime import datetime, timedelta, timezone
from typing import Optional, List, Dict, Any, Tuple
import numpy as np
from sqlalchemy.orm import Session
from sqlalchemy import func, desc

from core.config import logger
from db.models.user import User
from db.models.personnel import Personnel
from db.models.assessment import StressAssessment
from db.models.alert import WelfareAlert
from db.models.anomaly import WelfareAnomaly, WelfareAnomalyAudit
from db.models.telemetry import WearableTelemetry
from services.longitudinal_analytics_service import LongitudinalAnalyticsService
from services.commander_analytics_service import CommanderAnalyticsService

# Configurable minimum history and privacy thresholds
MIN_PERSONAL_ASSESSMENTS_FOR_ANOMALY = int(os.getenv("MIN_PERSONAL_ASSESSMENTS_FOR_ANOMALY", "3"))
MIN_UNIT_PERIODS_FOR_ANOMALY = int(os.getenv("MIN_UNIT_PERIODS_FOR_ANOMALY", "2"))
ANALYTICS_MIN_GROUP_SIZE = int(os.getenv("ANALYTICS_MIN_GROUP_SIZE", "5"))


class WelfareAnomalyService:
    """
    Phase 39: Early-Warning & Welfare Anomaly Detection Service.
    Identifies unusual or accelerating welfare patterns for human welfare review.
    Does NOT modify Phase 34 risk scoring, ML models, or category thresholds.
    """

    # =========================================================================
    # 1. PERSONALIZED ANOMALY DETECTION
    # =========================================================================
    @classmethod
    def detect_personal_anomalies(
        cls,
        personnel: Personnel,
        db: Session,
        reference_time: Optional[datetime] = None,
        persist: bool = True
    ) -> Tuple[str, str, List[WelfareAnomaly], Dict[str, Any]]:
        """
        Detects anomalies for an individual personnel by comparing current observations
        against their personalized historical baseline.
        Returns (status, message, detected_anomalies, baseline_summary).
        """
        now = reference_time or datetime.now(timezone.utc)

        # 1. Query all assessments chronologically
        assessments = (
            db.query(StressAssessment)
            .filter(StressAssessment.personnel_id == personnel.id)
            .order_by(StressAssessment.assessment_timestamp.asc(), StressAssessment.id.asc())
            .all()
        )

        if not assessments:
            return (
                "INSUFFICIENT_DATA",
                "No assessments recorded for this personnel. Baseline cannot be established.",
                [],
                {}
            )

        if len(assessments) < MIN_PERSONAL_ASSESSMENTS_FOR_ANOMALY:
            return (
                "INSUFFICIENT_BASELINE",
                f"Insufficient historical assessments ({len(assessments)} / {MIN_PERSONAL_ASSESSMENTS_FOR_ANOMALY} required). Personalized baseline cannot be reliably established.",
                [],
                {"sample_count": len(assessments), "min_required": MIN_PERSONAL_ASSESSMENTS_FOR_ANOMALY}
            )

        current_assessment = assessments[-1]
        prior_assessments = assessments[:-1]

        # Filter valid prior scores for baseline
        prior_scores = []
        for a in prior_assessments:
            if a.risk_score is not None:
                try:
                    s = float(a.risk_score)
                    if not (np.isnan(s) or np.isinf(s)):
                        prior_scores.append(s)
                except (ValueError, TypeError):
                    continue

        if not prior_scores or len(prior_scores) < (MIN_PERSONAL_ASSESSMENTS_FOR_ANOMALY - 1):
            return (
                "INSUFFICIENT_BASELINE",
                "Insufficient valid historical risk scores to establish an anomaly baseline.",
                [],
                {}
            )

        baseline_mean = round(float(np.mean(prior_scores)), 1)
        baseline_std = round(float(np.std(prior_scores)), 1) if len(prior_scores) > 1 else 0.0
        current_score = float(current_assessment.risk_score) if current_assessment.risk_score is not None else 0.0
        current_deviation = round(current_score - baseline_mean, 1)

        # Compute longitudinal trend using authoritative Phase 36 service
        longitudinal_data = LongitudinalAnalyticsService.calculate_longitudinal_trend(
            personnel_id=personnel.id,
            assessments=assessments,
            reference_time=now
        )
        trend = longitudinal_data.get("trend", {})
        score_change = trend.get("score_change")
        trend_slope = trend.get("slope")
        trend_accel = trend.get("acceleration")
        trend_direction = trend.get("direction", "STABLE")

        baseline_summary = {
            "historical_mean": baseline_mean,
            "historical_std": baseline_std,
            "sample_count": len(prior_scores),
            "current_score": current_score,
            "current_deviation": current_deviation,
            "score_change": score_change,
            "trend_direction": trend_direction,
            "acceleration": trend_accel,
        }

        detected_signals: List[Dict[str, Any]] = []
        current_ts = current_assessment.assessment_timestamp or now
        if current_ts.tzinfo is None:
            current_ts = current_ts.replace(tzinfo=timezone.utc)
        obs_date_str = current_ts.strftime("%Y-%m-%d")

        # ---------------------------------------------------------------------
        # Anomaly A: RAPID_RISK_CHANGE
        # ---------------------------------------------------------------------
        is_rapid_change = False
        if score_change is not None and score_change >= 20.0:
            is_rapid_change = True
        elif baseline_std > 2.0 and current_deviation >= 2.5 * baseline_std and current_deviation >= 15.0:
            is_rapid_change = True

        if is_rapid_change:
            sev = "URGENT_REVIEW" if current_score >= 70.0 else "ATTENTION"
            conf = "HIGH" if len(prior_scores) >= 5 else "MEDIUM"
            prev_score = prior_assessments[-1].risk_score
            detected_signals.append({
                "anomaly_type": "RAPID_RISK_CHANGE",
                "severity": sev,
                "confidence": conf,
                "evidence": {
                    "reason": "Rapid shift in risk score compared to prior baseline",
                    "baseline_metric": "risk_score",
                    "baseline_value": baseline_mean,
                    "baseline_std": baseline_std,
                    "previous_value": prev_score,
                    "current_value": current_score,
                    "delta": score_change if score_change is not None else current_deviation,
                    "sample_count": len(prior_scores),
                    "window_description": "Preceding check-in to current assessment",
                    "explanation": (
                        f"Current risk score ({current_score}) increased substantially "
                        f"(+{score_change if score_change is not None else current_deviation} pts) "
                        f"from recent baseline (mean: {baseline_mean}). Warrant human welfare review."
                    )
                }
            })

        # ---------------------------------------------------------------------
        # Anomaly B: RAPID_RISK_ACCELERATION
        # ---------------------------------------------------------------------
        if trend_accel == "ACCELERATING" and (trend_slope is not None and trend_slope >= 0.4) and (score_change is not None and score_change >= 8.0):
            conf = "HIGH" if len(prior_scores) >= 4 else "MEDIUM"
            detected_signals.append({
                "anomaly_type": "RAPID_RISK_ACCELERATION",
                "severity": "ATTENTION",
                "confidence": conf,
                "evidence": {
                    "reason": "Risk progression velocity is accelerating across assessment intervals",
                    "baseline_metric": "trend_slope",
                    "slope": trend_slope,
                    "acceleration": trend_accel,
                    "score_change": score_change,
                    "sample_count": len(prior_scores),
                    "window_description": "Multi-assessment velocity window",
                    "explanation": (
                        f"Longitudinal velocity analysis indicates increasing rate of strain progression "
                        f"(+{trend_slope} pts/day) compared to steady baseline."
                    )
                }
            })

        # ---------------------------------------------------------------------
        # Anomaly C: WORKLOAD_ANOMALY
        # ---------------------------------------------------------------------
        # Compare current duty hours against established standard or personal baseline
        duty_hours = personnel.duty_hours_per_week or 40.0
        # If duty hours exceed standard threshold (e.g. 65+ hrs) or jump by 15+ hrs
        if duty_hours >= 65.0:
            detected_signals.append({
                "anomaly_type": "WORKLOAD_ANOMALY",
                "severity": "ATTENTION",
                "confidence": "HIGH",
                "evidence": {
                    "reason": "Unusual operational workload increase relative to baseline roster",
                    "baseline_metric": "duty_hours_per_week",
                    "baseline_value": 44.0,
                    "current_value": duty_hours,
                    "delta": round(duty_hours - 44.0, 1),
                    "sample_count": len(prior_scores),
                    "window_description": "Current weekly roster",
                    "explanation": (
                        f"Current operational duty schedule ({duty_hours} hrs/week) reflects "
                        f"an acute surge (+{round(duty_hours - 44.0, 1)} hrs above standard baseline). "
                        f"Human relief and rest interval scheduling recommended."
                    )
                }
            })

        # ---------------------------------------------------------------------
        # Anomaly D: SLEEP_RECOVERY_ANOMALY
        # ---------------------------------------------------------------------
        # Check wearable telemetry history if available
        telemetry_records = (
            db.query(WearableTelemetry)
            .filter(WearableTelemetry.personnel_id == personnel.id)
            .order_by(WearableTelemetry.recorded_at.asc())
            .all()
        )

        sleep_anomaly_detected = False
        if len(telemetry_records) >= 5:
            past_sleeps = [t.sleep_duration_hours for t in telemetry_records[:-2] if t.sleep_duration_hours is not None]
            recent_sleeps = [t.sleep_duration_hours for t in telemetry_records[-2:] if t.sleep_duration_hours is not None]
            if past_sleeps and recent_sleeps:
                past_sleep_mean = round(float(np.mean(past_sleeps)), 1)
                recent_sleep_mean = round(float(np.mean(recent_sleeps)), 1)
                if (recent_sleep_mean <= past_sleep_mean - 2.0) or (recent_sleep_mean < 5.0 and past_sleep_mean >= 6.5):
                    sleep_anomaly_detected = True
                    detected_signals.append({
                        "anomaly_type": "SLEEP_RECOVERY_ANOMALY",
                        "severity": "ATTENTION",
                        "confidence": "HIGH",
                        "evidence": {
                            "reason": "Significant reduction in restorative sleep duration relative to personal baseline",
                            "baseline_metric": "sleep_duration_hours",
                            "baseline_value": past_sleep_mean,
                            "current_value": recent_sleep_mean,
                            "delta": round(recent_sleep_mean - past_sleep_mean, 1),
                            "sample_count": len(past_sleeps),
                            "window_description": "Rolling telemetry recovery window",
                            "explanation": (
                                f"Recent recovery pattern differs substantially from the person's historical baseline "
                                f"(average {recent_sleep_mean} hrs/night vs baseline {past_sleep_mean} hrs/night). "
                                f"Non-diagnostic administrative early-warning signal."
                            )
                        }
                    })

        # Fallback to structural recovery factors if wearable telemetry is absent
        if not sleep_anomaly_detected and personnel.consecutive_duty_days and personnel.consecutive_duty_days >= 14:
            detected_signals.append({
                "anomaly_type": "SLEEP_RECOVERY_ANOMALY",
                "severity": "ATTENTION",
                "confidence": "MEDIUM",
                "evidence": {
                    "reason": "Prolonged continuous duty without rest recovery interval",
                    "baseline_metric": "consecutive_duty_days",
                    "baseline_value": 3.0,
                    "current_value": float(personnel.consecutive_duty_days),
                    "delta": float(personnel.consecutive_duty_days - 3),
                    "sample_count": len(prior_scores),
                    "window_description": "Current duty roster",
                    "explanation": (
                        f"Personnel has completed {personnel.consecutive_duty_days} continuous duty days "
                        f"without mandatory respite interval, presenting cumulative recovery strain."
                    )
                }
            })

        # ---------------------------------------------------------------------
        # Anomaly E: NIGHT_SHIFT_PATTERN_CHANGE
        # ---------------------------------------------------------------------
        night_shifts = personnel.night_shifts_per_month or 0
        if night_shifts >= 8:
            baseline_shifts = 3.0
            detected_signals.append({
                "anomaly_type": "NIGHT_SHIFT_PATTERN_CHANGE",
                "severity": "WATCH",
                "confidence": "HIGH",
                "evidence": {
                    "reason": "Unusual surge in night-shift roster assignments",
                    "baseline_metric": "night_shifts_per_month",
                    "baseline_value": baseline_shifts,
                    "current_value": float(night_shifts),
                    "delta": float(night_shifts - baseline_shifts),
                    "sample_count": len(prior_scores),
                    "window_description": "Monthly roster schedule",
                    "explanation": (
                        f"Night-shift allocation ({night_shifts} shifts/month) significantly exceeds "
                        f"standard operational baseline ({baseline_shifts} shifts/month)."
                    )
                }
            })

        # ---------------------------------------------------------------------
        # Anomaly F: WELFARE_FACTOR_CLUSTER
        # ---------------------------------------------------------------------
        co_factors = []
        if duty_hours >= 55.0:
            co_factors.append(f"Elevated workload ({duty_hours} hrs/week)")
        if (personnel.consecutive_duty_days and personnel.consecutive_duty_days >= 10) or sleep_anomaly_detected:
            co_factors.append("Recovery / sleep restriction")
        if night_shifts >= 6:
            co_factors.append(f"Frequent night shifts ({night_shifts}/month)")
        if personnel.leave_gap_days and personnel.leave_gap_days >= 60:
            co_factors.append(f"Prolonged leave gap ({personnel.leave_gap_days} days)")
        if trend_direction == "WORSENING":
            co_factors.append("Worsening longitudinal trajectory")

        if len(co_factors) >= 3:
            sev = "URGENT_REVIEW" if current_score >= 70.0 else "ATTENTION"
            detected_signals.append({
                "anomaly_type": "WELFARE_FACTOR_CLUSTER",
                "severity": sev,
                "confidence": "HIGH",
                "evidence": {
                    "reason": "Multi-factor operational strain cluster co-occurring in unison",
                    "sample_count": len(prior_scores),
                    "co_occurring_factors": co_factors,
                    "current_value": current_score,
                    "window_description": "Current assessment & operational profile",
                    "explanation": (
                        f"Identified synchronous co-occurrence of multiple strain indicators: "
                        f"{'; '.join(co_factors)}. Pattern signal for prioritized human review."
                    )
                }
            })

        # ---------------------------------------------------------------------
        # Persistence & Deduplication
        # ---------------------------------------------------------------------
        active_anomalies: List[WelfareAnomaly] = []
        if persist:
            for sig in detected_signals:
                anom = cls._persist_or_update_anomaly(
                    db=db,
                    personnel_id=personnel.id,
                    scope_type="INDIVIDUAL",
                    scope_battalion=personnel.battalion,
                    scope_location=personnel.location,
                    anomaly_type=sig["anomaly_type"],
                    severity=sig["severity"],
                    confidence=sig["confidence"],
                    baseline_sample_count=len(prior_scores),
                    obs_date_str=obs_date_str,
                    evidence_dict=sig["evidence"],
                    current_ts=current_ts
                )
                active_anomalies.append(anom)
            db.commit()
        else:
            # Ephemeral models for read-only evaluations
            for sig in detected_signals:
                ephem = WelfareAnomaly(
                    personnel_id=personnel.id,
                    scope_type="INDIVIDUAL",
                    scope_battalion=personnel.battalion,
                    scope_location=personnel.location,
                    anomaly_type=sig["anomaly_type"],
                    severity=sig["severity"],
                    status="DETECTED",
                    confidence=sig["confidence"],
                    baseline_sample_count=len(prior_scores),
                    detected_at=current_ts,
                    evidence_json=json.dumps(sig["evidence"]),
                    dedup_hash="ephemeral"
                )
                active_anomalies.append(ephem)

        status_code = "DETECTED" if active_anomalies else "NO_ANOMALY"
        msg = (
            f"{len(active_anomalies)} early-warning welfare anomaly signal(s) flagged for human review."
            if active_anomalies
            else "No anomalous departures detected relative to personal baseline."
        )

        return status_code, msg, active_anomalies, baseline_summary

    # =========================================================================
    # 2. UNIT-LEVEL ANOMALY DETECTION
    # =========================================================================
    @classmethod
    def detect_unit_anomalies(
        cls,
        db: Session,
        current_user: User,
        reference_time: Optional[datetime] = None,
        persist: bool = True
    ) -> Tuple[str, str, List[WelfareAnomaly], Dict[str, Any]]:
        """
        Detects unit-level welfare anomalies across the user's authorized scope.
        Compares current 14-day window against prior 15-60 day baseline.
        """
        now = reference_time or datetime.now(timezone.utc)

        # Enforce Scope
        p_query = CommanderAnalyticsService.get_scoped_personnel_query(db, current_user)
        scoped_personnel = p_query.all()
        total_authorized = len(scoped_personnel)

        scope_battalion = current_user.battalion or "Command Scope"
        scope_location = current_user.location or "All Assigned Outposts"

        # Small-group privacy protection
        if total_authorized < ANALYTICS_MIN_GROUP_SIZE:
            return (
                "INSUFFICIENT_GROUP_SIZE",
                f"Aggregate anomaly detection unavailable for population under {ANALYTICS_MIN_GROUP_SIZE} personnel (k-anonymity privacy protection).",
                [],
                {"total_authorized": total_authorized, "min_required": ANALYTICS_MIN_GROUP_SIZE}
            )

        scoped_pids = [p.id for p in scoped_personnel]

        # Windows: Current (past 14 days) vs Prior Baseline (past 15 - 60 days)
        recent_start = now - timedelta(days=14)
        baseline_start = now - timedelta(days=60)
        baseline_end = recent_start

        all_assessments = (
            db.query(StressAssessment)
            .filter(StressAssessment.personnel_id.in_(scoped_pids))
            .filter(StressAssessment.assessment_timestamp >= baseline_start)
            .all()
        )

        recent_assessments: List[StressAssessment] = []
        baseline_assessments: List[StressAssessment] = []

        for a in all_assessments:
            ts = a.assessment_timestamp
            if ts is None:
                continue
            if ts.tzinfo is None:
                ts = ts.replace(tzinfo=timezone.utc)

            if ts >= recent_start:
                recent_assessments.append(a)
            elif ts >= baseline_start and ts < baseline_end:
                baseline_assessments.append(a)

        # Baseline sufficiency check
        if len(baseline_assessments) < 5 or len(recent_assessments) < 3:
            return (
                "INSUFFICIENT_DATA",
                "Insufficient historical assessment periods to establish unit-level anomaly baseline.",
                [],
                {
                    "recent_count": len(recent_assessments),
                    "baseline_count": len(baseline_assessments),
                    "min_required": 5
                }
            )

        # Calculate High/Critical proportion in baseline vs recent
        def get_high_crit_pct(ass_list: List[StressAssessment]) -> float:
            if not ass_list:
                return 0.0
            count = sum(1 for a in ass_list if (a.risk_score is not None and float(a.risk_score) >= 70.0))
            return round((count / len(ass_list)) * 100.0, 1)

        baseline_high_crit_pct = get_high_crit_pct(baseline_assessments)
        recent_high_crit_pct = get_high_crit_pct(recent_assessments)
        high_crit_delta = round(recent_high_crit_pct - baseline_high_crit_pct, 1)

        unit_signals: List[Dict[str, Any]] = []
        obs_date_str = now.strftime("%Y-%m-%d")

        # Anomaly G: UNIT_LEVEL_ANOMALY (Sudden spike in elevated strain)
        if high_crit_delta >= 15.0:
            sev = "URGENT_REVIEW" if recent_high_crit_pct >= 40.0 else "ATTENTION"
            unit_signals.append({
                "anomaly_type": "UNIT_LEVEL_ANOMALY",
                "severity": sev,
                "confidence": "HIGH",
                "evidence": {
                    "reason": "Sudden increase in unit-wide High/Critical risk proportion",
                    "baseline_metric": "unit_high_critical_percentage",
                    "baseline_value": baseline_high_crit_pct,
                    "current_value": recent_high_crit_pct,
                    "delta": high_crit_delta,
                    "sample_count": len(baseline_assessments),
                    "recent_records": len(recent_assessments),
                    "window_description": "Past 14 days vs prior 45-day baseline",
                    "explanation": (
                        f"An unusual increase in unit welfare indicators (+{high_crit_delta}%) was detected. "
                        f"High/Critical proportion rose from {baseline_high_crit_pct}% to {recent_high_crit_pct}%. "
                        f"Command-level workload and rotation review recommended."
                    )
                }
            })

        # Persistence & Deduplication
        active_unit_anomalies: List[WelfareAnomaly] = []
        if persist:
            for sig in unit_signals:
                anom = cls._persist_or_update_anomaly(
                    db=db,
                    personnel_id=None,
                    scope_type="UNIT",
                    scope_battalion=scope_battalion,
                    scope_location=scope_location,
                    anomaly_type=sig["anomaly_type"],
                    severity=sig["severity"],
                    confidence=sig["confidence"],
                    baseline_sample_count=len(baseline_assessments),
                    obs_date_str=obs_date_str,
                    evidence_dict=sig["evidence"],
                    current_ts=now
                )
                active_unit_anomalies.append(anom)
            db.commit()
        else:
            for sig in unit_signals:
                ephem = WelfareAnomaly(
                    personnel_id=None,
                    scope_type="UNIT",
                    scope_battalion=scope_battalion,
                    scope_location=scope_location,
                    anomaly_type=sig["anomaly_type"],
                    severity=sig["severity"],
                    status="DETECTED",
                    confidence=sig["confidence"],
                    baseline_sample_count=len(baseline_assessments),
                    detected_at=now,
                    evidence_json=json.dumps(sig["evidence"]),
                    dedup_hash="ephemeral_unit"
                )
                active_unit_anomalies.append(ephem)

        status_code = "DETECTED" if active_unit_anomalies else "NO_ANOMALY"
        msg = (
            f"{len(active_unit_anomalies)} unit-level welfare anomaly signal(s) flagged."
            if active_unit_anomalies
            else "Unit-wide welfare indicators remain within expected historical baseline variation."
        )

        data_quality = {
            "total_authorized": total_authorized,
            "baseline_assessments": len(baseline_assessments),
            "recent_assessments": len(recent_assessments),
            "baseline_high_crit_pct": baseline_high_crit_pct,
            "recent_high_crit_pct": recent_high_crit_pct,
        }

        return status_code, msg, active_unit_anomalies, data_quality

    # =========================================================================
    # 3. DEDUPLICATION HELPER
    # =========================================================================
    @classmethod
    def _persist_or_update_anomaly(
        cls,
        db: Session,
        personnel_id: Optional[int],
        scope_type: str,
        scope_battalion: Optional[str],
        scope_location: Optional[str],
        anomaly_type: str,
        severity: str,
        confidence: str,
        baseline_sample_count: int,
        obs_date_str: str,
        evidence_dict: Dict[str, Any],
        current_ts: datetime
    ) -> WelfareAnomaly:
        """
        Ensures strict deduplication:
        Checks for an existing open anomaly (DETECTED, ACKNOWLEDGED, UNDER_REVIEW)
        with matching subject and anomaly_type. If found, updates evidence instead of inserting duplicate!
        """
        raw_key = f"{scope_type}:{personnel_id or 0}:{scope_battalion or ''}:{scope_location or ''}:{anomaly_type}:{obs_date_str}"
        dedup_hash = hashlib.sha256(raw_key.encode("utf-8")).hexdigest()

        # Check existing active anomaly
        query = db.query(WelfareAnomaly).filter(
            WelfareAnomaly.scope_type == scope_type,
            WelfareAnomaly.anomaly_type == anomaly_type,
            WelfareAnomaly.status.in_(["DETECTED", "ACKNOWLEDGED", "UNDER_REVIEW"])
        )
        if personnel_id:
            query = query.filter(WelfareAnomaly.personnel_id == personnel_id)
        else:
            query = query.filter(
                func.lower(WelfareAnomaly.scope_battalion) == (scope_battalion or "").lower(),
                func.lower(WelfareAnomaly.scope_location) == (scope_location or "").lower()
            )

        existing = query.first()
        if existing:
            # Update evidence and timestamp, preserve current lifecycle status
            existing.evidence_json = json.dumps(evidence_dict)
            existing.severity = severity
            existing.confidence = confidence
            existing.baseline_sample_count = baseline_sample_count
            existing.updated_at = current_ts
            return existing

        # Create new anomaly
        new_anomaly = WelfareAnomaly(
            personnel_id=personnel_id,
            scope_type=scope_type,
            scope_battalion=scope_battalion,
            scope_location=scope_location,
            anomaly_type=anomaly_type,
            severity=severity,
            status="DETECTED",
            confidence=confidence,
            baseline_sample_count=baseline_sample_count,
            detected_at=current_ts,
            observation_window_end=current_ts,
            evidence_json=json.dumps(evidence_dict),
            dedup_hash=dedup_hash
        )
        db.add(new_anomaly)
        db.flush()

        # Phase 37 Integration: If severity is high and individual scope, link or enrich WelfareAlert
        if personnel_id and severity in ["ATTENTION", "URGENT_REVIEW"]:
            try:
                cls._integrate_with_phase37_alerts(db, new_anomaly, evidence_dict)
            except Exception as e:
                logger.warning(f"Optional Phase 37 alert integration notice: {e}")

        return new_anomaly

    @classmethod
    def _integrate_with_phase37_alerts(
        cls,
        db: Session,
        anomaly: WelfareAnomaly,
        evidence: Dict[str, Any]
    ):
        """
        Integrates high-severity anomalies with Phase 37 WelfareAlerts.
        Records source = 'PHASE_39_ANOMALY' in metadata.
        """
        # Check if an open alert exists for this personnel
        existing_alert = (
            db.query(WelfareAlert)
            .filter(
                WelfareAlert.personnel_id == anomaly.personnel_id,
                WelfareAlert.status.in_(["OPEN", "ACKNOWLEDGED", "UNDER_REVIEW"])
            )
            .first()
        )
        if existing_alert:
            anomaly.associated_alert_id = existing_alert.id
        else:
            alert_sev = "URGENT_REVIEW" if anomaly.severity == "URGENT_REVIEW" else "HIGH_PRIORITY"
            new_alert = WelfareAlert(
                personnel_id=anomaly.personnel_id,
                alert_type=anomaly.anomaly_type,
                severity=alert_sev,
                status="OPEN",
                trigger_reason=f"Phase 39 Anomaly: {evidence.get('reason', anomaly.anomaly_type)}"
            )
            db.add(new_alert)
            db.flush()
            anomaly.associated_alert_id = new_alert.id

    # =========================================================================
    # 4. LIFECYCLE MANAGEMENT
    # =========================================================================
    VALID_REVIEW_DECISIONS = {
        "CONTINUE_MONITORING",
        "CONTACT_PERSONNEL",
        "OFFER_WELFARE_SUPPORT",
        "REVIEW_DUTY_WORKLOAD",
        "SCHEDULE_FOLLOW_UP",
        "CREATE_WELFARE_CASE",
        "RESOLVE_SIGNAL",
    }

    @classmethod
    def acknowledge_anomaly(cls, anomaly_id: int, current_user: User, db: Session) -> WelfareAnomaly:
        anom = db.query(WelfareAnomaly).filter(WelfareAnomaly.id == anomaly_id).first()
        if not anom:
            raise ValueError(f"Anomaly ID {anomaly_id} not found.")

        cls._check_anomaly_scope(anom, current_user, db)

        if anom.status in ["RESOLVED", "DISMISSED"]:
            raise ValueError(f"Cannot acknowledge anomaly with terminal status '{anom.status}'.")

        prev_status = anom.status
        anom.status = "ACKNOWLEDGED"
        anom.acknowledged_at = datetime.now(timezone.utc)
        anom.acknowledged_by = current_user.id

        audit = WelfareAnomalyAudit(
            anomaly_id=anom.id,
            action="ANOMALY_ACKNOWLEDGED",
            actor_id=current_user.id,
            previous_status=prev_status,
            new_status="ACKNOWLEDGED",
            timestamp=datetime.now(timezone.utc),
            details=None,
        )
        db.add(audit)
        db.commit()
        db.refresh(anom)
        return anom

    @classmethod
    def review_anomaly(
        cls,
        anomaly_id: int,
        current_user: User,
        db: Session,
        decision: Optional[str] = None,
        notes: Optional[str] = None,
    ) -> WelfareAnomaly:
        anom = db.query(WelfareAnomaly).filter(WelfareAnomaly.id == anomaly_id).first()
        if not anom:
            raise ValueError(f"Anomaly ID {anomaly_id} not found.")

        cls._check_anomaly_scope(anom, current_user, db)

        if anom.status in ["RESOLVED", "DISMISSED"]:
            raise ValueError(f"Cannot start review on anomaly with terminal status '{anom.status}'.")

        clean_decision = None
        if decision:
            norm_decision = decision.strip().upper()
            if norm_decision not in cls.VALID_REVIEW_DECISIONS:
                raise ValueError(
                    f"Invalid review decision '{decision}'. Must be one of: {', '.join(sorted(cls.VALID_REVIEW_DECISIONS))}"
                )
            clean_decision = norm_decision

        clean_notes = None
        if notes:
            clean_notes = re.sub(r'<[^>]*>', '', notes.strip())
            if not clean_notes:
                clean_notes = None

        prev_status = anom.status
        anom.status = "UNDER_REVIEW"
        anom.review_decision = clean_decision
        anom.review_notes = clean_notes
        anom.reviewed_at = datetime.now(timezone.utc)
        anom.reviewed_by = current_user.id

        audit = WelfareAnomalyAudit(
            anomaly_id=anom.id,
            action="ANOMALY_REVIEWED",
            actor_id=current_user.id,
            previous_status=prev_status,
            new_status="UNDER_REVIEW",
            timestamp=datetime.now(timezone.utc),
            details=json.dumps({"decision": clean_decision, "notes": clean_notes}),
        )
        db.add(audit)
        db.commit()
        db.refresh(anom)
        return anom

    @classmethod
    def resolve_anomaly(
        cls,
        anomaly_id: int,
        resolution_notes: str,
        current_user: User,
        db: Session,
        notify_personnel: bool = True,
        custom_message: Optional[str] = None,
    ) -> WelfareAnomaly:
        anom = db.query(WelfareAnomaly).filter(WelfareAnomaly.id == anomaly_id).first()
        if not anom:
            raise ValueError(f"Anomaly ID {anomaly_id} not found.")

        cls._check_anomaly_scope(anom, current_user, db)

        if anom.status in ["RESOLVED", "DISMISSED"]:
            raise ValueError(f"Cannot resolve anomaly: Signal is already in terminal status '{anom.status}'.")

        clean_notes = re.sub(r'<[^>]*>', '', (resolution_notes or "").strip())
        if not clean_notes or len(clean_notes) < 3:
            raise ValueError("A meaningful resolution note (at least 3 characters) is required to resolve a signal.")

        clean_custom_msg = None
        if custom_message and custom_message.strip():
            clean_custom_msg = re.sub(r'<[^>]*>', '', custom_message.strip())

        prev_status = anom.status
        anom.status = "RESOLVED"
        anom.resolved_at = datetime.now(timezone.utc)
        anom.resolved_by = current_user.id
        anom.resolution_notes = clean_notes

        audit = WelfareAnomalyAudit(
            anomaly_id=anom.id,
            action="ANOMALY_RESOLVED",
            actor_id=current_user.id,
            previous_status=prev_status,
            new_status="RESOLVED",
            timestamp=datetime.now(timezone.utc),
            details=json.dumps({
                "resolution_notes": clean_notes,
                "notify_personnel": notify_personnel,
                "custom_message": clean_custom_msg,
            }),
        )
        db.add(audit)

        # Dispatch Jawan Welfare Notification if requested and individual personnel is targeted
        if notify_personnel and anom.personnel_id:
            from services.welfare_notification_service import WelfareNotificationService

            default_msg = (
                "Your recent welfare signal has been reviewed and resolved by your welfare officer. "
                "Please continue to monitor your wellbeing and contact your welfare officer if you need support."
            )
            final_msg = clean_custom_msg if clean_custom_msg else default_msg

            try:
                WelfareNotificationService.create_notification(
                    db=db,
                    recipient_personnel_id=anom.personnel_id,
                    title="Welfare Signal Resolved",
                    message=final_msg,
                    notification_type="WELFARE_SUPPORT",
                    priority="STANDARD",
                    source_type="ANOMALY",
                    source_id=anom.id,
                    action_url=None,
                    created_by=current_user.id,
                    metadata={
                        "anomaly_id": anom.id,
                        "anomaly_type": anom.anomaly_type,
                        "severity": anom.severity,
                        "resolver_username": current_user.username,
                    },
                )
            except Exception as e:
                db.rollback()
                logger.error(f"Failed to create resolution notification for Anomaly #{anom.id}: {e}")
                raise ValueError(f"Resolution failed because notification could not be created: {str(e)}")

        db.commit()
        db.refresh(anom)
        return anom

    @classmethod
    def get_anomaly_audits(cls, anomaly_id: int, current_user: User, db: Session) -> List[WelfareAnomalyAudit]:
        anom = db.query(WelfareAnomaly).filter(WelfareAnomaly.id == anomaly_id).first()
        if not anom:
            raise ValueError(f"Anomaly ID {anomaly_id} not found.")

        cls._check_anomaly_scope(anom, current_user, db)
        return (
            db.query(WelfareAnomalyAudit)
            .filter(WelfareAnomalyAudit.anomaly_id == anomaly_id)
            .order_by(desc(WelfareAnomalyAudit.timestamp))
            .all()
        )

    @classmethod
    def _check_anomaly_scope(cls, anom: WelfareAnomaly, current_user: User, db: Session):
        """Enforces RBAC and Battalion + Location isolation on anomaly actions."""
        if current_user.role == "admin":
            return

        if current_user.role in ["officer", "welfare"]:
            user_bat = (current_user.battalion or "").strip().lower()
            user_loc = (current_user.location or "").strip().lower()

            target_bat = (anom.scope_battalion or "").strip().lower()
            target_loc = (anom.scope_location or "").strip().lower()

            if anom.personnel_id and not target_bat:
                p = db.query(Personnel).filter(Personnel.id == anom.personnel_id).first()
                if p:
                    target_bat = (p.battalion or "").strip().lower()
                    target_loc = (p.location or "").strip().lower()

            if user_bat and target_bat and user_bat != target_bat:
                raise PermissionError("Access denied: Anomaly is outside your assigned Battalion scope.")
            if user_loc and target_loc and user_loc != target_loc:
                raise PermissionError("Access denied: Anomaly is outside your assigned Location scope.")
            return

        raise PermissionError("Access denied: Unauthorized role.")
