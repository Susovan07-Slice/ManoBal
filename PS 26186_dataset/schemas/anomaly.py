from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime

class AnomalyEvidence(BaseModel):
    reason: str = Field(..., description="Primary reason the anomaly was flagged")
    baseline_metric: Optional[str] = Field(None, description="Metric being evaluated")
    baseline_value: Optional[float] = Field(None, description="Historical baseline value or mean")
    baseline_std: Optional[float] = Field(None, description="Historical baseline standard deviation")
    current_value: Optional[float] = Field(None, description="Current observed value")
    delta: Optional[float] = Field(None, description="Observed change from baseline")
    sample_count: int = Field(0, description="Number of baseline samples utilized")
    window_description: Optional[str] = Field(None, description="Time window evaluated")
    co_occurring_factors: List[str] = Field(default_factory=list, description="Co-occurring operational strain factors")
    explanation: str = Field(..., description="Explainable, non-punitive description of the signal")

class WelfareAnomalyOut(BaseModel):
    id: int
    personnel_id: Optional[int] = None
    personnel_code: Optional[str] = None
    personnel_name: Optional[str] = None
    department: Optional[str] = None
    battalion: Optional[str] = None
    location: Optional[str] = None
    scope_type: str
    scope_battalion: Optional[str] = None
    scope_location: Optional[str] = None
    anomaly_type: str
    severity: str
    status: str
    confidence: str
    baseline_sample_count: int
    detected_at: datetime
    observation_window_start: Optional[datetime] = None
    observation_window_end: Optional[datetime] = None
    evidence: Dict[str, Any] = Field(default_factory=dict)
    acknowledged_at: Optional[datetime] = None
    acknowledged_by: Optional[int] = None
    resolved_at: Optional[datetime] = None
    resolved_by: Optional[int] = None
    resolution_notes: Optional[str] = None
    associated_alert_id: Optional[int] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

class AnomalyActionRequest(BaseModel):
    notes: Optional[str] = None

class AnomalyResolutionRequest(BaseModel):
    resolution_notes: str = Field(..., description="Actionable notes explaining welfare resolution or supportive follow-up")

class PersonnelAnomalyHistoryResponse(BaseModel):
    personnel_id: int
    status: str = Field(..., description="DETECTED, NO_ANOMALY, INSUFFICIENT_BASELINE, or INSUFFICIENT_DATA")
    message: str
    active_anomalies_count: int
    anomalies: List[WelfareAnomalyOut] = Field(default_factory=list)
    baseline_summary: Optional[Dict[str, Any]] = None

class CommanderAnomalyScope(BaseModel):
    role: str
    battalion: Optional[str] = None
    location: Optional[str] = None
    total_authorized_personnel: int
    min_group_size_threshold: int

class CommanderAnomalySummaryResponse(BaseModel):
    status: str = Field(..., description="SUCCESS, INSUFFICIENT_GROUP_SIZE, or INSUFFICIENT_DATA")
    message: Optional[str] = None
    scope: CommanderAnomalyScope
    total_detected_anomalies: int = 0
    active_anomalies_count: int = 0
    by_severity: Dict[str, int] = Field(default_factory=dict)
    by_type: Dict[str, int] = Field(default_factory=dict)
    by_status: Dict[str, int] = Field(default_factory=dict)
    anomalies: List[WelfareAnomalyOut] = Field(default_factory=list)
    unit_level_signals: List[WelfareAnomalyOut] = Field(default_factory=list)
    data_quality: Dict[str, Any] = Field(default_factory=dict)

    class Config:
        from_attributes = True
