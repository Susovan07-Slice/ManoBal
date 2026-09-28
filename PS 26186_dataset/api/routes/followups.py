import json
from datetime import datetime, timezone
from typing import Optional, List, Dict, Any
from fastapi import APIRouter, Depends, Query, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import desc

from core.config import logger
from db.session import get_db
from db.models.user import User
from db.models.personnel import Personnel
from db.models.welfare_followup import WelfareFollowup, WelfareFollowupAudit
from api.deps import get_current_user, require_roles
from schemas.followup import (
    WelfareFollowupOut,
    FollowupCreateRequest,
    FollowupScheduleRequest,
    FollowupCompleteRequest,
    FollowupDeferRequest,
    FollowupCancelRequest,
    FollowupAuditOut,
    PersonnelFollowupsResponse,
    UnitFollowupAnalyticsResponse,
)
from services.welfare_outcome_service import WelfareOutcomeService

router = APIRouter(prefix="/followups", tags=["Welfare Follow-Up & Outcome Tracking"])

def _parse_json_field(val: Any) -> Any:
    if not val:
        return {}
    if isinstance(val, (dict, list)):
        return val
    try:
        return json.loads(val)
    except Exception:
        return {"raw": str(val)}

def _serialize_followup(f: WelfareFollowup, db: Session) -> WelfareFollowupOut:
    p_code = None
    p_name = None
    dept = None
    bat = None
    loc = None

    if f.personnel_id:
        p = db.query(Personnel).filter(Personnel.id == f.personnel_id).first()
        if p:
            p_code = p.personnel_code
            p_name = p.name
            dept = p.department
            bat = p.battalion
            loc = p.location

    evidence = _parse_json_field(f.evidence_json)
    if not isinstance(evidence, dict):
        evidence = {"data": evidence}

    # Overdue check
    is_overdue = False
    if f.status in ["PENDING", "SCHEDULED"] and f.due_date:
        dd = f.due_date
        if dd.tzinfo is None:
            dd = dd.replace(tzinfo=timezone.utc)
        is_overdue = dd < datetime.now(timezone.utc)

    return WelfareFollowupOut(
        id=f.id,
        personnel_id=f.personnel_id,
        personnel_code=p_code,
        personnel_name=p_name,
        department=dept,
        battalion=bat,
        location=loc,
        recommendation_id=f.recommendation_id,
        intervention_id=f.intervention_id,
        alert_id=f.alert_id,
        followup_type=f.followup_type,
        status=f.status,
        scheduled_at=f.scheduled_at,
        review_window=f.review_window,
        due_date=f.due_date,
        is_overdue=is_overdue,
        completed_at=f.completed_at,
        created_by=f.created_by,
        completed_by=f.completed_by,
        notes=f.notes,
        outcome_status=f.outcome_status or "INSUFFICIENT_DATA",
        baseline_source=f.baseline_source,
        baseline_assessment_id=f.baseline_assessment_id,
        followup_assessment_id=f.followup_assessment_id,
        evidence=evidence,
        created_at=f.created_at or datetime.now(timezone.utc),
        updated_at=f.updated_at or f.created_at or datetime.now(timezone.utc),
    )

# -----------------------------------------------------------------------------
# 1. LIST FOLLOW-UPS FOR PERSONNEL
# -----------------------------------------------------------------------------
@router.get(
    "/personnel/{personnel_id}",
    response_model=PersonnelFollowupsResponse,
    summary="Get personnel follow-up timeline & records",
)
def get_personnel_followups(
    personnel_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    try:
        WelfareOutcomeService.verify_access_and_get_personnel(personnel_id, current_user, db)
    except LookupError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except PermissionError as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))

    records = (
        db.query(WelfareFollowup)
        .filter(WelfareFollowup.personnel_id == personnel_id)
        .order_by(desc(WelfareFollowup.created_at), desc(WelfareFollowup.id))
        .all()
    )

    items = [_serialize_followup(r, db) for r in records]
    msg = f"Retrieved {len(items)} follow-up record(s)."
    return PersonnelFollowupsResponse(
        personnel_id=personnel_id,
        status="ACTIVE" if items else "NONE",
        message=msg,
        followups=items,
    )

# -----------------------------------------------------------------------------
# 1b. LIST ALL ACCESSIBLE FOLLOW-UPS
# -----------------------------------------------------------------------------
@router.get(
    "",
    response_model=List[WelfareFollowupOut],
    summary="List all accessible welfare follow-up records",
)
def list_followups(
    personnel_id: Optional[int] = Query(None),
    status_filter: Optional[str] = Query(None, alias="status"),
    followup_type: Optional[str] = Query(None),
    outcome_status: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    query = db.query(WelfareFollowup)

    role = (getattr(current_user, "role", "") or "").lower()
    if role in ["admin", "superadmin"]:
        pass
    elif role in ["officer", "welfare", "doctor", "psychologist"]:
        user_bat = getattr(current_user, "battalion", None)
        user_loc = getattr(current_user, "location", None)
        p_query = db.query(Personnel.id)
        if user_bat:
            p_query = p_query.filter(Personnel.battalion == user_bat)
        if user_loc:
            p_query = p_query.filter(Personnel.location == user_loc)
        accessible_ids = [pid for (pid,) in p_query.all()]
        query = query.filter(WelfareFollowup.personnel_id.in_(accessible_ids))
    else:
        user_p_id = getattr(current_user, "personnel_id", None)
        if not user_p_id:
            return []
        query = query.filter(WelfareFollowup.personnel_id == user_p_id)

    if personnel_id:
        try:
            WelfareOutcomeService.verify_access_and_get_personnel(personnel_id, current_user, db)
            query = query.filter(WelfareFollowup.personnel_id == personnel_id)
        except (LookupError, PermissionError):
            return []

    if status_filter:
        query = query.filter(WelfareFollowup.status == status_filter)
    if followup_type:
        query = query.filter(WelfareFollowup.followup_type == followup_type)
    if outcome_status:
        query = query.filter(WelfareFollowup.outcome_status == outcome_status)

    records = query.order_by(desc(WelfareFollowup.created_at), desc(WelfareFollowup.id)).all()
    return [_serialize_followup(r, db) for r in records]

# -----------------------------------------------------------------------------
# 2. CREATE A NEW FOLLOW-UP
# -----------------------------------------------------------------------------
@router.post(
    "",
    response_model=WelfareFollowupOut,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new welfare follow-up record",
)
def create_followup(
    payload: FollowupCreateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles("admin", "officer", "welfare")),
):
    try:
        followup = WelfareOutcomeService.create_followup(
            db=db,
            user=current_user,
            personnel_id=payload.personnel_id,
            followup_type=payload.followup_type,
            recommendation_id=payload.recommendation_id,
            intervention_id=payload.intervention_id,
            alert_id=payload.alert_id,
            review_window=payload.review_window,
            scheduled_at=payload.scheduled_at,
            notes=payload.notes,
        )
        return _serialize_followup(followup, db)
    except LookupError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except PermissionError as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

# -----------------------------------------------------------------------------
# 3. GET SINGLE FOLLOW-UP
# -----------------------------------------------------------------------------
@router.get(
    "/{followup_id}",
    response_model=WelfareFollowupOut,
    summary="Get follow-up record by ID",
)
def get_followup(
    followup_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    followup = db.query(WelfareFollowup).filter(WelfareFollowup.id == followup_id).first()
    if not followup:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Follow-up not found.")

    try:
        WelfareOutcomeService.verify_access_and_get_personnel(followup.personnel_id, current_user, db)
    except LookupError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except PermissionError as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))

    return _serialize_followup(followup, db)

# -----------------------------------------------------------------------------
# 4. SCHEDULE FOLLOW-UP
# -----------------------------------------------------------------------------
@router.post(
    "/{followup_id}/schedule",
    response_model=WelfareFollowupOut,
    summary="Schedule a follow-up review date",
)
def schedule_followup(
    followup_id: int,
    payload: FollowupScheduleRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles("admin", "officer", "welfare")),
):
    try:
        followup = WelfareOutcomeService.schedule_followup(
            db=db,
            followup_id=followup_id,
            user=current_user,
            scheduled_at=payload.scheduled_at,
            notes=payload.notes,
        )
        return _serialize_followup(followup, db)
    except LookupError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except PermissionError as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

# -----------------------------------------------------------------------------
# 5. COMPLETE FOLLOW-UP & RECORD OUTCOME
# -----------------------------------------------------------------------------
@router.post(
    "/{followup_id}/complete",
    response_model=WelfareFollowupOut,
    summary="Complete a follow-up and record observational outcome",
)
def complete_followup(
    followup_id: int,
    payload: Optional[FollowupCompleteRequest] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles("admin", "officer", "welfare")),
):
    try:
        notes = payload.notes if payload else None
        f_ass_id = payload.followup_assessment_id if payload else None
        trigger_rec = payload.trigger_new_recommendation_if_worsening if payload else True

        followup = WelfareOutcomeService.complete_followup(
            db=db,
            followup_id=followup_id,
            user=current_user,
            notes=notes,
            followup_assessment_id=f_ass_id,
            trigger_new_recommendation=trigger_rec,
        )
        return _serialize_followup(followup, db)
    except LookupError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except PermissionError as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

# -----------------------------------------------------------------------------
# 6. DEFER FOLLOW-UP
# -----------------------------------------------------------------------------
@router.post(
    "/{followup_id}/defer",
    response_model=WelfareFollowupOut,
    summary="Defer follow-up review for specified days",
)
def defer_followup(
    followup_id: int,
    payload: FollowupDeferRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles("admin", "officer", "welfare")),
):
    try:
        followup = WelfareOutcomeService.defer_followup(
            db=db,
            followup_id=followup_id,
            user=current_user,
            defer_days=payload.defer_days,
            notes=payload.notes,
        )
        return _serialize_followup(followup, db)
    except LookupError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except PermissionError as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

# -----------------------------------------------------------------------------
# 7. CANCEL FOLLOW-UP
# -----------------------------------------------------------------------------
@router.post(
    "/{followup_id}/cancel",
    response_model=WelfareFollowupOut,
    summary="Cancel follow-up with documented reason",
)
def cancel_followup(
    followup_id: int,
    payload: FollowupCancelRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles("admin", "officer", "welfare")),
):
    try:
        followup = WelfareOutcomeService.cancel_followup(
            db=db,
            followup_id=followup_id,
            user=current_user,
            reason=payload.reason,
        )
        return _serialize_followup(followup, db)
    except LookupError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except PermissionError as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

# -----------------------------------------------------------------------------
# 8. REASSESS OUTCOME
# -----------------------------------------------------------------------------
@router.post(
    "/{followup_id}/reassess-outcome",
    response_model=WelfareFollowupOut,
    summary="Re-evaluate outcome observation with latest subsequent assessment",
)
def reassess_outcome(
    followup_id: int,
    followup_assessment_id: Optional[int] = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles("admin", "officer", "welfare")),
):
    try:
        followup = WelfareOutcomeService.reassess_outcome(
            db=db,
            followup_id=followup_id,
            user=current_user,
            explicit_followup_assessment_id=followup_assessment_id,
        )
        return _serialize_followup(followup, db)
    except LookupError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except PermissionError as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

# -----------------------------------------------------------------------------
# 9. GET FOLLOW-UP AUDIT TRAIL
# -----------------------------------------------------------------------------
@router.get(
    "/{followup_id}/audits",
    response_model=List[FollowupAuditOut],
    summary="Get lifecycle audit logs for a follow-up record",
)
def get_followup_audits(
    followup_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles("admin", "officer", "welfare")),
):
    followup = db.query(WelfareFollowup).filter(WelfareFollowup.id == followup_id).first()
    if not followup:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Follow-up not found.")

    try:
        WelfareOutcomeService.verify_access_and_get_personnel(followup.personnel_id, current_user, db)
    except LookupError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except PermissionError as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))

    audits = (
        db.query(WelfareFollowupAudit)
        .filter(WelfareFollowupAudit.followup_id == followup_id)
        .order_by(WelfareFollowupAudit.timestamp.asc())
        .all()
    )

    out = []
    for a in audits:
        meta = _parse_json_field(a.metadata_json)
        out.append(
            FollowupAuditOut(
                id=a.id,
                followup_id=a.followup_id,
                action=a.action,
                actor_id=a.actor_id,
                previous_status=a.previous_status,
                new_status=a.new_status,
                timestamp=a.timestamp or datetime.now(timezone.utc),
                metadata=meta if isinstance(meta, dict) else {"raw": meta},
            )
        )
    return out

# -----------------------------------------------------------------------------
# 10. UNIT-LEVEL PRIVACY-PRESERVING ANALYTICS
# -----------------------------------------------------------------------------
@router.get(
    "/unit/summary",
    response_model=UnitFollowupAnalyticsResponse,
    summary="Unit-level aggregate follow-up metrics",
)
def get_unit_followup_summary(
    battalion: Optional[str] = Query(None),
    location: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles("admin", "officer", "welfare")),
):
    try:
        data = WelfareOutcomeService.get_unit_followup_analytics(
            db=db,
            user=current_user,
            battalion=battalion,
            location=location,
        )
        return UnitFollowupAnalyticsResponse(**data)
    except PermissionError as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))
