import math
from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from sqlalchemy import desc, func

from core.config import logger
from db.session import get_db
from db.models.user import User
from db.models.personnel import Personnel
from db.models.assessment import StressAssessment
from schemas.personnel import (
    PersonnelCreate,
    PersonnelUpdate,
    PersonnelOut,
    PersonnelListResponse
)
from api.deps import get_current_user, require_roles, check_personnel_access

router = APIRouter(prefix="/personnel", tags=["Personnel Records"])

def _enrich_personnel_out(p: Personnel, db: Session) -> PersonnelOut:
    """Helper to attach latest assessment risk metrics to personnel record."""
    latest_assessment = (
        db.query(StressAssessment)
        .filter(StressAssessment.personnel_id == p.id)
        .order_by(desc(StressAssessment.assessment_timestamp))
        .first()
    )
    p_dict = {
        "id": p.id,
        "personnel_code": p.personnel_code,
        "name": p.name,
        "age": p.age,
        "gender": p.gender,
        "department": p.department,
        "battalion": p.battalion,
        "job_role": p.job_role,
        "location": p.location,
        "experience_years": p.experience_years,
        "duty_hours_per_week": p.duty_hours_per_week,
        "night_shifts_per_month": p.night_shifts_per_month,
        "consecutive_duty_days": p.consecutive_duty_days,
        "transfer_frequency": p.transfer_frequency,
        "training_load": p.training_load,
        "leave_gap_days": p.leave_gap_days,
        "deployment_days": p.deployment_days,
        "remote_posting": p.remote_posting,
        "operational_exposure": p.operational_exposure,
        "created_at": p.created_at,
        "updated_at": p.updated_at,
        "latest_risk_score": latest_assessment.risk_score if latest_assessment else None,
        "latest_stress_level": latest_assessment.stress_level if latest_assessment else None,
        "latest_priority": latest_assessment.risk_priority if latest_assessment else None,
    }
    return PersonnelOut(**p_dict)


@router.post(
    "",
    response_model=PersonnelOut,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new personnel record (Admin / Officer)"
)
def create_personnel(
    personnel_in: PersonnelCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles("admin", "officer"))
):
    """
    Creates a new synthetic personnel record.
    Restricted to Admin and Officer roles. Officers automatically bind personnel
    to their assigned battalion and location scope.
    """
    existing = db.query(Personnel).filter(Personnel.personnel_code == personnel_in.personnel_code).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Personnel with code '{personnel_in.personnel_code}' already exists."
        )

    data = personnel_in.model_dump()
    if current_user.role == "officer":
        # Force officer's organizational scope
        if current_user.battalion:
            data["battalion"] = current_user.battalion
        if current_user.location:
            data["location"] = current_user.location

    new_personnel = Personnel(**data)
    db.add(new_personnel)
    db.commit()
    db.refresh(new_personnel)
    logger.info(f"Personnel record created: {new_personnel.personnel_code} by {current_user.username}")
    return _enrich_personnel_out(new_personnel, db)


@router.get(
    "",
    response_model=PersonnelListResponse,
    summary="List personnel records with pagination and scope enforcement"
)
def list_personnel(
    page: int = Query(1, ge=1, description="Page number"),
    size: int = Query(20, ge=1, le=100, description="Items per page"),
    department: Optional[str] = Query(None, description="Filter by operational department"),
    location: Optional[str] = Query(None, description="Filter by duty base location"),
    battalion: Optional[str] = Query(None, description="Filter by battalion unit"),
    risk_priority: Optional[str] = Query(None, description="Filter by latest risk priority (Routine, Preventive, Priority)"),
    stress_level: Optional[str] = Query(None, description="Filter by latest stress tier (Low, Medium, High)"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Retrieves paginated personnel records.
    - Admin: Can view all personnel across all battalions and locations.
    - Officer / Welfare: Restricted strictly to matching Battalion AND Location.
    - Personnel: Restricted strictly to their own individual record.
    """
    # If the user is individual personnel, restrict strictly to their own record
    if current_user.role == "personnel":
        if not current_user.personnel_id:
            return PersonnelListResponse(items=[], total=0, page=page, size=size, pages=0)
        p = db.query(Personnel).filter(Personnel.id == current_user.personnel_id).first()
        items = [_enrich_personnel_out(p, db)] if p else []
        return PersonnelListResponse(items=items, total=len(items), page=1, size=size, pages=1)

    query = db.query(Personnel)

    # Scoped access control for Officer and Welfare roles
    if current_user.role in ["officer", "welfare"]:
        user_battalion = (current_user.battalion or "").strip()
        user_location = (current_user.location or "").strip()
        query = query.filter(
            func.lower(Personnel.battalion) == user_battalion.lower(),
            func.lower(Personnel.location) == user_location.lower()
        )
        # Client query parameters can only narrow within the already-authorized scope
        if location:
            query = query.filter(Personnel.location.ilike(f"%{location}%"))
        if battalion:
            query = query.filter(Personnel.battalion.ilike(f"%{battalion}%"))
    elif current_user.role == "admin":
        if battalion:
            query = query.filter(Personnel.battalion.ilike(f"%{battalion}%"))
        if location:
            query = query.filter(Personnel.location.ilike(f"%{location}%"))

    if department:
        query = query.filter(Personnel.department.ilike(f"%{department}%"))

    # If filtering by latest assessment metrics, join with latest assessments
    all_personnel = query.order_by(Personnel.id.asc()).all()
    enriched = [_enrich_personnel_out(p, db) for p in all_personnel]

    if risk_priority:
        enriched = [p for p in enriched if p.latest_priority and p.latest_priority.lower() == risk_priority.lower()]
    if stress_level:
        enriched = [p for p in enriched if p.latest_stress_level and p.latest_stress_level.lower() == stress_level.lower()]

    total = len(enriched)
    pages = math.ceil(total / size) if total > 0 else 0
    start_idx = (page - 1) * size
    end_idx = start_idx + size
    paginated_items = enriched[start_idx:end_idx]

    return PersonnelListResponse(
        items=paginated_items,
        total=total,
        page=page,
        size=size,
        pages=pages
    )


@router.get(
    "/{personnel_id}",
    response_model=PersonnelOut,
    summary="Retrieve individual personnel record by ID with scope enforcement"
)
def get_personnel(
    personnel_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Retrieves an individual personnel record.
    Enforces RBAC and scope-based access:
    - Personnel can only access their own record.
    - Officer / Welfare can only access records from their assigned Battalion + Location.
    - Admin can access any record.
    """
    p = check_personnel_access(current_user, personnel_id, db)
    return _enrich_personnel_out(p, db)


@router.put(
    "/{personnel_id}",
    response_model=PersonnelOut,
    summary="Update an existing personnel record (Admin / Officer)"
)
def update_personnel(
    personnel_id: int,
    update_data: PersonnelUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles("admin", "officer"))
):
    """
    Updates an existing personnel record.
    Enforces that officers cannot modify personnel outside their scope or reassign
    them to a different battalion or location.
    """
    p = check_personnel_access(current_user, personnel_id, db)

    update_dict = update_data.model_dump(exclude_unset=True)
    # Non-admin users cannot reassign organizational scope
    if current_user.role != "admin":
        update_dict.pop("battalion", None)
        update_dict.pop("location", None)

    for field, val in update_dict.items():
        setattr(p, field, val)

    db.commit()
    db.refresh(p)
    logger.info(f"Personnel record {p.personnel_code} updated by {current_user.username}")
    return _enrich_personnel_out(p, db)
