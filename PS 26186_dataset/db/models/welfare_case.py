from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, Index
from sqlalchemy.orm import relationship
from db.base import Base

class WelfareCase(Base):
    """
    Phase 43: Welfare Case Management & Human Review Workspace.
    Workflow layer that converts existing welfare signals (Phases 34–42)
    into a structured, traceable human-review workflow.

    CRITICAL ARCHITECTURAL CONSTRAINTS:
      - Does NOT calculate a new risk score, priority score, or composite index.
      - Does NOT automatically reassign duties or make disciplinary determinations.
      - Does NOT automatically close cases.
      - Strictly preserves small-group k-anonymity privacy (k >= 5) on aggregates.
      - Enforces strict RBAC and Anti-IDOR boundaries.
    """
    __tablename__ = "welfare_cases"

    id = Column(Integer, primary_key=True, index=True)
    personnel_id = Column(Integer, ForeignKey("personnel.id", ondelete="CASCADE"), nullable=False, index=True)
    case_reference = Column(String(32), unique=True, index=True, nullable=False)
    title = Column(String(256), nullable=False)

    # Case Types:
    # CURRENT_RISK_REVIEW, WORSENING_TREND, ACTIVE_ALERT, ANOMALY_REVIEW, SUPPORT_FOLLOW_UP, REPEATED_WELFARE_CONCERN, OTHER
    case_type = Column(String(64), nullable=False, default="CURRENT_RISK_REVIEW", index=True)

    # Lifecycle Status:
    # OPEN, UNDER_REVIEW, SUPPORT_IN_PROGRESS, AWAITING_FOLLOW_UP, MONITORING, RESOLVED, CLOSED
    status = Column(String(32), nullable=False, default="OPEN", index=True)

    # Trigger Source:
    # PHASE_34_RISK, PHASE_36_TREND, PHASE_37_ALERT, PHASE_39_ANOMALY, PHASE_40_RECOMMENDATION, PHASE_41_FOLLOWUP, PHASE_42_INTELLIGENCE, MANUAL_REVIEW
    trigger_source = Column(String(64), nullable=False, default="MANUAL_REVIEW")

    # Linked Existing Authoritative Entities (Foreign Keys)
    assessment_id = Column(Integer, ForeignKey("stress_assessments.id", ondelete="SET NULL"), nullable=True, index=True)
    alert_id = Column(Integer, ForeignKey("welfare_alerts.id", ondelete="SET NULL"), nullable=True, index=True)
    anomaly_id = Column(Integer, ForeignKey("welfare_anomalies.id", ondelete="SET NULL"), nullable=True, index=True)
    recommendation_id = Column(Integer, ForeignKey("welfare_recommendations.id", ondelete="SET NULL"), nullable=True, index=True)
    intervention_id = Column(Integer, ForeignKey("welfare_interventions.id", ondelete="SET NULL"), nullable=True, index=True)
    followup_id = Column(Integer, ForeignKey("welfare_followups.id", ondelete="SET NULL"), nullable=True, index=True)

    # Human Actor & Lifecycle Tracking
    opened_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    opened_by = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)

    last_reviewed_at = Column(DateTime(timezone=True), nullable=True)
    last_reviewed_by = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)

    closed_at = Column(DateTime(timezone=True), nullable=True)
    closed_by = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    closure_reason = Column(String(64), nullable=True)  # RESOLVED, MONITORING_COMPLETED, SUPPORT_COMPLETED, NO_FURTHER_ACTION_REQUIRED, TRANSFERRED, DUPLICATE, OTHER
    closure_notes = Column(Text, nullable=True)

    reopened_at = Column(DateTime(timezone=True), nullable=True)
    reopened_by = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    reopen_reason = Column(Text, nullable=True)

    summary = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), index=True)
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    # Relationships
    personnel = relationship("Personnel", back_populates="cases")
    assessment = relationship("StressAssessment")
    alert = relationship("WelfareAlert")
    anomaly = relationship("WelfareAnomaly")
    recommendation = relationship("WelfareRecommendation")
    intervention = relationship("WelfareIntervention")
    followup = relationship("WelfareFollowup")

    opener = relationship("User", foreign_keys=[opened_by])
    last_reviewer = relationship("User", foreign_keys=[last_reviewed_by])
    closer = relationship("User", foreign_keys=[closed_by])
    reopener = relationship("User", foreign_keys=[reopened_by])

    reviews = relationship("WelfareCaseReview", back_populates="case", cascade="all, delete-orphan", order_by="desc(WelfareCaseReview.reviewed_at)")
    notes = relationship("WelfareCaseNote", back_populates="case", cascade="all, delete-orphan", order_by="desc(WelfareCaseNote.created_at)")
    audits = relationship("WelfareCaseAudit", back_populates="case", cascade="all, delete-orphan", order_by="desc(WelfareCaseAudit.timestamp)")

    __table_args__ = (
        Index("ix_welfare_cases_personnel_status", "personnel_id", "status"),
        Index("ix_welfare_cases_status_updated", "status", "updated_at"),
    )


class WelfareCaseReview(Base):
    """
    Phase 43: Structured Human Review Record.
    Captures human reviewer observations, decisions, next steps, and review windows.
    Never labeled as medical diagnoses or disciplinary determinations.
    """
    __tablename__ = "welfare_case_reviews"

    id = Column(Integer, primary_key=True, index=True)
    case_id = Column(Integer, ForeignKey("welfare_cases.id", ondelete="CASCADE"), nullable=False, index=True)
    reviewer_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)
    reviewed_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)

    # Review Types:
    # INITIAL_TRIAGE, PROGRESS_EVALUATION, INTERVENTION_REVIEW, FOLLOWUP_ASSESSMENT, CLOSURE_REVIEW, ROUTINE_MONITORING
    review_type = Column(String(64), nullable=False, default="INITIAL_TRIAGE")

    observations = Column(Text, nullable=False)

    # Decisions:
    # CONTINUE_MONITORING, CONTACT_PERSONNEL, REVIEW_DUTY_SUPPORT, OFFER_SUPPORT_RESOURCE, SCHEDULE_FOLLOW_UP, CONTINUE_EXISTING_INTERVENTION, CLOSE_CASE, REFER_TO_AUTHORIZED_SUPPORT, OTHER
    decision = Column(String(64), nullable=False)

    next_step = Column(Text, nullable=True)
    review_window = Column(String(64), nullable=True, default="Within 14 days")
    notes = Column(Text, nullable=True)

    case = relationship("WelfareCase", back_populates="reviews")
    reviewer = relationship("User", foreign_keys=[reviewer_id])


class WelfareCaseNote(Base):
    """
    Phase 43: Immutable Case Notes.
    Preserves audit history of human observations, support notes, and closure justifications.
    """
    __tablename__ = "welfare_case_notes"

    id = Column(Integer, primary_key=True, index=True)
    case_id = Column(Integer, ForeignKey("welfare_cases.id", ondelete="CASCADE"), nullable=False, index=True)
    author_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)

    # Note Types:
    # REVIEW_NOTE, SUPPORT_NOTE, FOLLOW_UP_NOTE, OUTCOME_NOTE, CLOSURE_NOTE, GENERAL_NOTE
    note_type = Column(String(64), nullable=False, default="GENERAL_NOTE")
    content = Column(Text, nullable=False)

    case = relationship("WelfareCase", back_populates="notes")
    author = relationship("User", foreign_keys=[author_id])


class WelfareCaseAudit(Base):
    """
    Phase 43: Append-Only Case Audit Trail.
    Tracks state transitions, reviews, note additions, closures, and reopenings.
    """
    __tablename__ = "welfare_case_audits"

    id = Column(Integer, primary_key=True, index=True)
    case_id = Column(Integer, ForeignKey("welfare_cases.id", ondelete="CASCADE"), nullable=False, index=True)
    action = Column(String(64), nullable=False)
    # CASE_CREATED, CASE_OPENED, CASE_REVIEWED, STATUS_CHANGED, NOTE_ADDED, RECOMMENDATION_LINKED, INTERVENTION_LINKED, FOLLOWUP_LINKED, CASE_REOPENED, CASE_CLOSED
    actor_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)
    previous_status = Column(String(32), nullable=True)
    new_status = Column(String(32), nullable=True)
    timestamp = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    metadata_json = Column(Text, nullable=True)

    case = relationship("WelfareCase", back_populates="audits")
    actor = relationship("User", foreign_keys=[actor_id])
