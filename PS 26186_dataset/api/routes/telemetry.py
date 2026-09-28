from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from core.config import logger
from db.session import get_db
from db.models.user import User
from db.models.personnel import Personnel
from db.models.telemetry import WearableTelemetry
from schemas.telemetry import WearableTelemetryIngest, WearableTelemetryResponse
from api.deps import get_current_user

router = APIRouter(prefix="/telemetry", tags=["Simulated Wearable Telemetry Ingestion Bridge"])

@router.post(
    "/wearable",
    response_model=WearableTelemetryResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Ingest simulated wearable biometric and recovery telemetry"
)
def ingest_wearable_telemetry(
    payload: WearableTelemetryIngest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Simulated wearable device telemetry ingestion endpoint.
    Accepts time-series physiological, recovery, and ambulatory activity signals.
    
    Security & Scope Enforcement:
    - Jawans (role: 'personnel') can strictly ingest telemetry for their own linked profile.
    - Officers and Welfare officers are constrained to personnel within their assigned Battalion + Location.
    - Administrators can ingest simulated telemetry across all personnel.
    - Unauthorized access or cross-scope attempts are strictly rejected with HTTP 403 Forbidden.
    
    Synthetic Data Governance:
    - Records are explicitly tagged with source='simulated_wearable'.
    - Clear disclaimers denote non-medical, prototype-only status.
    """
    # 1. Personnel Existence Check
    personnel = db.query(Personnel).filter(Personnel.id == payload.personnel_id).first()
    if not personnel:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Personnel record ID {payload.personnel_id} not found."
        )

    # 2. Authorization & Scope Boundary
    if current_user.role == "personnel":
        if current_user.personnel_id != payload.personnel_id:
            logger.warning(
                f"TELEMETRY_ACCESS_DENIED: Jawan '{current_user.username}' (linked ID: {current_user.personnel_id}) "
                f"attempted to ingest telemetry for peer personnel ID {payload.personnel_id}"
            )
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied: Personnel accounts may only submit telemetry for their own profile."
            )
    elif current_user.role in ["officer", "welfare"]:
        user_battalion = (current_user.battalion or "").strip().lower()
        p_battalion = (personnel.battalion or "").strip().lower()

        if user_battalion and p_battalion and user_battalion != p_battalion:
            logger.warning(
                f"TELEMETRY_SCOPE_VIOLATION: User '{current_user.username}' ({user_battalion}) "
                f"attempted telemetry ingestion for out-of-scope personnel ID {personnel.id} ({p_battalion})"
            )
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied: Target personnel is outside your assigned Battalion and Location scope."
            )

        user_location = (current_user.location or "").strip().lower()
        p_location = (personnel.location or "").strip().lower()
        if user_location and p_location and user_location != p_location:
            logger.warning(
                f"TELEMETRY_LOCATION_VIOLATION: User '{current_user.username}' ({user_location}) "
                f"attempted telemetry ingestion for out-of-scope personnel ID {personnel.id} ({p_location})"
            )
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied: Target personnel is outside your assigned Battalion and Location scope."
            )

    now = datetime.now(timezone.utc)

    # 3. Create Time-Series Telemetry Record
    telemetry_entry = WearableTelemetry(
        personnel_id=personnel.id,
        recorded_at=payload.recorded_at,
        heart_rate=payload.heart_rate,
        hrv_rmssd=payload.hrv_rmssd,
        sleep_duration_hours=payload.sleep_duration_hours,
        sleep_quality_score=payload.sleep_quality_score,
        step_count=payload.step_count,
        active_minutes=payload.active_minutes,
        source="simulated_wearable",
        device_model=payload.device_model or "Simulated Band v1",
        created_at=now
    )

    try:
        db.add(telemetry_entry)
        db.commit()
        db.refresh(telemetry_entry)
    except Exception as e:
        db.rollback()
        logger.error(f"Failed to persist wearable telemetry for personnel {payload.personnel_id}: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to persist wearable telemetry record. Database transaction rolled back."
        )

    logger.info(
        f"TELEMETRY_INGEST_SUCCESS: entry_id={telemetry_entry.id} personnel_id={personnel.id} "
        f"recorded_at='{telemetry_entry.recorded_at}' user_id={current_user.id} source='{telemetry_entry.source}'"
    )

    return WearableTelemetryResponse(
        status="success",
        telemetry_id=telemetry_entry.id,
        personnel_id=telemetry_entry.personnel_id,
        recorded_at=telemetry_entry.recorded_at,
        heart_rate=telemetry_entry.heart_rate,
        hrv_rmssd=telemetry_entry.hrv_rmssd,
        sleep_duration_hours=telemetry_entry.sleep_duration_hours,
        sleep_quality_score=telemetry_entry.sleep_quality_score,
        step_count=telemetry_entry.step_count,
        active_minutes=telemetry_entry.active_minutes,
        source=telemetry_entry.source,
        created_at=telemetry_entry.created_at
    )
