from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from core.config import logger
from db.session import get_db
from db.models.user import User
from db.models.personnel import Personnel
from db.models.hrms import HrmsServiceRecord
from schemas.hrms import HrmsSyncRequest, HrmsSyncResponse
from api.deps import get_current_user

router = APIRouter(prefix="/hrms", tags=["Mock HRMS Ingestion Bridge"])

@router.post(
    "/sync",
    response_model=HrmsSyncResponse,
    status_code=status.HTTP_200_OK,
    summary="Synchronize mock HRMS personnel service record"
)
def sync_hrms_record(
    payload: HrmsSyncRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Mock HRMS service record synchronization interface.
    Accepts structured service and operational history fields for an existing personnel profile.
    
    Security & RBAC:
    - Restricted to 'admin', 'officer', and 'welfare' roles (Jawans cannot sync HRMS data).
    - Officers and Welfare users are strictly constrained to their assigned Battalion + Location scope.
    
    Synchronization & Idempotency:
    - First sync creates a dedicated HrmsServiceRecord linked to the personnel record.
    - Subsequent syncs update the existing record rather than creating duplicate entries.
    - Relevant operational fields are propagated to the Personnel entity for model evaluation.
    - Source is stamped as 'mock_hrms' to maintain synthetic-data disclosures.
    """
    # 1. RBAC Check
    if current_user.role not in ["admin", "officer", "welfare"]:
        logger.warning(
            f"HRMS_SYNC_DENIED: User '{current_user.username}' (role: {current_user.role}) attempted HRMS sync."
        )
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access forbidden: Only administrative and commander/officer roles can synchronize HRMS service records."
        )

    # 2. Personnel Existence Check
    personnel = db.query(Personnel).filter(Personnel.id == payload.personnel_id).first()
    if not personnel:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Personnel record ID {payload.personnel_id} not found."
        )

    # 3. Scope Enforcement for Officers and Welfare
    if current_user.role in ["officer", "welfare"]:
        user_battalion = (current_user.battalion or "").strip().lower()
        p_battalion = (personnel.battalion or "").strip().lower()

        if user_battalion and p_battalion and user_battalion != p_battalion:
            logger.warning(
                f"HRMS_SCOPE_VIOLATION: User '{current_user.username}' ({user_battalion}) "
                f"attempted to sync personnel ID {personnel.id} ({p_battalion})"
            )
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied: Target personnel is outside your assigned Battalion and Location scope."
            )

        user_location = (current_user.location or "").strip().lower()
        p_location = (personnel.location or "").strip().lower()
        if user_location and p_location and user_location != p_location:
            logger.warning(
                f"HRMS_LOCATION_VIOLATION: User '{current_user.username}' ({user_location}) "
                f"attempted to sync personnel ID {personnel.id} ({p_location})"
            )
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied: Target personnel is outside your assigned Battalion and Location scope."
            )

    now = datetime.now(timezone.utc)

    # 4. Idempotent Synchronization
    rec = db.query(HrmsServiceRecord).filter(HrmsServiceRecord.personnel_id == personnel.id).first()
    is_new = rec is None
    if not rec:
        rec = HrmsServiceRecord(
            personnel_id=personnel.id,
            created_at=now
        )
        db.add(rec)

    # Update HRMS service record fields
    if payload.service_number is not None:
        rec.service_number = payload.service_number
    if payload.department is not None:
        rec.department = payload.department
    if payload.battalion is not None:
        rec.battalion = payload.battalion
    if payload.location is not None:
        rec.location = payload.location
    if payload.job_role is not None:
        rec.job_role = payload.job_role
    if payload.rank is not None:
        rec.rank = payload.rank
    if payload.deployment_days is not None:
        rec.deployment_days = payload.deployment_days
    if payload.duty_hours_per_week is not None:
        rec.duty_hours_per_week = payload.duty_hours_per_week
    if payload.night_shifts_per_month is not None:
        rec.night_shifts_per_month = payload.night_shifts_per_month
    
    consec_val = payload.consecutive_days_on_duty if payload.consecutive_days_on_duty is not None else payload.consecutive_duty_days
    if consec_val is not None:
        rec.consecutive_duty_days = consec_val

    leave_gap_val = payload.leave_balance_days if payload.leave_balance_days is not None else payload.leave_gap_days
    if leave_gap_val is not None:
        rec.leave_gap_days = leave_gap_val

    leaves_taken_val = payload.leaves_taken_past_year if payload.leaves_taken_past_year is not None else payload.annual_leaves_taken
    if leaves_taken_val is not None:
        rec.annual_leaves_taken = leaves_taken_val

    if payload.transfer_frequency is not None:
        rec.transfer_frequency = payload.transfer_frequency
    if payload.training_load is not None:
        rec.training_load = payload.training_load

    exp_val = payload.years_of_service if payload.years_of_service is not None else payload.experience_years
    if exp_val is not None:
        rec.experience_years = exp_val

    # Construct and preserve raw metadata
    meta_parts = []
    if payload.deployment_history:
        meta_parts.append(f"DEPLOYMENT:{payload.deployment_history.strip()}")
    if payload.transfer_history:
        meta_parts.append(f"TRANSFER:{payload.transfer_history.strip()}")
    if payload.training_history:
        meta_parts.append(f"TRAINING:{payload.training_history.strip()}")
    if payload.raw_metadata:
        meta_parts.append(payload.raw_metadata.strip())
    if meta_parts:
        rec.raw_metadata = " | ".join(meta_parts)[:512]

    rec.source = "mock_hrms"
    rec.synced_at = now
    rec.updated_at = now

    # Also synchronize corresponding operational fields on the Personnel model
    if payload.duty_hours_per_week is not None:
        personnel.duty_hours_per_week = payload.duty_hours_per_week
    if payload.deployment_days is not None:
        personnel.deployment_days = payload.deployment_days
    if payload.night_shifts_per_month is not None:
        personnel.night_shifts_per_month = payload.night_shifts_per_month
    if payload.consecutive_duty_days is not None:
        personnel.consecutive_duty_days = payload.consecutive_duty_days
    if payload.leave_gap_days is not None:
        personnel.leave_gap_days = payload.leave_gap_days
    if payload.transfer_frequency is not None:
        personnel.transfer_frequency = payload.transfer_frequency
    if payload.training_load is not None:
        personnel.training_load = payload.training_load
    if payload.experience_years is not None:
        personnel.experience_years = payload.experience_years
    if payload.department is not None:
        personnel.department = payload.department
    if payload.job_role is not None:
        personnel.job_role = payload.job_role
    personnel.updated_at = now

    try:
        db.commit()
        db.refresh(rec)
    except Exception as e:
        db.rollback()
        logger.error(f"Failed to persist HRMS sync for personnel {payload.personnel_id}: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to persist HRMS service record. Database transaction rolled back."
        )

    action_str = "created" if is_new else "updated"
    logger.info(
        f"HRMS_SYNC_SUCCESS: personnel_id={personnel.id} action={action_str} "
        f"user_id={current_user.id} source='{rec.source}'"
    )

    return HrmsSyncResponse(
        status="success",
        message=f"Mock HRMS service record successfully {action_str} for personnel {personnel.personnel_code}.",
        record_id=rec.id,
        personnel_id=personnel.id,
        personnel_code=personnel.personnel_code,
        service_number=rec.service_number,
        battalion=rec.battalion or personnel.battalion,
        location=rec.location or personnel.location,
        synced_at=rec.synced_at,
        source=rec.source
    )
