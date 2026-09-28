import os
import json
import hashlib
from datetime import datetime, timedelta, timezone
from typing import Optional, List, Dict, Any, Tuple
import numpy as np
from sqlalchemy.orm import Session
from sqlalchemy import and_, desc, func

from core.config import logger
from db.models.user import User
from db.models.personnel import Personnel
from db.models.assessment import StressAssessment
from db.models.alert import WelfareAlert, WelfareIntervention
from db.models.anomaly import WelfareAnomaly
from db.models.recommendation import WelfareRecommendation
from db.models.telemetry import WearableTelemetry
from services.longitudinal_analytics_service import LongitudinalAnalyticsService

ANALYTICS_MIN_GROUP_SIZE = int(os.getenv("ANALYTICS_MIN_GROUP_SIZE", "5"))

class WelfareRecommendationService:
    """
    Phase 40: Welfare Recommendation & Support Engine.
    Provides explainable, non-punitive decision support suggestions to authorized human reviewers.
    Consumes existing signals from:
      - Phase 34 authoritative risk engine (risk_score, risk_category, stress_level, key_factors)
      - Phase 36 longitudinal trend intelligence (direction, slope, persistence, baseline deviation)
      - Phase 37 welfare alerts (HIGH_CURRENT_RISK, PERSISTENT_HIGH_RISK, etc.)
      - Phase 39 welfare anomalies (WORKLOAD_ANOMALY, SLEEP_RECOVERY_ANOMALY, etc.)
      - HRMS & telemetry operational indicators (duty hours, night shifts, sleep duration)

    CORE PRINCIPLES:
      - Decision support for human reviewers: never automated punitive or personnel action.
      - No new risk score: uses existing authoritative Phase 34 scores and signals.
      - Explainable & traceable: every recommendation carries triggers, evidence, and source signals.
      - Deterministic deduplication: prevents recommendation spam.
      - Direct integration with Phase 37 interventions upon explicit human review decision.
    """

    # Supported explainable recommendation types
    TYPES = [
        "RECOVERY_REVIEW",
        "DUTY_SCHEDULE_REVIEW",
        "WELFARE_FOLLOW_UP",
        "VOLUNTARY_WELLNESS_CHECKIN",
        "SUPPORT_RESOURCE_REFERRAL",
        "FOLLOW_UP_ASSESSMENT",
        "CONTINUE_MONITORING",
        "HUMAN_REVIEW",
    ]

    # Valid lifecycle states
    STATUSES = [
        "SUGGESTED",
        "ACKNOWLEDGED",
        "ACCEPTED",
        "DEFERRED",
        "DISMISSED",
        "ACTIONED",
        "EXPIRED",
        "RESOLVED",
    ]

    @classmethod
    def evaluate_and_generate_recommendations(
        cls,
        personnel: Personnel,
        db: Session,
        current_assessment: Optional[StressAssessment] = None,
        reference_time: Optional[datetime] = None,
        persist: bool = True
    ) -> Tuple[str, str, List[WelfareRecommendation]]:
        """
        Evaluates existing welfare signals across Phase 34, 36, 37, 39 and operational factors
        to generate explainable, non-punitive support suggestions.
        Returns: (status_code, message, list_of_recommendations)
        """
        now = reference_time or datetime.now(timezone.utc)
        obs_date_str = now.strftime("%Y-%m-%d")

        # 1. Fetch assessments history chronologically
        assessments = (
            db.query(StressAssessment)
            .filter(StressAssessment.personnel_id == personnel.id)
            .order_by(StressAssessment.assessment_timestamp.asc(), StressAssessment.id.asc())
            .all()
        )

        if not assessments and not current_assessment:
            return (
                "INSUFFICIENT_DATA",
                "No assessment records found for this personnel. Recommendations cannot be evaluated.",
                []
            )

        if current_assessment and current_assessment not in assessments:
            assessments.append(current_assessment)

        active_assessment = current_assessment or assessments[-1]

        # 2. Extract Phase 34 authoritative risk indicators safely
        risk_score: Optional[float] = None
        if active_assessment.risk_score is not None:
            try:
                s = float(active_assessment.risk_score)
                if not (np.isnan(s) or np.isinf(s)):
                    risk_score = s
            except (ValueError, TypeError):
                pass

        risk_category = None
        top_risk_factors: List[str] = []
        protective_factors: List[str] = []

        if active_assessment.key_factors:
            try:
                kf_data = json.loads(active_assessment.key_factors)
                if isinstance(kf_data, dict):
                    risk_category = kf_data.get("risk_category")
                    top_risk_factors = kf_data.get("top_risk_factors", kf_data.get("key_factors", []))
                    protective_factors = kf_data.get("protective_factors", [])
                elif isinstance(kf_data, list):
                    top_risk_factors = [str(x) for x in kf_data]
            except Exception:
                top_risk_factors = [active_assessment.key_factors]

        if not risk_category:
            risk_category = active_assessment.stress_level or "Low"

        stress_level = active_assessment.stress_level or "Low"
        risk_priority = active_assessment.risk_priority or "Routine"

        # 3. Extract Phase 36 longitudinal trend intelligence
        trend_data = LongitudinalAnalyticsService.calculate_longitudinal_trend(
            personnel.id, assessments, reference_time=now
        )
        trend_direction = trend_data.get("trend", {}).get("direction", "INSUFFICIENT_DATA")
        trend_slope = trend_data.get("trend", {}).get("slope")
        trend_acceleration = trend_data.get("trend", {}).get("acceleration", "INSUFFICIENT_DATA")
        persistent_elevated_risk = trend_data.get("history", {}).get("persistent_elevated_risk", False)
        consecutive_elevated = trend_data.get("history", {}).get("consecutive_elevated_assessments", 0)
        current_deviation = trend_data.get("baseline", {}).get("current_deviation")

        # 4. Extract Phase 37 active alerts
        active_alerts = (
            db.query(WelfareAlert)
            .filter(
                WelfareAlert.personnel_id == personnel.id,
                WelfareAlert.status.in_(["OPEN", "ACKNOWLEDGED", "UNDER_REVIEW", "INTERVENTION_PLANNED", "FOLLOW_UP"])
            )
            .all()
        )
        active_alert_types = [a.alert_type for a in active_alerts]
        has_urgent_alert = any(a.severity == "URGENT_REVIEW" for a in active_alerts)
        primary_alert_id = active_alerts[0].id if active_alerts else None

        # 5. Extract Phase 39 active anomalies
        active_anomalies = (
            db.query(WelfareAnomaly)
            .filter(
                WelfareAnomaly.personnel_id == personnel.id,
                WelfareAnomaly.status.in_(["DETECTED", "ACKNOWLEDGED", "UNDER_REVIEW"])
            )
            .all()
        )
        active_anomaly_types = [anom.anomaly_type for anom in active_anomalies]
        has_urgent_anomaly = any(anom.severity == "URGENT_REVIEW" for anom in active_anomalies)
        primary_anomaly_id = active_anomalies[0].id if active_anomalies else None

        # 6. Extract operational factors
        duty_hours = personnel.duty_hours_per_week if personnel.duty_hours_per_week is not None else 40.0
        night_shifts = personnel.night_shifts_per_month if personnel.night_shifts_per_month is not None else 0
        consecutive_days = personnel.consecutive_duty_days if personnel.consecutive_duty_days is not None else 0
        leave_gap = personnel.leave_gap_days if personnel.leave_gap_days is not None else 0
        operational_exposure = personnel.operational_exposure or "Moderate"
        deployment_days = personnel.deployment_days or 0

        # Query wearable telemetry if available
        telemetry_records = (
            db.query(WearableTelemetry)
            .filter(WearableTelemetry.personnel_id == personnel.id)
            .order_by(WearableTelemetry.recorded_at.desc())
            .limit(5)
            .all()
        )
        recent_sleep_hours = None
        if telemetry_records:
            sleep_vals = [t.sleep_duration_hours for t in telemetry_records if t.sleep_duration_hours is not None]
            if sleep_vals:
                recent_sleep_hours = round(float(np.mean(sleep_vals)), 1)

        # ---------------------------------------------------------------------
        # CANDIDATE RECOMMENDATION GENERATION
        # ---------------------------------------------------------------------
        candidates: List[Dict[str, Any]] = []

        # Check for ambiguous / conflicting signals first (Type 8: HUMAN_REVIEW)
        is_conflicting = False
        conflict_reasons = []
        if risk_category in ["Low", "Moderate"] and (has_urgent_alert or has_urgent_anomaly):
            is_conflicting = True
            conflict_reasons.append("Low overall assessment score despite active urgent anomaly or welfare alert.")
        elif risk_category in ["High", "Critical"] and trend_direction == "IMPROVING" and len(protective_factors) >= 2:
            is_conflicting = True
            conflict_reasons.append("Elevated current risk category but longitudinal trend shows robust improvement with active protective factors.")

        if is_conflicting:
            candidates.append({
                "type": "HUMAN_REVIEW",
                "priority": "HIGH",
                "title": "Human Decision Review",
                "description": "Available welfare signals display divergent or conflicting patterns that require contextual human judgment.",
                "reason": " ".join(conflict_reasons),
                "recommendation_text": "Consider human review of the available welfare signals before determining any further support.",
                "review_window": "Within 48–72 hours",
                "confidence": "HIGH",
                "source_signals": ["Phase 34 risk category", "Phase 36 trend direction", "Phase 37/39 alerts and anomalies"],
                "trigger": "CONFLICTING_WELFARE_SIGNALS",
                "metrics": {
                    "risk_score": risk_score,
                    "risk_category": risk_category,
                    "trend_direction": trend_direction,
                    "active_alerts_count": len(active_alerts),
                    "active_anomalies_count": len(active_anomalies)
                },
                "linked_alert_id": primary_alert_id,
                "linked_anomaly_id": primary_anomaly_id,
            })

        # Type 1: RECOVERY_REVIEW
        has_workload_strain = (
            duty_hours >= 60.0
            or (recent_sleep_hours is not None and recent_sleep_hours <= 5.0)
            or consecutive_days >= 10
            or "WORKLOAD_ANOMALY" in active_anomaly_types
            or "SLEEP_RECOVERY_ANOMALY" in active_anomaly_types
        )
        if has_workload_strain:
            is_urgent_rec = (duty_hours >= 72.0 or consecutive_days >= 14 or (recent_sleep_hours is not None and recent_sleep_hours <= 4.0))
            prio = "HIGH" if is_urgent_rec else "MEDIUM"
            window = "Within 3–5 days" if prio == "HIGH" else "Within 7 days"
            
            evidence_metrics = {"duty_hours_per_week": duty_hours, "consecutive_duty_days": consecutive_days}
            if recent_sleep_hours is not None:
                evidence_metrics["recent_avg_sleep_hours"] = recent_sleep_hours

            srcs = ["Operational roster"]
            if "WORKLOAD_ANOMALY" in active_anomaly_types:
                srcs.append("Phase 39 Workload Anomaly")
            if "SLEEP_RECOVERY_ANOMALY" in active_anomaly_types:
                srcs.append("Phase 39 Sleep Anomaly")
            if risk_score is not None:
                srcs.append("Phase 34 Assessment")

            candidates.append({
                "type": "RECOVERY_REVIEW",
                "priority": prio,
                "title": "Workload & Recovery Review",
                "description": "Telemetry and roster indicators reflect prolonged operational pacing and compressed recovery intervals.",
                "reason": (
                    f"Operational parameters ({duty_hours} hrs/week, {consecutive_days} consecutive duty days"
                    f"{f', {recent_sleep_hours} hrs sleep' if recent_sleep_hours is not None else ''}) "
                    f"indicate that reviewing recovery spacing would support sustained operational readiness."
                ),
                "recommendation_text": "Consider reviewing workload and recovery opportunities.",
                "review_window": window,
                "confidence": "HIGH" if len(telemetry_records) >= 3 else "MEDIUM",
                "source_signals": srcs,
                "trigger": "ELEVATED_WORKLOAD_RECOVERY_STRAIN",
                "metrics": evidence_metrics,
                "linked_alert_id": primary_alert_id,
                "linked_anomaly_id": primary_anomaly_id,
            })

        # Type 2: DUTY_SCHEDULE_REVIEW
        has_schedule_strain = (
            night_shifts >= 6
            or consecutive_days >= 12
            or "NIGHT_SHIFT_PATTERN_CHANGE" in active_anomaly_types
        )
        if has_schedule_strain:
            prio = "HIGH" if (night_shifts >= 8 or consecutive_days >= 14) else "MEDIUM"
            window = "Within 5–7 days"
            candidates.append({
                "type": "DUTY_SCHEDULE_REVIEW",
                "priority": prio,
                "title": "Duty Schedule & Rotation Review",
                "description": "Shift rotation telemetry reflects concentrated night duty allocations or extended consecutive duty periods.",
                "reason": (
                    f"Roster records indicate {night_shifts} night shifts per month and {consecutive_days} consecutive duty days. "
                    f"Reviewing shift rotation and rest intervals is recommended."
                ),
                "recommendation_text": "Consider reviewing duty schedule, consecutive duty periods, and recovery spacing.",
                "review_window": window,
                "confidence": "HIGH",
                "source_signals": ["Roster schedule parameters", "Phase 39 Anomaly Detection"],
                "trigger": "CONCENTRATED_SHIFT_SCHEDULE_STRAIN",
                "metrics": {
                    "night_shifts_per_month": night_shifts,
                    "consecutive_duty_days": consecutive_days
                },
                "linked_alert_id": primary_alert_id,
                "linked_anomaly_id": primary_anomaly_id,
            })

        # Type 3: WELFARE_FOLLOW_UP
        has_persistent_or_high = (
            persistent_elevated_risk
            or trend_direction == "WORSENING"
            or risk_category in ["Critical", "High"]
            or stress_level in ["Critical", "High"]
            or "HIGH_CURRENT_RISK" in active_alert_types
            or "PERSISTENT_HIGH_RISK" in active_alert_types
        )
        if has_persistent_or_high:
            is_critical = (risk_category == "Critical" or stress_level == "Critical" or has_urgent_alert)
            prio = "URGENT" if is_critical else "HIGH"
            window = "Within 24–48 hours" if prio == "URGENT" else "Within 3–5 days"
            
            candidates.append({
                "type": "WELFARE_FOLLOW_UP",
                "priority": prio,
                "title": "Supportive Welfare Follow-Up",
                "description": "Longitudinal welfare tracking indicates persistent or worsening stress signals that benefit from supportive human check-in.",
                "reason": (
                    f"Authoritative risk category is {risk_category} (Score: {risk_score if risk_score is not None else 'N/A'}), "
                    f"with longitudinal trend '{trend_direction}' over {len(assessments)} assessments."
                ),
                "recommendation_text": "Consider a welfare follow-up with the individual.",
                "review_window": window,
                "confidence": "HIGH",
                "source_signals": ["Phase 34 Authoritative Risk", "Phase 36 Longitudinal Trend", "Phase 37 Alerts"],
                "trigger": "PERSISTENT_OR_ACUTE_WELFARE_STRAIN",
                "metrics": {
                    "risk_score": risk_score,
                    "risk_category": risk_category,
                    "trend_direction": trend_direction,
                    "persistent_elevated_risk": persistent_elevated_risk,
                    "consecutive_elevated_assessments": consecutive_elevated
                },
                "linked_alert_id": primary_alert_id,
                "linked_anomaly_id": primary_anomaly_id,
            })

        # Type 4: VOLUNTARY_WELLNESS_CHECKIN
        # Suggested for moderate/elevated risk without acute crisis, or baseline shift
        has_moderate_or_baseline_shift = (
            risk_category == "Elevated"
            or stress_level == "Medium"
            or (current_deviation is not None and current_deviation >= 8.0)
        )
        if has_moderate_or_baseline_shift:
            candidates.append({
                "type": "VOLUNTARY_WELLNESS_CHECKIN",
                "priority": "MEDIUM",
                "title": "Voluntary Wellness Check-In",
                "description": "Observation of subtle shifts relative to personal historical baseline suggests offering a supportive conversation.",
                "reason": (
                    f"Current risk index is {risk_category} (Score: {risk_score if risk_score is not None else 'N/A'}), "
                    f"with baseline deviation of {f'+{current_deviation} pts' if current_deviation else 'mild divergence'}."
                ),
                "recommendation_text": "Consider offering a voluntary wellness check-in and an opportunity to discuss current concerns.",
                "review_window": "Within 7–14 days",
                "confidence": "HIGH" if current_deviation is not None else "MEDIUM",
                "source_signals": ["Phase 36 Personal Baseline", "Phase 34 Assessment"],
                "trigger": "BASELINE_DIVERGENCE_MODERATE_STRAIN",
                "metrics": {
                    "risk_score": risk_score,
                    "risk_category": risk_category,
                    "current_deviation": current_deviation
                },
                "linked_alert_id": primary_alert_id,
                "linked_anomaly_id": primary_anomaly_id,
            })

        # Type 5: SUPPORT_RESOURCE_REFERRAL
        has_extended_posting_or_leave_gap = (
            leave_gap >= 60
            or (operational_exposure == "High" and deployment_days >= 90)
            or any("family" in str(f).lower() or "leave" in str(f).lower() or "isolation" in str(f).lower() for f in top_risk_factors)
        )
        if has_extended_posting_or_leave_gap:
            candidates.append({
                "type": "SUPPORT_RESOURCE_REFERRAL",
                "priority": "MEDIUM",
                "title": "Support Resource Information",
                "description": "Deployment duration and leave gap parameters suggest sharing available unit welfare and family support resources.",
                "reason": (
                    f"Operational parameters reflect leave gap of {leave_gap} days and deployment duration of {deployment_days} days. "
                    f"Sharing supportive welfare resources fosters proactive well-being."
                ),
                "recommendation_text": "Consider informing the individual about available welfare and support resources.",
                "review_window": "Within 14 days",
                "confidence": "HIGH",
                "source_signals": ["HRMS Service Records", "Phase 34 Operational Factors"],
                "trigger": "EXTENDED_DEPLOYMENT_LEAVE_GAP",
                "metrics": {
                    "leave_gap_days": leave_gap,
                    "deployment_days": deployment_days,
                    "operational_exposure": operational_exposure
                },
                "linked_alert_id": primary_alert_id,
                "linked_anomaly_id": primary_anomaly_id,
            })

        # Type 6: FOLLOW_UP_ASSESSMENT
        has_velocity_or_accelerating = (
            trend_acceleration == "ACCELERATING"
            or (trend_slope is not None and abs(trend_slope) >= 1.5)
            or "RAPID_ACCELERATION" in active_anomaly_types
        )
        if has_velocity_or_accelerating:
            candidates.append({
                "type": "FOLLOW_UP_ASSESSMENT",
                "priority": "MEDIUM" if trend_acceleration != "ACCELERATING" else "HIGH",
                "title": "Scheduled Follow-Up Assessment",
                "description": "Longitudinal velocity indicators reflect rapid trend movement that benefits from scheduled reassessment.",
                "reason": (
                    f"Longitudinal acceleration is '{trend_acceleration}' (Slope: {trend_slope if trend_slope is not None else 'N/A'} pts/day). "
                    f"Reassessment allows tracking trajectory response."
                ),
                "recommendation_text": "Consider scheduling a follow-up assessment to observe response and trajectory.",
                "review_window": "Within 3–5 days" if trend_acceleration == "ACCELERATING" else "Within 7 days",
                "confidence": "HIGH",
                "source_signals": ["Phase 36 Acceleration Tracking", "Phase 39 Velocity Anomaly"],
                "trigger": "RAPID_SCORE_TRAJECTORY_CHANGE",
                "metrics": {
                    "trend_slope": trend_slope,
                    "trend_acceleration": trend_acceleration,
                    "trend_direction": trend_direction
                },
                "linked_alert_id": primary_alert_id,
                "linked_anomaly_id": primary_anomaly_id,
            })

        # Type 7: CONTINUE_MONITORING
        # If no concerning strain patterns are identified, or risk is low/moderate and stable
        if not candidates:
            candidates.append({
                "type": "CONTINUE_MONITORING",
                "priority": "LOW",
                "title": "Routine Welfare Monitoring",
                "description": "Current welfare telemetry and operational indicators remain within expected baseline variation.",
                "reason": (
                    f"Assessment score is {risk_score if risk_score is not None else 'N/A'} ({risk_category}). "
                    f"No anomalous strain or persistent elevation detected."
                ),
                "recommendation_text": "Continue routine welfare monitoring and reassess if conditions change.",
                "review_window": "Routine schedule (14–30 days)",
                "confidence": "HIGH",
                "source_signals": ["Phase 34 Baseline Assessment", "Phase 36 Stable History"],
                "trigger": "STABLE_ROUTINE_PROFILE",
                "metrics": {
                    "risk_score": risk_score,
                    "risk_category": risk_category,
                    "trend_direction": trend_direction
                },
                "linked_alert_id": None,
                "linked_anomaly_id": None,
            })

        # ---------------------------------------------------------------------
        # PERSISTENCE & DEDUPLICATION
        # ---------------------------------------------------------------------
        generated_recommendations: List[WelfareRecommendation] = []

        if persist:
            for item in candidates:
                rec = cls._persist_or_update_recommendation(
                    db=db,
                    personnel_id=personnel.id,
                    assessment_id=active_assessment.id if active_assessment else None,
                    recommendation_type=item["type"],
                    priority=item["priority"],
                    title=item["title"],
                    description=item["description"],
                    reason=item["reason"],
                    recommendation_text=item["recommendation_text"],
                    review_window=item["review_window"],
                    confidence=item["confidence"],
                    source_signals=item["source_signals"],
                    trigger=item["trigger"],
                    metrics=item["metrics"],
                    linked_alert_id=item.get("linked_alert_id"),
                    linked_anomaly_id=item.get("linked_anomaly_id"),
                    obs_date_str=obs_date_str,
                    current_ts=now
                )
                generated_recommendations.append(rec)
            db.commit()
        else:
            # Ephemeral models for read-only preview/evaluation
            for item in candidates:
                ephem = WelfareRecommendation(
                    personnel_id=personnel.id,
                    assessment_id=active_assessment.id if active_assessment else None,
                    recommendation_type=item["type"],
                    recommendation_text=item["recommendation_text"],
                    title=item["title"],
                    description=item["description"],
                    reason=item["reason"],
                    priority=item["priority"],
                    status="SUGGESTED",
                    confidence=item["confidence"],
                    evidence_json=json.dumps({
                        "trigger": item["trigger"],
                        "reason": item["reason"],
                        "metrics": item["metrics"],
                        "explanation": item["description"]
                    }),
                    source_signals_json=json.dumps(item["source_signals"]),
                    recommended_review_window=item["review_window"],
                    linked_alert_id=item.get("linked_alert_id"),
                    linked_anomaly_id=item.get("linked_anomaly_id"),
                    dedup_hash="ephemeral",
                    created_at=now,
                    updated_at=now
                )
                generated_recommendations.append(ephem)

        status_code = "GENERATED" if generated_recommendations else "NONE"
        msg = f"{len(generated_recommendations)} supportive welfare recommendation(s) prepared for human review."
        return status_code, msg, generated_recommendations

    @classmethod
    def _persist_or_update_recommendation(
        cls,
        db: Session,
        personnel_id: int,
        assessment_id: Optional[int],
        recommendation_type: str,
        priority: str,
        title: str,
        description: str,
        reason: str,
        recommendation_text: str,
        review_window: str,
        confidence: str,
        source_signals: List[str],
        trigger: str,
        metrics: Dict[str, Any],
        linked_alert_id: Optional[int],
        linked_anomaly_id: Optional[int],
        obs_date_str: str,
        current_ts: datetime
    ) -> WelfareRecommendation:
        """
        Deduplication and persistence helper.
        Checks for an existing open recommendation (SUGGESTED, ACKNOWLEDGED, DEFERRED)
        matching this personnel and recommendation_type.
        If found, updates evidence, signals, review window, and priority rather than duplicating!
        """
        raw_key = f"{personnel_id}:{recommendation_type}:{obs_date_str}"
        dedup_hash = hashlib.sha256(raw_key.encode("utf-8")).hexdigest()

        evidence_dict = {
            "trigger": trigger,
            "reason": reason,
            "metrics": metrics,
            "explanation": description
        }

        # Check existing active recommendation
        existing = (
            db.query(WelfareRecommendation)
            .filter(
                WelfareRecommendation.personnel_id == personnel_id,
                WelfareRecommendation.recommendation_type == recommendation_type,
                WelfareRecommendation.status.in_(["SUGGESTED", "ACKNOWLEDGED", "DEFERRED"])
            )
            .first()
        )

        if existing:
            # Update existing recommendation
            existing.title = title
            existing.description = description
            existing.reason = reason
            existing.recommendation_text = recommendation_text
            existing.priority = priority
            existing.confidence = confidence
            existing.recommended_review_window = review_window
            existing.evidence_json = json.dumps(evidence_dict)
            existing.source_signals_json = json.dumps(source_signals)
            existing.assessment_id = assessment_id or existing.assessment_id
            if linked_alert_id:
                existing.linked_alert_id = linked_alert_id
            if linked_anomaly_id:
                existing.linked_anomaly_id = linked_anomaly_id
            existing.updated_at = current_ts
            return existing

        # Create new recommendation
        new_rec = WelfareRecommendation(
            personnel_id=personnel_id,
            assessment_id=assessment_id,
            recommendation_type=recommendation_type,
            recommendation_text=recommendation_text,
            title=title,
            description=description,
            reason=reason,
            priority=priority,
            status="SUGGESTED",
            confidence=confidence,
            dedup_hash=dedup_hash,
            evidence_json=json.dumps(evidence_dict),
            source_signals_json=json.dumps(source_signals),
            recommended_review_window=review_window,
            linked_alert_id=linked_alert_id,
            linked_anomaly_id=linked_anomaly_id,
            created_at=current_ts,
            updated_at=current_ts
        )
        db.add(new_rec)
        db.flush()
        return new_rec

    # =========================================================================
    # LIFECYCLE MANAGEMENT
    # =========================================================================
    @classmethod
    def acknowledge_recommendation(
        cls,
        db: Session,
        recommendation_id: int,
        user: User,
        notes: Optional[str] = None
    ) -> WelfareRecommendation:
        rec = db.query(WelfareRecommendation).filter(WelfareRecommendation.id == recommendation_id).first()
        if not rec:
            raise ValueError(f"Recommendation with ID {recommendation_id} not found.")

        rec.status = "ACKNOWLEDGED"
        rec.acknowledged_at = datetime.now(timezone.utc)
        rec.acknowledged_by = user.id
        if notes:
            rec.action_notes = f"Acknowledged with notes: {notes}"
        rec.updated_at = datetime.now(timezone.utc)
        db.commit()
        db.refresh(rec)
        return rec

    @classmethod
    def accept_recommendation(
        cls,
        db: Session,
        recommendation_id: int,
        user: User,
        create_intervention: bool = False,
        intervention_type: Optional[str] = None,
        scheduled_date: Optional[datetime] = None,
        notes: Optional[str] = None
    ) -> Tuple[WelfareRecommendation, Optional[WelfareIntervention]]:
        """
        Accepts recommendation and optionally initiates a Phase 37 WelfareIntervention.
        """
        rec = db.query(WelfareRecommendation).filter(WelfareRecommendation.id == recommendation_id).first()
        if not rec:
            raise ValueError(f"Recommendation with ID {recommendation_id} not found.")

        rec.status = "ACCEPTED"
        rec.actioned_at = datetime.now(timezone.utc)
        rec.actioned_by = user.id
        rec.action_notes = notes or "Recommendation accepted by authorized reviewer."
        rec.updated_at = datetime.now(timezone.utc)

        intervention = None
        if create_intervention:
            # Map recommendation type to Phase 37 intervention type safely
            itype = intervention_type or cls._map_rec_type_to_intervention_type(rec.recommendation_type)
            pdate = scheduled_date or (datetime.now(timezone.utc) + timedelta(days=3))

            # Phase 37 requires alert_id on WelfareIntervention; find or create alert link
            alert_id = rec.linked_alert_id
            if not alert_id:
                # Find an existing open alert for personnel, or create one for tracking
                existing_alert = (
                    db.query(WelfareAlert)
                    .filter(WelfareAlert.personnel_id == rec.personnel_id)
                    .order_by(WelfareAlert.created_at.desc())
                    .first()
                )
                if existing_alert:
                    alert_id = existing_alert.id
                else:
                    new_alert = WelfareAlert(
                        personnel_id=rec.personnel_id,
                        alert_type=rec.recommendation_type,
                        severity=rec.priority,
                        trigger_reason=f"Generated via accepted welfare recommendation #{rec.id}",
                        status="INTERVENTION_PLANNED"
                    )
                    db.add(new_alert)
                    db.flush()
                    alert_id = new_alert.id
                rec.linked_alert_id = alert_id

            intervention = WelfareIntervention(
                alert_id=alert_id,
                personnel_id=rec.personnel_id,
                intervention_type=itype,
                planned_date=pdate,
                status="PLANNED",
                notes=notes or f"Initiated from accepted recommendation: {rec.title}",
                created_by=user.id,
                created_at=datetime.now(timezone.utc)
            )
            db.add(intervention)
            db.flush()
            rec.linked_intervention_id = intervention.id

        db.commit()
        db.refresh(rec)
        return rec, intervention

    @classmethod
    def defer_recommendation(
        cls,
        db: Session,
        recommendation_id: int,
        user: User,
        defer_days: int = 7,
        notes: Optional[str] = None
    ) -> WelfareRecommendation:
        rec = db.query(WelfareRecommendation).filter(WelfareRecommendation.id == recommendation_id).first()
        if not rec:
            raise ValueError(f"Recommendation with ID {recommendation_id} not found.")

        rec.status = "DEFERRED"
        rec.actioned_at = datetime.now(timezone.utc)
        rec.actioned_by = user.id
        rec.recommended_review_window = f"Deferred for {defer_days} days"
        rec.action_notes = notes or f"Deferred review for {defer_days} days."
        rec.updated_at = datetime.now(timezone.utc)
        db.commit()
        db.refresh(rec)
        return rec

    @classmethod
    def dismiss_recommendation(
        cls,
        db: Session,
        recommendation_id: int,
        user: User,
        reason: str
    ) -> WelfareRecommendation:
        rec = db.query(WelfareRecommendation).filter(WelfareRecommendation.id == recommendation_id).first()
        if not rec:
            raise ValueError(f"Recommendation with ID {recommendation_id} not found.")

        rec.status = "DISMISSED"
        rec.actioned_at = datetime.now(timezone.utc)
        rec.actioned_by = user.id
        rec.action_notes = f"Dismissed: {reason}"
        rec.updated_at = datetime.now(timezone.utc)
        db.commit()
        db.refresh(rec)
        return rec

    @classmethod
    def action_recommendation(
        cls,
        db: Session,
        recommendation_id: int,
        user: User,
        action_notes: str
    ) -> WelfareRecommendation:
        rec = db.query(WelfareRecommendation).filter(WelfareRecommendation.id == recommendation_id).first()
        if not rec:
            raise ValueError(f"Recommendation with ID {recommendation_id} not found.")

        rec.status = "ACTIONED"
        rec.actioned_at = datetime.now(timezone.utc)
        rec.actioned_by = user.id
        rec.action_notes = action_notes
        rec.updated_at = datetime.now(timezone.utc)
        db.commit()
        db.refresh(rec)
        return rec

    @classmethod
    def _map_rec_type_to_intervention_type(cls, rec_type: str) -> str:
        mapping = {
            "RECOVERY_REVIEW": "MANDATORY_REST_INTERVAL",
            "DUTY_SCHEDULE_REVIEW": "DUTY_ROTATION",
            "WELFARE_FOLLOW_UP": "COUNSELING_SESSION",
            "VOLUNTARY_WELLNESS_CHECKIN": "WELLNESS_CHECKIN",
            "SUPPORT_RESOURCE_REFERRAL": "PEER_SUPPORT",
            "FOLLOW_UP_ASSESSMENT": "WELLNESS_CHECKIN",
            "HUMAN_REVIEW": "COUNSELING_SESSION",
        }
        return mapping.get(rec_type, "WELLNESS_CHECKIN")

    # =========================================================================
    # RBAC & QUERY HELPERS
    # =========================================================================
    @classmethod
    def verify_access_and_get_personnel(cls, personnel_id: int, user: User, db: Session) -> Personnel:
        """
        Enforces strict RBAC and Anti-IDOR protections:
        - Personnel role: can only access their own record.
        - Officer / Welfare: can only access personnel in their battalion/location.
        - Admin: can access all.
        """
        personnel = db.query(Personnel).filter(Personnel.id == personnel_id).first()
        if not personnel:
            raise LookupError(f"Personnel record #{personnel_id} not found.")

        if user.role == "personnel":
            if user.personnel_id != personnel_id:
                logger.warning(
                    f"IDOR Violation attempt: Personnel user #{user.id} ({user.username}) "
                    f"attempted to access recommendations for personnel #{personnel_id}"
                )
                raise PermissionError("Access forbidden: Personnel can only access their own welfare recommendations.")

        elif user.role in ["officer", "welfare"]:
            if user.battalion and personnel.battalion:
                if user.battalion.strip().lower() != personnel.battalion.strip().lower():
                    logger.warning(
                        f"Scope Violation: User #{user.id} ({user.battalion}) "
                        f"attempted to access personnel #{personnel_id} in ({personnel.battalion})"
                    )
                    raise PermissionError(f"Access forbidden: Cross-battalion access restricted to {user.battalion}.")
            if user.location and personnel.location:
                if user.location.strip().lower() != personnel.location.strip().lower():
                    logger.warning(
                        f"Scope Violation: User #{user.id} ({user.location}) "
                        f"attempted to access personnel #{personnel_id} in ({personnel.location})"
                    )
                    raise PermissionError(f"Access forbidden: Cross-location access restricted to {user.location}.")

        return personnel
