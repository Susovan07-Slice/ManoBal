import json
from datetime import datetime, timezone
from typing import Optional, List, Dict, Any, Tuple
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import desc, func, or_

from core.config import logger
from db.models.user import User
from db.models.personnel import Personnel
from db.models.assessment import StressAssessment
from db.models.alert import WelfareAlert, WelfareIntervention
from db.models.anomaly import WelfareAnomaly
from db.models.recommendation import WelfareRecommendation
from db.models.welfare_followup import WelfareFollowup
from db.models.welfare_case import (
    WelfareCase,
    WelfareCaseReview,
    WelfareCaseNote,
    WelfareCaseAudit,
)
from services.unified_welfare_intelligence_service import (
    UnifiedWelfareIntelligenceService,
    ANALYTICS_MIN_GROUP_SIZE,
)
from schemas.welfare_case import (
    VALID_CASE_STATUSES,
    VALID_CASE_TYPES,
    VALID_TRIGGER_SOURCES,
    VALID_CLOSURE_REASONS,
    VALID_HUMAN_DECISIONS,
    VALID_NOTE_TYPES,
    VALID_REVIEW_TYPES,
    WelfareCaseCreateRequest,
    WelfareCaseReviewRequest,
    WelfareCaseNoteCreateRequest,
    WelfareCaseStatusUpdateRequest,
    WelfareCaseCloseRequest,
    WelfareCaseReopenRequest,
    WelfareCaseListItemOut,
    SignalsSummaryOut,
    WelfareCaseDetailOut,
    WelfareCaseEvidenceOut,
    WelfareCaseReviewOut,
    WelfareCaseNoteOut,
    WelfareCaseAuditOut,
    TimelineEventOut,
    WelfareCaseTimelineResponse,
    WelfareCaseAuditsResponse,
    WelfareCaseListResponse,
    WelfareCaseSummaryStatsResponse,
)

# -----------------------------------------------------------------------------
# CONTROLLED STATE TRANSITIONS
# -----------------------------------------------------------------------------
# Explicit human-driven state transitions. Arbitrary transitions are rejected.
VALID_STATUS_TRANSITIONS: Dict[str, set] = {
    "OPEN": {"UNDER_REVIEW", "MONITORING", "CLOSED"},
    "UNDER_REVIEW": {"SUPPORT_IN_PROGRESS", "AWAITING_FOLLOW_UP", "MONITORING", "RESOLVED", "CLOSED"},
    "SUPPORT_IN_PROGRESS": {"AWAITING_FOLLOW_UP", "MONITORING", "RESOLVED", "CLOSED"},
    "AWAITING_FOLLOW_UP": {"MONITORING", "SUPPORT_IN_PROGRESS", "RESOLVED", "CLOSED"},
    "MONITORING": {"UNDER_REVIEW", "SUPPORT_IN_PROGRESS", "AWAITING_FOLLOW_UP", "RESOLVED", "CLOSED"},
    "RESOLVED": {"CLOSED", "MONITORING", "UNDER_REVIEW"},
    "CLOSED": {"OPEN"},  # Only allowed through explicit reopen workflow
}


class WelfareCaseService:
    """
    Phase 43: Welfare Case Management & Human Review Workspace Service.
    Converts existing welfare signals (Phases 34–42) into a structured, traceable
    human-review workflow without creating another risk engine or ranking personnel.

    CRITICAL ARCHITECTURAL CONSTRAINTS:
      - Does NOT calculate a new risk score, composite index, or case score.
      - Does NOT rank personnel or produce 'worst cases' lists.
      - Does NOT automatically reassign duties or make disciplinary determinations.
      - Does NOT automatically close cases without explicit human action.
      - Strictly enforces Anti-IDOR and Battalion/Location scoping.
      - Strictly enforces small-group k-anonymity privacy (k >= 5) on aggregate stats.
      - Uses batched loading to avoid N+1 queries.
    """

    # -------------------------------------------------------------------------
    # AUTHORIZATION & SCOPING (Anti-IDOR)
    # -------------------------------------------------------------------------
    @classmethod
    def verify_case_access(
        cls,
        case: WelfareCase,
        user: User,
        require_write: bool = False,
    ) -> None:
        """
        Enforces strict RBAC and Anti-IDOR for a specific WelfareCase:
        - Jawan (personnel role): Read-only access to own linked cases ONLY. Cannot write/edit.
        - Officer / Welfare: Can only access cases where target personnel belongs to assigned battalion (and location).
        - Admin: Global system-wide access.
        """
        role = (getattr(user, "role", "") or "").lower()

        # 1. Jawan role checks
        if role == "personnel":
            if require_write:
                logger.warning(
                    f"RBAC Violation: Jawan '{user.username}' attempted write operation on Case ID {case.id}."
                )
                raise PermissionError("Jawans are not authorized to modify welfare cases or record reviews.")

            user_p_id = getattr(user, "personnel_id", None)
            if user_p_id != case.personnel_id:
                logger.warning(
                    f"Anti-IDOR Violation: User '{user.username}' (Personnel ID: {user_p_id}) "
                    f"attempted to access Case ID {case.id} belonging to Personnel ID {case.personnel_id}."
                )
                raise PermissionError("Access denied: You are only authorized to view your own welfare cases.")
            return

        # 2. Officer & Welfare scoping
        if role in ["officer", "welfare", "doctor", "psychologist"]:
            user_bat = getattr(user, "battalion", None)
            user_loc = getattr(user, "location", None)

            p_bat = case.personnel.battalion if case.personnel else None
            p_loc = case.personnel.location if case.personnel else None

            if user_bat and p_bat and user_bat.strip().lower() != p_bat.strip().lower():
                logger.warning(
                    f"Scope Violation: Officer '{user.username}' (Battalion: '{user_bat}') "
                    f"attempted cross-battalion access to Case ID {case.id} (Personnel Battalion: '{p_bat}')."
                )
                raise PermissionError(
                    f"Access denied: Target case personnel is outside your assigned Battalion scope ('{user_bat}')."
                )

            if user_loc and p_loc and user_loc.strip().lower() != p_loc.strip().lower():
                logger.warning(
                    f"Scope Violation: Officer '{user.username}' (Location: '{user_loc}') "
                    f"attempted cross-location access to Case ID {case.id} (Personnel Location: '{p_loc}')."
                )
                raise PermissionError(
                    f"Access denied: Target case personnel is outside your assigned Station/Location scope ('{user_loc}')."
                )
            return

        # 3. Admins have unrestricted access
        if role in ["admin", "superadmin"]:
            return

        raise PermissionError("Access forbidden: Insufficient authorization level.")

    @classmethod
    def verify_personnel_creation_access(
        cls,
        personnel_id: int,
        user: User,
        db: Session,
    ) -> Personnel:
        """
        Verifies that an authorized human reviewer has permission to open a case
        for the given personnel. Jawans cannot open cases.
        """
        role = (getattr(user, "role", "") or "").lower()
        if role == "personnel":
            raise PermissionError("Jawans are not authorized to create welfare cases.")

        personnel = db.query(Personnel).filter(Personnel.id == personnel_id).first()
        if not personnel:
            raise LookupError(f"Personnel ID {personnel_id} does not exist.")

        if role in ["officer", "welfare", "doctor", "psychologist"]:
            user_bat = getattr(user, "battalion", None)
            user_loc = getattr(user, "location", None)

            if user_bat and personnel.battalion and user_bat.strip().lower() != personnel.battalion.strip().lower():
                raise PermissionError(
                    f"Cannot open case: Personnel belongs to battalion '{personnel.battalion}', "
                    f"which is outside your assigned battalion '{user_bat}'."
                )

            if user_loc and personnel.location and user_loc.strip().lower() != personnel.location.strip().lower():
                raise PermissionError(
                    f"Cannot open case: Personnel location '{personnel.location}' "
                    f"is outside your assigned location '{user_loc}'."
                )

        return personnel

    # -------------------------------------------------------------------------
    # CASE REFERENCE GENERATOR
    # -------------------------------------------------------------------------
    @classmethod
    def _generate_case_reference(cls, db: Session) -> str:
        """Generates a stable, human-readable case reference code (e.g. WC-2026-0001)."""
        year = datetime.now(timezone.utc).year
        # Count existing cases this year
        count = db.query(func.count(WelfareCase.id)).scalar() or 0
        ref = f"WC-{year}-{count + 1:04d}"

        # Ensure uniqueness
        collision = db.query(WelfareCase.id).filter(WelfareCase.case_reference == ref).first()
        if collision:
            import uuid
            ref = f"WC-{year}-{count + 1:04d}-{uuid.uuid4().hex[:4].upper()}"
        return ref

    # -------------------------------------------------------------------------
    # AUDIT TRAIL LOGGING
    # -------------------------------------------------------------------------
    @classmethod
    def _log_audit(
        cls,
        db: Session,
        case_id: int,
        action: str,
        actor_id: Optional[int],
        previous_status: Optional[str] = None,
        new_status: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> WelfareCaseAudit:
        """Appends an immutable audit event to welfare_case_audits."""
        audit = WelfareCaseAudit(
            case_id=case_id,
            action=action,
            actor_id=actor_id,
            previous_status=previous_status,
            new_status=new_status,
            timestamp=datetime.now(timezone.utc),
            metadata_json=json.dumps(metadata or {}),
        )
        db.add(audit)
        return audit

    # -------------------------------------------------------------------------
    # CASE CREATION
    # -------------------------------------------------------------------------
    @classmethod
    def create_case(
        cls,
        payload: WelfareCaseCreateRequest,
        current_user: User,
        db: Session,
    ) -> WelfareCase:
        """
        Opens a new WelfareCase initiated by an authorized reviewer.
        Records reviewer identity, trigger signal, and appends CASE_CREATED audit.
        """
        personnel = cls.verify_personnel_creation_access(payload.personnel_id, current_user, db)

        if payload.case_type not in VALID_CASE_TYPES:
            raise ValueError(f"Invalid case_type '{payload.case_type}'. Allowed: {VALID_CASE_TYPES}")

        if payload.trigger_source not in VALID_TRIGGER_SOURCES:
            raise ValueError(f"Invalid trigger_source '{payload.trigger_source}'. Allowed: {VALID_TRIGGER_SOURCES}")

        now_utc = datetime.now(timezone.utc)
        ref = cls._generate_case_reference(db)
        title = payload.title or f"Welfare Review — {payload.case_type.replace('_', ' ').title()} — {personnel.personnel_code}"

        # Verify linked foreign keys if provided
        if payload.assessment_id:
            ass = db.query(StressAssessment).filter(StressAssessment.id == payload.assessment_id).first()
            if not ass or ass.personnel_id != personnel.id:
                raise ValueError(f"StressAssessment ID {payload.assessment_id} does not match target personnel.")

        if payload.alert_id:
            alt = db.query(WelfareAlert).filter(WelfareAlert.id == payload.alert_id).first()
            if not alt or alt.personnel_id != personnel.id:
                raise ValueError(f"WelfareAlert ID {payload.alert_id} does not match target personnel.")

        if payload.anomaly_id:
            anom = db.query(WelfareAnomaly).filter(WelfareAnomaly.id == payload.anomaly_id).first()
            if not anom or anom.personnel_id != personnel.id:
                raise ValueError(f"WelfareAnomaly ID {payload.anomaly_id} does not match target personnel.")

        if payload.recommendation_id:
            rec = db.query(WelfareRecommendation).filter(WelfareRecommendation.id == payload.recommendation_id).first()
            if not rec or rec.personnel_id != personnel.id:
                raise ValueError(f"WelfareRecommendation ID {payload.recommendation_id} does not match target personnel.")

        if payload.intervention_id:
            itv = db.query(WelfareIntervention).filter(WelfareIntervention.id == payload.intervention_id).first()
            if not itv or itv.personnel_id != personnel.id:
                raise ValueError(f"WelfareIntervention ID {payload.intervention_id} does not match target personnel.")

        if payload.followup_id:
            fup = db.query(WelfareFollowup).filter(WelfareFollowup.id == payload.followup_id).first()
            if not fup or fup.personnel_id != personnel.id:
                raise ValueError(f"WelfareFollowup ID {payload.followup_id} does not match target personnel.")

        case = WelfareCase(
            personnel_id=personnel.id,
            case_reference=ref,
            title=title,
            case_type=payload.case_type,
            status="OPEN",
            trigger_source=payload.trigger_source,
            assessment_id=payload.assessment_id,
            alert_id=payload.alert_id,
            anomaly_id=payload.anomaly_id,
            recommendation_id=payload.recommendation_id,
            intervention_id=payload.intervention_id,
            followup_id=payload.followup_id,
            opened_at=now_utc,
            opened_by=current_user.id,
            summary=payload.summary,
            created_at=now_utc,
            updated_at=now_utc,
        )
        db.add(case)
        db.flush()

        cls._log_audit(
            db=db,
            case_id=case.id,
            action="CASE_CREATED",
            actor_id=current_user.id,
            previous_status=None,
            new_status="OPEN",
            metadata={
                "case_reference": ref,
                "case_type": payload.case_type,
                "trigger_source": payload.trigger_source,
                "personnel_code": personnel.personnel_code,
                "linked_signals": {
                    "assessment_id": payload.assessment_id,
                    "alert_id": payload.alert_id,
                    "anomaly_id": payload.anomaly_id,
                    "recommendation_id": payload.recommendation_id,
                    "intervention_id": payload.intervention_id,
                    "followup_id": payload.followup_id,
                },
            },
        )
        db.commit()
        db.refresh(case)
        logger.info(f"Welfare case '{ref}' opened for Personnel '{personnel.personnel_code}' by user '{current_user.username}'.")
        return case

    # -------------------------------------------------------------------------
    # HUMAN REVIEW RECORDING
    # -------------------------------------------------------------------------
    @classmethod
    def record_review(
        cls,
        case_id: int,
        payload: WelfareCaseReviewRequest,
        current_user: User,
        db: Session,
    ) -> WelfareCaseReview:
        """
        Records a structured human review for a welfare case.
        Distinguishes explicit human decisions from system recommendations.
        Optionally transitions case status if permitted by the state machine.
        """
        case = db.query(WelfareCase).options(joinedload(WelfareCase.personnel)).filter(WelfareCase.id == case_id).first()
        if not case:
            raise LookupError(f"WelfareCase ID {case_id} not found.")

        cls.verify_case_access(case, current_user, require_write=True)

        if payload.review_type not in VALID_REVIEW_TYPES:
            raise ValueError(f"Invalid review_type '{payload.review_type}'. Allowed: {VALID_REVIEW_TYPES}")

        if payload.decision not in VALID_HUMAN_DECISIONS:
            raise ValueError(f"Invalid decision '{payload.decision}'. Allowed: {VALID_HUMAN_DECISIONS}")

        now_utc = datetime.now(timezone.utc)

        # Handle optional status transition
        prev_status = case.status
        new_status = payload.new_status
        if new_status:
            if new_status not in VALID_CASE_STATUSES:
                raise ValueError(f"Invalid target status '{new_status}'. Allowed: {VALID_CASE_STATUSES}")
            if new_status != prev_status:
                allowed_next = VALID_STATUS_TRANSITIONS.get(prev_status, set())
                if new_status not in allowed_next:
                    raise ValueError(
                        f"Status transition from '{prev_status}' to '{new_status}' is not permitted. "
                        f"Allowed transitions from '{prev_status}': {sorted(list(allowed_next))}"
                    )
                case.status = new_status
                case.updated_at = now_utc
                cls._log_audit(
                    db=db,
                    case_id=case.id,
                    action="STATUS_CHANGED",
                    actor_id=current_user.id,
                    previous_status=prev_status,
                    new_status=new_status,
                    metadata={"reason": f"Status update triggered by {payload.review_type} review."},
                )

        review = WelfareCaseReview(
            case_id=case.id,
            reviewer_id=current_user.id,
            reviewed_at=now_utc,
            review_type=payload.review_type,
            observations=payload.observations.strip(),
            decision=payload.decision,
            next_step=payload.next_step.strip() if payload.next_step else None,
            review_window=payload.review_window or "Within 14 days",
            notes=payload.notes.strip() if payload.notes else None,
        )
        db.add(review)

        # Update case metadata
        case.last_reviewed_at = now_utc
        case.last_reviewed_by = current_user.id
        case.updated_at = now_utc

        db.flush()

        cls._log_audit(
            db=db,
            case_id=case.id,
            action="CASE_REVIEWED",
            actor_id=current_user.id,
            previous_status=prev_status,
            new_status=case.status,
            metadata={
                "review_id": review.id,
                "review_type": payload.review_type,
                "decision": payload.decision,
                "review_window": payload.review_window,
            },
        )
        db.commit()
        db.refresh(review)
        logger.info(f"Recorded human review (ID: {review.id}) on case '{case.case_reference}' by '{current_user.username}'.")
        return review

    # -------------------------------------------------------------------------
    # CASE NOTES (IMMUTABLE)
    # -------------------------------------------------------------------------
    @classmethod
    def add_note(
        cls,
        case_id: int,
        payload: WelfareCaseNoteCreateRequest,
        current_user: User,
        db: Session,
    ) -> WelfareCaseNote:
        """
        Appends an immutable note to the case history. Overwrites are forbidden.
        """
        case = db.query(WelfareCase).options(joinedload(WelfareCase.personnel)).filter(WelfareCase.id == case_id).first()
        if not case:
            raise LookupError(f"WelfareCase ID {case_id} not found.")

        cls.verify_case_access(case, current_user, require_write=True)

        if payload.note_type not in VALID_NOTE_TYPES:
            raise ValueError(f"Invalid note_type '{payload.note_type}'. Allowed: {VALID_NOTE_TYPES}")

        now_utc = datetime.now(timezone.utc)
        note = WelfareCaseNote(
            case_id=case.id,
            author_id=current_user.id,
            created_at=now_utc,
            note_type=payload.note_type,
            content=payload.content.strip(),
        )
        db.add(note)
        case.updated_at = now_utc
        db.flush()

        cls._log_audit(
            db=db,
            case_id=case.id,
            action="NOTE_ADDED",
            actor_id=current_user.id,
            previous_status=case.status,
            new_status=case.status,
            metadata={"note_id": note.id, "note_type": payload.note_type},
        )
        db.commit()
        db.refresh(note)
        return note

    # -------------------------------------------------------------------------
    # STATUS TRANSITIONS
    # -------------------------------------------------------------------------
    @classmethod
    def update_status(
        cls,
        case_id: int,
        payload: WelfareCaseStatusUpdateRequest,
        current_user: User,
        db: Session,
    ) -> WelfareCase:
        """
        Transitions case status through controlled lifecycle.
        Arbitrary or unpermitted state hops are rejected.
        """
        case = db.query(WelfareCase).options(joinedload(WelfareCase.personnel)).filter(WelfareCase.id == case_id).first()
        if not case:
            raise LookupError(f"WelfareCase ID {case_id} not found.")

        cls.verify_case_access(case, current_user, require_write=True)

        target = payload.status
        if target not in VALID_CASE_STATUSES:
            raise ValueError(f"Invalid target status '{target}'. Allowed: {VALID_CASE_STATUSES}")

        prev = case.status
        if prev == target:
            return case

        # Terminal state protection
        if prev == "CLOSED" and target != "OPEN":
            raise ValueError("Case is CLOSED. A closed case can only be reopened to 'OPEN' using the reopen action.")

        allowed_next = VALID_STATUS_TRANSITIONS.get(prev, set())
        if target not in allowed_next:
            raise ValueError(
                f"Status transition from '{prev}' to '{target}' is not permitted. "
                f"Permitted next states from '{prev}': {sorted(list(allowed_next))}"
            )

        now_utc = datetime.now(timezone.utc)
        case.status = target
        case.updated_at = now_utc

        cls._log_audit(
            db=db,
            case_id=case.id,
            action="STATUS_CHANGED",
            actor_id=current_user.id,
            previous_status=prev,
            new_status=target,
            metadata={"reason": payload.reason or "Explicit human status transition."},
        )
        db.commit()
        db.refresh(case)
        return case

    # -------------------------------------------------------------------------
    # CASE CLOSURE
    # -------------------------------------------------------------------------
    @classmethod
    def close_case(
        cls,
        case_id: int,
        payload: WelfareCaseCloseRequest,
        current_user: User,
        db: Session,
    ) -> WelfareCase:
        """
        Closes a case via explicit human action.
        Requires a structured closure reason. Cases are NEVER automatically closed.
        """
        case = db.query(WelfareCase).options(joinedload(WelfareCase.personnel)).filter(WelfareCase.id == case_id).first()
        if not case:
            raise LookupError(f"WelfareCase ID {case_id} not found.")

        cls.verify_case_access(case, current_user, require_write=True)

        if case.status == "CLOSED":
            raise ValueError(f"Case '{case.case_reference}' is already closed.")

        if payload.closure_reason not in VALID_CLOSURE_REASONS:
            raise ValueError(f"Invalid closure_reason '{payload.closure_reason}'. Allowed: {VALID_CLOSURE_REASONS}")

        prev_status = case.status
        now_utc = datetime.now(timezone.utc)

        case.status = "CLOSED"
        case.closed_at = now_utc
        case.closed_by = current_user.id
        case.closure_reason = payload.closure_reason
        case.closure_notes = payload.closure_notes.strip() if payload.closure_notes else None
        case.updated_at = now_utc

        cls._log_audit(
            db=db,
            case_id=case.id,
            action="CASE_CLOSED",
            actor_id=current_user.id,
            previous_status=prev_status,
            new_status="CLOSED",
            metadata={
                "closure_reason": payload.closure_reason,
                "closure_notes": payload.closure_notes,
            },
        )
        db.commit()
        db.refresh(case)
        logger.info(f"Case '{case.case_reference}' closed by '{current_user.username}'. Reason: {payload.closure_reason}")
        return case

    # -------------------------------------------------------------------------
    # CASE REOPENING
    # -------------------------------------------------------------------------
    @classmethod
    def reopen_case(
        cls,
        case_id: int,
        payload: WelfareCaseReopenRequest,
        current_user: User,
        db: Session,
    ) -> WelfareCase:
        """
        Reopens a previously closed case (CLOSED -> OPEN) through explicit human action.
        Records reviewer identity, reopen timestamp, and mandatory justification.
        """
        case = db.query(WelfareCase).options(joinedload(WelfareCase.personnel)).filter(WelfareCase.id == case_id).first()
        if not case:
            raise LookupError(f"WelfareCase ID {case_id} not found.")

        cls.verify_case_access(case, current_user, require_write=True)

        if case.status != "CLOSED":
            raise ValueError(f"Cannot reopen case '{case.case_reference}': only CLOSED cases can be reopened (current: {case.status}).")

        now_utc = datetime.now(timezone.utc)
        prev_status = case.status

        case.status = "OPEN"
        case.reopened_at = now_utc
        case.reopened_by = current_user.id
        case.reopen_reason = payload.reopen_reason.strip()
        case.closed_at = None
        case.closed_by = None
        case.closure_reason = None
        case.closure_notes = None
        case.updated_at = now_utc

        cls._log_audit(
            db=db,
            case_id=case.id,
            action="CASE_REOPENED",
            actor_id=current_user.id,
            previous_status=prev_status,
            new_status="OPEN",
            metadata={"reopen_reason": payload.reopen_reason},
        )
        db.commit()
        db.refresh(case)
        logger.info(f"Case '{case.case_reference}' reopened by '{current_user.username}'. Reason: {payload.reopen_reason}")
        return case

    # -------------------------------------------------------------------------
    # SIGNAL LINKING
    # -------------------------------------------------------------------------
    @classmethod
    def link_signals(
        cls,
        case_id: int,
        signals: Dict[str, Optional[int]],
        current_user: User,
        db: Session,
    ) -> WelfareCase:
        """
        Explicitly links authoritative signals (assessments, alerts, anomalies,
        recommendations, interventions, followups) to a case.
        """
        case = db.query(WelfareCase).options(joinedload(WelfareCase.personnel)).filter(WelfareCase.id == case_id).first()
        if not case:
            raise LookupError(f"WelfareCase ID {case_id} not found.")

        cls.verify_case_access(case, current_user, require_write=True)

        updated_fields = {}
        for key in ["assessment_id", "alert_id", "anomaly_id", "recommendation_id", "intervention_id", "followup_id"]:
            val = signals.get(key)
            if val is not None:
                setattr(case, key, val)
                updated_fields[key] = val

        if updated_fields:
            case.updated_at = datetime.now(timezone.utc)
            cls._log_audit(
                db=db,
                case_id=case.id,
                action="SIGNALS_LINKED",
                actor_id=current_user.id,
                previous_status=case.status,
                new_status=case.status,
                metadata={"linked_fields": updated_fields},
            )
            db.commit()
            db.refresh(case)

        return case

    # -------------------------------------------------------------------------
    # BATCHED CASE LIST QUERY (NO N+1)
    # -------------------------------------------------------------------------
    @classmethod
    def get_cases_list(
        cls,
        db: Session,
        current_user: User,
        status: Optional[str] = None,
        case_type: Optional[str] = None,
        search: Optional[str] = None,
        personnel_id: Optional[int] = None,
        battalion: Optional[str] = None,
        location: Optional[str] = None,
        limit: int = 100,
        offset: int = 0,
    ) -> WelfareCaseListResponse:
        """
        Retrieves an authorized, unranked case roster.
        Batch loads associated signals to guarantee ZERO N+1 database queries.
        Preserves stable non-evaluative ordering: updated_at DESC, case_reference ASC.
        """
        role = (getattr(current_user, "role", "") or "").lower()

        # Build base query with eager joins
        query = db.query(WelfareCase).join(Personnel, WelfareCase.personnel_id == Personnel.id)

        # 1. RBAC & Organizational Scoping
        if role == "personnel":
            user_p_id = getattr(current_user, "personnel_id", None)
            if not user_p_id:
                return WelfareCaseListResponse(cases=[], total_count=0)
            query = query.filter(WelfareCase.personnel_id == user_p_id)
        elif role in ["officer", "welfare", "doctor", "psychologist"]:
            user_bat = getattr(current_user, "battalion", None)
            user_loc = getattr(current_user, "location", None)
            if user_bat:
                query = query.filter(func.lower(Personnel.battalion) == user_bat.strip().lower())
            if user_loc:
                query = query.filter(func.lower(Personnel.location) == user_loc.strip().lower())
        elif role in ["admin", "superadmin"]:
            # Broader filter if requested
            if battalion:
                query = query.filter(func.lower(Personnel.battalion) == battalion.strip().lower())
            if location:
                query = query.filter(func.lower(Personnel.location) == location.strip().lower())
        else:
            raise PermissionError("Access forbidden: Insufficient authorization level.")

        # 2. Specific filters
        if personnel_id:
            query = query.filter(WelfareCase.personnel_id == personnel_id)

        if status:
            if status != "ALL":
                query = query.filter(WelfareCase.status == status.upper())

        if case_type:
            if case_type != "ALL":
                query = query.filter(WelfareCase.case_type == case_type.upper())

        if search:
            s = f"%{search.strip().lower()}%"
            query = query.filter(
                or_(
                    func.lower(WelfareCase.case_reference).like(s),
                    func.lower(WelfareCase.title).like(s),
                    func.lower(Personnel.personnel_code).like(s),
                    func.lower(Personnel.name).like(s),
                )
            )

        total_count = query.count()

        # 3. Stable, non-evaluative ordering: updated_at DESC, case_reference ASC
        cases: List[WelfareCase] = (
            query.options(
                joinedload(WelfareCase.personnel),
                joinedload(WelfareCase.opener),
                joinedload(WelfareCase.last_reviewer),
                joinedload(WelfareCase.closer),
            )
            .order_by(WelfareCase.updated_at.desc(), WelfareCase.case_reference.asc())
            .offset(offset)
            .limit(limit)
            .all()
        )

        if not cases:
            return WelfareCaseListResponse(cases=[], total_count=total_count)

        # 4. Batch query signals for all personnel in the current page (BATCH LOADING: NO N+1)
        target_personnel_ids = list({c.personnel_id for c in cases})

        # Batch assessments (latest per personnel)
        latest_assessments_map: Dict[int, StressAssessment] = {}
        all_assessments = (
            db.query(StressAssessment)
            .filter(StressAssessment.personnel_id.in_(target_personnel_ids))
            .order_by(StressAssessment.personnel_id, StressAssessment.assessment_timestamp.asc())
            .all()
        )
        for ass in all_assessments:
            latest_assessments_map[ass.personnel_id] = ass  # last one per personnel will overwrite

        # Batch active alerts
        active_alerts_map: Dict[int, WelfareAlert] = {}
        all_active_alerts = (
            db.query(WelfareAlert)
            .filter(
                WelfareAlert.personnel_id.in_(target_personnel_ids),
                WelfareAlert.status.in_(["OPEN", "ACKNOWLEDGED", "UNDER_REVIEW", "INTERVENTION_PLANNED", "FOLLOW_UP"]),
            )
            .order_by(WelfareAlert.created_at.desc())
            .all()
        )
        for al in all_active_alerts:
            if al.personnel_id not in active_alerts_map:
                active_alerts_map[al.personnel_id] = al

        # Batch active anomalies
        active_anomalies_map: Dict[int, WelfareAnomaly] = {}
        all_active_anomalies = (
            db.query(WelfareAnomaly)
            .filter(
                WelfareAnomaly.personnel_id.in_(target_personnel_ids),
                WelfareAnomaly.status.in_(["DETECTED", "UNDER_REVIEW"]),
            )
            .order_by(WelfareAnomaly.detected_at.desc())
            .all()
        )
        for an in all_active_anomalies:
            if an.personnel_id not in active_anomalies_map:
                active_anomalies_map[an.personnel_id] = an

        # Batch open recommendations
        open_recs_map: Dict[int, WelfareRecommendation] = {}
        all_open_recs = (
            db.query(WelfareRecommendation)
            .filter(
                WelfareRecommendation.personnel_id.in_(target_personnel_ids),
                WelfareRecommendation.status.in_(["SUGGESTED", "ACKNOWLEDGED"]),
            )
            .order_by(WelfareRecommendation.created_at.desc())
            .all()
        )
        for rec in all_open_recs:
            if rec.personnel_id not in open_recs_map:
                open_recs_map[rec.personnel_id] = rec

        # Batch active interventions
        interventions_map: Dict[int, WelfareIntervention] = {}
        all_interventions = (
            db.query(WelfareIntervention)
            .filter(WelfareIntervention.personnel_id.in_(target_personnel_ids))
            .order_by(WelfareIntervention.created_at.desc())
            .all()
        )
        for itv in all_interventions:
            if itv.personnel_id not in interventions_map:
                interventions_map[itv.personnel_id] = itv

        # Batch latest followups
        followups_map: Dict[int, WelfareFollowup] = {}
        all_followups = (
            db.query(WelfareFollowup)
            .filter(WelfareFollowup.personnel_id.in_(target_personnel_ids))
            .order_by(WelfareFollowup.created_at.desc())
            .all()
        )
        for fup in all_followups:
            if fup.personnel_id not in followups_map:
                followups_map[fup.personnel_id] = fup

        # Assemble items
        items: List[WelfareCaseListItemOut] = []
        for c in cases:
            p = c.personnel
            pid = c.personnel_id

            lat_ass = latest_assessments_map.get(pid)
            act_alt = active_alerts_map.get(pid)
            act_anom = active_anomalies_map.get(pid)
            opn_rec = open_recs_map.get(pid)
            lat_itv = interventions_map.get(pid)
            lat_fup = followups_map.get(pid)

            signals_summary = SignalsSummaryOut(
                current_risk_category=lat_ass.stress_level if lat_ass else None,
                trend_direction="STABLE" if lat_ass else "INSUFFICIENT_DATA",
                has_active_alert=act_alt is not None,
                alert_severity=act_alt.severity if act_alt else None,
                has_active_anomaly=act_anom is not None,
                anomaly_severity=act_anom.severity if act_anom else None,
                has_open_recommendation=opn_rec is not None,
                recommendation_priority=opn_rec.priority if opn_rec else None,
                intervention_status=lat_itv.status if lat_itv else None,
                followup_status=lat_fup.status if lat_fup else None,
                latest_outcome=lat_fup.outcome_status if lat_fup else None,
            )

            opener_name = c.opener.username if c.opener else None
            reviewer_name = c.last_reviewer.username if c.last_reviewer else None

            items.append(
                WelfareCaseListItemOut(
                    id=c.id,
                    case_reference=c.case_reference,
                    personnel_id=p.id,
                    personnel_code=p.personnel_code,
                    personnel_name=p.name,
                    department=p.department,
                    battalion=p.battalion,
                    location=p.location,
                    status=c.status,
                    case_type=c.case_type,
                    trigger_source=c.trigger_source,
                    title=c.title,
                    summary=c.summary,
                    opened_at=c.opened_at,
                    opened_by_name=opener_name,
                    last_reviewed_at=c.last_reviewed_at,
                    last_reviewed_by_name=reviewer_name,
                    closed_at=c.closed_at,
                    closure_reason=c.closure_reason,
                    signals_summary=signals_summary,
                    created_at=c.created_at,
                    updated_at=c.updated_at,
                )
            )

        return WelfareCaseListResponse(cases=items, total_count=total_count)

    # -------------------------------------------------------------------------
    # CASE DETAIL & EVIDENCE
    # -------------------------------------------------------------------------
    @classmethod
    def get_case_detail(
        cls,
        case_id: int,
        current_user: User,
        db: Session,
    ) -> WelfareCaseDetailOut:
        """
        Retrieves the complete welfare case workspace record including
        authoritative evidence signals, human reviews, notes, and audit summaries.
        """
        case = (
            db.query(WelfareCase)
            .options(
                joinedload(WelfareCase.personnel),
                joinedload(WelfareCase.opener),
                joinedload(WelfareCase.last_reviewer),
                joinedload(WelfareCase.closer),
                joinedload(WelfareCase.reopener),
                joinedload(WelfareCase.reviews).joinedload(WelfareCaseReview.reviewer),
                joinedload(WelfareCase.notes).joinedload(WelfareCaseNote.author),
                joinedload(WelfareCase.audits).joinedload(WelfareCaseAudit.actor),
            )
            .filter(WelfareCase.id == case_id)
            .first()
        )
        if not case:
            raise LookupError(f"WelfareCase ID {case_id} not found.")

        cls.verify_case_access(case, current_user, require_write=False)
        personnel = case.personnel

        # Assemble authoritative evidence without computing any new score
        snapshot = UnifiedWelfareIntelligenceService.get_personnel_welfare_snapshot(
            db=db,
            current_user=current_user,
            personnel_id=personnel.id,
        )

        alerts_list = snapshot.get("alerts") or snapshot.get("active_alerts") or []
        anomalies_list = snapshot.get("anomalies") or snapshot.get("active_anomalies") or []
        recs_list = snapshot.get("recommendations") or snapshot.get("open_recommendations") or []
        interventions_list = snapshot.get("interventions") or snapshot.get("active_interventions") or []
        followups_list = snapshot.get("followups") or snapshot.get("pending_followups") or []

        evidence = WelfareCaseEvidenceOut(
            current_risk=snapshot.get("current_risk") or {},
            trend=snapshot.get("trend") or {},
            active_alert=alerts_list[0] if alerts_list else None,
            active_anomaly=anomalies_list[0] if anomalies_list else None,
            open_recommendation=recs_list[0] if recs_list else None,
            intervention=interventions_list[0] if interventions_list else None,
            followup=followups_list[0] if followups_list else None,
            outcome=snapshot.get("recent_completed_followups", [None])[0] if snapshot.get("recent_completed_followups") else None,
            notice="Authoritative evidence consolidated from Phases 34–41. No composite score computed.",
        )

        # Reviews
        reviews_out: List[WelfareCaseReviewOut] = []
        for r in case.reviews:
            rev_name = r.reviewer.username if r.reviewer else None
            rev_role = r.reviewer.role if r.reviewer else None
            reviews_out.append(
                WelfareCaseReviewOut(
                    id=r.id,
                    case_id=r.case_id,
                    reviewer_id=r.reviewer_id,
                    reviewer_name=rev_name,
                    reviewer_role=rev_role,
                    reviewed_at=r.reviewed_at,
                    review_type=r.review_type,
                    observations=r.observations,
                    decision=r.decision,
                    next_step=r.next_step,
                    review_window=r.review_window,
                    notes=r.notes,
                )
            )

        # Notes
        notes_out: List[WelfareCaseNoteOut] = []
        for n in case.notes:
            auth_name = n.author.username if n.author else None
            auth_role = n.author.role if n.author else None
            notes_out.append(
                WelfareCaseNoteOut(
                    id=n.id,
                    case_id=n.case_id,
                    author_id=n.author_id,
                    author_name=auth_name,
                    author_role=auth_role,
                    created_at=n.created_at,
                    note_type=n.note_type,
                    content=n.content,
                )
            )

        # Latest audit
        latest_audit_out = None
        if case.audits:
            lat = case.audits[0]
            lat_actor = lat.actor.username if lat.actor else None
            meta = {}
            if lat.metadata_json:
                try:
                    meta = json.loads(lat.metadata_json)
                except Exception:
                    meta = {"raw": lat.metadata_json}
            latest_audit_out = WelfareCaseAuditOut(
                id=lat.id,
                case_id=lat.case_id,
                action=lat.action,
                actor_id=lat.actor_id,
                actor_name=lat_actor,
                previous_status=lat.previous_status,
                new_status=lat.new_status,
                timestamp=lat.timestamp,
                metadata=meta,
            )

        return WelfareCaseDetailOut(
            id=case.id,
            case_reference=case.case_reference,
            personnel_id=personnel.id,
            personnel_code=personnel.personnel_code,
            personnel_name=personnel.name,
            department=personnel.department,
            battalion=personnel.battalion,
            location=personnel.location,
            job_role=personnel.job_role,
            status=case.status,
            case_type=case.case_type,
            trigger_source=case.trigger_source,
            title=case.title,
            summary=case.summary,
            opened_at=case.opened_at,
            opened_by_id=case.opened_by,
            opened_by_name=case.opener.username if case.opener else None,
            last_reviewed_at=case.last_reviewed_at,
            last_reviewed_by_id=case.last_reviewed_by,
            last_reviewed_by_name=case.last_reviewer.username if case.last_reviewer else None,
            closed_at=case.closed_at,
            closed_by_id=case.closed_by,
            closed_by_name=case.closer.username if case.closer else None,
            closure_reason=case.closure_reason,
            closure_notes=case.closure_notes,
            reopened_at=case.reopened_at,
            reopened_by_id=case.reopened_by,
            reopened_by_name=case.reopener.username if case.reopener else None,
            reopen_reason=case.reopen_reason,
            assessment_id=case.assessment_id,
            alert_id=case.alert_id,
            anomaly_id=case.anomaly_id,
            recommendation_id=case.recommendation_id,
            intervention_id=case.intervention_id,
            followup_id=case.followup_id,
            evidence=evidence,
            reviews=reviews_out,
            notes=notes_out,
            latest_audit=latest_audit_out,
            created_at=case.created_at,
            updated_at=case.updated_at,
        )

    # -------------------------------------------------------------------------
    # CASE TIMELINE
    # -------------------------------------------------------------------------
    @classmethod
    def get_case_timeline(
        cls,
        case_id: int,
        current_user: User,
        db: Session,
    ) -> WelfareCaseTimelineResponse:
        """
        Synthesizes a unified chronological event timeline for the case.
        Strictly distinguishes SYSTEM EVENT from HUMAN ACTION using true timestamps.
        """
        case = (
            db.query(WelfareCase)
            .options(
                joinedload(WelfareCase.personnel),
                joinedload(WelfareCase.opener),
                joinedload(WelfareCase.reviews).joinedload(WelfareCaseReview.reviewer),
                joinedload(WelfareCase.notes).joinedload(WelfareCaseNote.author),
                joinedload(WelfareCase.audits).joinedload(WelfareCaseAudit.actor),
            )
            .filter(WelfareCase.id == case_id)
            .first()
        )
        if not case:
            raise LookupError(f"WelfareCase ID {case_id} not found.")

        cls.verify_case_access(case, current_user, require_write=False)
        personnel = case.personnel
        events: List[TimelineEventOut] = []

        # 1. Human Action: Case Opened
        events.append(
            TimelineEventOut(
                id=f"case-open-{case.id}",
                event_type="HUMAN_ACTION",
                category="CASE_CREATED",
                timestamp=case.opened_at,
                title=f"Welfare Case Opened ({case.case_reference})",
                description=f"Case opened by {case.opener.username if case.opener else 'Authorized Reviewer'}. Reason: {case.case_type.replace('_', ' ').title()}.",
                actor=case.opener.username if case.opener else None,
                metadata={"trigger_source": case.trigger_source, "summary": case.summary},
            )
        )

        # 2. Human Actions: Reviews
        for rev in case.reviews:
            rev_actor = rev.reviewer.username if rev.reviewer else "Reviewer"
            events.append(
                TimelineEventOut(
                    id=f"case-review-{rev.id}",
                    event_type="HUMAN_ACTION",
                    category="HUMAN_REVIEW",
                    timestamp=rev.reviewed_at,
                    title=f"Human Review Completed ({rev.review_type.replace('_', ' ').title()})",
                    description=f"Decision: {rev.decision.replace('_', ' ').title()}. Observations: {rev.observations[:100]}...",
                    actor=rev_actor,
                    metadata={
                        "decision": rev.decision,
                        "review_window": rev.review_window,
                        "next_step": rev.next_step,
                    },
                )
            )

        # 3. Human Actions: Notes
        for note in case.notes:
            auth_actor = note.author.username if note.author else "Reviewer"
            events.append(
                TimelineEventOut(
                    id=f"case-note-{note.id}",
                    event_type="HUMAN_ACTION",
                    category="NOTE_ADDED",
                    timestamp=note.created_at,
                    title=f"Note Added ({note.note_type.replace('_', ' ').title()})",
                    description=note.content[:120] + ("..." if len(note.content) > 120 else ""),
                    actor=auth_actor,
                    metadata={"note_type": note.note_type},
                )
            )

        # 4. Human Actions: Audits (Status changes, closure, reopen)
        for aud in case.audits:
            act_actor = aud.actor.username if aud.actor else "System/Reviewer"
            if aud.action in ["CASE_CLOSED", "CASE_REOPENED", "STATUS_CHANGED"]:
                events.append(
                    TimelineEventOut(
                        id=f"case-audit-{aud.id}",
                        event_type="HUMAN_ACTION",
                        category=aud.action,
                        timestamp=aud.timestamp,
                        title=f"Case Lifecycle: {aud.action.replace('_', ' ').title()}",
                        description=f"Status changed from '{aud.previous_status}' to '{aud.new_status}'.",
                        actor=act_actor,
                        metadata=json.loads(aud.metadata_json or "{}"),
                    )
                )

        # 5. System Events: Stress Assessments (Phase 34)
        assessments = (
            db.query(StressAssessment)
            .filter(StressAssessment.personnel_id == personnel.id)
            .order_by(StressAssessment.assessment_timestamp.desc())
            .limit(10)
            .all()
        )
        for ass in assessments:
            if ass.assessment_timestamp:
                events.append(
                    TimelineEventOut(
                        id=f"sys-ass-{ass.id}",
                        event_type="SYSTEM_EVENT",
                        category="RISK_ASSESSMENT",
                        timestamp=ass.assessment_timestamp,
                        title=f"Phase 34 Risk Assessment (Score: {ass.risk_score:.1f})",
                        description=f"Stress Level: {ass.stress_level} • Priority: {ass.risk_priority}",
                        actor="Phase 34 Risk Engine",
                        metadata={"risk_score": ass.risk_score, "stress_level": ass.stress_level},
                    )
                )

        # 6. System Events: Welfare Alerts (Phase 37)
        alerts = (
            db.query(WelfareAlert)
            .filter(WelfareAlert.personnel_id == personnel.id)
            .order_by(WelfareAlert.created_at.desc())
            .limit(10)
            .all()
        )
        for al in alerts:
            if al.created_at:
                events.append(
                    TimelineEventOut(
                        id=f"sys-alert-{al.id}",
                        event_type="SYSTEM_EVENT",
                        category="ALERT",
                        timestamp=al.created_at,
                        title=f"Phase 37 Welfare Alert Generated ({al.severity})",
                        description=f"Type: {al.alert_type} • Status: {al.status}. Reason: {al.trigger_reason}",
                        actor="Phase 37 Alert Engine",
                        metadata={"severity": al.severity, "status": al.status},
                    )
                )

        # 7. System Events: Anomalies (Phase 39)
        anomalies = (
            db.query(WelfareAnomaly)
            .filter(WelfareAnomaly.personnel_id == personnel.id)
            .order_by(WelfareAnomaly.detected_at.desc())
            .limit(10)
            .all()
        )
        for an in anomalies:
            if an.detected_at:
                events.append(
                    TimelineEventOut(
                        id=f"sys-anom-{an.id}",
                        event_type="SYSTEM_EVENT",
                        category="ANOMALY",
                        timestamp=an.detected_at,
                        title=f"Phase 39 Anomaly Detected ({an.severity})",
                        description=f"Type: {an.anomaly_type} • {an.explanation}",
                        actor="Phase 39 Anomaly Detector",
                        metadata={"severity": an.severity, "anomaly_type": an.anomaly_type},
                    )
                )

        # 8. System Events: Recommendations (Phase 40)
        recs = (
            db.query(WelfareRecommendation)
            .filter(WelfareRecommendation.personnel_id == personnel.id)
            .order_by(WelfareRecommendation.created_at.desc())
            .limit(10)
            .all()
        )
        for r in recs:
            if r.created_at:
                events.append(
                    TimelineEventOut(
                        id=f"sys-rec-{r.id}",
                        event_type="SYSTEM_EVENT",
                        category="RECOMMENDATION",
                        timestamp=r.created_at,
                        title=f"Phase 40 Support Recommendation Generated ({r.priority})",
                        description=f"{r.title or r.recommendation_type}: {r.description or ''}",
                        actor="Phase 40 Recommendation Engine",
                        metadata={"priority": r.priority, "status": r.status},
                    )
                )

        # 9. Followups & Outcomes (Phase 41)
        followups = (
            db.query(WelfareFollowup)
            .filter(WelfareFollowup.personnel_id == personnel.id)
            .order_by(WelfareFollowup.created_at.desc())
            .limit(10)
            .all()
        )
        for fup in followups:
            if fup.scheduled_at:
                events.append(
                    TimelineEventOut(
                        id=f"human-fup-{fup.id}",
                        event_type="HUMAN_ACTION",
                        category="FOLLOWUP",
                        timestamp=fup.scheduled_at,
                        title=f"Phase 41 Follow-up Scheduled ({fup.followup_type})",
                        description=f"Due: {fup.due_date.strftime('%Y-%m-%d') if fup.due_date else 'TBD'} • Status: {fup.status}",
                        actor="Welfare Officer",
                        metadata={"status": fup.status, "due_date": str(fup.due_date)},
                    )
                )
            if fup.completed_at:
                events.append(
                    TimelineEventOut(
                        id=f"sys-outcome-{fup.id}",
                        event_type="SYSTEM_EVENT",
                        category="OUTCOME",
                        timestamp=fup.completed_at,
                        title=f"Phase 41 Outcome Evaluated ({fup.outcome_status})",
                        description=f"Follow-up completed. Outcome evaluation: {fup.outcome_status}.",
                        actor="Phase 41 Outcome Engine",
                        metadata={"outcome_status": fup.outcome_status},
                    )
                )

        # Ensure consistent timezone and sort chronologically (descending for presentation)
        def _get_ts(e: TimelineEventOut):
            dt = e.timestamp
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=timezone.utc)
            return dt

        events.sort(key=_get_ts, reverse=True)

        return WelfareCaseTimelineResponse(
            case_id=case.id,
            case_reference=case.case_reference,
            personnel_code=personnel.personnel_code,
            events=events,
        )

    # -------------------------------------------------------------------------
    # CASE AUDITS
    # -------------------------------------------------------------------------
    @classmethod
    def get_case_audits(
        cls,
        case_id: int,
        current_user: User,
        db: Session,
    ) -> WelfareCaseAuditsResponse:
        """Retrieves append-only audit trail for a case."""
        case = db.query(WelfareCase).options(joinedload(WelfareCase.personnel)).filter(WelfareCase.id == case_id).first()
        if not case:
            raise LookupError(f"WelfareCase ID {case_id} not found.")

        cls.verify_case_access(case, current_user, require_write=False)

        audits = (
            db.query(WelfareCaseAudit)
            .options(joinedload(WelfareCaseAudit.actor))
            .filter(WelfareCaseAudit.case_id == case.id)
            .order_by(WelfareCaseAudit.timestamp.desc())
            .all()
        )

        out: List[WelfareCaseAuditOut] = []
        for a in audits:
            act_name = a.actor.username if a.actor else None
            meta = {}
            if a.metadata_json:
                try:
                    meta = json.loads(a.metadata_json)
                except Exception:
                    meta = {"raw": a.metadata_json}
            out.append(
                WelfareCaseAuditOut(
                    id=a.id,
                    case_id=a.case_id,
                    action=a.action,
                    actor_id=a.actor_id,
                    actor_name=act_name,
                    previous_status=a.previous_status,
                    new_status=a.new_status,
                    timestamp=a.timestamp,
                    metadata=meta,
                )
            )

        return WelfareCaseAuditsResponse(
            case_id=case.id,
            case_reference=case.case_reference,
            audits=out,
        )

    # -------------------------------------------------------------------------
    # UNIT SUMMARY STATS (WITH PRIVACY k >= 5 CHECK)
    # -------------------------------------------------------------------------
    @classmethod
    def get_case_summary_stats(
        cls,
        db: Session,
        current_user: User,
        battalion: Optional[str] = None,
        location: Optional[str] = None,
    ) -> WelfareCaseSummaryStatsResponse:
        """
        Computes aggregate status counts across authorized scope.
        Strictly enforces small-group k-anonymity privacy (k >= 5).
        """
        role = (getattr(current_user, "role", "") or "").lower()
        if role == "personnel":
            raise PermissionError("Jawans are not authorized to view unit aggregate case statistics.")

        query = db.query(WelfareCase).join(Personnel, WelfareCase.personnel_id == Personnel.id)

        if role in ["officer", "welfare", "doctor", "psychologist"]:
            user_bat = getattr(current_user, "battalion", None)
            user_loc = getattr(current_user, "location", None)
            if user_bat:
                query = query.filter(func.lower(Personnel.battalion) == user_bat.strip().lower())
            if user_loc:
                query = query.filter(func.lower(Personnel.location) == user_loc.strip().lower())
        elif role in ["admin", "superadmin"]:
            if battalion:
                query = query.filter(func.lower(Personnel.battalion) == battalion.strip().lower())
            if location:
                query = query.filter(func.lower(Personnel.location) == location.strip().lower())

        total_cases = query.count()

        # Enforce small-group privacy
        if 0 < total_cases < ANALYTICS_MIN_GROUP_SIZE:
            logger.info(f"Privacy threshold applied: total cases ({total_cases}) < {ANALYTICS_MIN_GROUP_SIZE}")
            return WelfareCaseSummaryStatsResponse(
                total_cases=total_cases,
                open_cases=0,
                under_review_cases=0,
                monitoring_cases=0,
                closed_cases=0,
                status_counts={},
                data_suppressed=True,
                suppression_reason=f"Cohort case count ({total_cases}) is below the privacy threshold (k >= {ANALYTICS_MIN_GROUP_SIZE}). Breakdown suppressed.",
            )

        status_rows = (
            query.with_entities(WelfareCase.status, func.count(WelfareCase.id))
            .group_by(WelfareCase.status)
            .all()
        )
        counts = {s: cnt for s, cnt in status_rows}

        return WelfareCaseSummaryStatsResponse(
            total_cases=total_cases,
            open_cases=counts.get("OPEN", 0),
            under_review_cases=counts.get("UNDER_REVIEW", 0),
            monitoring_cases=counts.get("MONITORING", 0),
            closed_cases=counts.get("CLOSED", 0),
            status_counts=counts,
            data_suppressed=False,
            suppression_reason=None,
        )
