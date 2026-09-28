from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime

class ScopeInfo(BaseModel):
    role: str = Field(..., description="Role of the authenticated user requesting analytics")
    battalion: Optional[str] = Field(None, description="Authorized battalion scope")
    location: Optional[str] = Field(None, description="Authorized location scope")
    total_authorized_personnel: int = Field(..., description="Total personnel under this authorized scope")
    min_group_size_threshold: int = Field(..., description="Configured privacy k-anonymity minimum threshold")

class RiskCategoryDistributionItem(BaseModel):
    label: str = Field(..., description="Risk category: Low, Moderate, Elevated, High, Critical")
    count: int = Field(..., description="Number of personnel currently in this category")
    percentage: float = Field(..., description="Percentage of assessed personnel")

class RiskDistributionSection(BaseModel):
    total_represented: int = Field(..., description="Total unique personnel represented in distribution")
    categories: List[RiskCategoryDistributionItem] = Field(default_factory=list)
    low_count: int = 0
    low_pct: float = 0.0
    moderate_count: int = 0
    moderate_pct: float = 0.0
    elevated_count: int = 0
    elevated_pct: float = 0.0
    high_count: int = 0
    high_pct: float = 0.0
    critical_count: int = 0
    critical_pct: float = 0.0

class TimelinePoint(BaseModel):
    date: str = Field(..., description="Date identifier (YYYY-MM-DD)")
    average_risk_score: Optional[float] = None
    elevated_and_above_count: int = 0
    low_moderate_count: int = 0
    total_assessed: int = 0

class TrendSection(BaseModel):
    direction: str = Field(..., description="Overall trend: IMPROVING, STABLE, WORSENING, INSUFFICIENT_DATA, LIMITED_HISTORY")
    improving_count: int = 0
    improving_pct: float = 0.0
    stable_count: int = 0
    stable_pct: float = 0.0
    worsening_count: int = 0
    worsening_pct: float = 0.0
    insufficient_history_count: int = 0
    insufficient_history_pct: float = 0.0
    mean_risk_score: Optional[float] = None
    median_risk_score: Optional[float] = None
    persistent_elevated_population: int = 0
    persistent_elevated_pct: float = 0.0
    timeline: List[TimelinePoint] = Field(default_factory=list)

class AlertTimelinePoint(BaseModel):
    date: str = Field(..., description="Date identifier (YYYY-MM-DD)")
    created_count: int = 0
    resolved_count: int = 0

class AlertsSection(BaseModel):
    total_alerts: int = 0
    open_alerts: int = 0
    under_review_alerts: int = 0
    resolved_alerts: int = 0
    unresolved_alerts: int = 0
    by_type: Dict[str, int] = Field(default_factory=dict)
    by_severity: Dict[str, int] = Field(default_factory=dict)
    timeline: List[AlertTimelinePoint] = Field(default_factory=list)

class WelfareFactorItem(BaseModel):
    factor: str = Field(..., description="Non-punitive welfare factor description")
    affected_count: int = Field(..., description="Number of unique personnel affected")
    affected_pct: float = Field(..., description="Percentage of assessed personnel")
    trend: Optional[str] = Field("STABLE", description="Factor trend: INCREASING, STABLE, DECREASING, or INSUFFICIENT_DATA")

class WelfareFactorsSection(BaseModel):
    factors: List[WelfareFactorItem] = Field(default_factory=list)
    total_records_analyzed: int = 0

class InterventionsSection(BaseModel):
    total_interventions: int = 0
    planned: int = 0
    completed: int = 0
    follow_up_required: int = 0
    by_type: Dict[str, int] = Field(default_factory=dict)

class SummarySection(BaseModel):
    total_authorized_personnel: int = 0
    assessed_personnel_count: int = 0
    assessment_coverage_pct: float = 0.0
    open_alerts_count: int = 0
    worsening_trend_count: int = 0
    worsening_trend_pct: float = 0.0
    persistent_elevated_count: int = 0
    persistent_elevated_pct: float = 0.0
    average_risk_score: Optional[float] = None

class DateRangeInfo(BaseModel):
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    filter_type: str = "30d"

class DataQualitySection(BaseModel):
    records_analyzed: int = 0
    personnel_count: int = 0
    latest_assessment_date: Optional[datetime] = None
    date_range: DateRangeInfo
    insufficient_data: bool = False
    notes: List[str] = Field(default_factory=list)

class CommanderAnalyticsResponse(BaseModel):
    status: str = Field(..., description="SUCCESS, INSUFFICIENT_GROUP_SIZE, or INSUFFICIENT_DATA")
    message: Optional[str] = None
    scope: ScopeInfo
    summary: Optional[SummarySection] = None
    risk_distribution: Optional[RiskDistributionSection] = None
    trend: Optional[TrendSection] = None
    alerts: Optional[AlertsSection] = None
    welfare_factors: Optional[WelfareFactorsSection] = None
    interventions: Optional[InterventionsSection] = None
    data_quality: DataQualitySection

    class Config:
        from_attributes = True
