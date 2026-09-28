from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, List, Dict, Any
from datetime import datetime

class RecommendationEvidence(BaseModel):
    trigger: str = Field(..., description="Operational event or signal that initiated the recommendation")
    reason: str = Field(..., description="Specific explainable rationale for this recommendation")
    risk_score: Optional[float] = Field(None, description="Authoritative Phase 34 risk score")
    risk_category: Optional[str] = Field(None, description="Authoritative Phase 34 risk category")
    trend_direction: Optional[str] = Field(None, description="Phase 36 longitudinal trajectory")
    trend_slope: Optional[float] = Field(None, description="Rate of change in risk score per day")
    key_factors: List[str] = Field(default_factory=list, description="Top contributing operational stress factors")
    metrics: Dict[str, Any] = Field(default_factory=dict, description="Concrete operational metrics, e.g. duty hours, sleep")
    explanation: str = Field(..., description="Human-readable decision-support justification")

class WelfareRecommendationOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    personnel_id: int
    personnel_code: Optional[str] = None
    personnel_name: Optional[str] = None
    department: Optional[str] = None
    battalion: Optional[str] = None
    location: Optional[str] = None
    assessment_id: Optional[int] = None
    recommendation_type: str
    recommendation_text: str
    title: Optional[str] = None
    description: Optional[str] = None
    reason: Optional[str] = None
    priority: str
    status: str
    confidence: str
    evidence: Dict[str, Any] = Field(default_factory=dict)
    source_signals: List[str] = Field(default_factory=list)
    recommended_review_window: Optional[str] = None
    linked_alert_id: Optional[int] = None
    linked_anomaly_id: Optional[int] = None
    linked_intervention_id: Optional[int] = None
    acknowledged_at: Optional[datetime] = None
    acknowledged_by: Optional[int] = None
    actioned_at: Optional[datetime] = None
    actioned_by: Optional[int] = None
    action_notes: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

class RecommendationAcknowledgeRequest(BaseModel):
    notes: Optional[str] = Field(None, description="Optional notes upon acknowledging recommendation")

class RecommendationAcceptRequest(BaseModel):
    create_intervention: bool = Field(False, description="Optionally initiate a Phase 37 welfare intervention")
    intervention_type: Optional[str] = Field(None, description="Type of supportive intervention (e.g. WELLNESS_CHECKIN, DUTY_ROTATION)")
    scheduled_date: Optional[datetime] = Field(None, description="Planned scheduling date for supportive intervention")
    notes: Optional[str] = Field(None, description="Human reviewer justification and context")

class RecommendationDeferRequest(BaseModel):
    defer_days: int = Field(7, ge=1, le=90, description="Days to defer review of this recommendation")
    notes: Optional[str] = Field(None, description="Reason for deferring review")

class RecommendationDismissRequest(BaseModel):
    reason: str = Field(..., min_length=3, description="Mandatory non-punitive rationale for dismissing recommendation")

class RecommendationActionRequest(BaseModel):
    action_notes: str = Field(..., min_length=3, description="Specific actions taken to address the supportive recommendation")

class RecommendationStatusUpdateRequest(BaseModel):
    status: str = Field(..., description="Target status: e.g. ACCEPTED, ACKNOWLEDGED, ACTIONED, DISMISSED, DEFERRED")
    notes: Optional[str] = Field(None, description="Optional notes or operational rationale")

class PersonnelRecommendationsResponse(BaseModel):
    personnel_id: int
    status: str = Field(..., description="STATUS code, e.g. ACTIVE, NONE, INSUFFICIENT_DATA")
    message: str
    total_recommendations: int
    recommendations: List[WelfareRecommendationOut] = Field(default_factory=list)

class CommanderRecommendationSummaryResponse(BaseModel):
    scope_battalion: Optional[str] = None
    scope_location: Optional[str] = None
    total_active_recommendations: int
    priority_breakdown: Dict[str, int] = Field(default_factory=dict)
    status_breakdown: Dict[str, int] = Field(default_factory=dict)
    type_breakdown: Dict[str, int] = Field(default_factory=dict)
    small_group_suppressed: bool = False
    recommendations: List[WelfareRecommendationOut] = Field(default_factory=list)
