from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, Text, Index
from sqlalchemy.orm import relationship
from db.base import Base

class WelfareAnomaly(Base):
    """
    Phase 39: Welfare Anomaly & Early-Warning Record.
    Stores personalized and unit-level early-warning signals for human welfare review.
    Does NOT replace or modify Phase 34 risk scores or categories.
    """
    __tablename__ = "welfare_anomalies"

    id = Column(Integer, primary_key=True, index=True)
    personnel_id = Column(Integer, ForeignKey("personnel.id", ondelete="CASCADE"), nullable=True, index=True)
    scope_type = Column(String(16), nullable=False, default="INDIVIDUAL")  # INDIVIDUAL, UNIT
    scope_battalion = Column(String(64), nullable=True, index=True)
    scope_location = Column(String(64), nullable=True, index=True)
    
    # Anomaly Categories:
    # RAPID_RISK_CHANGE, RAPID_RISK_ACCELERATION, WORKLOAD_ANOMALY,
    # SLEEP_RECOVERY_ANOMALY, NIGHT_SHIFT_PATTERN_CHANGE, WELFARE_FACTOR_CLUSTER, UNIT_LEVEL_ANOMALY
    anomaly_type = Column(String(32), nullable=False, index=True)
    
    # Severity strictly for human review prioritization: INFO, WATCH, ATTENTION, URGENT_REVIEW
    severity = Column(String(16), nullable=False, default="ATTENTION")
    
    # Human Review Lifecycle: DETECTED, ACKNOWLEDGED, UNDER_REVIEW, RESOLVED, DISMISSED
    status = Column(String(24), nullable=False, default="DETECTED")
    
    # Confidence: HIGH, MEDIUM, LOW (represents evidence & baseline sufficiency)
    confidence = Column(String(16), nullable=False, default="MEDIUM")
    
    baseline_sample_count = Column(Integer, nullable=False, default=0)
    detected_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), index=True)
    observation_window_start = Column(DateTime(timezone=True), nullable=True)
    observation_window_end = Column(DateTime(timezone=True), nullable=True)
    
    # Explainable evidence JSON: baseline_mean, baseline_std, current_value, delta, explanation
    evidence_json = Column(Text, nullable=False)
    
    # Deterministic deduplication hash to prevent duplicate entries
    dedup_hash = Column(String(128), nullable=False, index=True)

    # Review tracking
    acknowledged_at = Column(DateTime(timezone=True), nullable=True)
    acknowledged_by = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)

    # Phase 48: Human Review Workspace tracking
    review_decision = Column(String(32), nullable=True)
    review_notes = Column(Text, nullable=True)
    reviewed_at = Column(DateTime(timezone=True), nullable=True)
    reviewed_by = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)

    resolved_at = Column(DateTime(timezone=True), nullable=True)
    resolved_by = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    resolution_notes = Column(Text, nullable=True)

    # Optional cross-reference to Phase 37 WelfareAlert
    associated_alert_id = Column(Integer, ForeignKey("welfare_alerts.id", ondelete="SET NULL"), nullable=True, index=True)

    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    personnel = relationship("Personnel", backref="welfare_anomalies")
    associated_alert = relationship("WelfareAlert")
    acknowledged_user = relationship("User", foreign_keys=[acknowledged_by])
    reviewed_user = relationship("User", foreign_keys=[reviewed_by])
    resolved_user = relationship("User", foreign_keys=[resolved_by])

    __table_args__ = (
        Index("ix_welfare_anomalies_scope_type_status", "scope_type", "status"),
        Index("ix_welfare_anomalies_personnel_type_status", "personnel_id", "anomaly_type", "status"),
    )


class WelfareAnomalyAudit(Base):
    """
    Phase 48: Immutable audit trail for early-warning anomaly lifecycle events.
    Records review decisions, resolution notes, and personnel notifications.
    """
    __tablename__ = "welfare_anomaly_audits"

    id = Column(Integer, primary_key=True, index=True)
    anomaly_id = Column(Integer, ForeignKey("welfare_anomalies.id", ondelete="CASCADE"), nullable=False, index=True)
    action = Column(String(32), nullable=False) # ANOMALY_ACKNOWLEDGED, ANOMALY_REVIEWED, ANOMALY_RESOLVED, ANOMALY_DISMISSED
    actor_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    previous_status = Column(String(24), nullable=True)
    new_status = Column(String(24), nullable=True)
    timestamp = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), index=True)
    details = Column(Text, nullable=True) # stringified JSON or observations

    anomaly = relationship("WelfareAnomaly", backref="audits")
    actor = relationship("User")

