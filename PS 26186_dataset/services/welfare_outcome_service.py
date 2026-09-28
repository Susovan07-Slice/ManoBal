import os
import re
import json
from datetime import datetime, timedelta, timezone
from typing import Optional, List, Dict, Any, Tuple
import numpy as np
from sqlalchemy.orm import Session
from sqlalchemy import desc, func, and_

from core.config import logger
from db.models.user import User
from db.models.personnel import Personnel
from db.models.assessment import StressAssessment
from db.models.alert import WelfareAlert, WelfareIntervention
from db.models.recommendation import WelfareRecommendation
from db.models.welfare_followup import WelfareFollowup, WelfareFollowupAudit
from services.longitudinal_analytics_service import LongitudinalAnalyticsService

ANALYTICS_MIN_GROUP_SIZE = int(os.getenv("ANALYTICS_MIN_GROUP_SIZE", "5"))

class WelfareOutcomeService:
    """
    Phase 41: Welfare Follow-Up, Outcome Tracking & Support Effectiveness Engine.
    Closed-loop monitoring layer after Phase 40 recommendations and Phase 37 interventions.
    
    CORE PRINCIPLES & CONSTRAINTS:
      - Does NOT create another risk score (no outcome_score, effectiveness_score, recovery_score, etc.).
      - Does NOT replace Phase 34 authoritative risk engine.
      - Does NOT automatically decide clinical recovery or fitness-for-duty.
      - Strictly enforces temporal ordering (baseline < recommendation/intervention <= follow-up observation).
      - Provides objective follow-up and observational outcome states for authorized human reviewers:
          * IMPROVED
          * STABLE
          * PERSISTENT_CONCERN
          * WORSENING
          * INSUFFICIENT_DATA
    """

    TYPES = [
        "WELFARE_CHECKIN",
        "RECOVERY_REVIEW",
        "DUTY_SCHEDULE_REVIEW",
        "SUPPORT_RESOURCE_FOLLOWUP",
        "REASSESSMENT",
        "INTERVENTION_REVIEW",
    ]

    STATUSES = [
        "PENDING",
        "SCHEDULED",
        "COMPLETED",
        "DEFERRED",
        "DECLINED",
        "CANCELLED",
        "EXPIRED",
    ]

    OUTCOME_STATES = [
        "IMPROVED",
        "STABLE",
        "PERSISTENT_CONCERN",
        "WORSENING",
        "INSUFFICIENT_DATA",
    ]

    VALID_TRANSITIONS = {
        "PENDING": {"SCHEDULED", "COMPLETED", "DEFERRED", "DECLINED", "CANCELLED", "EXPIRED"},
        "SCHEDULED": {"COMPLETED", "DEFERRED", "DECLINED", "CANCELLED", "EXPIRED"},
        "DEFERRED": {"SCHEDULED", "PENDING", "COMPLETED", "CANCELLED", "DECLINED"},
        "COMPLETED": set(),
        "DECLINED": set(),
        "CANCELLED": set(),
        "EXPIRED": set(),
    }

    # =========================================================================
    # AUDIT TRAIL HELPER
    # =========================================================================
    @classmethod
    def _create_audit_log(
        cls,
        db: Session,
        followup_id: int,
        action: str,
        actor_id: Optional[int] = None,
        previous_status: Optional[str] = None,
        new_status: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> WelfareFollowupAudit:
        audit = WelfareFollowupAudit(
            followup_id=followup_id,
            action=action,
            actor_id=actor_id,
            previous_status=previous_status,
            new_status=new_status,
            timestamp=datetime.now(timezone.utc),
            metadata_json=json.dumps(metadata) if metadata else None,
        )
        db.add(audit)
        db.flush()
        return audit

    # =========================================================================
    # REVIEW WINDOW & DUE DATE DERIVATION
    # =========================================================================
    @classmethod
    def calculate_due_date(cls, reference_time: datetime, review_window: Optional[str]) -> Optional[datetime]:
        """
        Derives an operational due date from documented review window strings without
        inventing arbitrary medical schedules.
        Example strings: 'Within 24–48 hours', 'Within 3–5 days', 'Within 7 days', 'Within 14 days'
        """
        if not review_window or review_window.strip().upper() == "NOT_SPECIFIED":
            return None

        clean = review_window.lower()
        # Look for hours
        match_hrs = re.findall(r"(\d+)\s*(?:–|-|\s+to\s+)?\s*(\d+)?\s*(?:hours|hrs|hr)", clean)
        if match_hrs:
            hours = int(match_hrs[0][1] if match_hrs[0][1] else match_hrs[0][0])
            return reference_time + timedelta(hours=hours)

        # Look for days
        match_days = re.findall(r"(\d+)\s*(?:–|-|\s+to\s+)?\s*(\d+)?\s*(?:days|day)", clean)
        if match_days:
            days = int(match_days[0][1] if match_days[0][1] else match_days[0][0])
            return reference_time + timedelta(days=days)

        return None

    # =========================================================================
    # BASELINE & TEMPORAL INTEGRITY
    # =========================================================================
    @classmethod
    def resolve_baseline(
        cls,
        db: Session,
        personnel_id: int,
        anchor_time: datetime,
        recommendation_id: Optional[int] = None,
        intervention_id: Optional[int] = None,
        alert_id: Optional[int] = None,
    ) -> Tuple[Optional[StressAssessment], str]:
        """
        Explicitly identifies the appropriate pre-followup baseline assessment.
        Adheres to strict temporal ordering: baseline_timestamp <= anchor_time.
        """
        baseline: Optional[StressAssessment] = None
        source_label = "PRE_FOLLOWUP_ASSESSMENT"

        # 1. From linked recommendation
        if recommendation_id:
            rec = db.query(WelfareRecommendation).filter(WelfareRecommendation.id == recommendation_id).first()
            if rec and rec.assessment_id:
                cand = db.query(StressAssessment).filter(StressAssessment.id == rec.assessment_id).first()
                if cand and cand.personnel_id == personnel_id:
                    cand_ts = cand.assessment_timestamp or datetime.min.replace(tzinfo=timezone.utc)
                    if cand_ts.tzinfo is None:
                        cand_ts = cand_ts.replace(tzinfo=timezone.utc)
                    if cand_ts <= anchor_time:
                        baseline = cand
                        source_label = "PRE_RECOMMENDATION_ASSESSMENT"

        # 2. From linked intervention / alert
        if not baseline and (intervention_id or alert_id):
            target_alert_id = alert_id
            if intervention_id and not target_alert_id:
                interv = db.query(WelfareIntervention).filter(WelfareIntervention.id == intervention_id).first()
                if interv:
                    target_alert_id = interv.alert_id

            if target_alert_id:
                alert = db.query(WelfareAlert).filter(WelfareAlert.id == target_alert_id).first()
                if alert and alert.trigger_assessment_id:
                    cand = db.query(StressAssessment).filter(StressAssessment.id == alert.trigger_assessment_id).first()
                    if cand and cand.personnel_id == personnel_id:
                        cand_ts = cand.assessment_timestamp or datetime.min.replace(tzinfo=timezone.utc)
                        if cand_ts.tzinfo is None:
                            cand_ts = cand_ts.replace(tzinfo=timezone.utc)
                        if cand_ts <= anchor_time:
                            baseline = cand
                            source_label = "PRE_INTERVENTION_ASSESSMENT"

        # 3. Fallback: most recent valid assessment before or at anchor time
        if not baseline:
            all_past = (
                db.query(StressAssessment)
                .filter(
                    StressAssessment.personnel_id == personnel_id,
                    StressAssessment.assessment_timestamp <= anchor_time,
                )
                .order_by(StressAssessment.assessment_timestamp.desc(), StressAssessment.id.desc())
                .first()
            )
            if all_past:
                baseline = all_past
                source_label = "HISTORICAL_BASELINE"

        return baseline, source_label

    @classmethod
    def resolve_subsequent_assessment(
        cls,
        db: Session,
        personnel_id: int,
        baseline: Optional[StressAssessment],
        anchor_time: datetime,
        explicit_followup_assessment_id: Optional[int] = None,
    ) -> Optional[StressAssessment]:
        """
        Locates subsequent assessment strictly timestamped after baseline and anchor time.
        Raises ValueError if explicit subsequent assessment violates temporal ordering.
        """
        if explicit_followup_assessment_id:
            cand = db.query(StressAssessment).filter(StressAssessment.id == explicit_followup_assessment_id).first()
            if not cand:
                raise ValueError(f"Follow-up assessment ID {explicit_followup_assessment_id} not found.")
            if cand.personnel_id != personnel_id:
                raise ValueError(f"Follow-up assessment #{cand.id} does not belong to personnel #{personnel_id}.")

            cand_ts = cand.assessment_timestamp or datetime.min.replace(tzinfo=timezone.utc)
            if cand_ts.tzinfo is None:
                cand_ts = cand_ts.replace(tzinfo=timezone.utc)

            if baseline:
                base_ts = baseline.assessment_timestamp or datetime.min.replace(tzinfo=timezone.utc)
                if base_ts.tzinfo is None:
                    base_ts = base_ts.replace(tzinfo=timezone.utc)

                if cand_ts < base_ts or cand.id == baseline.id:
                    raise ValueError(
                        f"Temporal integrity violation: follow-up assessment (ts: {cand_ts.isoformat()}, id: {cand.id}) "
                        f"cannot precede or equal baseline assessment (ts: {base_ts.isoformat()}, id: {baseline.id})."
                    )
            return cand

        # Auto-query latest valid assessment after baseline timestamp
        query = db.query(StressAssessment).filter(StressAssessment.personnel_id == personnel_id)

        if baseline and baseline.assessment_timestamp:
            base_ts = baseline.assessment_timestamp
            if base_ts.tzinfo is None:
                base_ts = base_ts.replace(tzinfo=timezone.utc)
            query = query.filter(
                (StressAssessment.assessment_timestamp > base_ts) |
                ((StressAssessment.assessment_timestamp == base_ts) & (StressAssessment.id > baseline.id))
            )
        else:
            query = query.filter(StressAssessment.assessment_timestamp >= anchor_time)

        subsequent = (
            query.order_by(StressAssessment.assessment_timestamp.desc(), StressAssessment.id.desc())
            .first()
        )
        return subsequent

    # =========================================================================
    # OUTCOME EVALUATION ENGINE
    # =========================================================================
    @classmethod
    def evaluate_outcome(
        cls,
        db: Session,
        personnel_id: int,
        baseline: Optional[StressAssessment],
        followup_assessment: Optional[StressAssessment],
        baseline_source: str = "HISTORICAL_BASELINE",
    ) -> Tuple[str, Dict[str, Any]]:
        """
        Deterministic, observational outcome evaluation comparing post-follow-up indicators with baseline.
        Does NOT invent arbitrary medical scores or treatment assertions.
        Reuses Phase 34/36 established delta thresholds (5.0 pts meaningful delta).
        """
        notice = "Observational monitoring state based on available data; not a clinical diagnosis or determination of fitness for duty."

        if not baseline or not followup_assessment:
            return "INSUFFICIENT_DATA", {
                "baseline_source": baseline_source,
                "baseline_assessment_id": baseline.id if baseline else None,
                "followup_assessment_id": followup_assessment.id if followup_assessment else None,
                "score_delta": None,
                "data_sufficiency": "INSUFFICIENT",
                "explanation": "Insufficient assessment observations available before or after follow-up to evaluate trajectory.",
                "notice": notice,
            }

        # Check numeric validity of scores
        b_score = baseline.risk_score
        f_score = followup_assessment.risk_score

        try:
            b_float = float(b_score) if b_score is not None else None
            f_float = float(f_score) if f_score is not None else None
        except (ValueError, TypeError):
            b_float, f_float = None, None

        if b_float is None or f_float is None or np.isnan(b_float) or np.isnan(f_float) or np.isinf(b_float) or np.isinf(f_float):
            return "INSUFFICIENT_DATA", {
                "baseline_source": baseline_source,
                "baseline_assessment_id": baseline.id,
                "followup_assessment_id": followup_assessment.id,
                "score_delta": None,
                "data_sufficiency": "INSUFFICIENT",
                "explanation": "One or more assessment records contain null or invalid non-numeric risk score data.",
                "notice": notice,
            }

        # Temporal integrity safeguard: strictly require timestamps and strict chronological ordering (baseline < followup)
        if not baseline.assessment_timestamp or not followup_assessment.assessment_timestamp:
            return "INSUFFICIENT_DATA", {
                "baseline_source": baseline_source,
                "baseline_assessment_id": baseline.id,
                "followup_assessment_id": followup_assessment.id,
                "score_delta": None,
                "data_sufficiency": "INSUFFICIENT",
                "explanation": "One or more assessment records lack a valid timestamp; temporal ordering cannot be verified.",
                "notice": notice,
            }

        b_ts = baseline.assessment_timestamp
        f_ts = followup_assessment.assessment_timestamp
        if b_ts.tzinfo is None:
            b_ts = b_ts.replace(tzinfo=timezone.utc)
        if f_ts.tzinfo is None:
            f_ts = f_ts.replace(tzinfo=timezone.utc)

        if f_ts <= b_ts:
            return "INSUFFICIENT_DATA", {
                "baseline_source": baseline_source,
                "baseline_assessment_id": baseline.id,
                "followup_assessment_id": followup_assessment.id,
                "score_delta": None,
                "data_sufficiency": "INSUFFICIENT",
                "explanation": "Follow-up assessment timestamp does not strictly follow baseline assessment; chronological integrity violated.",
                "notice": notice,
            }

        now_utc = datetime.now(timezone.utc)
        if f_ts > now_utc + timedelta(hours=24):
            return "INSUFFICIENT_DATA", {
                "baseline_source": baseline_source,
                "baseline_assessment_id": baseline.id,
                "followup_assessment_id": followup_assessment.id,
                "score_delta": None,
                "data_sufficiency": "INSUFFICIENT",
                "explanation": "Follow-up assessment contains a future timestamp; invalid temporal record.",
                "notice": notice,
            }

        score_delta = round(f_float - b_float, 1)

        b_cat = baseline.stress_level or "Low"
        f_cat = followup_assessment.stress_level or "Low"

        # Deterministic Classification Rules (Aligned with Phase 36 longitudinal trend logic)
        # 1. Meaningful improvement: score_delta <= -5.0
        if score_delta <= -5.0:
            outcome_status = "IMPROVED"
            explanation = (
                f"Subsequent validated welfare indicators show meaningful improvement "
                f"({score_delta} pts, {b_cat} -> {f_cat}) relative to baseline."
            )

        # 2. Meaningful worsening: score_delta >= +5.0
        elif score_delta >= 5.0:
            outcome_status = "WORSENING"
            explanation = (
                f"Subsequent validated welfare indicators show deterioration "
                f"(+{score_delta} pts, {b_cat} -> {f_cat}) relative to baseline."
            )

        # 3. Persistent concern: Delta is within +/-5 pts, but baseline was Elevated/High/Critical (>= 55.0) and followup remains >= 55.0
        elif (b_float >= 55.0 or b_cat in ["High", "Critical", "Elevated"]) and (f_float >= 55.0 or f_cat in ["High", "Critical", "Elevated"]):
            outcome_status = "PERSISTENT_CONCERN"
            explanation = (
                f"Elevated welfare strain remains persistent across subsequent observations "
                f"(Score: {f_float:.1f}, {f_cat}; delta: {score_delta:+.1f} pts)."
            )

        # 4. Stable: Delta is within +/-5 pts and indicators remain broadly consistent without persistent elevated concern
        else:
            outcome_status = "STABLE"
            explanation = (
                f"Subsequent indicators remain broadly consistent with established baseline "
                f"(Score: {f_float:.1f}, {f_cat}; delta: {score_delta:+.1f} pts)."
            )

        evidence_dict = {
            "baseline_source": baseline_source,
            "baseline_assessment_id": baseline.id,
            "baseline_score": b_float,
            "baseline_category": b_cat,
            "baseline_timestamp": b_ts.isoformat(),
            "followup_assessment_id": followup_assessment.id,
            "followup_score": f_float,
            "followup_category": f_cat,
            "followup_timestamp": f_ts.isoformat(),
            "score_delta": score_delta,
            "data_sufficiency": "SUFFICIENT",
            "explanation": explanation,
            "notice": notice,
        }

        return outcome_status, evidence_dict

    # =========================================================================
    # LIFECYCLE MANAGEMENT
    # =========================================================================
    @classmethod
    def create_followup(
        cls,
        db: Session,
        user: User,
        personnel_id: int,
        followup_type: str,
        recommendation_id: Optional[int] = None,
        intervention_id: Optional[int] = None,
        alert_id: Optional[int] = None,
        review_window: Optional[str] = "NOT_SPECIFIED",
        scheduled_at: Optional[datetime] = None,
        notes: Optional[str] = None,
    ) -> WelfareFollowup:
        """
        Creates a new WelfareFollowup record.
        Maintains timeline history without overwriting previous follow-ups.
        """
        if followup_type not in cls.TYPES:
            raise ValueError(f"Invalid follow-up type: '{followup_type}'. Must be one of: {cls.TYPES}")

        # Verify target personnel exists
        personnel = db.query(Personnel).filter(Personnel.id == personnel_id).first()
        if not personnel:
            raise LookupError(f"Personnel #{personnel_id} not found.")

        # Enforce scope / authorization
        cls.verify_access_and_get_personnel(personnel_id, user, db)

        now = datetime.now(timezone.utc)

        # Derive review window from recommendation if not provided
        derived_window = review_window or "NOT_SPECIFIED"
        if recommendation_id and (not review_window or review_window == "NOT_SPECIFIED"):
            rec = db.query(WelfareRecommendation).filter(WelfareRecommendation.id == recommendation_id).first()
            if rec and rec.recommended_review_window:
                derived_window = rec.recommended_review_window

        due_date = cls.calculate_due_date(now, derived_window)
        initial_status = "SCHEDULED" if scheduled_at else "PENDING"

        # Resolve explicit baseline
        baseline, b_source = cls.resolve_baseline(
            db, personnel_id, now, recommendation_id, intervention_id, alert_id
        )

        initial_evidence = {
            "baseline_source": b_source,
            "baseline_assessment_id": baseline.id if baseline else None,
            "baseline_score": baseline.risk_score if baseline else None,
            "data_sufficiency": "INSUFFICIENT" if not baseline else "LIMITED",
            "explanation": "Follow-up initiated. Pending subsequent post-follow-up observation.",
            "notice": "Observational monitoring state based on available data; not a clinical diagnosis or determination of fitness for duty."
        }

        followup = WelfareFollowup(
            personnel_id=personnel_id,
            recommendation_id=recommendation_id,
            intervention_id=intervention_id,
            alert_id=alert_id,
            followup_type=followup_type,
            status=initial_status,
            scheduled_at=scheduled_at,
            review_window=derived_window,
            due_date=due_date,
            created_by=user.id,
            notes=notes,
            outcome_status="INSUFFICIENT_DATA",
            baseline_source=b_source,
            baseline_assessment_id=baseline.id if baseline else None,
            evidence_json=json.dumps(initial_evidence),
            created_at=now,
            updated_at=now,
        )
        db.add(followup)
        db.flush()

        cls._create_audit_log(
            db=db,
            followup_id=followup.id,
            action="FOLLOWUP_CREATED",
            actor_id=user.id,
            new_status=initial_status,
            metadata={
                "followup_type": followup_type,
                "recommendation_id": recommendation_id,
                "intervention_id": intervention_id,
                "review_window": derived_window,
                "baseline_assessment_id": baseline.id if baseline else None,
            },
        )
        db.commit()
        db.refresh(followup)
        return followup

    @classmethod
    def schedule_followup(
        cls,
        db: Session,
        followup_id: int,
        user: User,
        scheduled_at: datetime,
        notes: Optional[str] = None,
    ) -> WelfareFollowup:
        followup = db.query(WelfareFollowup).filter(WelfareFollowup.id == followup_id).first()
        if not followup:
            raise LookupError(f"Follow-up #{followup_id} not found.")

        cls.verify_access_and_get_personnel(followup.personnel_id, user, db)

        if "SCHEDULED" not in cls.VALID_TRANSITIONS.get(followup.status, set()):
            raise ValueError(f"Cannot schedule follow-up from current status '{followup.status}'.")

        prev_status = followup.status
        followup.status = "SCHEDULED"
        followup.scheduled_at = scheduled_at
        if notes:
            followup.notes = f"{followup.notes}\n[Scheduled: {notes}]" if followup.notes else notes
        followup.updated_at = datetime.now(timezone.utc)

        cls._create_audit_log(
            db=db,
            followup_id=followup.id,
            action="FOLLOWUP_SCHEDULED",
            actor_id=user.id,
            previous_status=prev_status,
            new_status="SCHEDULED",
            metadata={"scheduled_at": scheduled_at.isoformat(), "notes": notes},
        )
        db.commit()
        db.refresh(followup)
        return followup

    @classmethod
    def complete_followup(
        cls,
        db: Session,
        followup_id: int,
        user: User,
        notes: Optional[str] = None,
        followup_assessment_id: Optional[int] = None,
        trigger_new_recommendation: bool = True,
    ) -> WelfareFollowup:
        """
        Completes follow-up, records authorized reviewer, evaluates outcome,
        and optionally alerts Phase 40 if outcome indicates WORSENING or PERSISTENT_CONCERN.
        """
        followup = db.query(WelfareFollowup).filter(WelfareFollowup.id == followup_id).first()
        if not followup:
            raise LookupError(f"Follow-up #{followup_id} not found.")

        cls.verify_access_and_get_personnel(followup.personnel_id, user, db)

        if "COMPLETED" not in cls.VALID_TRANSITIONS.get(followup.status, set()):
            raise ValueError(f"Cannot complete follow-up from current status '{followup.status}'.")

        prev_status = followup.status
        now = datetime.now(timezone.utc)

        # Baseline resolution
        baseline = None
        if followup.baseline_assessment_id:
            baseline = db.query(StressAssessment).filter(StressAssessment.id == followup.baseline_assessment_id).first()
        if not baseline:
            baseline, b_source = cls.resolve_baseline(
                db, followup.personnel_id, followup.created_at or now,
                followup.recommendation_id, followup.intervention_id, followup.alert_id
            )
            if baseline:
                followup.baseline_assessment_id = baseline.id
                followup.baseline_source = b_source

        # Subsequent assessment resolution
        subsequent = cls.resolve_subsequent_assessment(
            db=db,
            personnel_id=followup.personnel_id,
            baseline=baseline,
            anchor_time=followup.created_at or now,
            explicit_followup_assessment_id=followup_assessment_id,
        )

        outcome_status, evidence = cls.evaluate_outcome(
            db=db,
            personnel_id=followup.personnel_id,
            baseline=baseline,
            followup_assessment=subsequent,
            baseline_source=followup.baseline_source or "HISTORICAL_BASELINE",
        )

        followup.status = "COMPLETED"
        followup.completed_at = now
        followup.completed_by = user.id
        followup.followup_assessment_id = subsequent.id if subsequent else None
        followup.outcome_status = outcome_status
        followup.evidence_json = json.dumps(evidence)
        if notes:
            followup.notes = f"{followup.notes}\n[Completed: {notes}]" if followup.notes else notes
        followup.updated_at = now

        cls._create_audit_log(
            db=db,
            followup_id=followup.id,
            action="FOLLOWUP_COMPLETED",
            actor_id=user.id,
            previous_status=prev_status,
            new_status="COMPLETED",
            metadata={
                "outcome_status": outcome_status,
                "baseline_assessment_id": baseline.id if baseline else None,
                "followup_assessment_id": subsequent.id if subsequent else None,
                "score_delta": evidence.get("score_delta"),
            },
        )

        cls._create_audit_log(
            db=db,
            followup_id=followup.id,
            action="OUTCOME_RECORDED",
            actor_id=user.id,
            new_status=outcome_status,
            metadata=evidence,
        )

        # Phase 40 Integration: If WORSENING or PERSISTENT_CONCERN and requested, evaluate new supportive recommendations
        if trigger_new_recommendation and outcome_status in ["WORSENING", "PERSISTENT_CONCERN"]:
            try:
                from services.welfare_recommendation_service import WelfareRecommendationService
                personnel = db.query(Personnel).filter(Personnel.id == followup.personnel_id).first()
                if personnel:
                    WelfareRecommendationService.evaluate_and_generate_recommendations(
                        personnel=personnel,
                        db=db,
                        current_assessment=subsequent,
                        persist=True,
                    )
            except Exception as e:
                logger.warning(f"Could not trigger Phase 40 recommendation evaluation upon follow-up completion: {e}")

        db.commit()
        db.refresh(followup)
        return followup

    @classmethod
    def defer_followup(
        cls,
        db: Session,
        followup_id: int,
        user: User,
        defer_days: int = 7,
        notes: Optional[str] = None,
    ) -> WelfareFollowup:
        followup = db.query(WelfareFollowup).filter(WelfareFollowup.id == followup_id).first()
        if not followup:
            raise LookupError(f"Follow-up #{followup_id} not found.")

        cls.verify_access_and_get_personnel(followup.personnel_id, user, db)

        if "DEFERRED" not in cls.VALID_TRANSITIONS.get(followup.status, set()):
            raise ValueError(f"Cannot defer follow-up from current status '{followup.status}'.")

        prev_status = followup.status
        now = datetime.now(timezone.utc)
        followup.status = "DEFERRED"
        followup.review_window = f"Deferred for {defer_days} days"
        followup.due_date = now + timedelta(days=defer_days)
        if notes:
            followup.notes = f"{followup.notes}\n[Deferred {defer_days}d: {notes}]" if followup.notes else notes
        followup.updated_at = now

        cls._create_audit_log(
            db=db,
            followup_id=followup.id,
            action="FOLLOWUP_DEFERRED",
            actor_id=user.id,
            previous_status=prev_status,
            new_status="DEFERRED",
            metadata={"defer_days": defer_days, "notes": notes},
        )
        db.commit()
        db.refresh(followup)
        return followup

    @classmethod
    def cancel_followup(
        cls,
        db: Session,
        followup_id: int,
        user: User,
        reason: str,
    ) -> WelfareFollowup:
        followup = db.query(WelfareFollowup).filter(WelfareFollowup.id == followup_id).first()
        if not followup:
            raise LookupError(f"Follow-up #{followup_id} not found.")

        cls.verify_access_and_get_personnel(followup.personnel_id, user, db)

        if "CANCELLED" not in cls.VALID_TRANSITIONS.get(followup.status, set()):
            raise ValueError(f"Cannot cancel follow-up from current status '{followup.status}'.")

        prev_status = followup.status
        now = datetime.now(timezone.utc)
        followup.status = "CANCELLED"
        followup.notes = f"{followup.notes}\n[Cancelled: {reason}]" if followup.notes else f"[Cancelled: {reason}]"
        followup.updated_at = now

        cls._create_audit_log(
            db=db,
            followup_id=followup.id,
            action="FOLLOWUP_CANCELLED",
            actor_id=user.id,
            previous_status=prev_status,
            new_status="CANCELLED",
            metadata={"reason": reason},
        )
        db.commit()
        db.refresh(followup)
        return followup

    @classmethod
    def expire_followup(
        cls,
        db: Session,
        followup_id: int,
        user: Optional[User] = None,
        reason: str = "Review window elapsed without completion",
    ) -> WelfareFollowup:
        followup = db.query(WelfareFollowup).filter(WelfareFollowup.id == followup_id).first()
        if not followup:
            raise LookupError(f"Follow-up #{followup_id} not found.")

        if user:
            cls.verify_access_and_get_personnel(followup.personnel_id, user, db)

        if "EXPIRED" not in cls.VALID_TRANSITIONS.get(followup.status, set()):
            raise ValueError(f"Cannot expire follow-up from current status '{followup.status}'.")

        prev_status = followup.status
        now = datetime.now(timezone.utc)
        followup.status = "EXPIRED"
        followup.notes = f"{followup.notes}\n[Expired: {reason}]" if followup.notes else f"[Expired: {reason}]"
        followup.updated_at = now

        cls._create_audit_log(
            db=db,
            followup_id=followup.id,
            action="FOLLOWUP_EXPIRED",
            actor_id=user.id if user else None,
            previous_status=prev_status,
            new_status="EXPIRED",
            metadata={"reason": reason},
        )
        db.commit()
        db.refresh(followup)
        return followup

    @classmethod
    def reassess_outcome(
        cls,
        db: Session,
        followup_id: int,
        user: User,
        explicit_followup_assessment_id: Optional[int] = None,
    ) -> WelfareFollowup:
        """
        Re-evaluates outcome observation for a completed follow-up when new subsequent assessments arrive.
        Preserves complete history without deleting prior records.
        """
        followup = db.query(WelfareFollowup).filter(WelfareFollowup.id == followup_id).first()
        if not followup:
            raise LookupError(f"Follow-up #{followup_id} not found.")

        cls.verify_access_and_get_personnel(followup.personnel_id, user, db)

        baseline = None
        if followup.baseline_assessment_id:
            baseline = db.query(StressAssessment).filter(StressAssessment.id == followup.baseline_assessment_id).first()

        subsequent = cls.resolve_subsequent_assessment(
            db=db,
            personnel_id=followup.personnel_id,
            baseline=baseline,
            anchor_time=followup.created_at or datetime.now(timezone.utc),
            explicit_followup_assessment_id=explicit_followup_assessment_id,
        )

        outcome_status, evidence = cls.evaluate_outcome(
            db=db,
            personnel_id=followup.personnel_id,
            baseline=baseline,
            followup_assessment=subsequent,
            baseline_source=followup.baseline_source or "HISTORICAL_BASELINE",
        )

        prev_outcome = followup.outcome_status
        followup.outcome_status = outcome_status
        followup.evidence_json = json.dumps(evidence)
        if subsequent:
            followup.followup_assessment_id = subsequent.id
        followup.updated_at = datetime.now(timezone.utc)

        cls._create_audit_log(
            db=db,
            followup_id=followup.id,
            action="OUTCOME_REASSESSED",
            actor_id=user.id,
            previous_status=prev_outcome,
            new_status=outcome_status,
            metadata=evidence,
        )
        db.commit()
        db.refresh(followup)
        return followup

    # =========================================================================
    # RBAC & SECURITY HELPERS
    # =========================================================================
    @classmethod
    def verify_access_and_get_personnel(cls, personnel_id: int, user: User, db: Session) -> Personnel:
        """
        Enforces strict RBAC and Anti-IDOR protections:
        - Personnel role: can only access their own record.
        - Officer / Welfare: can only access personnel in their matching battalion/location.
        - Admin: full access.
        """
        personnel = db.query(Personnel).filter(Personnel.id == personnel_id).first()
        if not personnel:
            raise LookupError(f"Personnel record #{personnel_id} not found.")

        if user.role == "personnel":
            if user.personnel_id != personnel_id:
                logger.warning(
                    f"IDOR Violation attempt: Personnel user #{user.id} ({user.username}) "
                    f"attempted to access follow-ups for personnel #{personnel_id}"
                )
                raise PermissionError("Access forbidden: Personnel can only access their own welfare follow-ups.")

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

    # =========================================================================
    # COMMANDER ANALYTICS & PRIVACY-PRESERVING AGGREGATION
    # =========================================================================
    @classmethod
    def get_unit_followup_analytics(
        cls,
        db: Session,
        user: User,
        battalion: Optional[str] = None,
        location: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Aggregated follow-up metrics respecting the minimum-group privacy threshold (k-anonymity).
        Does NOT rank personnel or output best/worst lists.
        """
        query = db.query(Personnel)

        # Scoping based on user role
        if user.role in ["officer", "welfare"]:
            if user.battalion:
                query = query.filter(func.lower(Personnel.battalion) == user.battalion.strip().lower())
            if user.location:
                query = query.filter(func.lower(Personnel.location) == user.location.strip().lower())
        elif user.role == "admin":
            if battalion:
                query = query.filter(func.lower(Personnel.battalion) == battalion.strip().lower())
            if location:
                query = query.filter(func.lower(Personnel.location) == location.strip().lower())
        else:
            raise PermissionError("Access forbidden: Insufficient privileges for commander analytics.")

        total_personnel = query.count()

        # Check Privacy Threshold
        if total_personnel < ANALYTICS_MIN_GROUP_SIZE:
            return {
                "scope_battalion": battalion or (user.battalion if user.role != "admin" else None),
                "scope_location": location or (user.location if user.role != "admin" else None),
                "total_personnel_in_scope": total_personnel,
                "privacy_threshold": ANALYTICS_MIN_GROUP_SIZE,
                "data_suppressed": True,
                "suppression_reason": (
                    f"Group size ({total_personnel}) is below minimum privacy threshold "
                    f"({ANALYTICS_MIN_GROUP_SIZE}). Data suppressed to protect individual privacy."
                ),
                "followups_total": 0,
                "followups_pending": 0,
                "followups_scheduled": 0,
                "followups_completed": 0,
                "followups_overdue": 0,
                "followups_deferred": 0,
                "followups_cancelled": 0,
                "outcome_distribution": {k: 0 for k in cls.OUTCOME_STATES},
                "persistent_concern_count": 0,
                "disclaimer": (
                    "Phase 41 reports observable follow-up and outcome patterns from available welfare data. "
                    "It does not establish clinical recovery, fitness for duty, treatment effectiveness, or personnel suitability."
                )
            }

        personnel_ids = [p.id for p in query.all()]
        now = datetime.now(timezone.utc)

        followups = (
            db.query(WelfareFollowup)
            .filter(WelfareFollowup.personnel_id.in_(personnel_ids))
            .all()
        )

        total_f = len(followups)
        pending_c = sum(1 for f in followups if f.status == "PENDING")
        scheduled_c = sum(1 for f in followups if f.status == "SCHEDULED")
        completed_c = sum(1 for f in followups if f.status == "COMPLETED")
        deferred_c = sum(1 for f in followups if f.status == "DEFERRED")
        cancelled_c = sum(1 for f in followups if f.status in ["CANCELLED", "DECLINED"])

        # Overdue check: status in PENDING/SCHEDULED and due_date < now
        overdue_c = 0
        for f in followups:
            if f.status in ["PENDING", "SCHEDULED"] and f.due_date:
                dd = f.due_date
                if dd.tzinfo is None:
                    dd = dd.replace(tzinfo=timezone.utc)
                if dd < now:
                    overdue_c += 1

        outcome_dist = {k: 0 for k in cls.OUTCOME_STATES}
        for f in followups:
            if f.status == "COMPLETED" and f.outcome_status in outcome_dist:
                outcome_dist[f.outcome_status] += 1

        persistent_c = outcome_dist.get("PERSISTENT_CONCERN", 0)

        return {
            "scope_battalion": battalion or (user.battalion if user.role != "admin" else None),
            "scope_location": location or (user.location if user.role != "admin" else None),
            "total_personnel_in_scope": total_personnel,
            "privacy_threshold": ANALYTICS_MIN_GROUP_SIZE,
            "data_suppressed": False,
            "suppression_reason": None,
            "followups_total": total_f,
            "followups_pending": pending_c,
            "followups_scheduled": scheduled_c,
            "followups_completed": completed_c,
            "followups_overdue": overdue_c,
            "followups_deferred": deferred_c,
            "followups_cancelled": cancelled_c,
            "outcome_distribution": outcome_dist,
            "persistent_concern_count": persistent_c,
            "disclaimer": (
                "Phase 41 reports observable follow-up and outcome patterns from available welfare data. "
                "It does not establish clinical recovery, fitness for duty, treatment effectiveness, or personnel suitability."
            )
        }
