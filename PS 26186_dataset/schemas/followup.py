from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, List, Dict, Any
from datetime import datetime

class FollowupEvidence(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    baseline_source: Optional[str] = Field(None, description="Source of baseline: PRE_INTERVENTION_ASSESSMENT, PRE_RECOMMENDATION_ASSESSMENT, or HISTORICAL_BASELINE")
    baseline_assessment_id: Optional[int] = Field(None, description="ID of baseline StressAssessment")
    baseline_score: Optional[float] = Field(None, description="Baseline risk score (0-100)")
    baseline_category: Optional[str] = Field(None, description="Baseline risk category")
    baseline_timestamp: Optional[str] = Field(None, description="Timestamp of baseline assessment")
    followup_assessment_id: Optional[int] = Field(None, description="ID of post-follow-up StressAssessment")
    followup_score: Optional[float] = Field(None, description="Post-follow-up risk score (0-100)")
    followup_category: Optional[str] = Field(None, description="Post-follow-up risk category")
    followup_timestamp: Optional[str] = Field(None, description="Timestamp of post-follow-up assessment")
    score_delta: Optional[float] = Field(None, description="Change in score (followup - baseline)")
    data_sufficiency: str = Field("INSUFFICIENT", description="SUFFICIENT, LIMITED, or INSUFFICIENT")
    explanation: str = Field(..., description="Objective observational narrative describing data pattern")
    notice: str = Field(
        "Observational monitoring state based on available data; not a clinical diagnosis or determination of fitness for duty.",
        description="Mandatory ethical boundary notice"
    )

class WelfareFollowupOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    personnel_id: int
    personnel_code: Optional[str] = None
    personnel_name: Optional[str] = None
    department: Optional[str] = None
    battalion: Optional[str] = None
    location: Optional[str] = None
    recommendation_id: Optional[int] = None
    intervention_id: Optional[int] = None
    alert_id: Optional[int] = None
    followup_type: str
    status: str
    scheduled_at: Optional[datetime] = None
    review_window: Optional[str] = None
    due_date: Optional[datetime] = None
    is_overdue: bool = False
    completed_at: Optional[datetime] = None
    created_by: Optional[int] = None
    completed_by: Optional[int] = None
    notes: Optional[str] = None
    outcome_status: str = "INSUFFICIENT_DATA"
    baseline_source: Optional[str] = None
    baseline_assessment_id: Optional[int] = None
    followup_assessment_id: Optional[int] = None
    evidence: Dict[str, Any] = Field(default_factory=dict)
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

class FollowupCreateRequest(BaseModel):
    personnel_id: int = Field(..., description="Target personnel ID")
    followup_type: str = Field(..., description="WELFARE_CHECKIN, RECOVERY_REVIEW, DUTY_SCHEDULE_REVIEW, SUPPORT_RESOURCE_FOLLOWUP, REASSESSMENT, INTERVENTION_REVIEW")
    recommendation_id: Optional[int] = Field(None, description="Linked Phase 40 WelfareRecommendation ID")
    intervention_id: Optional[int] = Field(None, description="Linked Phase 37 WelfareIntervention ID")
    alert_id: Optional[int] = Field(None, description="Linked Phase 37 WelfareAlert ID")
    review_window: Optional[str] = Field("NOT_SPECIFIED", description="Review window, e.g. 'Within 7 days', 'Within 14 days', 'Within 30 days', 'NOT_SPECIFIED'")
    scheduled_at: Optional[datetime] = Field(None, description="Optionally schedule initial follow-up date")
    notes: Optional[str] = Field(None, description="Initial review or context notes")

class FollowupScheduleRequest(BaseModel):
    scheduled_at: datetime = Field(..., description="Scheduled date and time for follow-up")
    notes: Optional[str] = Field(None, description="Scheduling notes or agenda")

class FollowupCompleteRequest(BaseModel):
    notes: Optional[str] = Field(None, description="Review notes or observations upon completion")
    followup_assessment_id: Optional[int] = Field(None, description="Explicit subsequent assessment ID if specified")
    trigger_new_recommendation_if_worsening: bool = Field(True, description="Optionally generate new Phase 40 supportive recommendation if outcome indicates WORSENING or PERSISTENT_CONCERN")

class FollowupDeferRequest(BaseModel):
    defer_days: int = Field(7, ge=1, le=90, description="Days to defer follow-up review")
    notes: Optional[str] = Field(None, description="Reason for deferring follow-up")

class FollowupCancelRequest(BaseModel):
    reason: str = Field(..., min_length=3, description="Mandatory reason for cancelling follow-up")

class FollowupAuditOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    followup_id: int
    action: str
    actor_id: Optional[int] = None
    previous_status: Optional[str] = None
    new_status: Optional[str] = None
    timestamp: datetime
    metadata: Dict[str, Any] = Field(default_factory=dict)

class PersonnelFollowupsResponse(BaseModel):
    personnel_id: int
    status: str
    message: str
    followups: List[WelfareFollowupOut] = Field(default_factory=list)

class UnitFollowupAnalyticsResponse(BaseModel):
    scope_battalion: Optional[str] = None
    scope_location: Optional[str] = None
    total_personnel_in_scope: int
    privacy_threshold: int = 5
    data_suppressed: bool = False
    suppression_reason: Optional[str] = None
    followups_total: int = 0
    followups_pending: int = 0
    followups_scheduled: int = 0
    followups_completed: int = 0
    followups_overdue: int = 0
    followups_deferred: int = 0
    followups_cancelled: int = 0
    outcome_distribution: Dict[str, int] = Field(default_factory=dict)
    persistent_concern_count: int = 0
    disclaimer: str = (
        "Phase 41 reports observable follow-up and outcome patterns from available welfare data. "
        "It does not establish clinical recovery, fitness for duty, treatment effectiveness, or personnel suitability."
    )
