from typing import Optional
from fastapi import APIRouter, Depends, Query, HTTPException, status, Response
from sqlalchemy.orm import Session

from core.config import logger
from db.session import get_db
from db.models.user import User
from api.deps import get_current_user, require_roles, check_personnel_access
from schemas.notification import (
    WelfareNotificationOut,
    CommanderNotificationSendRequest,
    NotificationListResponse,
    UnreadCountResponse,
)
from services.welfare_notification_service import WelfareNotificationService

router = APIRouter(prefix="/notifications", tags=["Phase 47: Jawan Welfare Notifications"])


@router.get(
    "",
    response_model=NotificationListResponse,
    status_code=status.HTTP_200_OK,
    summary="List Authorized Welfare Notifications",
    description=(
        "Retrieves a list of welfare notifications. "
        "Strictly enforces Anti-IDOR: Jawans can only view their own notifications. "
        "Commanders and welfare officers can view notifications within their battalion scope."
    ),
)
def get_notifications(
    response: Response,
    status_filter: Optional[str] = Query(None, alias="status", description="Filter by status: UNREAD, READ, ACKNOWLEDGED, DISMISSED"),
    personnel_id: Optional[int] = Query(None, description="Target personnel ID (Commanders/Admin only)"),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> NotificationListResponse:
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate, max-age=0"
    response.headers["Pragma"] = "no-cache"
    response.headers["Expires"] = "0"
    if current_user.role == "personnel" and personnel_id is not None and personnel_id != current_user.personnel_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied: You cannot view another personnel's notifications."
        )

    if personnel_id is not None and current_user.role in ["officer", "welfare"]:
        check_personnel_access(current_user, personnel_id, db)

    return WelfareNotificationService.get_notifications_for_user(
        db=db,
        current_user=current_user,
        status_filter=status_filter,
        target_personnel_id=personnel_id,
        limit=limit,
        offset=offset,
    )


@router.get(
    "/unread-count",
    response_model=UnreadCountResponse,
    status_code=status.HTTP_200_OK,
    summary="Get Unread Notification Count",
    description="Returns the count of unread welfare notifications for the authenticated user.",
)
def get_unread_count(
    response: Response,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> UnreadCountResponse:
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate, max-age=0"
    response.headers["Pragma"] = "no-cache"
    response.headers["Expires"] = "0"
    count = WelfareNotificationService.get_unread_count_for_user(db=db, current_user=current_user)
    return UnreadCountResponse(unread_count=count)


@router.get(
    "/{notification_id}",
    response_model=WelfareNotificationOut,
    status_code=status.HTTP_200_OK,
    summary="Get Notification Detail",
    description="Retrieves a single notification by ID with strict Anti-IDOR verification.",
)
def get_notification(
    notification_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> WelfareNotificationOut:
    try:
        notif = WelfareNotificationService.get_notification_with_security_check(
            db=db, notification_id=notification_id, current_user=current_user
        )
        return WelfareNotificationService.serialize_notification(notif, db)
    except LookupError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except PermissionError as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))


@router.post(
    "/{notification_id}/read",
    response_model=WelfareNotificationOut,
    status_code=status.HTTP_200_OK,
    summary="Mark Notification as Read",
    description="Marks a welfare notification as READ and records an audit log.",
)
def mark_notification_read(
    notification_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> WelfareNotificationOut:
    try:
        updated = WelfareNotificationService.mark_as_read(
            db=db, notification_id=notification_id, current_user=current_user
        )
        return WelfareNotificationService.serialize_notification(updated, db)
    except LookupError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except PermissionError as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))


@router.post(
    "/read-all",
    response_model=UnreadCountResponse,
    status_code=status.HTTP_200_OK,
    summary="Mark All Notifications as Read",
    description="Marks all unread notifications for the current authenticated Jawan as READ.",
)
def mark_all_read(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> UnreadCountResponse:
    read_count = WelfareNotificationService.mark_all_as_read(db=db, current_user=current_user)
    return UnreadCountResponse(unread_count=0)


@router.post(
    "/send",
    response_model=WelfareNotificationOut,
    status_code=status.HTTP_201_CREATED,
    summary="Send Authorized Commander Welfare Notification",
    description=(
        "Enables authorized commanders, welfare officers, or admins to send a supportive, "
        "non-punitive welfare notification directly to a personnel within their authorized scope."
    ),
)
def send_welfare_notification(
    payload: CommanderNotificationSendRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles("admin", "officer", "welfare")),
) -> WelfareNotificationOut:
    # 1. Enforce organizational scope on recipient personnel
    check_personnel_access(current_user, payload.recipient_personnel_id, db)

    # 2. Persist notification and audit trail
    try:
        notif = WelfareNotificationService.create_notification(
            db=db,
            recipient_personnel_id=payload.recipient_personnel_id,
            title=payload.title,
            message=payload.message,
            notification_type=payload.notification_type,
            priority=payload.priority or "STANDARD",
            source_type=payload.source_type or "COMMANDER_ACTION",
            source_id=payload.source_id,
            action_url=payload.action_url,
            created_by=current_user.id,
        )
        return WelfareNotificationService.serialize_notification(notif, db)
    except LookupError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
