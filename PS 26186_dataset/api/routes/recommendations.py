import json
from datetime import datetime, timezone
from typing import Optional, List, Dict, Any
from fastapi import APIRouter, Depends, Query, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import desc, func

from core.config import logger
from db.session import get_db
from db.models.user import User
from db.models.personnel import Personnel
from db.models.recommendation import WelfareRecommendation
from api.deps import get_current_user, check_personnel_access, require_roles
from schemas.recommendation import (
    WelfareRecommendationOut,
    RecommendationAcknowledgeRequest,
    RecommendationAcceptRequest,
    RecommendationDeferRequest,
    RecommendationDismissRequest,
    RecommendationActionRequest,
    PersonnelRecommendationsResponse,
    CommanderRecommendationSummaryResponse,
)
from services.welfare_recommendation_service import (
    WelfareRecommendationService,
    ANALYTICS_MIN_GROUP_SIZE,
)

router = APIRouter(prefix="/recommendations", tags=["Welfare Recommendation & Support Engine"])

def _parse_json_field(val: Any) -> Any:
    if not val:
        return {}
    if isinstance(val, (dict, list)):
        return val
    try:
        return json.loads(val)
    except Exception:
        return {"raw": str(val)}

def _serialize_recommendation(rec: WelfareRecommendation, db: Session) -> WelfareRecommendationOut:
    p_code = None
    p_name = None
    dept = None
    bat = None
    loc = None

    if rec.personnel_id:
        p = db.query(Personnel).filter(Personnel.id == rec.personnel_id).first()
        if p:
            p_code = p.personnel_code
            p_name = p.name
            dept = p.department
            bat = p.battalion
            loc = p.location

    evidence = _parse_json_field(rec.evidence_json)
    if not isinstance(evidence, dict):
        evidence = {"data": evidence}

    sources = _parse_json_field(rec.source_signals_json)
    if not isinstance(sources, list):
        sources = [str(sources)] if sources else []

    return WelfareRecommendationOut(
        id=rec.id,
        personnel_id=rec.personnel_id,
        personnel_code=p_code,
        personnel_name=p_name,
        department=dept,
        battalion=bat,
        location=loc,
        assessment_id=rec.assessment_id,
        recommendation_type=rec.recommendation_type,
        recommendation_text=rec.recommendation_text or "",
        title=rec.title or rec.recommendation_type.replace("_", " ").title(),
        description=rec.description,
        reason=rec.reason,
        priority=rec.priority,
        status=rec.status,
        confidence=rec.confidence,
        evidence=evidence,
        source_signals=sources,
        recommended_review_window=rec.recommended_review_window,
        linked_alert_id=rec.linked_alert_id,
        linked_anomaly_id=rec.linked_anomaly_id,
        linked_intervention_id=rec.linked_intervention_id,
        acknowledged_at=rec.acknowledged_at,
        acknowledged_by=rec.acknowledged_by,
        actioned_at=rec.actioned_at,
        actioned_by=rec.actioned_by,
        action_notes=rec.action_notes,
        created_at=rec.created_at,
        updated_at=rec.updated_at,
    )

def _verify_personnel_access(personnel_id: int, user: User, db: Session) -> Personnel:
    try:
        return WelfareRecommendationService.verify_access_and_get_personnel(personnel_id, user, db)
    except LookupError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except PermissionError as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))

# -----------------------------------------------------------------------------
# 1. PERSONNEL-FACING / AUTHORIZED REVIEWER ACCESS
# -----------------------------------------------------------------------------
@router.get(
    "/personnel/{personnel_id}",
    response_model=PersonnelRecommendationsResponse,
    summary="Get welfare recommendations for a personnel record"
)
def get_recommendations_for_personnel(
    personnel_id: int,
    status_filter: Optional[str] = Query(None, alias="status"),
    priority_filter: Optional[str] = Query(None, alias="priority"),
    recommendation_type: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Retrieves supportive welfare recommendations for a given personnel.
    Strictly enforces RBAC:
      - Personnel can only access their own recommendations (Anti-IDOR).
      - Officers/Welfare can access personnel within their battalion/location scope.
      - Admins can access system-wide.
    """
    personnel = _verify_personnel_access(personnel_id, current_user, db)

    query = db.query(WelfareRecommendation).filter(WelfareRecommendation.personnel_id == personnel_id)

    if status_filter:
        query = query.filter(WelfareRecommendation.status == status_filter)
    if priority_filter:
        query = query.filter(WelfareRecommendation.priority == priority_filter)
    if recommendation_type:
        query = query.filter(WelfareRecommendation.recommendation_type == recommendation_type)

    recs = query.order_by(desc(WelfareRecommendation.updated_at)).all()
    serialized = [_serialize_recommendation(r, db) for r in recs]

    status_code = "ACTIVE" if serialized else "NONE"
    msg = f"{len(serialized)} recommendation(s) found for personnel #{personnel.personnel_code}."

    return PersonnelRecommendationsResponse(
        personnel_id=personnel_id,
        status=status_code,
        message=msg,
        total_recommendations=len(serialized),
        recommendations=serialized
    )

# -----------------------------------------------------------------------------
# 2. EVALUATION TRIGGER
# -----------------------------------------------------------------------------
@router.post(
    "/evaluate/{personnel_id}",
    response_model=PersonnelRecommendationsResponse,
    summary="Evaluate existing signals and generate recommendations for personnel"
)
def evaluate_recommendations(
    personnel_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles("admin", "officer", "welfare"))
):
    """
    Triggers recommendation engine evaluation over existing signals for a personnel.
    """
    personnel = _verify_personnel_access(personnel_id, current_user, db)
    status_code, msg, recs = WelfareRecommendationService.evaluate_and_generate_recommendations(
        personnel=personnel,
        db=db,
        persist=True
    )
    serialized = [_serialize_recommendation(r, db) for r in recs]

    return PersonnelRecommendationsResponse(
        personnel_id=personnel_id,
        status=status_code,
        message=msg,
        total_recommendations=len(serialized),
        recommendations=serialized
    )

# -----------------------------------------------------------------------------
# 3. COMMANDER / UNIT SUMMARY (WITH PRIVACY PROTECTION)
# -----------------------------------------------------------------------------
@router.get(
    "/commander",
    response_model=CommanderRecommendationSummaryResponse,
    summary="Get unit-level recommendations for commander review"
)
def get_commander_recommendations(
    status_filter: Optional[str] = Query(None, alias="status"),
    priority_filter: Optional[str] = Query(None, alias="priority"),
    recommendation_type: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles("admin", "officer", "welfare"))
):
    """
    Returns unit-level recommendations for authorized officers/welfare personnel.
    Enforces organizational scoping and privacy protection (ANALYTICS_MIN_GROUP_SIZE = 5).
    """
    query = db.query(WelfareRecommendation).join(Personnel, WelfareRecommendation.personnel_id == Personnel.id)

    scope_bat = current_user.battalion
    scope_loc = current_user.location

    if current_user.role in ["officer", "welfare"]:
        if scope_bat:
            query = query.filter(func.lower(Personnel.battalion) == scope_bat.strip().lower())
        if scope_loc:
            query = query.filter(func.lower(Personnel.location) == scope_loc.strip().lower())

    # Check total personnel count in scope for small-group privacy threshold
    personnel_count_query = db.query(Personnel)
    if current_user.role in ["officer", "welfare"]:
        if scope_bat:
            personnel_count_query = personnel_count_query.filter(func.lower(Personnel.battalion) == scope_bat.strip().lower())
        if scope_loc:
            personnel_count_query = personnel_count_query.filter(func.lower(Personnel.location) == scope_loc.strip().lower())

    total_in_scope = personnel_count_query.count()
    small_group_suppressed = False

    if total_in_scope < ANALYTICS_MIN_GROUP_SIZE and current_user.role != "admin":
        small_group_suppressed = True
        return CommanderRecommendationSummaryResponse(
            scope_battalion=scope_bat,
            scope_location=scope_loc,
            total_active_recommendations=0,
            priority_breakdown={},
            status_breakdown={},
            type_breakdown={},
            small_group_suppressed=True,
            recommendations=[]
        )

    if status_filter:
        query = query.filter(WelfareRecommendation.status == status_filter)
    if priority_filter:
        query = query.filter(WelfareRecommendation.priority == priority_filter)
    if recommendation_type:
        query = query.filter(WelfareRecommendation.recommendation_type == recommendation_type)

    all_recs = query.order_by(desc(WelfareRecommendation.updated_at)).all()

    priority_breakdown: Dict[str, int] = {}
    status_breakdown: Dict[str, int] = {}
    type_breakdown: Dict[str, int] = {}

    for r in all_recs:
        p = r.priority or "UNKNOWN"
        priority_breakdown[p] = priority_breakdown.get(p, 0) + 1
        s = r.status or "UNKNOWN"
        status_breakdown[s] = status_breakdown.get(s, 0) + 1
        t = r.recommendation_type or "UNKNOWN"
        type_breakdown[t] = type_breakdown.get(t, 0) + 1

    serialized = [_serialize_recommendation(r, db) for r in all_recs]

    return CommanderRecommendationSummaryResponse(
        scope_battalion=scope_bat,
        scope_location=scope_loc,
        total_active_recommendations=len(serialized),
        priority_breakdown=priority_breakdown,
        status_breakdown=status_breakdown,
        type_breakdown=type_breakdown,
        small_group_suppressed=False,
        recommendations=serialized
    )

# -----------------------------------------------------------------------------
# 4. LIFECYCLE MANAGEMENT ENDPOINTS
# -----------------------------------------------------------------------------
def _check_rec_access(rec: WelfareRecommendation, user: User, db: Session):
    _verify_personnel_access(rec.personnel_id, user, db)

@router.post(
    "/{recommendation_id}/acknowledge",
    response_model=WelfareRecommendationOut,
    summary="Acknowledge review of a welfare recommendation"
)
def acknowledge_recommendation(
    recommendation_id: int,
    payload: RecommendationAcknowledgeRequest = RecommendationAcknowledgeRequest(),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles("admin", "officer", "welfare"))
):
    rec = db.query(WelfareRecommendation).filter(WelfareRecommendation.id == recommendation_id).first()
    if not rec:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Recommendation #{recommendation_id} not found.")

    _check_rec_access(rec, current_user, db)
    updated = WelfareRecommendationService.acknowledge_recommendation(db, recommendation_id, current_user, payload.notes)
    return _serialize_recommendation(updated, db)

@router.post(
    "/{recommendation_id}/accept",
    response_model=WelfareRecommendationOut,
    summary="Accept recommendation and optionally initiate a Phase 37 intervention"
)
def accept_recommendation(
    recommendation_id: int,
    payload: RecommendationAcceptRequest = RecommendationAcceptRequest(),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles("admin", "officer", "welfare"))
):
    rec = db.query(WelfareRecommendation).filter(WelfareRecommendation.id == recommendation_id).first()
    if not rec:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Recommendation #{recommendation_id} not found.")

    _check_rec_access(rec, current_user, db)
    updated, intervention = WelfareRecommendationService.accept_recommendation(
        db=db,
        recommendation_id=recommendation_id,
        user=current_user,
        create_intervention=payload.create_intervention,
        intervention_type=payload.intervention_type,
        scheduled_date=payload.scheduled_date,
        notes=payload.notes
    )
    return _serialize_recommendation(updated, db)

@router.post(
    "/{recommendation_id}/defer",
    response_model=WelfareRecommendationOut,
    summary="Defer review of a welfare recommendation"
)
def defer_recommendation(
    recommendation_id: int,
    payload: RecommendationDeferRequest = RecommendationDeferRequest(),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles("admin", "officer", "welfare"))
):
    rec = db.query(WelfareRecommendation).filter(WelfareRecommendation.id == recommendation_id).first()
    if not rec:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Recommendation #{recommendation_id} not found.")

    _check_rec_access(rec, current_user, db)
    updated = WelfareRecommendationService.defer_recommendation(
        db=db,
        recommendation_id=recommendation_id,
        user=current_user,
        defer_days=payload.defer_days,
        notes=payload.notes
    )
    return _serialize_recommendation(updated, db)

@router.post(
    "/{recommendation_id}/dismiss",
    response_model=WelfareRecommendationOut,
    summary="Dismiss a welfare recommendation with rationale"
)
def dismiss_recommendation(
    recommendation_id: int,
    payload: RecommendationDismissRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles("admin", "officer", "welfare"))
):
    rec = db.query(WelfareRecommendation).filter(WelfareRecommendation.id == recommendation_id).first()
    if not rec:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Recommendation #{recommendation_id} not found.")

    _check_rec_access(rec, current_user, db)
    updated = WelfareRecommendationService.dismiss_recommendation(
        db=db,
        recommendation_id=recommendation_id,
        user=current_user,
        reason=payload.reason
    )
    return _serialize_recommendation(updated, db)

@router.post(
    "/{recommendation_id}/action",
    response_model=WelfareRecommendationOut,
    summary="Record supportive action notes and complete recommendation"
)
def action_recommendation(
    recommendation_id: int,
    payload: RecommendationActionRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles("admin", "officer", "welfare"))
):
    rec = db.query(WelfareRecommendation).filter(WelfareRecommendation.id == recommendation_id).first()
    if not rec:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Recommendation #{recommendation_id} not found.")

    _check_rec_access(rec, current_user, db)
    updated = WelfareRecommendationService.action_recommendation(
        db=db,
        recommendation_id=recommendation_id,
        user=current_user,
        action_notes=payload.action_notes
    )
    return _serialize_recommendation(updated, db)
