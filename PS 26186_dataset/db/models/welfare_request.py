from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from db.base import Base

class WelfareRequest(Base):
    __tablename__ = "welfare_requests"

    id = Column(Integer, primary_key=True, index=True)
    personnel_id = Column(Integer, ForeignKey("personnel.id", ondelete="CASCADE"), nullable=False, index=True)
    category = Column(String(64), nullable=False)  # Workload & Duty, Rest & Sleep, Personal & Family, Operational Stress, General Support, Emergency SOS
    message = Column(Text, nullable=True)
    urgency = Column(String(16), nullable=False, default="Routine", index=True)  # Routine, Medium, High
    status = Column(String(16), nullable=False, default="pending", index=True)  # pending, acknowledged, in_progress, resolved
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), index=True)
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
    resolved_at = Column(DateTime(timezone=True), nullable=True)

    personnel = relationship("Personnel", back_populates="welfare_requests")
