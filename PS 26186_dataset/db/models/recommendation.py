from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, Index
from sqlalchemy.orm import relationship
from db.base import Base

class WelfareRecommendation(Base):
    """
    Phase 40: Welfare Recommendation & Support Engine.
    Provides explainable, non-punitive support suggestions to authorized human reviewers.
    Does NOT modify Phase 34 risk scores or create automated disciplinary/personnel actions.
    """
    __tablename__ = "welfare_recommendations"

    id = Column(Integer, primary_key=True, index=True)
    personnel_id = Column(Integer, ForeignKey("personnel.id", ondelete="CASCADE"), nullable=False, index=True)
    assessment_id = Column(Integer, ForeignKey("stress_assessments.id", ondelete="CASCADE"), nullable=True, index=True)
    
    # Recommendation Types:
    # RECOVERY_REVIEW, DUTY_SCHEDULE_REVIEW, WELFARE_FOLLOW_UP, VOLUNTARY_WELLNESS_CHECKIN,
    # SUPPORT_RESOURCE_REFERRAL, FOLLOW_UP_ASSESSMENT, CONTINUE_MONITORING, HUMAN_REVIEW
    # (also preserves legacy: workload, sleep, leave, medical, duty)
    recommendation_type = Column(String(64), nullable=False, index=True)
    
    # Backward compatible text column; also serves as short action summary
    recommendation_text = Column(Text, nullable=False)
    
    # Extended Phase 40 fields
    title = Column(String(128), nullable=True)
    description = Column(Text, nullable=True)
    reason = Column(Text, nullable=True)
    evidence_json = Column(Text, nullable=True)
    source_signals_json = Column(Text, nullable=True)
    recommended_review_window = Column(String(64), nullable=True)
    
    # Priority for human review scheduling: URGENT, HIGH, MEDIUM, LOW (independent of risk score)
    # (also preserves legacy: Routine, Preventive, Priority)
    priority = Column(String(16), nullable=False, index=True)
    
    # Lifecycle: SUGGESTED, ACKNOWLEDGED, ACCEPTED, DEFERRED, DISMISSED, ACTIONED, EXPIRED, RESOLVED (and legacy: pending)
    status = Column(String(24), default="SUGGESTED", index=True)
    
    # Confidence / Data Sufficiency: HIGH, MEDIUM, LOW
    confidence = Column(String(16), nullable=False, default="MEDIUM")
    
    # Deterministic deduplication hash
    dedup_hash = Column(String(128), nullable=True, index=True)

    # Cross-references to upstream Phase 37/39 entities and downstream interventions
    linked_alert_id = Column(Integer, ForeignKey("welfare_alerts.id", ondelete="SET NULL"), nullable=True, index=True)
    linked_anomaly_id = Column(Integer, ForeignKey("welfare_anomalies.id", ondelete="SET NULL"), nullable=True, index=True)
    linked_intervention_id = Column(Integer, ForeignKey("welfare_interventions.id", ondelete="SET NULL"), nullable=True, index=True)

    # Human Review Lifecycle Audit
    acknowledged_at = Column(DateTime(timezone=True), nullable=True)
    acknowledged_by = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)

    actioned_at = Column(DateTime(timezone=True), nullable=True)
    actioned_by = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    action_notes = Column(Text, nullable=True)

    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), index=True)
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    personnel = relationship("Personnel", back_populates="recommendations")
    assessment = relationship("StressAssessment", back_populates="recommendations")
    linked_alert = relationship("WelfareAlert")
    linked_anomaly = relationship("WelfareAnomaly")
    linked_intervention = relationship("WelfareIntervention")
    acknowledged_user = relationship("User", foreign_keys=[acknowledged_by])
    actioned_user = relationship("User", foreign_keys=[actioned_by])
    followups = relationship("WelfareFollowup", back_populates="recommendation")


    __table_args__ = (
        Index("ix_welfare_recommendations_personnel_type_status", "personnel_id", "recommendation_type", "status"),
    )
