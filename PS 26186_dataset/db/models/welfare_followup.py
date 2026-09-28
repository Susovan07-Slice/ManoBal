from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, Index
from sqlalchemy.orm import relationship
from db.base import Base

class WelfareFollowup(Base):
    """
    Phase 41: Welfare Follow-Up, Outcome Tracking & Support Effectiveness.
    Closed-loop monitoring layer after Phase 40 recommendations and Phase 37 interventions.
    Tracks follow-up requirements, lifecycle states, and objective observational outcomes.
    
    CRITICAL ARCHITECTURAL CONSTRAINTS:
      - Does NOT generate a new risk score or effectiveness score.
      - Does NOT make automated medical diagnoses, treatment claims, or fitness-for-duty decisions.
      - Preserves chronological integrity (baseline < intervention/recommendation < follow-up).
      - Retains complete timeline history without overwriting historical records.
    """
    __tablename__ = "welfare_followups"

    id = Column(Integer, primary_key=True, index=True)
    personnel_id = Column(Integer, ForeignKey("personnel.id", ondelete="CASCADE"), nullable=False, index=True)
    recommendation_id = Column(Integer, ForeignKey("welfare_recommendations.id", ondelete="SET NULL"), nullable=True, index=True)
    intervention_id = Column(Integer, ForeignKey("welfare_interventions.id", ondelete="SET NULL"), nullable=True, index=True)
    alert_id = Column(Integer, ForeignKey("welfare_alerts.id", ondelete="SET NULL"), nullable=True, index=True)

    # Follow-Up Types:
    # WELFARE_CHECKIN, RECOVERY_REVIEW, DUTY_SCHEDULE_REVIEW, SUPPORT_RESOURCE_FOLLOWUP, REASSESSMENT, INTERVENTION_REVIEW
    followup_type = Column(String(64), nullable=False, index=True)

    # Lifecycle Status:
    # PENDING, SCHEDULED, COMPLETED, DEFERRED, DECLINED, CANCELLED, EXPIRED
    status = Column(String(32), nullable=False, default="PENDING", index=True)

    scheduled_at = Column(DateTime(timezone=True), nullable=True)
    review_window = Column(String(64), nullable=True, default="NOT_SPECIFIED")
    due_date = Column(DateTime(timezone=True), nullable=True)
    completed_at = Column(DateTime(timezone=True), nullable=True)
    created_by = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    completed_by = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    notes = Column(Text, nullable=True)

    # Observational Outcome Status:
    # IMPROVED, STABLE, PERSISTENT_CONCERN, WORSENING, INSUFFICIENT_DATA
    outcome_status = Column(String(32), nullable=False, default="INSUFFICIENT_DATA", index=True)

    # Baseline & Subsequent Assessment References
    baseline_source = Column(String(64), nullable=True)  # e.g., PRE_INTERVENTION_ASSESSMENT, PRE_RECOMMENDATION_ASSESSMENT, HISTORICAL_BASELINE
    baseline_assessment_id = Column(Integer, ForeignKey("stress_assessments.id", ondelete="SET NULL"), nullable=True)
    followup_assessment_id = Column(Integer, ForeignKey("stress_assessments.id", ondelete="SET NULL"), nullable=True)

    # Explainable Evidence JSON (stores delta, scores, explanation, data sufficiency)
    evidence_json = Column(Text, nullable=True)

    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), index=True)
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    personnel = relationship("Personnel", back_populates="followups")
    recommendation = relationship("WelfareRecommendation", back_populates="followups")
    intervention = relationship("WelfareIntervention")
    alert = relationship("WelfareAlert")
    baseline_assessment = relationship("StressAssessment", foreign_keys=[baseline_assessment_id])
    followup_assessment = relationship("StressAssessment", foreign_keys=[followup_assessment_id])
    created_user = relationship("User", foreign_keys=[created_by])
    completed_user = relationship("User", foreign_keys=[completed_by])
    audits = relationship("WelfareFollowupAudit", back_populates="followup", cascade="all, delete-orphan")

    __table_args__ = (
        Index("ix_welfare_followups_personnel_status", "personnel_id", "status"),
        Index("ix_welfare_followups_personnel_type", "personnel_id", "followup_type"),
    )


class WelfareFollowupAudit(Base):
    """
    Audit log for Welfare Follow-Up lifecycle transitions and outcome observations.
    Ensures complete traceability without recording unnecessary sensitive details.
    """
    __tablename__ = "welfare_followup_audits"

    id = Column(Integer, primary_key=True, index=True)
    followup_id = Column(Integer, ForeignKey("welfare_followups.id", ondelete="CASCADE"), nullable=False, index=True)
    action = Column(String(64), nullable=False) # FOLLOWUP_CREATED, FOLLOWUP_SCHEDULED, FOLLOWUP_DEFERRED, FOLLOWUP_COMPLETED, etc.
    actor_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    previous_status = Column(String(32), nullable=True)
    new_status = Column(String(32), nullable=True)
    timestamp = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    metadata_json = Column(Text, nullable=True)

    followup = relationship("WelfareFollowup", back_populates="audits")
    actor = relationship("User", foreign_keys=[actor_id])
