from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, Index
from sqlalchemy.orm import relationship
from db.base import Base

class WelfareNotification(Base):
    """
    Phase 47: Jawan Welfare Notifications & Commander-to-Personnel Signal Delivery.
    Persistent data model for delivering authorized, supportive welfare communications
    from commanders, welfare officers, and authoritative lifecycle workflows to Jawans.

    CRITICAL ARCHITECTURAL CONSTRAINTS:
      - Does NOT expose internal commander-only ML risk scores, SHAP values, or anomaly scores.
      - Enforces strict Anti-IDOR and organizational scoping boundaries.
      - Uses non-stigmatizing, welfare/support oriented language.
      - Fully auditable lifecycle transitions (CREATED, READ, ACKNOWLEDGED, DISMISSED).
    """
    __tablename__ = "welfare_notifications"

    id = Column(Integer, primary_key=True, index=True)
    recipient_personnel_id = Column(Integer, ForeignKey("personnel.id", ondelete="CASCADE"), nullable=False, index=True)

    # Explicit notification types
    # WELFARE_SUPPORT, FOLLOW_UP_REQUEST, FOLLOW_UP_REMINDER, SUPPORT_RECOMMENDATION,
    # DUTY_SUPPORT_REVIEW, RECOVERY_SUPPORT, CASE_UPDATE, WELFARE_MESSAGE
    notification_type = Column(String(64), nullable=False, index=True, default="WELFARE_SUPPORT")

    title = Column(String(256), nullable=False)
    message = Column(Text, nullable=False)

    # Source linkage (e.g., RECOMMENDATION, FOLLOWUP, ALERT, CASE, COMMANDER_ACTION, WELFARE_REQUEST)
    source_type = Column(String(64), nullable=True)
    source_id = Column(Integer, nullable=True)

    # Priority: INFO, STANDARD, PRIORITY, URGENT
    priority = Column(String(16), nullable=False, default="STANDARD")

    # Deep link URL in Jawan application (e.g., '/assessment', '/check-in', '/trends')
    action_url = Column(String(256), nullable=True)

    # Lifecycle status: UNREAD, READ, ACKNOWLEDGED, DISMISSED
    status = Column(String(32), nullable=False, default="UNREAD", index=True)

    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), index=True)
    read_at = Column(DateTime(timezone=True), nullable=True)
    acknowledged_at = Column(DateTime(timezone=True), nullable=True)
    expires_at = Column(DateTime(timezone=True), nullable=True)

    # Actor who created/authorized the notification (Officer/Welfare user ID, or NULL for system lifecycle)
    created_by = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)

    # Contextual metadata (JSON)
    metadata_json = Column(Text, nullable=True)

    # Relationships
    recipient = relationship("Personnel", back_populates="notifications")
    creator = relationship("User", foreign_keys=[created_by])
    audits = relationship("WelfareNotificationAudit", back_populates="notification", cascade="all, delete-orphan")

    __table_args__ = (
        Index("ix_welfare_notifications_recipient_status", "recipient_personnel_id", "status"),
        Index("ix_welfare_notifications_created_at_desc", "created_at"),
    )


class WelfareNotificationAudit(Base):
    """
    Append-only audit trail for all welfare notification lifecycle events.
    Records creation, reads, acknowledgments, and delivery state changes.
    """
    __tablename__ = "welfare_notification_audits"

    id = Column(Integer, primary_key=True, index=True)
    notification_id = Column(Integer, ForeignKey("welfare_notifications.id", ondelete="CASCADE"), nullable=False, index=True)
    
    # Actions: NOTIFICATION_CREATED, NOTIFICATION_READ, NOTIFICATION_ACKNOWLEDGED, NOTIFICATION_DISMISSED
    action = Column(String(64), nullable=False)
    actor_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    
    previous_status = Column(String(32), nullable=True)
    new_status = Column(String(32), nullable=True)
    timestamp = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    metadata_json = Column(Text, nullable=True)

    notification = relationship("WelfareNotification", back_populates="audits")
    actor = relationship("User", foreign_keys=[actor_id])
