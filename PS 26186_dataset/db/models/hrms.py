from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from db.base import Base

class HrmsServiceRecord(Base):
    """
    Dedicated HRMS Service Record entity representing structured personnel service history.
    Explicitly marked with source="mock_hrms" to maintain synthetic-data disclosures.
    """
    __tablename__ = "hrms_service_records"

    id = Column(Integer, primary_key=True, index=True)
    personnel_id = Column(Integer, ForeignKey("personnel.id", ondelete="CASCADE"), nullable=False, unique=True, index=True)
    service_number = Column(String(64), nullable=True, index=True)
    department = Column(String(64), nullable=True)
    battalion = Column(String(64), nullable=True, index=True)
    location = Column(String(64), nullable=True, index=True)
    job_role = Column(String(64), nullable=True)
    rank = Column(String(64), nullable=True)
    deployment_days = Column(Integer, default=0, nullable=True)
    duty_hours_per_week = Column(Float, nullable=True)
    night_shifts_per_month = Column(Integer, default=0, nullable=True)
    consecutive_duty_days = Column(Integer, default=0, nullable=True)
    leave_gap_days = Column(Integer, default=30, nullable=True)
    annual_leaves_taken = Column(Integer, default=0, nullable=True)
    transfer_frequency = Column(Integer, default=0, nullable=True)
    training_load = Column(Integer, default=2, nullable=True)
    experience_years = Column(Float, nullable=True)
    source = Column(String(32), default="mock_hrms", nullable=False)
    raw_metadata = Column(String(512), nullable=True)
    synced_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc), nullable=False)

    personnel = relationship("Personnel", back_populates="hrms_record")
