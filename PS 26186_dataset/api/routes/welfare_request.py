from datetime import datetime, timezone
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from sqlalchemy import desc, func

from core.config import logger
from db.session import get_db
from db.models.user import User
from db.models.personnel import Personnel
from db.models.welfare_request import WelfareRequest
from db.models.assessment import StressAssessment
from schemas.welfare_request import (
    WelfareRequestCreate,
    WelfareRequestStatusUpdate,
    WelfareRequestOut,
)
from api.deps import get_current_user, require_roles

router = APIRouter(prefix="/welfare", tags=["Jawan Welfare Requests & Support Workflow"])

def _format_welfare_request_out(req: WelfareRequest, personnel: Optional[Personnel] = None, db: Optional[Session] = None) -> WelfareRequestOut:
    p = personnel or req.personnel
    p_code = p.personnel_code if p else None
    p_name = p.name if p else None
    dept = p.department if p else None
    batt = p.battalion if p else None
    role = p.job_role if p else None
    loc = p.location if p else None

    # Fetch latest assessment risk score if db session provided
    risk_score = None
    stress_level = None
    risk_priority = None
    if db and req.personnel_id:
        latest_ass = (
            db.query(StressAssessment)
            .filter(StressAssessment.personnel_id == req.personnel_id)
            .order_by(desc(StressAssessment.assessment_timestamp))
            .first()
        )
        if latest_ass:
            risk_score = latest_ass.risk_score
            stress_level = latest_ass.stress_level
            risk_priority = latest_ass.risk_priority

    return WelfareRequestOut(
        id=req.id,
        personnel_id=req.personnel_id,
        personnel_code=p_code,
        personnel_name=p_name,
        department=dept,
        battalion=batt,
        job_role=role,
        location=loc,
        current_risk_score=risk_score,
        current_stress_level=stress_level,
        current_risk_priority=risk_priority,
        category=req.category,
        message=req.message,
        urgency=req.urgency,
        status=req.status,
        source="Jawan Request",
        created_at=req.created_at,
        updated_at=req.updated_at,
        resolved_at=req.resolved_at,
    )


@router.post(
    "/requests",
    response_model=WelfareRequestOut,
    status_code=status.HTTP_201_CREATED,
    summary="Submit voluntary Jawan welfare support request"
)
def submit_welfare_request(
    request_in: WelfareRequestCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Voluntary welfare support request initiated by authenticated personnel.
    Binds directly to the authenticated user's personnel record (no spoofing allowed).
    Persists to PostgreSQL and triggers notification in Commander Welfare Alerts.
    """
    if not current_user.personnel_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Current user has no associated personnel profile."
        )

    personnel = db.query(Personnel).filter(Personnel.id == current_user.personnel_id).first()
    if not personnel:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Personnel record with ID {current_user.personnel_id} not found."
        )

    now = datetime.now(timezone.utc)
    new_request = WelfareRequest(
        personnel_id=personnel.id,
        category=request_in.category.strip(),
        message=request_in.message.strip() if request_in.message else None,
        urgency=request_in.urgency,
        status="pending",
        created_at=now,
        updated_at=now,
        resolved_at=None
    )
    db.add(new_request)
    db.commit()
    db.refresh(new_request)

    logger.info(
        f"Welfare request created: ID={new_request.id} for {personnel.personnel_code} "
        f"(Category='{new_request.category}', Urgency='{new_request.urgency}')"
    )

    return _format_welfare_request_out(new_request, personnel, db)


@router.get(
    "/requests/my",
    response_model=List[WelfareRequestOut],
    summary="Get authenticated Jawan's welfare support requests"
)
def get_my_welfare_requests(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Retrieves all personal welfare support requests submitted by the authenticated Jawan.
    Ordered chronologically descending.
    """
    if not current_user.personnel_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Current user has no associated personnel profile."
        )

    requests = (
        db.query(WelfareRequest)
        .filter(WelfareRequest.personnel_id == current_user.personnel_id)
        .order_by(desc(WelfareRequest.created_at))
        .all()
    )

    personnel = db.query(Personnel).filter(Personnel.id == current_user.personnel_id).first()
    return [_format_welfare_request_out(r, personnel, db) for r in requests]


@router.get(
    "/requests",
    response_model=List[WelfareRequestOut],
    summary="List all Jawan welfare support requests within scope (Commander / Welfare Officer / Admin)"
)
def list_welfare_requests(
    status_filter: Optional[str] = Query(None, alias="status"),
    urgency_filter: Optional[str] = Query(None, alias="urgency"),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles("admin", "officer", "welfare"))
):
    """
    Retrieves personnel-initiated welfare support requests.
    Enforces organizational scope: Officers and Welfare users only see requests
    originating from their assigned Battalion + Location.
    """
    query = db.query(WelfareRequest).join(Personnel, WelfareRequest.personnel_id == Personnel.id)

    if current_user.role in ["officer", "welfare"]:
        user_battalion = (current_user.battalion or "").strip().lower()
        user_location = (current_user.location or "").strip().lower()
        query = query.filter(
            func.lower(Personnel.battalion) == user_battalion,
            func.lower(Personnel.location) == user_location
        )

    if status_filter:
        query = query.filter(WelfareRequest.status == status_filter.lower())
    if urgency_filter:
        query = query.filter(WelfareRequest.urgency == urgency_filter)

    requests = query.order_by(desc(WelfareRequest.created_at)).all()
    return [_format_welfare_request_out(r, db=db) for r in requests]


@router.patch(
    "/requests/{request_id}/status",
    response_model=WelfareRequestOut,
    summary="Update Jawan welfare support request status (Scope Enforced)"
)
def update_welfare_request_status(
    request_id: int,
    status_update: WelfareRequestStatusUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles("admin", "officer", "welfare"))
):
    """
    Updates the lifecycle status of a Jawan welfare support request
    ('pending' -> 'acknowledged' -> 'in_progress' -> 'resolved').
    Restricted to Officer, Welfare Officer, and Admin roles.
    Officers can only update requests for personnel in their assigned Battalion and Location.
    """
    req = db.query(WelfareRequest).filter(WelfareRequest.id == request_id).first()
    if not req:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Welfare request ID {request_id} not found."
        )

    # Organizational scope verification
    if current_user.role in ["officer", "welfare"]:
        user_battalion = (current_user.battalion or "").strip().lower()
        user_location = (current_user.location or "").strip().lower()
        p_battalion = (req.personnel.battalion or "").strip().lower()
        p_location = (req.personnel.location or "").strip().lower()

        if not user_battalion or not user_location or user_battalion != p_battalion or user_location != p_location:
            logger.warning(
                f"Scope Violation: User '{current_user.username}' attempted to update out-of-scope welfare request ID {request_id}"
            )
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied: Target personnel is outside your assigned Battalion and Location scope."
            )

    now = datetime.now(timezone.utc)
    old_status = req.status
    req.status = status_update.status
    req.updated_at = now

    if status_update.status == "resolved":
        req.resolved_at = now
    elif old_status == "resolved" and status_update.status != "resolved":
        req.resolved_at = None

    db.commit()
    db.refresh(req)

    logger.info(
        f"Welfare request ID={request_id} status changed from '{old_status}' to '{req.status}' "
        f"by '{current_user.username}' (Role: {current_user.role})"
    )

    return _format_welfare_request_out(req, db=db)
