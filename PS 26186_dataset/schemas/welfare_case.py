from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, List, Dict, Any
from datetime import datetime

# -----------------------------------------------------------------------------
# ENUM-LIKE CONSTANTS & ALLOWED VALUES
# -----------------------------------------------------------------------------

VALID_CASE_STATUSES = [
    "OPEN",
    "UNDER_REVIEW",
    "SUPPORT_IN_PROGRESS",
    "AWAITING_FOLLOW_UP",
    "MONITORING",
    "RESOLVED",
    "CLOSED",
]

VALID_CASE_TYPES = [
    "CURRENT_RISK_REVIEW",
    "WORSENING_TREND",
    "ACTIVE_ALERT",
    "ANOMALY_REVIEW",
    "SUPPORT_FOLLOW_UP",
    "REPEATED_WELFARE_CONCERN",
    "OTHER",
]

VALID_TRIGGER_SOURCES = [
    "PHASE_34_RISK",
    "PHASE_36_TREND",
    "PHASE_37_ALERT",
    "PHASE_39_ANOMALY",
    "PHASE_40_RECOMMENDATION",
    "PHASE_41_FOLLOWUP",
    "PHASE_42_INTELLIGENCE",
    "MANUAL_REVIEW",
]

VALID_CLOSURE_REASONS = [
    "RESOLVED",
    "MONITORING_COMPLETED",
    "SUPPORT_COMPLETED",
    "NO_FURTHER_ACTION_REQUIRED",
    "TRANSFERRED",
    "DUPLICATE",
    "OTHER",
]

VALID_HUMAN_DECISIONS = [
    "CONTINUE_MONITORING",
    "CONTACT_PERSONNEL",
    "REVIEW_DUTY_SUPPORT",
    "OFFER_SUPPORT_RESOURCE",
    "SCHEDULE_FOLLOW_UP",
    "CONTINUE_EXISTING_INTERVENTION",
    "CLOSE_CASE",
    "REFER_TO_AUTHORIZED_SUPPORT",
    "OTHER",
]

VALID_NOTE_TYPES = [
    "REVIEW_NOTE",
    "SUPPORT_NOTE",
    "FOLLOW_UP_NOTE",
    "OUTCOME_NOTE",
    "CLOSURE_NOTE",
    "GENERAL_NOTE",
    "OTHER",
]

VALID_REVIEW_TYPES = [
    "INITIAL_TRIAGE",
    "PROGRESS_EVALUATION",
    "INTERVENTION_REVIEW",
    "FOLLOWUP_ASSESSMENT",
    "CLOSURE_REVIEW",
    "ROUTINE_MONITORING",
]


# -----------------------------------------------------------------------------
# REQUEST SCHEMAS
# -----------------------------------------------------------------------------

class WelfareCaseCreateRequest(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    personnel_id: int = Field(..., description="ID of the personnel member for whom case is opened")
    case_type: str = Field(
        "CURRENT_RISK_REVIEW",
        description="Structured reason/type for opening case (CURRENT_RISK_REVIEW, WORSENING_TREND, ACTIVE_ALERT, ANOMALY_REVIEW, SUPPORT_FOLLOW_UP, REPEATED_WELFARE_CONCERN, OTHER)",
    )
    title: Optional[str] = Field(None, max_length=256, description="Descriptive case title")
    summary: Optional[str] = Field(None, description="Human-entered explanation or background context")
    trigger_source: str = Field("MANUAL_REVIEW", description="Source signal triggering review")

    # Optional foreign key references to link existing authoritative entities
    assessment_id: Optional[int] = Field(None, description="Linked Phase 34 Stress Assessment ID")
    alert_id: Optional[int] = Field(None, description="Linked Phase 37 Welfare Alert ID")
    anomaly_id: Optional[int] = Field(None, description="Linked Phase 39 Welfare Anomaly ID")
    recommendation_id: Optional[int] = Field(None, description="Linked Phase 40 Welfare Recommendation ID")
    intervention_id: Optional[int] = Field(None, description="Linked Phase 37 Welfare Intervention ID")
    followup_id: Optional[int] = Field(None, description="Linked Phase 41 Welfare Followup ID")


class WelfareCaseReviewRequest(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    review_type: str = Field("INITIAL_TRIAGE", description="Type of human review performed")
    observations: str = Field(..., min_length=3, description="Reviewer observations and context assessment")
    decision: str = Field(
        ...,
        description="Explicit human workflow decision (CONTINUE_MONITORING, CONTACT_PERSONNEL, REVIEW_DUTY_SUPPORT, OFFER_SUPPORT_RESOURCE, SCHEDULE_FOLLOW_UP, CONTINUE_EXISTING_INTERVENTION, CLOSE_CASE, REFER_TO_AUTHORIZED_SUPPORT, OTHER)",
    )
    next_step: Optional[str] = Field(None, description="Specific follow-up action or plan")
    review_window: Optional[str] = Field("Within 14 days", description="Target timeframe for next review")
    notes: Optional[str] = Field(None, description="Additional review commentary")
    new_status: Optional[str] = Field(None, description="Optional target status transition triggered by review")


class WelfareCaseNoteCreateRequest(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    note_type: str = Field("REVIEW_NOTE", description="Category: REVIEW_NOTE, SUPPORT_NOTE, FOLLOW_UP_NOTE, OUTCOME_NOTE, CLOSURE_NOTE, GENERAL_NOTE, OTHER")
    content: str = Field(..., min_length=1, description="Immutable note content")


class WelfareCaseStatusUpdateRequest(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    status: str = Field(..., description="Target status transition")
    reason: Optional[str] = Field(None, description="Reason for status transition")


class WelfareCaseCloseRequest(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    closure_reason: str = Field(
        ...,
        description="Structured closure reason: RESOLVED, MONITORING_COMPLETED, SUPPORT_COMPLETED, NO_FURTHER_ACTION_REQUIRED, TRANSFERRED, DUPLICATE, OTHER",
    )
    closure_notes: Optional[str] = Field(None, description="Optional closure justification and summary notes")


class WelfareCaseReopenRequest(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    reopen_reason: str = Field(..., min_length=3, description="Mandatory reason for reopening previously closed case")


class WelfareCaseLinkSignalRequest(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    assessment_id: Optional[int] = None
    alert_id: Optional[int] = None
    anomaly_id: Optional[int] = None
    recommendation_id: Optional[int] = None
    intervention_id: Optional[int] = None
    followup_id: Optional[int] = None


# -----------------------------------------------------------------------------
# OUTPUT SCHEMAS
# -----------------------------------------------------------------------------

class WelfareCaseNoteOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    case_id: int
    author_id: Optional[int] = None
    author_name: Optional[str] = None
    author_role: Optional[str] = None
    created_at: datetime
    note_type: str
    content: str


class WelfareCaseReviewOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    case_id: int
    reviewer_id: Optional[int] = None
    reviewer_name: Optional[str] = None
    reviewer_role: Optional[str] = None
    reviewed_at: datetime
    review_type: str
    observations: str
    decision: str
    next_step: Optional[str] = None
    review_window: Optional[str] = None
    notes: Optional[str] = None


class WelfareCaseAuditOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    case_id: int
    action: str
    actor_id: Optional[int] = None
    actor_name: Optional[str] = None
    previous_status: Optional[str] = None
    new_status: Optional[str] = None
    timestamp: datetime
    metadata: Dict[str, Any] = Field(default_factory=dict)


class TimelineEventOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    event_type: str  # "SYSTEM_EVENT" | "HUMAN_ACTION"
    category: str    # "CASE_CREATED", "RISK_ASSESSMENT", "ALERT", "ANOMALY", "RECOMMENDATION", "HUMAN_REVIEW", "NOTE_ADDED", "STATUS_CHANGE", "INTERVENTION", "FOLLOWUP", "CASE_CLOSED", "CASE_REOPENED"
    timestamp: datetime
    title: str
    description: str
    actor: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)


class WelfareCaseEvidenceOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    current_risk: Dict[str, Any] = Field(default_factory=dict, description="Phase 34 authoritative risk")
    trend: Dict[str, Any] = Field(default_factory=dict, description="Phase 36 longitudinal trend")
    active_alert: Optional[Dict[str, Any]] = Field(None, description="Phase 37 active alert")
    active_anomaly: Optional[Dict[str, Any]] = Field(None, description="Phase 39 anomaly")
    open_recommendation: Optional[Dict[str, Any]] = Field(None, description="Phase 40 recommendation")
    intervention: Optional[Dict[str, Any]] = Field(None, description="Phase 37 intervention")
    followup: Optional[Dict[str, Any]] = Field(None, description="Phase 41 follow-up")
    outcome: Optional[Dict[str, Any]] = Field(None, description="Phase 41 outcome")
    notice: str = Field(
        "Synthesized from authoritative existing phases. No composite score.",
        description="Mandatory non-scoring notice"
    )


class SignalsSummaryOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    current_risk_category: Optional[str] = None
    trend_direction: Optional[str] = None
    has_active_alert: bool = False
    alert_severity: Optional[str] = None
    has_active_anomaly: bool = False
    anomaly_severity: Optional[str] = None
    has_open_recommendation: bool = False
    recommendation_priority: Optional[str] = None
    intervention_status: Optional[str] = None
    followup_status: Optional[str] = None
    latest_outcome: Optional[str] = None


class WelfareCaseListItemOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    case_reference: str
    personnel_id: int
    personnel_code: str
    personnel_name: str
    department: str
    battalion: str
    location: str

    status: str
    case_type: str
    trigger_source: str
    title: str
    summary: Optional[str] = None

    opened_at: datetime
    opened_by_name: Optional[str] = None

    last_reviewed_at: Optional[datetime] = None
    last_reviewed_by_name: Optional[str] = None

    closed_at: Optional[datetime] = None
    closure_reason: Optional[str] = None

    signals_summary: SignalsSummaryOut
    created_at: datetime
    updated_at: datetime


class WelfareCaseDetailOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    case_reference: str
    personnel_id: int
    personnel_code: str
    personnel_name: str
    department: str
    battalion: str
    location: str
    job_role: Optional[str] = None

    status: str
    case_type: str
    trigger_source: str
    title: str
    summary: Optional[str] = None

    opened_at: datetime
    opened_by_id: Optional[int] = None
    opened_by_name: Optional[str] = None

    last_reviewed_at: Optional[datetime] = None
    last_reviewed_by_id: Optional[int] = None
    last_reviewed_by_name: Optional[str] = None

    closed_at: Optional[datetime] = None
    closed_by_id: Optional[int] = None
    closed_by_name: Optional[str] = None
    closure_reason: Optional[str] = None
    closure_notes: Optional[str] = None

    reopened_at: Optional[datetime] = None
    reopened_by_id: Optional[int] = None
    reopened_by_name: Optional[str] = None
    reopen_reason: Optional[str] = None

    # Linked entity IDs
    assessment_id: Optional[int] = None
    alert_id: Optional[int] = None
    anomaly_id: Optional[int] = None
    recommendation_id: Optional[int] = None
    intervention_id: Optional[int] = None
    followup_id: Optional[int] = None

    evidence: WelfareCaseEvidenceOut
    reviews: List[WelfareCaseReviewOut] = Field(default_factory=list)
    notes: List[WelfareCaseNoteOut] = Field(default_factory=list)
    latest_audit: Optional[WelfareCaseAuditOut] = None

    created_at: datetime
    updated_at: datetime


class WelfareCaseListResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    cases: List[WelfareCaseListItemOut]
    total_count: int
    data_suppressed: bool = False
    suppression_reason: Optional[str] = None


class WelfareCaseTimelineResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    case_id: int
    case_reference: str
    personnel_code: str
    events: List[TimelineEventOut]


class WelfareCaseAuditsResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    case_id: int
    case_reference: str
    audits: List[WelfareCaseAuditOut]


class WelfareCaseSummaryStatsResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    total_cases: int = 0
    open_cases: int = 0
    under_review_cases: int = 0
    monitoring_cases: int = 0
    closed_cases: int = 0
    status_counts: Dict[str, int] = Field(default_factory=dict)
    data_suppressed: bool = False
    suppression_reason: Optional[str] = None
