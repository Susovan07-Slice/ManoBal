import json
from datetime import datetime, timezone, timedelta
from typing import Optional, List, Dict, Any, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import desc, func

from core.config import logger
from db.models.user import User
from db.models.personnel import Personnel
from db.models.assessment import StressAssessment
from db.models.alert import WelfareAlert, WelfareIntervention
from db.models.anomaly import WelfareAnomaly
from db.models.recommendation import WelfareRecommendation
from db.models.welfare_followup import WelfareFollowup
from services.longitudinal_analytics_service import LongitudinalAnalyticsService

ANALYTICS_MIN_GROUP_SIZE = 5

class UnifiedWelfareIntelligenceService:
    """
    Phase 42: Unified Welfare Intelligence & Decision-Support Service.
    Aggregates authoritative intelligence from Phases 34 through 41.
    
    CRITICAL ARCHITECTURAL CONSTRAINTS:
      - Does NOT calculate a new risk score, composite score, or rank personnel.
      - Phase 34 remains sole authoritative risk engine.
      - Phase 36 provides longitudinal analytics.
      - Phase 37 owns alert and intervention lifecycles.
      - Phase 39 owns anomaly detection.
      - Phase 40 owns support recommendations.
      - Phase 41 owns follow-ups and outcome tracking.
      - Strictly preserves small-group k-anonymity privacy (k >= 5).
      - Enforces strict RBAC and Anti-IDOR boundaries.
    """

    @staticmethod
    def _format_relative_time(dt: Optional[datetime], now_utc: datetime) -> str:
        if not dt:
            return "Unavailable"
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        
        diff = now_utc - dt
        seconds = diff.total_seconds()
        if seconds < 0:
            return "Just now"
        if seconds < 60:
            return "Just now"
        if seconds < 3600:
            mins = int(seconds // 60)
            return f"{mins} minute{'s' if mins > 1 else ''} ago"
        if seconds < 86400:
            hrs = int(seconds // 3600)
            return f"{hrs} hour{'s' if hrs > 1 else ''} ago"
        if diff.days == 1:
            return "Yesterday"
        if diff.days < 60:
            return f"{diff.days} days ago"
        if diff.days < 365:
            months = int(diff.days // 30)
            return f"{months} month{'s' if months > 1 else ''} ago"
        years = int(diff.days // 365)
        return f"{years} year{'s' if years > 1 else ''} ago"

    @classmethod
    def verify_access_and_get_personnel(
        cls, personnel_id: int, user: User, db: Session
    ) -> Personnel:
        """
        Enforces strict RBAC and Anti-IDOR:
        - Personnel (Jawan): can ONLY access their own records (HTTP 403 otherwise).
        - Officers / Welfare: can only access personnel within their assigned Battalion / Location.
        - Admin: full access across all battalions.
        """
        personnel = db.query(Personnel).filter(Personnel.id == personnel_id).first()
        if not personnel:
            raise LookupError(f"Personnel ID {personnel_id} not found.")

        role = (getattr(user, "role", "") or "").lower()

        # 1. Jawan role anti-IDOR
        if role == "personnel":
            user_p_id = getattr(user, "personnel_id", None)
            if user_p_id != personnel_id:
                logger.warning(
                    f"Anti-IDOR Violation: User '{user.username}' (Personnel ID: {user_p_id}) "
                    f"attempted unauthorized access to Personnel ID {personnel_id}."
                )
                raise PermissionError("Personnel can only access their own welfare intelligence snapshot.")
            return personnel

        # 2. Officer / Welfare organizational scoping
        if role in ["officer", "welfare", "doctor", "psychologist"]:
            user_bat = getattr(user, "battalion", None)
            user_loc = getattr(user, "location", None)

            if user_bat and personnel.battalion:
                if user_bat.strip().lower() != personnel.battalion.strip().lower():
                    logger.warning(
                        f"Scope Violation: Officer '{user.username}' (Battalion: {user_bat}) "
                        f"attempted cross-battalion access to Personnel ID {personnel_id} (Battalion: {personnel.battalion})."
                    )
                    raise PermissionError(
                        f"Cross-battalion access restricted. Officer battalion '{user_bat}' "
                        f"does not match personnel battalion '{personnel.battalion}'."
                    )

            if user_loc and personnel.location:
                if user_loc.strip().lower() != personnel.location.strip().lower():
                    logger.warning(
                        f"Scope Violation: Officer '{user.username}' (Location: {user_loc}) "
                        f"attempted cross-location access to Personnel ID {personnel_id} (Location: {personnel.location})."
                    )
                    raise PermissionError(
                        f"Cross-location access restricted. Officer location '{user_loc}' "
                        f"does not match personnel location '{personnel.location}'."
                    )
            return personnel

        # 3. Admins have unrestricted access
        if role in ["admin", "superadmin"]:
            return personnel

        # Unknown or unhandled role
        raise PermissionError("Insufficient permissions to view welfare intelligence snapshot.")

    @classmethod
    def get_personnel_welfare_snapshot(
        cls,
        db: Session,
        current_user: User,
        personnel_id: int,
        reference_time: Optional[datetime] = None,
    ) -> Dict[str, Any]:
        """
        Assembles a comprehensive, explainable welfare snapshot for a single personnel member.
        Consumes Phase 34 risk, Phase 36 trends, Phase 37 alerts/interventions,
        Phase 39 anomalies, Phase 40 recommendations, and Phase 41 follow-up outcomes.
        """
        personnel = cls.verify_access_and_get_personnel(personnel_id, current_user, db)
        now_utc = reference_time or datetime.now(timezone.utc)
        if now_utc.tzinfo is None:
            now_utc = now_utc.replace(tzinfo=timezone.utc)

        # 1. Phase 34: Authoritative Risk Assessments
        assessments: List[StressAssessment] = (
            db.query(StressAssessment)
            .filter(StressAssessment.personnel_id == personnel_id)
            .order_by(StressAssessment.assessment_timestamp.asc(), StressAssessment.id.asc())
            .all()
        )

        latest_assessment: Optional[StressAssessment] = assessments[-1] if assessments else None

        current_risk: Dict[str, Any] = {
            "risk_score": None,
            "stress_level": None,
            "risk_priority": None,
            "assessment_timestamp": None,
            "confidence": "UNAVAILABLE",
            "data_sufficiency": "INSUFFICIENT_DATA",
            "key_factors": [],
            "notice": "Phase 34 authoritative risk inference; administrative welfare monitoring, non-diagnostic.",
        }

        if latest_assessment and latest_assessment.risk_score is not None:
            ts = latest_assessment.assessment_timestamp
            if ts and ts.tzinfo is None:
                ts = ts.replace(tzinfo=timezone.utc)

            factors = []
            if latest_assessment.key_factors:
                try:
                    parsed = json.loads(latest_assessment.key_factors)
                    if isinstance(parsed, list):
                        factors = parsed
                    elif isinstance(parsed, dict):
                        factors = parsed.get("top_risk_factors", parsed.get("key_factors", []))
                except Exception:
                    factors = [str(latest_assessment.key_factors)]

            current_risk = {
                "risk_score": round(float(latest_assessment.risk_score), 1),
                "stress_level": latest_assessment.stress_level,
                "risk_priority": latest_assessment.risk_priority,
                "assessment_timestamp": ts,
                "confidence": "HIGH" if len(assessments) >= 3 else ("MEDIUM" if len(assessments) >= 2 else "LOW"),
                "data_sufficiency": "SUFFICIENT",
                "key_factors": factors,
                "notice": "Phase 34 authoritative risk inference; administrative welfare monitoring, non-diagnostic.",
            }

        # 2. Phase 36: Longitudinal Trend
        trend_raw = LongitudinalAnalyticsService.calculate_longitudinal_trend(
            personnel_id=personnel_id,
            assessments=assessments,
            reference_time=now_utc,
        )

        t_data = trend_raw.get("trend") or {}
        h_data = trend_raw.get("history") or {}
        b_data = trend_raw.get("baseline") or {}

        persistence_str = "PERSISTENT_ELEVATED" if h_data.get("persistent_elevated_risk") else "NOT_PERSISTENT"
        if h_data.get("data_sufficiency") == "INSUFFICIENT_DATA":
            persistence_str = "INSUFFICIENT_DATA"

        trend_dir = t_data.get("direction", "INSUFFICIENT_DATA")
        data_suff = h_data.get("data_sufficiency", "INSUFFICIENT_DATA")
        base_mean = b_data.get("historical_mean")

        trend: Dict[str, Any] = {
            "trend_direction": trend_dir,
            "trend_slope": t_data.get("slope"),
            "persistence": persistence_str,
            "acceleration": t_data.get("acceleration", "INSUFFICIENT_DATA"),
            "personal_baseline_score": base_mean,
            "personal_baseline_category": LongitudinalAnalyticsService._get_v2_category(base_mean) if base_mean is not None else None,
            "score_change": t_data.get("score_change"),
            "data_sufficiency": data_suff,
            "explanation": f"Trend derived from {h_data.get('assessment_count', 0)} historical assessments." if h_data.get("assessment_count", 0) > 0 else "Insufficient assessment history available.",
        }

        # 3. Phase 37: Alerts & Interventions
        alerts_all: List[WelfareAlert] = (
            db.query(WelfareAlert)
            .filter(WelfareAlert.personnel_id == personnel_id)
            .order_by(WelfareAlert.created_at.desc())
            .all()
        )
        active_alerts: List[Dict[str, Any]] = []
        for al in alerts_all:
            if al.status in ["OPEN", "ACKNOWLEDGED", "UNDER_REVIEW", "INTERVENTION_PLANNED", "FOLLOW_UP"]:
                active_alerts.append({
                    "id": al.id,
                    "alert_type": al.alert_type,
                    "severity": al.severity,
                    "status": al.status,
                    "trigger_reason": al.trigger_reason,
                    "created_at": al.created_at or now_utc,
                    "linked_intervention_id": al.interventions[0].id if al.interventions else None,
                })

        interventions_all: List[WelfareIntervention] = (
            db.query(WelfareIntervention)
            .filter(WelfareIntervention.personnel_id == personnel_id)
            .order_by(WelfareIntervention.created_at.desc())
            .all()
        )
        active_interventions: List[Dict[str, Any]] = []
        for inv in interventions_all:
            active_interventions.append({
                "id": inv.id,
                "alert_id": inv.alert_id,
                "intervention_type": inv.intervention_type,
                "status": inv.status,
                "planned_date": inv.planned_date,
                "completed_at": inv.completed_at,
                "follow_up_date": inv.follow_up_date,
                "notes": inv.notes,
            })

        # 4. Phase 39: Anomalies
        anomalies_all: List[WelfareAnomaly] = (
            db.query(WelfareAnomaly)
            .filter(WelfareAnomaly.personnel_id == personnel_id)
            .order_by(WelfareAnomaly.detected_at.desc())
            .all()
        )
        active_anomalies: List[Dict[str, Any]] = []
        for an in anomalies_all:
            if an.status in ["DETECTED", "ACKNOWLEDGED", "UNDER_REVIEW"]:
                evidence = {}
                if an.evidence_json:
                    try:
                        evidence = json.loads(an.evidence_json)
                    except Exception:
                        evidence = {"raw": str(an.evidence_json)}
                active_anomalies.append({
                    "id": an.id,
                    "anomaly_type": an.anomaly_type,
                    "severity": an.severity,
                    "status": an.status,
                    "confidence": an.confidence,
                    "detected_at": an.detected_at or now_utc,
                    "explanation": evidence.get("explanation", f"Anomaly detected in {an.anomaly_type}"),
                })

        # 5. Phase 40: Recommendations
        recs_all: List[WelfareRecommendation] = (
            db.query(WelfareRecommendation)
            .filter(WelfareRecommendation.personnel_id == personnel_id)
            .order_by(WelfareRecommendation.created_at.desc())
            .all()
        )
        active_recommendations: List[Dict[str, Any]] = []
        for rc in recs_all:
            if rc.status in ["SUGGESTED", "ACKNOWLEDGED", "pending"]:
                active_recommendations.append({
                    "id": rc.id,
                    "recommendation_type": rc.recommendation_type,
                    "title": rc.title or rc.recommendation_text,
                    "priority": rc.priority,
                    "status": rc.status,
                    "recommended_review_window": rc.recommended_review_window,
                    "reason": rc.reason,
                    "created_at": rc.created_at or now_utc,
                    "is_system_suggestion": True,
                    "system_vs_human_notice": "System support suggestion only; requires authorized human review and decision.",
                })

        # 6. Phase 41: Follow-Ups & Outcomes
        followups_all: List[WelfareFollowup] = (
            db.query(WelfareFollowup)
            .filter(WelfareFollowup.personnel_id == personnel_id)
            .order_by(WelfareFollowup.created_at.desc())
            .all()
        )
        followup_signals: List[Dict[str, Any]] = []
        for f in followups_all:
            is_overdue = False
            if f.status in ["PENDING", "SCHEDULED"] and f.due_date:
                dd = f.due_date
                if dd.tzinfo is None:
                    dd = dd.replace(tzinfo=timezone.utc)
                is_overdue = dd < now_utc

            ev = {}
            if f.evidence_json:
                try:
                    ev = json.loads(f.evidence_json)
                except Exception:
                    ev = {}

            followup_signals.append({
                "id": f.id,
                "followup_type": f.followup_type,
                "status": f.status,
                "scheduled_at": f.scheduled_at,
                "due_date": f.due_date,
                "is_overdue": is_overdue,
                "outcome_status": f.outcome_status or "INSUFFICIENT_DATA",
                "score_delta": ev.get("score_delta"),
                "explanation": ev.get("explanation"),
            })

        # 7. Data Freshness Calculation
        last_ass_dt = latest_assessment.assessment_timestamp if latest_assessment else None
        last_trend_dt = latest_assessment.assessment_timestamp if (latest_assessment and len(assessments) >= 2) else None
        last_al_dt = alerts_all[0].created_at if alerts_all else None
        last_an_dt = anomalies_all[0].detected_at if anomalies_all else None
        last_rc_dt = recs_all[0].created_at if recs_all else None
        last_fu_dt = followups_all[0].created_at if followups_all else None

        is_stale = False
        if last_ass_dt:
            if last_ass_dt.tzinfo is None:
                last_ass_dt = last_ass_dt.replace(tzinfo=timezone.utc)
            is_stale = (now_utc - last_ass_dt).days > 30

        overall_freshness = "INSUFFICIENT_DATA"
        if latest_assessment:
            overall_freshness = "STALE" if is_stale else "FRESH"

        data_freshness = {
            "last_assessment_timestamp": last_ass_dt,
            "last_assessment_relative": cls._format_relative_time(last_ass_dt, now_utc),
            "last_trend_timestamp": last_trend_dt,
            "last_trend_relative": cls._format_relative_time(last_trend_dt, now_utc),
            "last_alert_timestamp": last_al_dt,
            "last_alert_relative": cls._format_relative_time(last_al_dt, now_utc) if last_al_dt else "None recorded",
            "last_anomaly_timestamp": last_an_dt,
            "last_anomaly_relative": cls._format_relative_time(last_an_dt, now_utc) if last_an_dt else "None recorded",
            "last_recommendation_timestamp": last_rc_dt,
            "last_recommendation_relative": cls._format_relative_time(last_rc_dt, now_utc) if last_rc_dt else "None recorded",
            "last_followup_timestamp": last_fu_dt,
            "last_followup_relative": cls._format_relative_time(last_fu_dt, now_utc) if last_fu_dt else "None recorded",
            "is_stale": is_stale,
            "overall_freshness_status": overall_freshness,
        }

        # 8. Human Review Indicators (Rule-Based, Non-Scored, Explainable)
        review_reasons: List[str] = []
        review_level: str = "NO_ACTIVE_REVIEW_SIGNAL"

        # Check Insufficient Data first
        if current_risk["data_sufficiency"] == "INSUFFICIENT_DATA":
            review_level = "INSUFFICIENT_DATA"
            review_reasons.append("No valid current assessment available; routine check-in recommended to establish baseline.")
        else:
            # Check REVIEW criteria
            urgent_alerts = [a for a in active_alerts if a["severity"] in ["HIGH_PRIORITY", "URGENT_REVIEW"]]
            urgent_anomalies = [a for a in active_anomalies if a["severity"] == "URGENT_REVIEW"]
            overdue_followups = [f for f in followup_signals if f["is_overdue"]]
            worsening_followup_outcomes = [f for f in followup_signals if f["status"] == "COMPLETED" and f["outcome_status"] in ["WORSENING", "PERSISTENT_CONCERN"]]
            urgent_recs = [r for r in active_recommendations if r["priority"] == "URGENT"]

            if urgent_alerts:
                review_reasons.append(f"Active {urgent_alerts[0]['severity']} welfare alert ({urgent_alerts[0]['alert_type']})")
            if urgent_anomalies:
                review_reasons.append(f"Active URGENT_REVIEW anomaly detected ({urgent_anomalies[0]['anomaly_type']})")
            if trend["trend_direction"] == "WORSENING":
                review_reasons.append(f"Longitudinal trend is worsening ({trend.get('score_change', 0):+.1f} pts)")
            if overdue_followups:
                review_reasons.append(f"{len(overdue_followups)} scheduled welfare follow-up(s) currently overdue")
            if worsening_followup_outcomes:
                review_reasons.append(f"Recent follow-up outcome indicates persistent concern or deterioration ({worsening_followup_outcomes[0]['outcome_status']})")
            if urgent_recs:
                review_reasons.append(f"High-priority supportive recommendation pending human decision ({urgent_recs[0]['title']})")

            if review_reasons:
                review_level = "REVIEW"
            else:
                # Check MONITOR criteria
                monitor_reasons: List[str] = []
                if active_alerts:
                    monitor_reasons.append(f"Active alert: {active_alerts[0]['alert_type']} ({active_alerts[0]['severity']})")
                if active_anomalies:
                    monitor_reasons.append(f"Active anomaly: {active_anomalies[0]['anomaly_type']}")
                if active_recommendations:
                    monitor_reasons.append(f"Pending support recommendation: {active_recommendations[0]['title']}")
                if active_interventions:
                    monitor_reasons.append(f"Planned welfare support intervention in progress ({active_interventions[0]['intervention_type']})")
                if current_risk["stress_level"] in ["High", "Medium"]:
                    monitor_reasons.append(f"Current assessment shows {current_risk['stress_level']} strain level")
                if is_stale:
                    monitor_reasons.append("Assessment telemetry is older than 30 days (stale data)")

                if monitor_reasons:
                    review_level = "MONITOR"
                    review_reasons = monitor_reasons
                else:
                    review_level = "NO_ACTIVE_REVIEW_SIGNAL"
                    review_reasons.append("All welfare indicators within standard operational parameters; no pending actions.")

        human_review_indicator = {
            "review_level": review_level,
            "reasons": review_reasons,
            "disclaimer": "Qualitative human decision-support guidance only; this is NOT a numerical score, priority score, or fitness-for-duty ranking.",
        }

        # 9. Chronological Unified Timeline
        timeline: List[Dict[str, Any]] = []

        # Add Assessments (Phase 34)
        for a in assessments:
            ats = a.assessment_timestamp
            if ats and ats.tzinfo is None:
                ats = ats.replace(tzinfo=timezone.utc)
            if ats:
                timeline.append({
                    "timestamp": ats,
                    "relative_time": cls._format_relative_time(ats, now_utc),
                    "phase": "Phase 34",
                    "event_type": "ASSESSMENT",
                    "title": f"Stress Assessment #{a.id}",
                    "status": "COMPLETED",
                    "severity_or_priority": a.risk_priority,
                    "summary": f"Risk Score: {a.risk_score:.1f}, Category: {a.stress_level}, Priority: {a.risk_priority}",
                    "evidence": {"risk_score": a.risk_score, "category": a.stress_level},
                })

        # Add Alerts (Phase 37)
        for al in alerts_all:
            al_ts = al.created_at
            if al_ts and al_ts.tzinfo is None:
                al_ts = al_ts.replace(tzinfo=timezone.utc)
            if al_ts:
                timeline.append({
                    "timestamp": al_ts,
                    "relative_time": cls._format_relative_time(al_ts, now_utc),
                    "phase": "Phase 37",
                    "event_type": "ALERT",
                    "title": f"Welfare Alert ({al.alert_type})",
                    "status": al.status,
                    "severity_or_priority": al.severity,
                    "summary": al.trigger_reason or f"Alert triggered with severity {al.severity}",
                    "evidence": {"alert_type": al.alert_type, "severity": al.severity},
                })

        # Add Anomalies (Phase 39)
        for an in anomalies_all:
            an_ts = an.detected_at
            if an_ts and an_ts.tzinfo is None:
                an_ts = an_ts.replace(tzinfo=timezone.utc)
            if an_ts:
                timeline.append({
                    "timestamp": an_ts,
                    "relative_time": cls._format_relative_time(an_ts, now_utc),
                    "phase": "Phase 39",
                    "event_type": "ANOMALY",
                    "title": f"Early Warning ({an.anomaly_type})",
                    "status": an.status,
                    "severity_or_priority": an.severity,
                    "summary": f"Early warning anomaly identified with {an.confidence} confidence",
                    "evidence": {"anomaly_type": an.anomaly_type, "severity": an.severity},
                })

        # Add Recommendations (Phase 40)
        for rc in recs_all:
            rc_ts = rc.created_at
            if rc_ts and rc_ts.tzinfo is None:
                rc_ts = rc_ts.replace(tzinfo=timezone.utc)
            if rc_ts:
                timeline.append({
                    "timestamp": rc_ts,
                    "relative_time": cls._format_relative_time(rc_ts, now_utc),
                    "phase": "Phase 40",
                    "event_type": "RECOMMENDATION",
                    "title": rc.title or f"Recommendation ({rc.recommendation_type})",
                    "status": rc.status,
                    "severity_or_priority": rc.priority,
                    "summary": rc.reason or rc.recommendation_text,
                    "evidence": {"type": rc.recommendation_type, "priority": rc.priority},
                })

        # Add Interventions (Phase 37)
        for inv in interventions_all:
            inv_ts = inv.created_at
            if inv_ts and inv_ts.tzinfo is None:
                inv_ts = inv_ts.replace(tzinfo=timezone.utc)
            if inv_ts:
                timeline.append({
                    "timestamp": inv_ts,
                    "relative_time": cls._format_relative_time(inv_ts, now_utc),
                    "phase": "Phase 37",
                    "event_type": "INTERVENTION",
                    "title": f"Welfare Intervention ({inv.intervention_type})",
                    "status": inv.status,
                    "severity_or_priority": None,
                    "summary": f"Support intervention status: {inv.status}",
                    "evidence": {"intervention_type": inv.intervention_type, "status": inv.status},
                })

        # Add Follow-ups (Phase 41)
        for fu in followups_all:
            fu_ts = fu.created_at
            if fu_ts and fu_ts.tzinfo is None:
                fu_ts = fu_ts.replace(tzinfo=timezone.utc)
            if fu_ts:
                timeline.append({
                    "timestamp": fu_ts,
                    "relative_time": cls._format_relative_time(fu_ts, now_utc),
                    "phase": "Phase 41",
                    "event_type": "FOLLOWUP",
                    "title": f"Welfare Follow-up ({fu.followup_type})",
                    "status": fu.status,
                    "severity_or_priority": fu.outcome_status,
                    "summary": f"Follow-up status: {fu.status}, Outcome observation: {fu.outcome_status}",
                    "evidence": {"followup_type": fu.followup_type, "outcome_status": fu.outcome_status},
                })

        # Sort timeline strictly descending (newest first)
        timeline.sort(key=lambda x: x["timestamp"], reverse=True)

        return {
            "personnel_id": personnel.id,
            "personnel_code": personnel.personnel_code,
            "name": personnel.name,
            "department": personnel.department,
            "battalion": personnel.battalion,
            "location": personnel.location,
            "job_role": personnel.job_role,
            "current_risk": current_risk,
            "trend": trend,
            "alerts": active_alerts,
            "anomalies": active_anomalies,
            "recommendations": active_recommendations,
            "interventions": active_interventions,
            "followups": followup_signals,
            "data_freshness": data_freshness,
            "data_sufficiency": current_risk["data_sufficiency"],
            "human_review_indicator": human_review_indicator,
            "timeline": timeline,
            "disclaimer": (
                "Phase 42 integrates authoritative welfare intelligence across Phases 34–41 for human decision-support. "
                "It does NOT calculate a composite risk score, diagnose medical conditions, assign disciplinary action, "
                "or replace commander clinical or operational judgement."
            ),
        }

    @classmethod
    def get_unit_welfare_intelligence(
        cls,
        db: Session,
        current_user: User,
        battalion: Optional[str] = None,
        location: Optional[str] = None,
        time_filter: str = "30d",
        reference_time: Optional[datetime] = None,
    ) -> Dict[str, Any]:
        """
        Computes aggregate unit-level welfare intelligence for commander decision-support.
        Optimized with batched queries to prevent N+1 query overhead.
        Strictly enforces k-anonymity privacy (k >= 5) and organizational scoping.
        """
        role = (getattr(current_user, "role", "") or "").lower()
        now_utc = reference_time or datetime.now(timezone.utc)
        if now_utc.tzinfo is None:
            now_utc = now_utc.replace(tzinfo=timezone.utc)

        # 1. Organizational Scoping & RBAC
        effective_bat = battalion
        effective_loc = location

        if role in ["officer", "welfare", "doctor", "psychologist"]:
            user_bat = getattr(current_user, "battalion", None)
            user_loc = getattr(current_user, "location", None)

            if battalion and user_bat and battalion.strip().lower() != user_bat.strip().lower():
                raise PermissionError(
                    f"Access denied: cannot query battalion '{battalion}' outside assigned battalion '{user_bat}'."
                )
            if location and user_loc and location.strip().lower() != user_loc.strip().lower():
                raise PermissionError(
                    f"Access denied: cannot query location '{location}' outside assigned location '{user_loc}'."
                )

            effective_bat = user_bat
            effective_loc = user_loc
        elif role not in ["admin", "superadmin"]:
            raise PermissionError("Insufficient permissions to view unit-level welfare intelligence.")

        # 2. Fetch Personnel in Scope
        p_query = db.query(Personnel)
        if effective_bat:
            p_query = p_query.filter(Personnel.battalion == effective_bat)
        if effective_loc:
            p_query = p_query.filter(Personnel.location == effective_loc)

        # Non-ranked deterministic order (by ID)
        personnel_list: List[Personnel] = p_query.order_by(Personnel.id.asc()).all()
        total_in_scope = len(personnel_list)

        base_response = {
            "scope_battalion": effective_bat,
            "scope_location": effective_loc,
            "total_personnel_in_scope": total_in_scope,
            "privacy_threshold": ANALYTICS_MIN_GROUP_SIZE,
            "data_suppressed": False,
            "suppression_reason": None,
            "unit_overview": {},
            "support_workflow": {},
            "data_quality": {},
            "human_review_summary": {},
            "personnel_cards": [],
            "disclaimer": (
                "Phase 42 aggregates authoritative welfare intelligence across Phases 34–41 for commander decision-support. "
                "It enforces small-group k-anonymity privacy (k >= 5) and does NOT rank personnel, compute composite scores, "
                "or automate personnel decisions."
            ),
        }

        # 3. Small-Group Privacy Suppression (k < 5)
        if total_in_scope < ANALYTICS_MIN_GROUP_SIZE:
            base_response["data_suppressed"] = True
            base_response["suppression_reason"] = (
                f"Data suppressed to protect individual privacy (population {total_in_scope} < threshold {ANALYTICS_MIN_GROUP_SIZE})"
            )
            base_response["unit_overview"] = {
                "personnel_monitored": 0,
                "risk_distribution": {"Low": 0, "Medium": 0, "High": 0, "Unavailable": 0},
                "trend_distribution": {"Improving": 0, "Stable": 0, "Worsening": 0, "Insufficient Data": 0},
                "active_alerts_total": 0,
                "active_anomalies_total": 0,
                "open_recommendations_total": 0,
                "open_interventions_total": 0,
                "followups_total": 0,
                "outcome_distribution": {"IMPROVED": 0, "STABLE": 0, "PERSISTENT_CONCERN": 0, "WORSENING": 0, "INSUFFICIENT_DATA": 0},
            }
            base_response["support_workflow"] = {
                "recommendations_count": 0,
                "human_decisions_count": 0,
                "interventions_active_count": 0,
                "followups_completed_count": 0,
                "outcomes_observed_count": 0,
            }
            base_response["data_quality"] = {
                "valid_assessments_count": 0,
                "stale_data_count": 0,
                "insufficient_data_count": 0,
            }
            base_response["human_review_summary"] = {
                "review_needed_count": 0,
                "monitor_count": 0,
                "no_signal_count": 0,
                "insufficient_data_count": 0,
            }
            base_response["personnel_cards"] = []
            return base_response

        # 4. Batched Database Ingestion (O(1) roundtrips, no N+1 queries)
        p_ids = [p.id for p in personnel_list]

        # A. All assessments for personnel in scope
        all_assessments: List[StressAssessment] = (
            db.query(StressAssessment)
            .filter(StressAssessment.personnel_id.in_(p_ids))
            .order_by(StressAssessment.assessment_timestamp.asc(), StressAssessment.id.asc())
            .all()
        )
        assessments_by_pid: Dict[int, List[StressAssessment]] = {pid: [] for pid in p_ids}
        for a in all_assessments:
            assessments_by_pid[a.personnel_id].append(a)

        # B. Active alerts
        all_alerts: List[WelfareAlert] = (
            db.query(WelfareAlert)
            .filter(
                WelfareAlert.personnel_id.in_(p_ids),
                WelfareAlert.status.in_(["OPEN", "ACKNOWLEDGED", "UNDER_REVIEW", "INTERVENTION_PLANNED", "FOLLOW_UP"]),
            )
            .all()
        )
        alerts_by_pid: Dict[int, List[WelfareAlert]] = {pid: [] for pid in p_ids}
        for al in all_alerts:
            alerts_by_pid[al.personnel_id].append(al)

        # C. Active anomalies
        all_anomalies: List[WelfareAnomaly] = (
            db.query(WelfareAnomaly)
            .filter(
                WelfareAnomaly.personnel_id.in_(p_ids),
                WelfareAnomaly.status.in_(["DETECTED", "ACKNOWLEDGED", "UNDER_REVIEW"]),
            )
            .all()
        )
        anomalies_by_pid: Dict[int, List[WelfareAnomaly]] = {pid: [] for pid in p_ids}
        for an in all_anomalies:
            anomalies_by_pid[an.personnel_id].append(an)

        # D. Open recommendations
        all_recs: List[WelfareRecommendation] = (
            db.query(WelfareRecommendation)
            .filter(
                WelfareRecommendation.personnel_id.in_(p_ids),
                WelfareRecommendation.status.in_(["SUGGESTED", "ACKNOWLEDGED", "pending"]),
            )
            .all()
        )
        recs_by_pid: Dict[int, List[WelfareRecommendation]] = {pid: [] for pid in p_ids}
        for rc in all_recs:
            recs_by_pid[rc.personnel_id].append(rc)

        # Actioned / Accepted recommendations count
        accepted_recs_count = (
            db.query(func.count(WelfareRecommendation.id))
            .filter(
                WelfareRecommendation.personnel_id.in_(p_ids),
                WelfareRecommendation.status.in_(["ACCEPTED", "ACTIONED", "COMPLETED", "completed"]),
            )
            .scalar() or 0
        )

        # E. Interventions
        all_invs: List[WelfareIntervention] = (
            db.query(WelfareIntervention)
            .filter(WelfareIntervention.personnel_id.in_(p_ids))
            .all()
        )
        invs_by_pid: Dict[int, List[WelfareIntervention]] = {pid: [] for pid in p_ids}
        for inv in all_invs:
            invs_by_pid[inv.personnel_id].append(inv)

        # F. Follow-ups
        all_followups: List[WelfareFollowup] = (
            db.query(WelfareFollowup)
            .filter(WelfareFollowup.personnel_id.in_(p_ids))
            .all()
        )
        followups_by_pid: Dict[int, List[WelfareFollowup]] = {pid: [] for pid in p_ids}
        for fu in all_followups:
            followups_by_pid[fu.personnel_id].append(fu)

        # 5. Aggregate Distributions & Personnel Cards
        risk_dist = {"Low": 0, "Medium": 0, "High": 0, "Unavailable": 0}
        trend_dist = {"Improving": 0, "Stable": 0, "Worsening": 0, "Insufficient Data": 0}
        outcome_dist = {"IMPROVED": 0, "STABLE": 0, "PERSISTENT_CONCERN": 0, "WORSENING": 0, "INSUFFICIENT_DATA": 0}

        review_counts = {
            "review_needed_count": 0,
            "monitor_count": 0,
            "no_signal_count": 0,
            "insufficient_data_count": 0,
        }

        valid_assessments_count = 0
        stale_data_count = 0
        insufficient_data_count = 0

        personnel_cards: List[Dict[str, Any]] = []

        for p in personnel_list:
            p_asses = assessments_by_pid.get(p.id, [])
            p_alerts = alerts_by_pid.get(p.id, [])
            p_anoms = anomalies_by_pid.get(p.id, [])
            p_recs = recs_by_pid.get(p.id, [])
            p_invs = invs_by_pid.get(p.id, [])
            p_fus = followups_by_pid.get(p.id, [])

            # Latest assessment
            latest_a = p_asses[-1] if p_asses else None
            cat = latest_a.stress_level if (latest_a and latest_a.stress_level) else "Unavailable"
            score = round(float(latest_a.risk_score), 1) if (latest_a and latest_a.risk_score is not None) else None

            if cat in risk_dist:
                risk_dist[cat] += 1
            else:
                risk_dist["Unavailable"] += 1

            # Trend
            if len(p_asses) >= 2 and latest_a and latest_a.risk_score is not None:
                prev_a = p_asses[-2]
                if prev_a.risk_score is not None:
                    delta = float(latest_a.risk_score) - float(prev_a.risk_score)
                    if delta <= -5.0:
                        t_dir = "Improving"
                    elif delta >= 5.0:
                        t_dir = "Worsening"
                    else:
                        t_dir = "Stable"
                else:
                    t_dir = "Insufficient Data"
            else:
                t_dir = "Insufficient Data"
            trend_dist[t_dir] += 1

            # Freshness
            freshness = "INSUFFICIENT_DATA"
            if latest_a and latest_a.assessment_timestamp:
                valid_assessments_count += 1
                ats = latest_a.assessment_timestamp
                if ats.tzinfo is None:
                    ats = ats.replace(tzinfo=timezone.utc)
                if (now_utc - ats).days > 30:
                    stale_data_count += 1
                    freshness = "STALE"
                else:
                    freshness = "FRESH"
            else:
                insufficient_data_count += 1

            # Overdue followups for this person
            has_overdue = False
            for fu in p_fus:
                if fu.status in ["PENDING", "SCHEDULED"] and fu.due_date:
                    dd = fu.due_date
                    if dd.tzinfo is None:
                        dd = dd.replace(tzinfo=timezone.utc)
                    if dd < now_utc:
                        has_overdue = True
                if fu.status == "COMPLETED":
                    oc = fu.outcome_status or "INSUFFICIENT_DATA"
                    outcome_dist[oc] = outcome_dist.get(oc, 0) + 1

            # Human Review Indicator logic
            if not latest_a or latest_a.risk_score is None:
                r_level = "INSUFFICIENT_DATA"
                review_counts["insufficient_data_count"] += 1
            elif (
                any(al.severity in ["HIGH_PRIORITY", "URGENT_REVIEW"] for al in p_alerts) or
                any(an.severity == "URGENT_REVIEW" for an in p_anoms) or
                t_dir == "Worsening" or
                has_overdue or
                any(r.priority == "URGENT" for r in p_recs)
            ):
                r_level = "REVIEW"
                review_counts["review_needed_count"] += 1
            elif (
                p_alerts or p_anoms or p_recs or
                any(inv.status == "PLANNED" for inv in p_invs) or
                cat in ["High", "Medium"] or
                freshness == "STALE"
            ):
                r_level = "MONITOR"
                review_counts["monitor_count"] += 1
            else:
                r_level = "NO_ACTIVE_REVIEW_SIGNAL"
                review_counts["no_signal_count"] += 1

            # Add to card list (strictly sorted by personnel ID, zero ranking!)
            personnel_cards.append({
                "personnel_id": p.id,
                "personnel_code": p.personnel_code,
                "name": p.name,
                "department": p.department,
                "battalion": p.battalion,
                "location": p.location,
                "current_risk_category": cat if cat != "Unavailable" else None,
                "current_risk_score": score,
                "trend_direction": t_dir,
                "review_level": r_level,
                "active_alerts_count": len(p_alerts),
                "active_anomalies_count": len(p_anoms),
                "open_recommendations_count": len(p_recs),
                "open_interventions_count": len([i for i in p_invs if i.status == "PLANNED"]),
                "pending_followups_count": len([f for f in p_fus if f.status in ["PENDING", "SCHEDULED"]]),
                "has_overdue_followup": has_overdue,
                "freshness_status": freshness,
            })

        # Totals for alerts/anomalies/etc
        fu_total = len(all_followups)
        fu_pending = sum(1 for f in all_followups if f.status == "PENDING")
        fu_scheduled = sum(1 for f in all_followups if f.status == "SCHEDULED")
        fu_completed = sum(1 for f in all_followups if f.status == "COMPLETED")
        fu_deferred = sum(1 for f in all_followups if f.status == "DEFERRED")
        fu_overdue = sum(
            1 for f in all_followups
            if f.status in ["PENDING", "SCHEDULED"] and f.due_date and
            (f.due_date.replace(tzinfo=timezone.utc) if f.due_date.tzinfo is None else f.due_date) < now_utc
        )

        unit_overview = {
            "personnel_monitored": total_in_scope,
            "risk_distribution": risk_dist,
            "trend_distribution": trend_dist,
            "active_alerts_total": len(all_alerts),
            "active_anomalies_total": len(all_anomalies),
            "open_recommendations_total": len(all_recs),
            "open_interventions_total": sum(1 for i in all_invs if i.status == "PLANNED"),
            "followups_total": fu_total,
            "followups_summary": {
                "total": fu_total,
                "pending": fu_pending,
                "scheduled": fu_scheduled,
                "completed": fu_completed,
                "overdue": fu_overdue,
                "deferred": fu_deferred,
            },
            "outcome_distribution": outcome_dist,
        }

        support_workflow = {
            "recommendations_count": len(all_recs),
            "human_decisions_count": accepted_recs_count,
            "interventions_active_count": sum(1 for i in all_invs if i.status == "PLANNED"),
            "followups_completed_count": fu_completed,
            "outcomes_observed_count": sum(v for k, v in outcome_dist.items() if k != "INSUFFICIENT_DATA"),
        }

        data_quality = {
            "valid_assessments_count": valid_assessments_count,
            "stale_data_count": stale_data_count,
            "insufficient_data_count": insufficient_data_count,
        }

        base_response["unit_overview"] = unit_overview
        base_response["support_workflow"] = support_workflow
        base_response["data_quality"] = data_quality
        base_response["human_review_summary"] = review_counts
        base_response["personnel_cards"] = personnel_cards

        return base_response
