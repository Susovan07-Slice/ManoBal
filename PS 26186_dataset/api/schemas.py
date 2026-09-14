from pydantic import BaseModel, Field
from typing import Optional, Dict, Any
from datetime import datetime

class DailyCheckIn(BaseModel):
    personnel_id: str = Field(..., description="Unique identifier for the personnel")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Time of the check-in")
    sleep_hours: float = Field(..., description="Number of hours slept")
    stress_level_self_reported: int = Field(..., ge=1, le=10, description="Self-reported stress level from 1 to 10")
    fatigue_level: int = Field(..., ge=1, le=10, description="Self-reported fatigue level from 1 to 10")
    heart_rate_bpm: Optional[int] = Field(None, description="Resting heart rate in BPM")
    blood_pressure_sys: Optional[int] = Field(None, description="Systolic blood pressure")
    blood_pressure_dia: Optional[int] = Field(None, description="Diastolic blood pressure")

class PersonnelAlert(BaseModel):
    alert_id: str = Field(..., description="Unique identifier for the alert")
    personnel_id: str = Field(..., description="Unique identifier for the personnel")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Time the alert was generated")
    risk_score: float = Field(..., ge=0, le=100, description="Calculated stress risk score (0-100)")
    risk_level: str = Field(..., description="Risk level classification: Low, Moderate, High, Critical")
    alert_message: str = Field(..., description="Detailed message describing the alert")
    shap_explanation: Optional[Dict[str, Any]] = Field(None, description="SHAP values explaining the risk score")
