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
    batt = req.battalion or (p.battalion if p else None)
    role = p.job_role if p else None
    loc = req.location or (p.location if p else None)

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
    if current_user.role not in ["personnel"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only personnel accounts can submit voluntary welfare support requests."
        )

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

    req_category = request_in.category.strip()

    now = datetime.now(timezone.utc)
    new_request = WelfareRequest(
        personnel_id=personnel.id,
        battalion=personnel.battalion,
        location=personnel.location,
        category=req_category,
        message=request_in.message.strip() if request_in.message else None,
        urgency=request_in.urgency,
        status="pending",
        created_at=now,
        updated_at=now,
        resolved_at=None
    )
    try:
        db.add(new_request)
        db.commit()
        db.refresh(new_request)
    except Exception as e:
        db.rollback()
        logger.error(f"Failed to persist welfare request: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to persist welfare request. Transaction rolled back."
        )

    logger.info(
        f"WELFARE_REQUEST_CREATE: user_id={current_user.id} personnel_id={personnel.id} "
        f"personnel_code={personnel.personnel_code} battalion='{new_request.battalion}' "
        f"location='{new_request.location}' request_id={new_request.id} status=pending "
        f"category='{new_request.category}' urgency='{new_request.urgency}'"
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
    "/requests/{request_id}",
    response_model=WelfareRequestOut,
    summary="Get single welfare support request (Scope Enforced)"
)
def get_welfare_request(
    request_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Retrieves a single welfare support request by ID.
    Enforces organizational scope (Officers and Welfare users can only view within their
    assigned Battalion and Location; Jawans can only view their own requests).
    """
    req = db.query(WelfareRequest).filter(WelfareRequest.id == request_id).first()
    if not req:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Welfare request ID {request_id} not found."
        )

    if current_user.role in ["officer", "welfare"]:
        user_battalion = (current_user.battalion or "").strip().lower()
        req_battalion = ((req.battalion or (req.personnel.battalion if req.personnel else "")) or "").strip().lower()
        user_location = (current_user.location or "").strip().lower()
        req_location = ((req.location or (req.personnel.location if req.personnel else "")) or "").strip().lower()

        if (user_battalion and req_battalion and user_battalion != req_battalion) or (user_location and req_location and user_location != req_location):
            logger.warning(
                f"Scope Violation: User '{current_user.username}' attempted to view out-of-scope welfare request ID {request_id}"
            )
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied: Target welfare request is outside your assigned Battalion and Location scope."
            )
    elif current_user.role == "personnel":
        if req.personnel_id != current_user.personnel_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied: You can only view your own welfare requests."
            )

    return _format_welfare_request_out(req, db=db)


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
    originating from their assigned Battalion + Location (strict AND condition).
    """
    query = db.query(WelfareRequest).join(Personnel, WelfareRequest.personnel_id == Personnel.id)

    if current_user.role in ["officer", "welfare"]:
        user_battalion = (current_user.battalion or "").strip().lower()
        user_location = (current_user.location or "").strip().lower()
        if user_battalion:
            query = query.filter(
                func.lower(func.coalesce(WelfareRequest.battalion, Personnel.battalion)) == user_battalion
            )
        if user_location:
            query = query.filter(
                func.lower(func.coalesce(WelfareRequest.location, Personnel.location)) == user_location
            )

    if status_filter:
        query = query.filter(WelfareRequest.status == status_filter.lower())
    if urgency_filter:
        query = query.filter(WelfareRequest.urgency == urgency_filter)

    requests = query.order_by(desc(WelfareRequest.created_at)).all()
    logger.info(
        f"WELFARE_REQUEST_QUERY: commander_id={current_user.id} role={current_user.role} "
        f"battalion='{current_user.battalion}' location='{current_user.location}' "
        f"status_filter={status_filter} urgency_filter={urgency_filter} result_count={len(requests)}"
    )
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
        req_battalion = ((req.battalion or (req.personnel.battalion if req.personnel else "")) or "").strip().lower()
        user_location = (current_user.location or "").strip().lower()
        req_location = ((req.location or (req.personnel.location if req.personnel else "")) or "").strip().lower()

        if (user_battalion and req_battalion and user_battalion != req_battalion) or (user_location and req_location and user_location != req_location):
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

    try:
        db.commit()
        db.refresh(req)
    except Exception as e:
        db.rollback()
        logger.error(f"Failed to update welfare request status: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update welfare request status."
        )

    logger.info(
        f"WELFARE_REQUEST_STATUS_UPDATE: request_id={request_id} commander_id={current_user.id} "
        f"role={current_user.role} old_status='{old_status}' new_status='{req.status}'"
    )

    try:
        from services.welfare_notification_service import WelfareNotificationService
        WelfareNotificationService.notify_on_welfare_request_update(db, req, current_user)
    except Exception as e:
        logger.warning(f"Could not dispatch automated notification for welfare request #{req.id}: {e}")

    return _format_welfare_request_out(req, db=db)
