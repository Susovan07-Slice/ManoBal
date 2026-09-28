from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from sqlalchemy import desc, func
from typing import List, Optional
from datetime import datetime

from db.session import get_db
from db.models.user import User
from db.models.personnel import Personnel
from db.models.alert import WelfareAlert, WelfareIntervention, WelfareAlertAudit
from schemas.alert import (
    WelfareAlertOut,
    WelfareAlertAuditOut,
    WelfareInterventionOut,
    WelfareInterventionCreate,
    FollowUpScheduleRequest,
    AlertResolveRequest,
    InterventionCompleteRequest,
    InterventionCancelRequest,
)
from api.deps import get_current_user, require_roles, check_personnel_access
from services.welfare_alert_service import WelfareAlertService

router = APIRouter(prefix="/welfare", tags=["Welfare Alerts & Interventions"])

@router.get(
    "/alerts",
    response_model=List[WelfareAlertOut],
    summary="List welfare alerts",
    description="Retrieve a list of welfare alerts based on filters. Enforces organizational battalion scope."
)
def list_alerts(
    personnel_id: Optional[int] = Query(None),
    status_filter: Optional[str] = Query(None, alias="status"),
    severity: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles("admin", "officer", "welfare"))
):
    query = db.query(WelfareAlert).join(Personnel, WelfareAlert.personnel_id == Personnel.id)

    # Enforce organizational scope for officer and welfare roles
    if current_user.role in ["officer", "welfare"]:
        user_battalion = (current_user.battalion or "").strip().lower()
        if user_battalion:
            query = query.filter(func.lower(Personnel.battalion) == user_battalion)
    
    if personnel_id is not None:
        # Check that specific personnel is in scope
        check_personnel_access(current_user, personnel_id, db)
        query = query.filter(WelfareAlert.personnel_id == personnel_id)
        
    if status_filter:
        query = query.filter(WelfareAlert.status == status_filter)
        
    if severity:
        query = query.filter(WelfareAlert.severity == severity)
        
    alerts = query.order_by(desc(WelfareAlert.created_at)).all()
    return alerts

@router.get(
    "/alerts/{alert_id}",
    response_model=WelfareAlertOut,
    summary="Get alert details"
)
def get_alert(
    alert_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles("admin", "officer", "welfare"))
):
    alert = db.query(WelfareAlert).filter(WelfareAlert.id == alert_id).first()
    if not alert:
        raise HTTPException(status_code=404, detail="Alert not found")
    check_personnel_access(current_user, alert.personnel_id, db)
    return alert

@router.post(
    "/alerts/{alert_id}/acknowledge",
    response_model=WelfareAlertOut,
    summary="Acknowledge an alert"
)
def acknowledge_alert(
    alert_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles("admin", "officer", "welfare"))
):
    alert = db.query(WelfareAlert).filter(WelfareAlert.id == alert_id).first()
    if not alert:
        raise HTTPException(status_code=404, detail="Alert not found")
    check_personnel_access(current_user, alert.personnel_id, db)
    try:
        alert = WelfareAlertService.acknowledge_alert(db, alert_id, current_user.id)
        return alert
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post(
    "/alerts/{alert_id}/review",
    response_model=WelfareAlertOut,
    summary="Start reviewing an alert"
)
def start_review(
    alert_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles("admin", "officer", "welfare"))
):
    alert = db.query(WelfareAlert).filter(WelfareAlert.id == alert_id).first()
    if not alert:
        raise HTTPException(status_code=404, detail="Alert not found")
    check_personnel_access(current_user, alert.personnel_id, db)
    try:
        alert = WelfareAlertService.start_review(db, alert_id, current_user.id)
        return alert
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post(
    "/alerts/{alert_id}/intervention",
    response_model=WelfareInterventionOut,
    summary="Create a welfare intervention"
)
def create_intervention(
    alert_id: int,
    payload: WelfareInterventionCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles("admin", "officer", "welfare"))
):
    alert = db.query(WelfareAlert).filter(WelfareAlert.id == alert_id).first()
    if not alert:
        raise HTTPException(status_code=404, detail="Alert not found")
    check_personnel_access(current_user, alert.personnel_id, db)
    try:
        intervention = WelfareAlertService.create_intervention(
            db, 
            alert_id, 
            current_user.id, 
            payload.intervention_type, 
            payload.planned_date, 
            payload.notes
        )
        return intervention
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post(
    "/interventions/{intervention_id}/follow-up",
    response_model=WelfareInterventionOut,
    summary="Schedule a follow-up for an intervention"
)
def schedule_followup(
    intervention_id: int,
    payload: FollowUpScheduleRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles("admin", "officer", "welfare"))
):
    intervention = db.query(WelfareIntervention).filter(WelfareIntervention.id == intervention_id).first()
    if not intervention:
        raise HTTPException(status_code=404, detail="Intervention not found")
    check_personnel_access(current_user, intervention.personnel_id, db)
    try:
        intervention = WelfareAlertService.schedule_followup(
            db, 
            intervention_id, 
            current_user.id, 
            payload.follow_up_date, 
            payload.notes
        )
        return intervention
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post(
    "/interventions/{intervention_id}/complete",
    response_model=WelfareInterventionOut,
    summary="Complete a welfare intervention"
)
def complete_intervention(
    intervention_id: int,
    payload: Optional[InterventionCompleteRequest] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles("admin", "officer", "welfare"))
):
    intervention = db.query(WelfareIntervention).filter(WelfareIntervention.id == intervention_id).first()
    if not intervention:
        raise HTTPException(status_code=404, detail="Intervention not found")
    check_personnel_access(current_user, intervention.personnel_id, db)
    try:
        notes = payload.notes if payload else None
        intervention = WelfareAlertService.complete_intervention(
            db, 
            intervention_id, 
            current_user.id, 
            notes=notes
        )
        return intervention
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post(
    "/interventions/{intervention_id}/cancel",
    response_model=WelfareInterventionOut,
    summary="Cancel a welfare intervention"
)
def cancel_intervention(
    intervention_id: int,
    payload: Optional[InterventionCancelRequest] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles("admin", "officer", "welfare"))
):
    intervention = db.query(WelfareIntervention).filter(WelfareIntervention.id == intervention_id).first()
    if not intervention:
        raise HTTPException(status_code=404, detail="Intervention not found")
    check_personnel_access(current_user, intervention.personnel_id, db)
    try:
        reason = payload.reason if payload else None
        intervention = WelfareAlertService.cancel_intervention(
            db, 
            intervention_id, 
            current_user.id, 
            reason=reason
        )
        return intervention
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post(
    "/alerts/{alert_id}/resolve",
    response_model=WelfareAlertOut,
    summary="Resolve a welfare alert"
)
def resolve_alert(
    alert_id: int,
    payload: AlertResolveRequest,
    dismiss: bool = Query(False),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles("admin", "officer", "welfare"))
):
    alert = db.query(WelfareAlert).filter(WelfareAlert.id == alert_id).first()
    if not alert:
        raise HTTPException(status_code=404, detail="Alert not found")
    check_personnel_access(current_user, alert.personnel_id, db)
    try:
        alert = WelfareAlertService.resolve_alert(
            db, 
            alert_id, 
            current_user.id, 
            payload.resolution_reason, 
            dismiss=dismiss
        )
        return alert
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
