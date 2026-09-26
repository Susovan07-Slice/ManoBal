from pydantic import BaseModel, Field
from typing import Optional, List, Literal
from datetime import datetime

class PersonnelBase(BaseModel):
    personnel_code: str = Field(..., description="Unique service code, e.g. PF-0001")
    name: str = Field(..., description="Synthetic demo personnel identifier")
    age: int = Field(..., ge=18, le=70)
    gender: Literal["Male", "Female", "Other"] = "Male"
    department: str = Field(..., description="Department or company battalion")
    battalion: str = Field("7th Battalion", description="Battalion unit assignment")
    job_role: str = Field(..., description="Duty role / assignment")
    location: str = Field(..., description="Station or field base location")
    experience_years: float = Field(..., ge=0.0)
    duty_hours_per_week: float = Field(..., ge=0.0, le=120.0)
    night_shifts_per_month: int = Field(0, ge=0, le=31)
    consecutive_duty_days: int = Field(0, ge=0, le=60)
    transfer_frequency: int = Field(0, ge=0)
    training_load: int = Field(2, ge=0, le=10)
    leave_gap_days: int = Field(30, ge=0)
    deployment_days: int = Field(0, ge=0, le=365)
    remote_posting: Literal["Yes", "No"] = "No"
    operational_exposure: Literal["Low", "Medium", "High"] = "Medium"

class PersonnelCreate(PersonnelBase):
    pass

class PersonnelUpdate(BaseModel):
    name: Optional[str] = None
    age: Optional[int] = Field(None, ge=18, le=70)
    gender: Optional[Literal["Male", "Female", "Other"]] = None
    department: Optional[str] = None
    battalion: Optional[str] = None
    job_role: Optional[str] = None
    location: Optional[str] = None
    experience_years: Optional[float] = Field(None, ge=0.0)
    duty_hours_per_week: Optional[float] = Field(None, ge=0.0, le=120.0)
    night_shifts_per_month: Optional[int] = Field(None, ge=0, le=31)
    consecutive_duty_days: Optional[int] = Field(None, ge=0, le=60)
    transfer_frequency: Optional[int] = None
    training_load: Optional[int] = Field(None, ge=0, le=10)
    leave_gap_days: Optional[int] = None
    deployment_days: Optional[int] = None
    remote_posting: Optional[Literal["Yes", "No"]] = None
    operational_exposure: Optional[Literal["Low", "Medium", "High"]] = None

class PersonnelOut(PersonnelBase):
    id: int
    created_at: datetime
    updated_at: datetime
    latest_risk_score: Optional[float] = None
    latest_stress_level: Optional[str] = None
    latest_priority: Optional[str] = None


    class Config:
        from_attributes = True

class PersonnelListResponse(BaseModel):
    items: List[PersonnelOut]
    total: int
    page: int
    size: int
    pages: int
