from datetime import datetime, timezone
from typing import Optional, Dict, Any
from fastapi import APIRouter, Depends, Query, HTTPException, status
from sqlalchemy.orm import Session

from core.config import logger
from db.session import get_db
from db.models.user import User
from api.deps import get_current_user, check_personnel_access, require_roles
from schemas.features import PersonnelFeatureSnapshotResponse
from schemas.commander_analytics import CommanderAnalyticsResponse
from services.feature_engineering.snapshot_service import FeatureSnapshotService
from services.commander_analytics_service import CommanderAnalyticsService

router = APIRouter(prefix="/analytics", tags=["Personnel Analytics & Feature Engineering"])

def _parse_reference_time(ref_str: Optional[str]) -> Optional[datetime]:
    if not ref_str:
        return None
    try:
        # Handles URL decoding where '+' becomes a space
        cleaned = ref_str.strip().replace(" ", "+")
        if cleaned.endswith("Z") or cleaned.endswith("z"):
            cleaned = cleaned[:-1] + "+00:00"
        dt = datetime.fromisoformat(cleaned)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Invalid reference_time format. Expected ISO 8601 (e.g. 2026-09-20T12:00:00Z): {e}"
        )


@router.get(
    "/personnel/{personnel_id}/features",
    response_model=PersonnelFeatureSnapshotResponse,
    status_code=status.HTTP_200_OK,
    summary="Get Derived HRMS and Wearable Feature Snapshot for Personnel",
    description=(
        "Retrieves a deterministic analytical feature snapshot combining derived HRMS indicators "
        "and rolling 7-day and 30-day wearable telemetry aggregates. "
        "Strictly enforces Battalion + Location scope and Jawan self-ownership. "
        "Signals are explicitly identified as simulated / mock data and are non-diagnostic."
    )
)
def get_personnel_feature_snapshot(
    personnel_id: int,
    reference_time: Optional[str] = Query(
        None,
        description="Optional UTC anchor timestamp for deterministic feature window calculations. Defaults to current time."
    ),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> PersonnelFeatureSnapshotResponse:
    # Enforces Authentication, RBAC, Battalion + Location scoping, and Jawan ownership
    personnel = check_personnel_access(current_user, personnel_id, db)

    parsed_ref = _parse_reference_time(reference_time)

    logger.info(
        f"User '{current_user.username}' (Role: {current_user.role}) requested feature snapshot "
        f"for Personnel ID {personnel_id} (Ref: {parsed_ref})"
    )

    snapshot = FeatureSnapshotService.generate_snapshot(
        personnel=personnel,
        db=db,
        reference_time=parsed_ref
    )
    return snapshot


@router.get(
    "/personnel/{personnel_id}/contextual-risk",
    response_model=Dict[str, Any],
    status_code=status.HTTP_200_OK,
    summary="Get Contextual Risk Integration Layer for Personnel",
    description=(
        "Integrates the validated LightGBM ML assessment with derived HRMS and wearable trend features "
        "into a contextual decision-support payload without altering model artifacts or coefficients."
    )
)
def get_personnel_contextual_risk(
    personnel_id: int,
    reference_time: Optional[str] = Query(
        None,
        description="Optional UTC anchor timestamp for deterministic calculations."
    ),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Dict[str, Any]:
    # Enforces Authentication, RBAC, Battalion + Location scoping, and Jawan ownership
    personnel = check_personnel_access(current_user, personnel_id, db)

    parsed_ref = _parse_reference_time(reference_time)

    logger.info(
        f"User '{current_user.username}' requested contextual risk summary for Personnel ID {personnel_id}"
    )

    summary = FeatureSnapshotService.get_contextual_risk_summary(
        personnel=personnel,
        db=db,
        reference_time=parsed_ref
    )
    return summary


@router.get(
    "/commander",
    response_model=CommanderAnalyticsResponse,
    status_code=status.HTTP_200_OK,
    summary="Get Unit-Level Commander Analytics & Welfare Intelligence (Phase 38)",
    description=(
        "Retrieves aggregate unit-level welfare intelligence strictly scoped to the authenticated "
        "user's authorized organizational scope (Battalion and Location). "
        "Aggregates authoritative Phase 34 V2 risk classifications, Phase 36 longitudinal trends, "
        "and Phase 37 welfare alerts. Enforces small-group k-anonymity privacy protection (default min 5)."
    )
)
def get_commander_analytics(
    time_filter: Optional[str] = Query("30d", description="Time range filter: 7d, 30d, 90d, all, custom"),
    time_range: Optional[str] = Query(None, description="Alias for time_filter"),
    start_date: Optional[str] = Query(None, description="ISO start date for custom range"),
    end_date: Optional[str] = Query(None, description="ISO end date for custom range"),
    reference_time: Optional[str] = Query(None, description="Optional UTC anchor timestamp for deterministic window calculations"),
    battalion: Optional[str] = Query(None, description="Ignored for non-admins; strictly scoped to user's authorized battalion"),
    location: Optional[str] = Query(None, description="Ignored for non-admins; strictly scoped to user's authorized location"),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles("admin", "officer", "welfare"))
) -> CommanderAnalyticsResponse:
    # Use time_range if time_filter is default and time_range is specified
    effective_filter = time_range if (time_range and time_filter == "30d") else time_filter
    parsed_ref = _parse_reference_time(reference_time)

    # If non-admin attempts to supply differing battalion or location, log warning and reject
    if current_user.role in ["officer", "welfare"]:
        if battalion and current_user.battalion and battalion.strip().lower() != current_user.battalion.strip().lower():
            logger.warning(
                f"Scope violation attempt: user '{current_user.username}' attempted to query battalion '{battalion}' "
                f"outside authorized scope '{current_user.battalion}'"
            )
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied: Cannot query organizational analytics outside your assigned Battalion scope."
            )
        if location and current_user.location and location.strip().lower() != current_user.location.strip().lower():
            logger.warning(
                f"Scope violation attempt: user '{current_user.username}' attempted to query location '{location}' "
                f"outside authorized scope '{current_user.location}'"
            )
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied: Cannot query organizational analytics outside your assigned Location scope."
            )

    logger.info(
        f"Commander analytics requested by user '{current_user.username}' (Role: {current_user.role}, "
        f"Battalion: {current_user.battalion}, Location: {current_user.location}, Filter: {effective_filter})"
    )

    analytics = CommanderAnalyticsService.compute_analytics(
        db=db,
        current_user=current_user,
        time_filter=effective_filter or "30d",
        start_date=start_date,
        end_date=end_date,
        reference_time=parsed_ref
    )
    return analytics

