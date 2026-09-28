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
from db.models.anomaly import WelfareAnomaly
from api.deps import get_current_user, check_personnel_access, require_roles
from schemas.anomaly import (
    WelfareAnomalyOut,
    AnomalyActionRequest,
    AnomalyResolutionRequest,
    PersonnelAnomalyHistoryResponse,
    CommanderAnomalyScope,
    CommanderAnomalySummaryResponse,
)
from services.welfare_anomaly_service import (
    WelfareAnomalyService,
    ANALYTICS_MIN_GROUP_SIZE,
)
from services.commander_analytics_service import CommanderAnalyticsService

router = APIRouter(prefix="/anomalies", tags=["Early-Warning & Welfare Anomaly Detection"])


def _parse_evidence(evidence_raw: Any) -> Dict[str, Any]:
    if not evidence_raw:
        return {}
    if isinstance(evidence_raw, dict):
        return evidence_raw
    try:
        return json.loads(evidence_raw)
    except Exception:
        return {"raw": str(evidence_raw)}


def _serialize_anomaly(anom: WelfareAnomaly, db: Session) -> WelfareAnomalyOut:
    p_code = None
    p_name = None
    dept = None
    bat = anom.scope_battalion
    loc = anom.scope_location

    if anom.personnel_id:
        p = db.query(Personnel).filter(Personnel.id == anom.personnel_id).first()
        if p:
            p_code = p.personnel_code
            p_name = p.name
            dept = p.department
            bat = p.battalion
            loc = p.location

    return WelfareAnomalyOut(
        id=anom.id,
        personnel_id=anom.personnel_id,
        personnel_code=p_code,
        personnel_name=p_name,
        department=dept,
        battalion=bat,
        location=loc,
        scope_type=anom.scope_type,
        scope_battalion=anom.scope_battalion,
        scope_location=anom.scope_location,
        anomaly_type=anom.anomaly_type,
        severity=anom.severity,
        status=anom.status,
        confidence=anom.confidence,
        baseline_sample_count=anom.baseline_sample_count,
        detected_at=anom.detected_at,
        observation_window_start=anom.observation_window_start,
        observation_window_end=anom.observation_window_end,
        evidence=_parse_evidence(anom.evidence_json),
        acknowledged_at=anom.acknowledged_at,
        acknowledged_by=anom.acknowledged_by,
        resolved_at=anom.resolved_at,
        resolved_by=anom.resolved_by,
        resolution_notes=anom.resolution_notes,
        associated_alert_id=anom.associated_alert_id,
        created_at=anom.created_at,
        updated_at=anom.updated_at,
    )


@router.get(
    "/personnel/{personnel_id}",
    response_model=PersonnelAnomalyHistoryResponse,
    status_code=status.HTTP_200_OK,
    summary="Get Early-Warning Welfare Anomalies for Personnel",
    description=(
        "Retrieves personalized early-warning anomaly signals for a specific personnel by evaluating "
        "their historical baseline. Strictly enforces Battalion + Location scope and Jawan self-ownership."
    )
)
def get_personnel_anomalies(
    personnel_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> PersonnelAnomalyHistoryResponse:
    # Enforces Authentication, RBAC, Battalion + Location scoping, and Jawan ownership
    personnel = check_personnel_access(current_user, personnel_id, db)

    logger.info(
        f"User '{current_user.username}' (Role: {current_user.role}) requested early-warning anomalies "
        f"for Personnel ID {personnel_id}"
    )

    stat, msg, anomalies, baseline_summary = WelfareAnomalyService.detect_personal_anomalies(
        personnel=personnel,
        db=db,
        persist=True
    )

    # Query all active or resolved anomalies for this personnel to present complete history
    db_anomalies = (
        db.query(WelfareAnomaly)
        .filter(WelfareAnomaly.personnel_id == personnel_id)
        .order_by(desc(WelfareAnomaly.detected_at))
        .all()
    )

    serialized = [_serialize_anomaly(a, db) for a in db_anomalies]
    active_count = sum(1 for a in serialized if a.status in ["DETECTED", "ACKNOWLEDGED", "UNDER_REVIEW"])

    return PersonnelAnomalyHistoryResponse(
        personnel_id=personnel_id,
        status=stat,
        message=msg,
        active_anomalies_count=active_count,
        anomalies=serialized,
        baseline_summary=baseline_summary
    )


@router.get(
    "/commander",
    response_model=CommanderAnomalySummaryResponse,
    status_code=status.HTTP_200_OK,
    summary="Get Unit-Level Early-Warning & Welfare Anomaly Intelligence",
    description=(
        "Aggregates active individual and unit-level welfare anomaly signals across the authenticated "
        "commander's authorized organizational scope (Battalion and Location). "
        "Enforces privacy k-anonymity (min 5 personnel)."
    )
)
def get_commander_anomalies(
    battalion: Optional[str] = Query(None, description="Ignored for non-admins; strictly scoped to user token"),
    location: Optional[str] = Query(None, description="Ignored for non-admins; strictly scoped to user token"),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles("admin", "officer", "welfare"))
) -> CommanderAnomalySummaryResponse:
    # Anti-IDOR: Non-admin cannot override battalion or location
    if current_user.role in ["officer", "welfare"]:
        if battalion and current_user.battalion and battalion.strip().lower() != current_user.battalion.strip().lower():
            logger.warning(f"Scope violation attempt: user '{current_user.username}' attempted to query battalion '{battalion}'")
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied: Cannot query anomaly signals outside your assigned Battalion scope."
            )
        if location and current_user.location and location.strip().lower() != current_user.location.strip().lower():
            logger.warning(f"Scope violation attempt: user '{current_user.username}' attempted to query location '{location}'")
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied: Cannot query anomaly signals outside your assigned Location scope."
            )

    logger.info(
        f"Commander anomaly summary requested by user '{current_user.username}' "
        f"(Scope: Battalion={current_user.battalion}, Location={current_user.location})"
    )

    # 1. Scope Evaluation
    p_query = CommanderAnalyticsService.get_scoped_personnel_query(db, current_user)
    scoped_personnel = p_query.all()
    total_authorized = len(scoped_personnel)

    scope_obj = CommanderAnomalyScope(
        role=current_user.role,
        battalion=current_user.battalion,
        location=current_user.location,
        total_authorized_personnel=total_authorized,
        min_group_size_threshold=ANALYTICS_MIN_GROUP_SIZE
    )

    # 2. Small-Group Privacy Protection (k-anonymity)
    if total_authorized < ANALYTICS_MIN_GROUP_SIZE:
        return CommanderAnomalySummaryResponse(
            status="INSUFFICIENT_GROUP_SIZE",
            message=(
                f"Aggregate welfare anomaly detection is withheld for this population size. "
                f"A minimum group size of {ANALYTICS_MIN_GROUP_SIZE} authorized personnel is required "
                f"to prevent deductive re-identification of sensitive early-warning signals."
            ),
            scope=scope_obj,
            total_detected_anomalies=0,
            active_anomalies_count=0,
            by_severity={},
            by_type={},
            by_status={},
            anomalies=[],
            unit_level_signals=[],
            data_quality={"total_authorized": total_authorized, "insufficient_group_size": True}
        )

    # 3. Detect Unit-Level Anomalies
    u_stat, u_msg, unit_anomalies, unit_dq = WelfareAnomalyService.detect_unit_anomalies(
        db=db,
        current_user=current_user,
        persist=True
    )

    # 4. Trigger detection across scoped personnel
    for p in scoped_personnel:
        try:
            WelfareAnomalyService.detect_personal_anomalies(personnel=p, db=db, persist=True)
        except Exception as e:
            logger.warning(f"Error evaluating anomalies for personnel {p.id}: {e}")

    # 5. Query all scoped anomalies from DB
    scoped_pids = [p.id for p in scoped_personnel]
    anom_query = db.query(WelfareAnomaly).filter(
        (WelfareAnomaly.personnel_id.in_(scoped_pids)) |
        (
            (WelfareAnomaly.scope_type == "UNIT") &
            (func.lower(WelfareAnomaly.scope_battalion) == (current_user.battalion or "").lower())
        )
    ).order_by(desc(WelfareAnomaly.detected_at))

    all_anomalies = anom_query.all()
    serialized_all = [_serialize_anomaly(a, db) for a in all_anomalies]

    active_anomalies = [a for a in serialized_all if a.status in ["DETECTED", "ACKNOWLEDGED", "UNDER_REVIEW"]]
    unit_signals = [a for a in serialized_all if a.scope_type == "UNIT"]

    # Compute breakdowns
    by_sev: Dict[str, int] = {}
    by_type: Dict[str, int] = {}
    by_status: Dict[str, int] = {}

    for a in active_anomalies:
        by_sev[a.severity] = by_sev.get(a.severity, 0) + 1
        by_type[a.anomaly_type] = by_type.get(a.anomaly_type, 0) + 1
        by_status[a.status] = by_status.get(a.status, 0) + 1

    return CommanderAnomalySummaryResponse(
        status="SUCCESS",
        message=f"Synthesized early-warning anomaly intelligence for {total_authorized} authorized personnel.",
        scope=scope_obj,
        total_detected_anomalies=len(serialized_all),
        active_anomalies_count=len(active_anomalies),
        by_severity=by_sev,
        by_type=by_type,
        by_status=by_status,
        anomalies=active_anomalies,
        unit_level_signals=unit_signals,
        data_quality={"total_authorized": total_authorized, "unit_data_quality": unit_dq}
    )


# =============================================================================
# Lifecycle Endpoints: Acknowledge, Review, Resolve
# =============================================================================

@router.post(
    "/{anomaly_id}/acknowledge",
    response_model=WelfareAnomalyOut,
    summary="Acknowledge Early-Warning Anomaly Signal"
)
def acknowledge_anomaly(
    anomaly_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles("admin", "officer", "welfare"))
) -> WelfareAnomalyOut:
    try:
        anom = WelfareAnomalyService.acknowledge_anomaly(anomaly_id, current_user, db)
        return _serialize_anomaly(anom, db)
    except ValueError as ve:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(ve))
    except PermissionError as pe:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(pe))


@router.post(
    "/{anomaly_id}/review",
    response_model=WelfareAnomalyOut,
    summary="Initiate Human Welfare Review on Anomaly Signal"
)
def start_review_anomaly(
    anomaly_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles("admin", "officer", "welfare"))
) -> WelfareAnomalyOut:
    try:
        anom = WelfareAnomalyService.review_anomaly(anomaly_id, current_user, db)
        return _serialize_anomaly(anom, db)
    except ValueError as ve:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(ve))
    except PermissionError as pe:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(pe))


@router.post(
    "/{anomaly_id}/resolve",
    response_model=WelfareAnomalyOut,
    summary="Resolve Early-Warning Anomaly Signal"
)
def resolve_anomaly(
    anomaly_id: int,
    request: AnomalyResolutionRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles("admin", "officer", "welfare"))
) -> WelfareAnomalyOut:
    try:
        anom = WelfareAnomalyService.resolve_anomaly(
            anomaly_id=anomaly_id,
            resolution_notes=request.resolution_notes,
            current_user=current_user,
            db=db
        )
        return _serialize_anomaly(anom, db)
    except ValueError as ve:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(ve))
    except PermissionError as pe:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(pe))
