from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, List, Dict, Any
from datetime import datetime

class CurrentRiskSignal(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    risk_score: Optional[float] = Field(None, description="Continuous risk score (0-100) from Phase 34, or None if unavailable")
    stress_level: Optional[str] = Field(None, description="Authoritative Phase 34 category: Low, Medium, High")
    risk_priority: Optional[str] = Field(None, description="Authoritative Phase 34 priority: Routine, Preventive, Priority")
    assessment_timestamp: Optional[datetime] = Field(None, description="Timestamp of most recent assessment")
    confidence: str = Field("UNAVAILABLE", description="Inference confidence: HIGH, MEDIUM, LOW, UNAVAILABLE")
    data_sufficiency: str = Field("INSUFFICIENT_DATA", description="SUFFICIENT or INSUFFICIENT_DATA")
    key_factors: List[str] = Field(default_factory=list, description="Top contributing factors from LightGBM model")
    notice: str = Field(
        "Phase 34 authoritative risk inference; administrative welfare monitoring, non-diagnostic.",
        description="Authoritative notice"
    )

class TrendSignal(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    trend_direction: str = Field("INSUFFICIENT_DATA", description="WORSENING, IMPROVING, STABLE, INSUFFICIENT_DATA")
    trend_slope: Optional[float] = Field(None, description="Linear slope (pts/day)")
    persistence: str = Field("INSUFFICIENT_DATA", description="PERSISTENT_ELEVATED, EPISODIC, TRANSIENT, NOT_ELEVATED, INSUFFICIENT_DATA")
    acceleration: str = Field("INSUFFICIENT_DATA", description="ACCELERATING, DECELERATING, LINEAR, STABLE, INSUFFICIENT_DATA")
    personal_baseline_score: Optional[float] = Field(None, description="Personal historical baseline score")
    personal_baseline_category: Optional[str] = Field(None, description="Personal historical baseline category")
    score_change: Optional[float] = Field(None, description="Delta from previous assessment")
    data_sufficiency: str = Field("INSUFFICIENT_DATA", description="SUFFICIENT_HISTORY, LIMITED_HISTORY, INSUFFICIENT_DATA")
    explanation: str = Field("No longitudinal assessment history available.", description="Descriptive trend narrative")

class AlertSignalItem(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    alert_type: str
    severity: str
    status: str
    trigger_reason: Optional[str] = None
    created_at: datetime
    linked_intervention_id: Optional[int] = None

class AnomalySignalItem(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    anomaly_type: str
    severity: str
    status: str
    confidence: str
    detected_at: datetime
    explanation: str

class RecommendationSignalItem(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    recommendation_type: str
    title: Optional[str] = None
    priority: str
    status: str
    recommended_review_window: Optional[str] = None
    reason: Optional[str] = None
    created_at: datetime
    is_system_suggestion: bool = True
    system_vs_human_notice: str = "System support suggestion only; requires authorized human review and decision."

class InterventionSignalItem(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    alert_id: int
    intervention_type: str
    status: str
    planned_date: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    follow_up_date: Optional[datetime] = None
    notes: Optional[str] = None

class FollowupSignalItem(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    followup_type: str
    status: str
    scheduled_at: Optional[datetime] = None
    due_date: Optional[datetime] = None
    is_overdue: bool = False
    outcome_status: str = "INSUFFICIENT_DATA"
    score_delta: Optional[float] = None
    explanation: Optional[str] = None

class DataFreshnessReport(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    last_assessment_timestamp: Optional[datetime] = None
    last_assessment_relative: str = "Unavailable"
    last_trend_timestamp: Optional[datetime] = None
    last_trend_relative: str = "Unavailable"
    last_alert_timestamp: Optional[datetime] = None
    last_alert_relative: str = "None recorded"
    last_anomaly_timestamp: Optional[datetime] = None
    last_anomaly_relative: str = "None recorded"
    last_recommendation_timestamp: Optional[datetime] = None
    last_recommendation_relative: str = "None recorded"
    last_followup_timestamp: Optional[datetime] = None
    last_followup_relative: str = "None recorded"
    is_stale: bool = False
    overall_freshness_status: str = "INSUFFICIENT_DATA" # FRESH, STALE, INSUFFICIENT_DATA

class HumanReviewIndicator(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    review_level: str = Field(..., description="REVIEW, MONITOR, NO_ACTIVE_REVIEW_SIGNAL, or INSUFFICIENT_DATA")
    reasons: List[str] = Field(default_factory=list, description="Explicit transparent rule-based explanations")
    disclaimer: str = Field(
        "Qualitative human decision-support guidance only; this is NOT a numerical score, priority score, or fitness-for-duty ranking.",
        description="Ethical decision-support disclaimer"
    )

class TimelineEventItem(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    timestamp: datetime
    relative_time: str
    phase: str
    event_type: str
    title: str
    status: Optional[str] = None
    severity_or_priority: Optional[str] = None
    summary: str
    evidence: Dict[str, Any] = Field(default_factory=dict)

class PersonnelWelfareSnapshotResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    personnel_id: int
    personnel_code: str
    name: str
    department: Optional[str] = None
    battalion: Optional[str] = None
    location: Optional[str] = None
    job_role: Optional[str] = None

    current_risk: CurrentRiskSignal
    trend: TrendSignal
    alerts: List[AlertSignalItem] = Field(default_factory=list)
    anomalies: List[AnomalySignalItem] = Field(default_factory=list)
    recommendations: List[RecommendationSignalItem] = Field(default_factory=list)
    interventions: List[InterventionSignalItem] = Field(default_factory=list)
    followups: List[FollowupSignalItem] = Field(default_factory=list)

    data_freshness: DataFreshnessReport
    data_sufficiency: str = "INSUFFICIENT_DATA"
    human_review_indicator: HumanReviewIndicator
    timeline: List[TimelineEventItem] = Field(default_factory=list)

    disclaimer: str = (
        "Phase 42 integrates authoritative welfare intelligence across Phases 34–41 for human decision-support. "
        "It does NOT calculate a composite risk score, diagnose medical conditions, assign disciplinary action, "
        "or replace commander clinical or operational judgement."
    )

class UnitPersonnelSummaryCard(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    personnel_id: int
    personnel_code: str
    name: str
    department: Optional[str] = None
    battalion: Optional[str] = None
    location: Optional[str] = None
    current_risk_category: Optional[str] = None
    current_risk_score: Optional[float] = None
    trend_direction: str = "INSUFFICIENT_DATA"
    review_level: str = "NO_ACTIVE_REVIEW_SIGNAL"
    active_alerts_count: int = 0
    active_anomalies_count: int = 0
    open_recommendations_count: int = 0
    open_interventions_count: int = 0
    pending_followups_count: int = 0
    has_overdue_followup: bool = False
    freshness_status: str = "INSUFFICIENT_DATA"

class UnitWelfareIntelligenceResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    scope_battalion: Optional[str] = None
    scope_location: Optional[str] = None
    total_personnel_in_scope: int
    privacy_threshold: int = 5
    data_suppressed: bool = False
    suppression_reason: Optional[str] = None

    unit_overview: Dict[str, Any] = Field(default_factory=dict)
    support_workflow: Dict[str, Any] = Field(default_factory=dict)
    data_quality: Dict[str, Any] = Field(default_factory=dict)
    human_review_summary: Dict[str, int] = Field(default_factory=dict)
    personnel_cards: List[UnitPersonnelSummaryCard] = Field(default_factory=list)

    disclaimer: str = (
        "Phase 42 aggregates authoritative welfare intelligence across Phases 34–41 for commander decision-support. "
        "It enforces small-group k-anonymity privacy (k >= 5) and does NOT rank personnel, compute composite scores, "
        "or automate personnel decisions."
    )
