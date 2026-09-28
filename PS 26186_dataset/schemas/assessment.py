from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Literal
from datetime import datetime

class AssessmentOverride(BaseModel):
    """Combined daily assessment inputs submitted by personnel."""
    duty_hours_per_week: Optional[float] = Field(None, ge=0.0, le=120.0, description="Weekly operational duty hours")
    night_shifts_per_month: Optional[int] = Field(None, ge=0, le=31, description="Night shifts assigned in trailing 30 days")
    consecutive_duty_days: Optional[int] = Field(None, ge=0, le=60, description="Continuous consecutive duty days without rest")
    leave_gap_days: Optional[int] = Field(None, ge=0, description="Days elapsed since last sanctioned leave")
    sleep_hours: Optional[float] = Field(None, ge=0.0, le=24.0, description="Average restorative sleep hours per day")
    physical_activity_hours_per_week: Optional[float] = Field(None, ge=0.0, le=50.0, description="Weekly physical conditioning hours")
    operational_exposure: Optional[Literal["Low", "Medium", "High"]] = Field(None, description="Current operational hazard exposure")
    remote_posting: Optional[Literal["Yes", "No"]] = Field(None, description="Remote posting status")
    mood_score: Optional[int] = Field(None, ge=1, le=7, description="Self-reported mood index (1-7)")
    burnout_symptoms: Optional[Literal["Rarely", "Sometimes", "Often"]] = Field(None, description="Self-reported burnout frequency")
    physical_fatigue: Optional[int] = Field(None, ge=1, le=5, description="Self-reported physical fatigue rating (1-5)")
    interest_score: Optional[int] = Field(None, ge=0, le=3, description="Interest in daily tasks (0=Very interested, 1=Moderately, 2=Low, 3=Very low)")
    discouraged_score: Optional[int] = Field(None, ge=0, le=3, description="Feeling down or discouraged (0=Never, 1=Several days, 2=More than half, 3=Nearly every day)")
    concentration_score: Optional[int] = Field(None, ge=0, le=3, description="Trouble concentrating (0=Never, 1=Several days, 2=More than half, 3=Nearly every day)")

class AssessmentScheduleStatus(BaseModel):
    personnel_id: int
    has_assessment: bool
    last_assessment_at: Optional[datetime] = None
    assessment_due: bool
    hours_since_last_assessment: Optional[float] = None
    next_assessment_due_at: Optional[datetime] = None
    latest_stress_level: Optional[str] = None
    latest_risk_score: Optional[float] = None
    latest_priority: Optional[str] = None
    message: str

class RecommendationOut(BaseModel):
    id: int
    personnel_id: int
    assessment_id: int
    recommendation_type: str
    recommendation_text: str
    priority: str
    status: str
    created_at: datetime

    class Config:
        from_attributes = True

class RecommendationStatusUpdate(BaseModel):
    status: Literal["pending", "acknowledged", "completed", "dismissed"] = Field(
        ..., description="New welfare recommendation status"
    )

class StressAssessmentOut(BaseModel):
    id: int
    personnel_id: int
    personnel_code: Optional[str] = None
    personnel_name: Optional[str] = None
    stress_level: str
    low_probability: float
    medium_probability: float
    high_probability: float
    risk_score: float
    risk_priority: str
    confidence: Optional[str] = "Moderate"
    uncertainty: Optional[float] = 0.0
    risk_trend: Optional[str] = "Stable"
    risk_change: Optional[float] = 0.0
    consecutive_high_risk: Optional[int] = 0
    risk_probability: Optional[float] = None
    risk_percentile: Optional[float] = None
    out_of_distribution: Optional[bool] = False
    ood_reasons: Optional[List[str]] = []
    key_factors: List[str] = []
    model_version: str
    assessment_timestamp: datetime
    recommendations: List[RecommendationOut] = []


    class Config:
        from_attributes = True

class AssessmentResponse(BaseModel):
    status: str = "success"
    message: str
    assessment: StressAssessmentOut
    disclaimer: str = (
        "AI-assisted early-warning decision-support prototype. "
        "Assessments indicate statistical model associations and are strictly intended "
        "for supportive welfare intervention, not disciplinary action or clinical diagnosis."
    )

class LongitudinalCurrentState(BaseModel):
    risk_score: float
    risk_category: str
    assessment_timestamp: datetime

class LongitudinalTrendState(BaseModel):
    direction: Literal["IMPROVING", "STABLE", "WORSENING", "INSUFFICIENT_DATA"]
    score_change: Optional[float]
    slope: Optional[float]
    acceleration: Literal["INCREASING", "DECREASING", "STABLE", "INSUFFICIENT_DATA"]

class LongitudinalHistoryState(BaseModel):
    assessment_count: int
    data_sufficiency: Literal["INSUFFICIENT_DATA", "LIMITED_HISTORY", "SUFFICIENT_HISTORY"]
    persistent_elevated_risk: bool
    consecutive_elevated_assessments: int
    recent_average_score: Optional[float]
    highest_recent_score: Optional[float]

class LongitudinalBaselineState(BaseModel):
    historical_mean: Optional[float]
    historical_median: Optional[float]
    historical_std: Optional[float]
    current_deviation: Optional[float]

class RepeatedFactor(BaseModel):
    factor: str
    type: Literal["risk", "protective"]
    frequency: int
    total_assessments: int
    most_recent_occurrence: str
    description: str

class LongitudinalTrendResponse(BaseModel):
    personnel_id: int
    current: Optional[LongitudinalCurrentState]
    trend: LongitudinalTrendState
    history: LongitudinalHistoryState
    baseline: LongitudinalBaselineState
    repeated_factors: List[RepeatedFactor]
    disclaimer: str = (
        "Longitudinal analytics are administrative welfare-monitoring signals "
        "and are not clinical diagnoses or causal conclusions."
    )
