from pydantic import BaseModel, Field
from typing import Optional, List, Literal, Any, Dict
from datetime import datetime

class WelfareAlertAuditOut(BaseModel):
    id: int
    alert_id: int
    action: str
    actor_id: Optional[int] = None
    previous_status: Optional[str] = None
    new_status: Optional[str] = None
    timestamp: datetime
    metadata_json: Optional[str] = None

    class Config:
        from_attributes = True

class WelfareInterventionBase(BaseModel):
    intervention_type: str
    planned_date: Optional[datetime] = None
    notes: Optional[str] = None

class WelfareInterventionCreate(WelfareInterventionBase):
    pass

class WelfareInterventionOut(WelfareInterventionBase):
    id: int
    alert_id: int
    personnel_id: int
    status: str
    created_by: int
    created_at: datetime
    completed_at: Optional[datetime] = None
    follow_up_date: Optional[datetime] = None

    class Config:
        from_attributes = True

class FollowUpScheduleRequest(BaseModel):
    follow_up_date: datetime
    notes: Optional[str] = None

class WelfareAlertBase(BaseModel):
    personnel_id: int
    alert_type: str
    severity: str
    trigger_assessment_id: Optional[int] = None
    trigger_reason: Optional[str] = None

class WelfareAlertCreate(WelfareAlertBase):
    pass

class WelfareAlertOut(WelfareAlertBase):
    id: int
    status: str
    created_at: datetime
    acknowledged_at: Optional[datetime] = None
    acknowledged_by: Optional[int] = None
    resolved_at: Optional[datetime] = None
    resolved_by: Optional[int] = None
    resolution_reason: Optional[str] = None
    interventions: List[WelfareInterventionOut] = []
    audits: List[WelfareAlertAuditOut] = []

    class Config:
        from_attributes = True

class AlertResolveRequest(BaseModel):
    resolution_reason: str

class InterventionCancelRequest(BaseModel):
    reason: Optional[str] = None

class InterventionCompleteRequest(BaseModel):
    notes: Optional[str] = None
