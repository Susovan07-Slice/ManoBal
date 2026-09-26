from datetime import datetime, timezone
from typing import Optional, Dict, Any
from fastapi import APIRouter, Depends, Query, HTTPException, status
from sqlalchemy.orm import Session

from core.config import logger
from db.session import get_db
from db.models.user import User
from api.deps import get_current_user, check_personnel_access
from schemas.features import PersonnelFeatureSnapshotResponse
from services.feature_engineering.snapshot_service import FeatureSnapshotService

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
