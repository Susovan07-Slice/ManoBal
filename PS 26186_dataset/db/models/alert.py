from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, Boolean
from sqlalchemy.orm import relationship
from datetime import datetime, timezone
from db.base import Base

class WelfareAlert(Base):
    __tablename__ = "welfare_alerts"

    id = Column(Integer, primary_key=True, index=True)
    personnel_id = Column(Integer, ForeignKey("personnel.id", ondelete="CASCADE"), nullable=False, index=True)
    alert_type = Column(String, nullable=False) # e.g., PERSISTENT_ELEVATED_RISK, WORSENING_TREND
    severity = Column(String, nullable=False) # e.g., INFO, ATTENTION, HIGH_PRIORITY, URGENT_REVIEW
    status = Column(String, nullable=False, default="OPEN") # OPEN, ACKNOWLEDGED, UNDER_REVIEW, INTERVENTION_PLANNED, FOLLOW_UP, RESOLVED, DISMISSED
    trigger_assessment_id = Column(Integer, ForeignKey("stress_assessments.id", ondelete="SET NULL"), nullable=True)
    trigger_reason = Column(String, nullable=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    
    acknowledged_at = Column(DateTime(timezone=True), nullable=True)
    acknowledged_by = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    
    resolved_at = Column(DateTime(timezone=True), nullable=True)
    resolved_by = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    resolution_reason = Column(String, nullable=True)

    personnel = relationship("Personnel", backref="welfare_alerts")
    trigger_assessment = relationship("StressAssessment")
    interventions = relationship("WelfareIntervention", back_populates="alert", cascade="all, delete-orphan")
    audits = relationship("WelfareAlertAudit", back_populates="alert", cascade="all, delete-orphan")


class WelfareIntervention(Base):
    __tablename__ = "welfare_interventions"

    id = Column(Integer, primary_key=True, index=True)
    alert_id = Column(Integer, ForeignKey("welfare_alerts.id", ondelete="CASCADE"), nullable=False, index=True)
    personnel_id = Column(Integer, ForeignKey("personnel.id", ondelete="CASCADE"), nullable=False, index=True)
    intervention_type = Column(String, nullable=False)
    status = Column(String, nullable=False, default="PLANNED") # PLANNED, COMPLETED, MISSED, CANCELLED
    created_by = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    planned_date = Column(DateTime(timezone=True), nullable=True)
    completed_at = Column(DateTime(timezone=True), nullable=True)
    follow_up_date = Column(DateTime(timezone=True), nullable=True)
    notes = Column(String, nullable=True)

    alert = relationship("WelfareAlert", back_populates="interventions")
    personnel = relationship("Personnel")


class WelfareAlertAudit(Base):
    __tablename__ = "welfare_alert_audits"

    id = Column(Integer, primary_key=True, index=True)
    alert_id = Column(Integer, ForeignKey("welfare_alerts.id", ondelete="CASCADE"), nullable=False, index=True)
    action = Column(String, nullable=False) # e.g., ALERT_CREATED, ALERT_ACKNOWLEDGED, REVIEW_STARTED, etc.
    actor_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    previous_status = Column(String, nullable=True)
    new_status = Column(String, nullable=True)
    timestamp = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    metadata_json = Column(String, nullable=True) # stringified JSON

    alert = relationship("WelfareAlert", back_populates="audits")
