from typing import Optional, Dict, Any
from fastapi import APIRouter, Depends, Query, HTTPException, status
from sqlalchemy.orm import Session

from core.config import logger
from db.session import get_db
from db.models.user import User
from api.deps import get_current_user, require_roles
from schemas.welfare_case import (
    WelfareCaseCreateRequest,
    WelfareCaseReviewRequest,
    WelfareCaseNoteCreateRequest,
    WelfareCaseStatusUpdateRequest,
    WelfareCaseCloseRequest,
    WelfareCaseReopenRequest,
    WelfareCaseLinkSignalRequest,
    WelfareCaseListItemOut,
    WelfareCaseDetailOut,
    WelfareCaseReviewOut,
    WelfareCaseNoteOut,
    WelfareCaseAuditOut,
    WelfareCaseListResponse,
    WelfareCaseTimelineResponse,
    WelfareCaseAuditsResponse,
    WelfareCaseSummaryStatsResponse,
)
from services.welfare_case_service import WelfareCaseService

router = APIRouter(prefix="/welfare-cases", tags=["Phase 43: Welfare Case Management & Human Review"])


@router.get(
    "",
    response_model=WelfareCaseListResponse,
    status_code=status.HTTP_200_OK,
    summary="List Authorized Welfare Cases",
    description=(
        "Retrieves a list of welfare cases accessible by the authenticated user. "
        "Enforces strict RBAC and organizational scoping. Zero N+1 queries. "
        "Default sorting is stable and non-evaluative (updated_at DESC, case_reference ASC)."
    ),
)
def get_welfare_cases(
    status: Optional[str] = Query(None, description="Filter by status: OPEN, UNDER_REVIEW, MONITORING, CLOSED, etc."),
    case_type: Optional[str] = Query(None, description="Filter by case type: CURRENT_RISK_REVIEW, ACTIVE_ALERT, etc."),
    search: Optional[str] = Query(None, description="Search term matching reference, personnel code, or name"),
    personnel_id: Optional[int] = Query(None, description="Filter by specific personnel ID"),
    battalion: Optional[str] = Query(None, description="Filter by battalion (Admin only)"),
    location: Optional[str] = Query(None, description="Filter by location (Admin only)"),
    limit: int = Query(100, ge=1, le=500),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> WelfareCaseListResponse:
    try:
        return WelfareCaseService.get_cases_list(
            db=db,
            current_user=current_user,
            status=status,
            case_type=case_type,
            search=search,
            personnel_id=personnel_id,
            battalion=battalion,
            location=location,
            limit=limit,
            offset=offset,
        )
    except PermissionError as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.post(
    "",
    response_model=WelfareCaseDetailOut,
    status_code=status.HTTP_201_CREATED,
    summary="Open a New Welfare Case",
    description=(
        "Opens a new welfare case for human review. Authorized for commanders, welfare officers, and admins. "
        "Records reviewer identity, trigger source, and creates an append-only audit trail."
    ),
)
def create_welfare_case(
    payload: WelfareCaseCreateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> WelfareCaseDetailOut:
    try:
        case = WelfareCaseService.create_case(
            payload=payload,
            current_user=current_user,
            db=db,
        )
        return WelfareCaseService.get_case_detail(case.id, current_user, db)
    except LookupError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except PermissionError as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.get(
    "/summary-stats",
    response_model=WelfareCaseSummaryStatsResponse,
    status_code=status.HTTP_200_OK,
    summary="Get Unit Case Summary Statistics",
    description=(
        "Retrieves aggregate case status counts across the authorized unit scope. "
        "Strictly enforces small-group k-anonymity privacy (k >= 5); cohorts with fewer "
        "than 5 cases have breakdown distributions suppressed."
    ),
)
def get_case_summary_stats(
    battalion: Optional[str] = Query(None, description="Battalion filter (Admin)"),
    location: Optional[str] = Query(None, description="Location filter (Admin)"),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles("admin", "officer", "welfare")),
) -> WelfareCaseSummaryStatsResponse:
    try:
        return WelfareCaseService.get_case_summary_stats(
            db=db,
            current_user=current_user,
            battalion=battalion,
            location=location,
        )
    except PermissionError as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))


@router.get(
    "/{case_id}",
    response_model=WelfareCaseDetailOut,
    status_code=status.HTTP_200_OK,
    summary="Get Welfare Case Details & Authoritative Evidence",
    description=(
        "Retrieves complete details of a welfare case including authoritative signals "
        "(risk, trend, alerts, anomalies, recommendations, followups), reviews, and notes. "
        "Strictly enforces Anti-IDOR."
    ),
)
def get_welfare_case_detail(
    case_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> WelfareCaseDetailOut:
    try:
        return WelfareCaseService.get_case_detail(case_id, current_user, db)
    except LookupError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except PermissionError as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))


@router.post(
    "/{case_id}/review",
    response_model=WelfareCaseReviewOut,
    status_code=status.HTTP_201_CREATED,
    summary="Record Human Review & Decision",
    description=(
        "Records a structured human review on a welfare case. "
        "Explicitly separates human decisions from system recommendations. "
        "Optionally transitions case status per controlled lifecycle rules."
    ),
)
def record_case_review(
    case_id: int,
    payload: WelfareCaseReviewRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles("admin", "officer", "welfare")),
) -> WelfareCaseReviewOut:
    try:
        rev = WelfareCaseService.record_review(
            case_id=case_id,
            payload=payload,
            current_user=current_user,
            db=db,
        )
        return WelfareCaseReviewOut(
            id=rev.id,
            case_id=rev.case_id,
            reviewer_id=rev.reviewer_id,
            reviewer_name=current_user.username,
            reviewer_role=current_user.role,
            reviewed_at=rev.reviewed_at,
            review_type=rev.review_type,
            observations=rev.observations,
            decision=rev.decision,
            next_step=rev.next_step,
            review_window=rev.review_window,
            notes=rev.notes,
        )
    except LookupError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except PermissionError as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.post(
    "/{case_id}/notes",
    response_model=WelfareCaseNoteOut,
    status_code=status.HTTP_201_CREATED,
    summary="Add Immutable Case Note",
    description="Appends an immutable observation or support note to the case history.",
)
def add_case_note(
    case_id: int,
    payload: WelfareCaseNoteCreateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles("admin", "officer", "welfare")),
) -> WelfareCaseNoteOut:
    try:
        note = WelfareCaseService.add_note(
            case_id=case_id,
            payload=payload,
            current_user=current_user,
            db=db,
        )
        return WelfareCaseNoteOut(
            id=note.id,
            case_id=note.case_id,
            author_id=note.author_id,
            author_name=current_user.username,
            author_role=current_user.role,
            created_at=note.created_at,
            note_type=note.note_type,
            content=note.content,
        )
    except LookupError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except PermissionError as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.post(
    "/{case_id}/status",
    response_model=WelfareCaseDetailOut,
    status_code=status.HTTP_200_OK,
    summary="Update Case Lifecycle Status",
    description=(
        "Explicitly transitions case status through permitted lifecycle states. "
        "Arbitrary or unpermitted state transitions are rejected."
    ),
)
def update_case_status(
    case_id: int,
    payload: WelfareCaseStatusUpdateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles("admin", "officer", "welfare")),
) -> WelfareCaseDetailOut:
    try:
        case = WelfareCaseService.update_status(
            case_id=case_id,
            payload=payload,
            current_user=current_user,
            db=db,
        )
        return WelfareCaseService.get_case_detail(case.id, current_user, db)
    except LookupError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except PermissionError as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.post(
    "/{case_id}/close",
    response_model=WelfareCaseDetailOut,
    status_code=status.HTTP_200_OK,
    summary="Close Welfare Case",
    description=(
        "Closes a welfare case with mandatory structured closure reason. "
        "Cases are NEVER automatically closed; requires explicit human action."
    ),
)
def close_welfare_case(
    case_id: int,
    payload: WelfareCaseCloseRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles("admin", "officer", "welfare")),
) -> WelfareCaseDetailOut:
    try:
        case = WelfareCaseService.close_case(
            case_id=case_id,
            payload=payload,
            current_user=current_user,
            db=db,
        )
        return WelfareCaseService.get_case_detail(case.id, current_user, db)
    except LookupError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except PermissionError as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.post(
    "/{case_id}/reopen",
    response_model=WelfareCaseDetailOut,
    status_code=status.HTTP_200_OK,
    summary="Reopen Closed Welfare Case",
    description="Reopens a closed case (CLOSED -> OPEN) through explicit human action with mandatory reason.",
)
def reopen_welfare_case(
    case_id: int,
    payload: WelfareCaseReopenRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles("admin", "officer", "welfare")),
) -> WelfareCaseDetailOut:
    try:
        case = WelfareCaseService.reopen_case(
            case_id=case_id,
            payload=payload,
            current_user=current_user,
            db=db,
        )
        return WelfareCaseService.get_case_detail(case.id, current_user, db)
    except LookupError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except PermissionError as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.post(
    "/{case_id}/link-signal",
    response_model=WelfareCaseDetailOut,
    status_code=status.HTTP_200_OK,
    summary="Link Existing Signals to Case",
    description="Explicitly associates authoritative signals (alert, anomaly, recommendation, followup) to a case.",
)
def link_case_signals(
    case_id: int,
    payload: WelfareCaseLinkSignalRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles("admin", "officer", "welfare")),
) -> WelfareCaseDetailOut:
    try:
        case = WelfareCaseService.link_signals(
            case_id=case_id,
            signals=payload.model_dump(),
            current_user=current_user,
            db=db,
        )
        return WelfareCaseService.get_case_detail(case.id, current_user, db)
    except LookupError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except PermissionError as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.get(
    "/{case_id}/timeline",
    response_model=WelfareCaseTimelineResponse,
    status_code=status.HTTP_200_OK,
    summary="Get Unified Case Chronological Timeline",
    description=(
        "Retrieves a complete chronological event timeline for the case. "
        "Strictly labels events as SYSTEM EVENT vs HUMAN ACTION."
    ),
)
def get_case_timeline(
    case_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> WelfareCaseTimelineResponse:
    try:
        return WelfareCaseService.get_case_timeline(case_id, current_user, db)
    except LookupError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except PermissionError as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))


@router.get(
    "/{case_id}/audits",
    response_model=WelfareCaseAuditsResponse,
    status_code=status.HTTP_200_OK,
    summary="Get Case Audit History",
    description="Retrieves the append-only audit trail for all actions on this welfare case.",
)
def get_case_audits(
    case_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> WelfareCaseAuditsResponse:
    try:
        return WelfareCaseService.get_case_audits(case_id, current_user, db)
    except LookupError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except PermissionError as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))
