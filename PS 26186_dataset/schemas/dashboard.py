from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional
from datetime import datetime

class DistributionItem(BaseModel):
    label: str
    count: int
    percentage: float

class DashboardSummary(BaseModel):
    total_personnel: int = Field(..., description="Total personnel currently in system")
    assessed_personnel: int = Field(..., description="Count of unique personnel with at least one assessment")
    low_risk: int = Field(..., description="Personnel categorized at Routine / Low Risk in latest assessment")
    medium_risk: int = Field(..., description="Personnel categorized at Preventive / Medium Risk in latest assessment")
    high_risk: int = Field(..., description="Personnel categorized at Priority / High Risk in latest assessment")
    pending_recommendations: int = Field(..., description="Active unaddressed welfare recommendations")
    acknowledged_recommendations: int = Field(..., description="Recommendations currently being handled by welfare officers")

class RiskDistributionResponse(BaseModel):
    total_assessed: int
    distribution: List[DistributionItem]

class StressDistributionResponse(BaseModel):
    total_assessed: int
    distribution: List[DistributionItem]

class RecentAssessmentItem(BaseModel):
    id: int
    personnel_id: int
    personnel_code: str
    personnel_name: str
    department: str
    battalion: Optional[str] = None
    location: str
    stress_level: str
    risk_score: float
    risk_priority: str
    assessment_timestamp: datetime

    class Config:
        from_attributes = True

class HighRiskPersonnelItem(BaseModel):
    id: int
    personnel_id: int
    personnel_code: str
    personnel_name: str
    department: str
    battalion: Optional[str] = None
    job_role: str
    location: str
    risk_score: float
    stress_level: str
    risk_priority: str
    duty_hours_per_week: float
    night_shifts_per_month: int
    consecutive_duty_days: int
    leave_gap_days: int
    key_factors: List[str]
    pending_recommendations_count: int
    latest_assessment_date: datetime

    class Config:
        from_attributes = True

