from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, Float, DateTime
from sqlalchemy.orm import relationship
from db.base import Base

class Personnel(Base):
    __tablename__ = "personnel"

    id = Column(Integer, primary_key=True, index=True)
    personnel_code = Column(String(32), unique=True, index=True, nullable=False)  # e.g. PF-0001
    name = Column(String(128), nullable=False)  # Demo/synthetic name
    age = Column(Integer, nullable=False)
    gender = Column(String(16), nullable=False)
    department = Column(String(64), nullable=False, index=True)
    battalion = Column(String(64), nullable=False, index=True, default="7th Battalion")
    job_role = Column(String(64), nullable=False)
    location = Column(String(64), nullable=False, index=True)
    experience_years = Column(Float, nullable=False)
    deployment_days = Column(Integer, default=0)
    duty_hours_per_week = Column(Float, nullable=False)
    night_shifts_per_month = Column(Integer, default=0)
    consecutive_duty_days = Column(Integer, default=0)
    transfer_frequency = Column(Integer, default=0)
    training_load = Column(Integer, default=2)
    leave_gap_days = Column(Integer, default=30)
    remote_posting = Column(String(8), default="No")
    operational_exposure = Column(String(16), default="Medium")
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    user = relationship("User", back_populates="personnel", uselist=False)
    assessments = relationship("StressAssessment", back_populates="personnel", cascade="all, delete-orphan")
    recommendations = relationship("WelfareRecommendation", back_populates="personnel", cascade="all, delete-orphan")
    welfare_requests = relationship("WelfareRequest", back_populates="personnel", cascade="all, delete-orphan")
    hrms_record = relationship("HrmsServiceRecord", back_populates="personnel", uselist=False, cascade="all, delete-orphan")
    wearable_telemetry = relationship("WearableTelemetry", back_populates="personnel", cascade="all, delete-orphan")
    followups = relationship("WelfareFollowup", back_populates="personnel", cascade="all, delete-orphan")
    cases = relationship("WelfareCase", back_populates="personnel", cascade="all, delete-orphan")
    notifications = relationship("WelfareNotification", back_populates="recipient", cascade="all, delete-orphan")


