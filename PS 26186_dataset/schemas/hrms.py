from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field, ConfigDict

class HrmsSyncRequest(BaseModel):
    """
    Structured payload for mock HRMS service-record synchronization.
    Clearly designated as mock/simulated integration interface.
    Supports standard naming conventions (years_of_service, leave_balance_days, etc.).
    """
    model_config = ConfigDict(from_attributes=True, populate_by_name=True)

    personnel_id: int = Field(..., description="Target personnel database ID")
    service_number: Optional[str] = Field(None, min_length=2, max_length=64, description="Service/employee identifier")
    department: Optional[str] = Field(None, min_length=2, max_length=64, description="Command department")
    battalion: Optional[str] = Field(None, min_length=2, max_length=64, description="Assigned battalion unit")
    location: Optional[str] = Field(None, min_length=2, max_length=64, description="Duty station location")
    job_role: Optional[str] = Field(None, min_length=2, max_length=64, description="Operational role or trade")
    rank: Optional[str] = Field(None, min_length=2, max_length=64, description="Military/police rank designation")
    deployment_days: Optional[int] = Field(None, ge=0, le=3650, description="Total days on field deployment")
    duty_hours_per_week: Optional[float] = Field(None, ge=0.0, le=168.0, description="Average duty hours per week")
    night_shifts_per_month: Optional[int] = Field(None, ge=0, le=31, description="Night shifts rostered per month")
    consecutive_duty_days: Optional[int] = Field(None, ge=0, le=365, description="Consecutive operational duty days")
    consecutive_days_on_duty: Optional[int] = Field(None, ge=0, le=365, description="Consecutive operational duty days alias")
    leave_gap_days: Optional[int] = Field(None, ge=0, le=3650, description="Days elapsed since last sanctioned leave")
    leave_balance_days: Optional[int] = Field(None, ge=0, le=3650, description="Remaining sanctioned leave days balance")
    annual_leaves_taken: Optional[int] = Field(None, ge=0, le=120, description="Annual leaves utilized in current calendar year")
    leaves_taken_past_year: Optional[int] = Field(None, ge=0, le=120, description="Annual leaves utilized alias")
    transfer_frequency: Optional[int] = Field(None, ge=0, le=50, description="Total station transfers in service history")
    training_load: Optional[int] = Field(None, ge=0, le=50, description="Training sessions completed this year")
    experience_years: Optional[float] = Field(None, ge=0.0, le=50.0, description="Total years in active uniformed service")
    years_of_service: Optional[float] = Field(None, ge=0.0, le=50.0, description="Years in active service alias")
    deployment_history: Optional[str] = Field(None, max_length=512, description="Raw deployment history description")
    transfer_history: Optional[str] = Field(None, max_length=512, description="Raw transfer history description")
    training_history: Optional[str] = Field(None, max_length=512, description="Raw training history description")
    raw_metadata: Optional[str] = Field(None, max_length=512, description="Optional raw HRMS JSON/string metadata")


class HrmsSyncResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    status: str = "success"
    message: str
    record_id: int
    personnel_id: int
    personnel_code: str
    service_number: Optional[str]
    battalion: Optional[str]
    location: Optional[str]
    synced_at: datetime
    source: str = "mock_hrms"
    disclaimer: str = "Mock HRMS ingestion interface. Data represents simulated service records and is not connected to real armed forces HRMS."
