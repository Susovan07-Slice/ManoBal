from datetime import datetime
from typing import Optional, Literal
from pydantic import BaseModel, Field

class WelfareRequestCreate(BaseModel):
    category: str = Field(..., min_length=2, max_length=64, description="Welfare concern category (Workload, Rest, Personal, Operational, General, Emergency)")
    message: Optional[str] = Field(None, max_length=1000, description="Optional brief context from Jawan")
    urgency: Literal["Routine", "Medium", "High"] = Field("Routine", description="Self-assessed urgency level")

class WelfareRequestStatusUpdate(BaseModel):
    status: Literal["pending", "acknowledged", "in_progress", "resolved"] = Field(..., description="Updated welfare request lifecycle status")

class WelfareRequestOut(BaseModel):
    id: int
    personnel_id: int
    personnel_code: Optional[str] = None
    personnel_name: Optional[str] = None
    department: Optional[str] = None
    battalion: Optional[str] = None
    job_role: Optional[str] = None
    location: Optional[str] = None
    current_risk_score: Optional[int] = None
    current_stress_level: Optional[str] = None
    current_risk_priority: Optional[str] = None
    category: str
    message: Optional[str] = None
    urgency: str
    status: str
    source: str = "Jawan Request"
    created_at: datetime
    updated_at: datetime
    resolved_at: Optional[datetime] = None

    class Config:
        from_attributes = True
