from pydantic import BaseModel, Field
from typing import Optional, Literal
from datetime import datetime

UserRole = Literal["admin", "officer", "welfare", "personnel"]

class UserRegister(BaseModel):
    username: str = Field(..., min_length=3, max_length=64, description="Unique username")
    password: str = Field(..., min_length=6, max_length=128, description="Plaintext password (hashed server-side)")
    role: UserRole = Field("personnel", description="RBAC Role: admin, officer, welfare, personnel")
    personnel_id: Optional[int] = Field(None, description="Optional linked personnel record ID (for personnel role)")
    battalion: Optional[str] = Field(None, description="Optional battalion scope assignment")
    location: Optional[str] = Field(None, description="Optional location scope assignment")

class CommanderSignup(BaseModel):
    username: str = Field(..., min_length=3, max_length=64, description="Unique commander username")
    password: str = Field(..., min_length=6, max_length=128, description="Account password")
    name: str = Field(..., min_length=2, max_length=128, description="Full commander name")
    battalion: str = Field(..., min_length=2, max_length=64, description="Assigned battalion command scope")
    location: str = Field(..., min_length=2, max_length=64, description="Assigned duty station location scope")

class JawanSignup(BaseModel):
    username: str = Field(..., min_length=3, max_length=64, description="Unique service username")
    password: str = Field(..., min_length=6, max_length=128, description="Account password")
    name: str = Field(..., min_length=2, max_length=128, description="Full personnel name")
    personnel_code: str = Field(..., min_length=2, max_length=32, description="Unique Personnel/Service ID")
    age: int = Field(..., ge=18, le=70, description="Age in years (18-70)")
    gender: Literal["Male", "Female", "Other"] = Field("Male", description="Gender identity")
    department: str = Field(..., min_length=2, max_length=64, description="Operational department")
    battalion: str = Field("7th Battalion", min_length=2, max_length=64, description="Assigned battalion unit")
    job_role: str = Field(..., min_length=2, max_length=64, description="Duty rank or operational role")
    location: str = Field(..., min_length=2, max_length=64, description="Base or duty station")
    experience_years: float = Field(..., ge=0.0, le=50.0, description="Years of service experience")
    duty_hours_per_week: Optional[float] = Field(40.0, ge=0.0, le=120.0, description="Baseline weekly duty hours")

class UserLogin(BaseModel):
    username: str
    password: str

class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"
    role: str
    username: str
    personnel_id: Optional[int] = None
    battalion: Optional[str] = None
    location: Optional[str] = None

class UserOut(BaseModel):
    id: int
    username: str
    role: str
    is_active: bool
    personnel_id: Optional[int] = None
    battalion: Optional[str] = None
    location: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True

class ChangePassword(BaseModel):
    old_password: str
    new_password: str = Field(..., min_length=6, max_length=128)

class ChangeBattalion(BaseModel):
    battalion: str = Field(..., min_length=2, max_length=64)
    location: str = Field(..., min_length=2, max_length=64)
