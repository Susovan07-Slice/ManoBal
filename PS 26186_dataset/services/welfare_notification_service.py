import re
import html
import json
from datetime import datetime, timezone
from typing import Optional, List, Dict, Any, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import desc, func

from core.config import logger
from db.models.user import User
from db.models.personnel import Personnel
from db.models.welfare_notification import WelfareNotification, WelfareNotificationAudit
from schemas.notification import (
    WelfareNotificationOut,
    CommanderNotificationSendRequest,
    NotificationListResponse,
    UnreadCountResponse,
    VALID_NOTIFICATION_TYPES,
    VALID_PRIORITIES,
)

# Forbidden internal technical analytical terms that must never leak to Jawan-facing messages
INTERNAL_JARGON_PATTERNS = [
    r"isolation\s*forest",
    r"anomaly\s*score",
    r"risk\s*score\s*is",
    r"shap\s*value",
    r"tree\s*shap",
    r"lightgbm",
    r"calibratedclassifier",
    r"high-risk\s*individual",
    r"disciplinary",
    r"punitive",
    r"\d+\.\d+σ",
]

class WelfareNotificationService:
    """
    Phase 47: Authoritative Welfare Notification & Signal Delivery Service.
    Connects Commander/Welfare Officer workflows to the Jawan application.
    """

    @classmethod
    def sanitize_and_validate_content(cls, title: str, message: str) -> Tuple[str, str]:
        """
        Ensures supportive, non-punitive language and strips harmful scripts or internal ML jargon.
        Strips HTML tags and normalizes characters without double-escaping entities.
        """
        clean_title = re.sub(r'<[^>]*>', '', title.strip())
        clean_msg = re.sub(r'<[^>]*>', '', message.strip())
        
        # Normalize and unescape any pre-escaped entities
        clean_title = html.unescape(clean_title)
        clean_msg = html.unescape(clean_msg)

        # Check for forbidden internal machine learning jargon
        for pattern in INTERNAL_JARGON_PATTERNS:
            if re.search(pattern, clean_title, re.IGNORECASE) or re.search(pattern, clean_msg, re.IGNORECASE):
                logger.warning(f"Sanitizing sensitive ML/disciplinary jargon matching '{pattern}' from notification.")
                clean_title = re.sub(pattern, "Support review", clean_title, flags=re.IGNORECASE)
                clean_msg = re.sub(pattern, "Support review requested", clean_msg, flags=re.IGNORECASE)

        return clean_title, clean_msg

    @classmethod
    def create_notification(
        cls,
        db: Session,
        recipient_personnel_id: int,
        title: str,
        message: str,
        notification_type: str = "WELFARE_SUPPORT",
        priority: str = "STANDARD",
        source_type: Optional[str] = None,
        source_id: Optional[int] = None,
        action_url: Optional[str] = None,
        created_by: Optional[int] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> WelfareNotification:
        """
        Creates and persists a welfare notification with audit logging.
        """
        # Verify personnel exists
        personnel = db.query(Personnel).filter(Personnel.id == recipient_personnel_id).first()
        if not personnel:
            raise LookupError(f"Recipient personnel #{recipient_personnel_id} not found.")

        # Validate type
        norm_type = (notification_type or "WELFARE_SUPPORT").strip().upper()
        if norm_type not in VALID_NOTIFICATION_TYPES:
            norm_type = "WELFARE_SUPPORT"

        # Validate priority
        norm_priority = (priority or "STANDARD").strip().upper()
        if norm_priority not in VALID_PRIORITIES:
            norm_priority = "STANDARD"

        clean_title, clean_msg = cls.sanitize_and_validate_content(title, message)

        notif = WelfareNotification(
            recipient_personnel_id=recipient_personnel_id,
            notification_type=norm_type,
            title=clean_title,
            message=clean_msg,
            priority=norm_priority,
            source_type=source_type,
            source_id=source_id,
            action_url=action_url,
            status="UNREAD",
            created_at=datetime.now(timezone.utc),
            created_by=created_by,
            metadata_json=json.dumps(metadata) if metadata else None,
        )
        db.add(notif)
        db.flush()

        # Audit creation
        audit = WelfareNotificationAudit(
            notification_id=notif.id,
            action="NOTIFICATION_CREATED",
            actor_id=created_by,
            previous_status=None,
            new_status="UNREAD",
            timestamp=datetime.now(timezone.utc),
            metadata_json=json.dumps({
                "recipient_personnel_id": recipient_personnel_id,
                "notification_type": norm_type,
                "priority": norm_priority,
                "source_type": source_type,
                "source_id": source_id,
            }),
        )
        db.add(audit)
        db.commit()
        db.refresh(notif)

        logger.info(
            f"Welfare notification #{notif.id} created for Personnel #{recipient_personnel_id} "
            f"[{norm_type}] by Actor #{created_by or 'SYSTEM'}"
        )
        return notif

    @classmethod
    def serialize_notification(cls, notif: WelfareNotification, db: Session) -> WelfareNotificationOut:
        p_code = None
        p_name = None
        if notif.recipient:
            p_code = notif.recipient.personnel_code
            p_name = notif.recipient.name
        else:
            p = db.query(Personnel).filter(Personnel.id == notif.recipient_personnel_id).first()
            if p:
                p_code = p.personnel_code
                p_name = p.name

        creator_name = None
        if notif.creator:
            creator_name = notif.creator.username
        elif notif.created_by:
            u = db.query(User).filter(User.id == notif.created_by).first()
            if u:
                creator_name = u.username

        return WelfareNotificationOut(
            id=notif.id,
            recipient_personnel_id=notif.recipient_personnel_id,
            recipient_personnel_code=p_code,
            recipient_name=p_name,
            notification_type=notif.notification_type,
            title=notif.title,
            message=notif.message,
            source_type=notif.source_type,
            source_id=notif.source_id,
            priority=notif.priority,
            action_url=notif.action_url,
            status=notif.status,
            created_at=notif.created_at,
            read_at=notif.read_at,
            acknowledged_at=notif.acknowledged_at,
            created_by=notif.created_by,
            creator_username=creator_name,
        )

    @classmethod
    def get_notifications_for_user(
        cls,
        db: Session,
        current_user: User,
        status_filter: Optional[str] = None,
        target_personnel_id: Optional[int] = None,
        limit: int = 50,
        offset: int = 0,
    ) -> NotificationListResponse:
        """
        Retrieves notifications with strict Anti-IDOR and scope boundaries.
        - Personnel: strictly restricted to their own linked personnel_id.
        - Officer / Welfare: restricted to their battalion/location scope.
        - Admin: unrestricted.
        """
        query = db.query(WelfareNotification)

        if current_user.role == "personnel":
            if not current_user.personnel_id:
                return NotificationListResponse(total=0, unread_count=0, notifications=[])
            query = query.filter(WelfareNotification.recipient_personnel_id == current_user.personnel_id)
            effective_personnel_id = current_user.personnel_id
        elif current_user.role in ["officer", "welfare"]:
            query = query.join(Personnel, WelfareNotification.recipient_personnel_id == Personnel.id)
            user_bat = (current_user.battalion or "").strip().lower()
            user_loc = (current_user.location or "").strip().lower()
            if user_bat:
                query = query.filter(func.lower(Personnel.battalion) == user_bat)
            if user_loc:
                query = query.filter(func.lower(Personnel.location) == user_loc)

            if target_personnel_id is not None:
                query = query.filter(WelfareNotification.recipient_personnel_id == target_personnel_id)
            effective_personnel_id = target_personnel_id
        else: # admin
            if target_personnel_id is not None:
                query = query.filter(WelfareNotification.recipient_personnel_id == target_personnel_id)
            effective_personnel_id = target_personnel_id

        # Total unread count for target recipient
        unread_q = db.query(WelfareNotification).filter(WelfareNotification.status == "UNREAD")
        if current_user.role == "personnel":
            unread_q = unread_q.filter(WelfareNotification.recipient_personnel_id == current_user.personnel_id)
        elif effective_personnel_id is not None:
            unread_q = unread_q.filter(WelfareNotification.recipient_personnel_id == effective_personnel_id)
        elif current_user.role in ["officer", "welfare"]:
            unread_q = unread_q.join(Personnel, WelfareNotification.recipient_personnel_id == Personnel.id)
            user_bat = (current_user.battalion or "").strip().lower()
            if user_bat:
                unread_q = unread_q.filter(func.lower(Personnel.battalion) == user_bat)

        unread_count = unread_q.count()

        if status_filter:
            clean_status = status_filter.strip().upper()
            if clean_status in {"UNREAD", "READ", "ACKNOWLEDGED", "DISMISSED"}:
                query = query.filter(WelfareNotification.status == clean_status)

        total = query.count()
        records = (
            query.order_by(desc(WelfareNotification.created_at), desc(WelfareNotification.id))
            .offset(offset)
            .limit(limit)
            .all()
        )

        serialized = [cls.serialize_notification(r, db) for r in records]
        return NotificationListResponse(
            total=total,
            unread_count=unread_count,
            notifications=serialized,
        )

    @classmethod
    def get_unread_count_for_user(cls, db: Session, current_user: User) -> int:
        """
        Returns unread count for authenticated user.
        """
        if current_user.role == "personnel":
            if not current_user.personnel_id:
                return 0
            return (
                db.query(WelfareNotification)
                .filter(
                    WelfareNotification.recipient_personnel_id == current_user.personnel_id,
                    WelfareNotification.status == "UNREAD"
                )
                .count()
            )
        elif current_user.role in ["officer", "welfare"]:
            query = db.query(WelfareNotification).join(Personnel, WelfareNotification.recipient_personnel_id == Personnel.id)
            user_bat = (current_user.battalion or "").strip().lower()
            if user_bat:
                query = query.filter(func.lower(Personnel.battalion) == user_bat)
            return query.filter(WelfareNotification.status == "UNREAD").count()
        else: # admin
            return db.query(WelfareNotification).filter(WelfareNotification.status == "UNREAD").count()

    @classmethod
    def get_notification_with_security_check(
        cls, db: Session, notification_id: int, current_user: User
    ) -> WelfareNotification:
        """
        Anti-IDOR validation: Ensures a Jawan can NEVER access another Jawan's notification.
        """
        notif = db.query(WelfareNotification).filter(WelfareNotification.id == notification_id).first()
        if not notif:
            raise LookupError("Notification not found.")

        if current_user.role == "personnel":
            if notif.recipient_personnel_id != current_user.personnel_id:
                logger.warning(
                    f"Anti-IDOR Violation: Personnel '{current_user.username}' (ID {current_user.personnel_id}) "
                    f"attempted to view notification #{notification_id} belonging to Personnel #{notif.recipient_personnel_id}."
                )
                raise PermissionError("Access denied: You are not authorized to view this notification.")
        elif current_user.role in ["officer", "welfare"]:
            personnel = db.query(Personnel).filter(Personnel.id == notif.recipient_personnel_id).first()
            if personnel:
                user_bat = (current_user.battalion or "").strip().lower()
                p_bat = (personnel.battalion or "").strip().lower()
                if user_bat and p_bat and user_bat != p_bat:
                    raise PermissionError("Access denied: Recipient personnel is outside your assigned Battalion scope.")

        return notif

    @classmethod
    def mark_as_read(cls, db: Session, notification_id: int, current_user: User) -> WelfareNotification:
        """
        Marks notification as READ with audit trail.
        """
        notif = cls.get_notification_with_security_check(db, notification_id, current_user)
        if notif.status == "UNREAD":
            prev_status = notif.status
            notif.status = "READ"
            notif.read_at = datetime.now(timezone.utc)

            audit = WelfareNotificationAudit(
                notification_id=notif.id,
                action="NOTIFICATION_READ",
                actor_id=current_user.id,
                previous_status=prev_status,
                new_status="READ",
                timestamp=datetime.now(timezone.utc),
            )
            db.add(audit)
            db.commit()
            db.refresh(notif)
        return notif

    @classmethod
    def mark_all_as_read(cls, db: Session, current_user: User) -> int:
        """
        Marks all unread notifications as read for current personnel.
        """
        if current_user.role != "personnel" or not current_user.personnel_id:
            return 0

        unreads = (
            db.query(WelfareNotification)
            .filter(
                WelfareNotification.recipient_personnel_id == current_user.personnel_id,
                WelfareNotification.status == "UNREAD"
            )
            .all()
        )

        now = datetime.now(timezone.utc)
        for n in unreads:
            n.status = "READ"
            n.read_at = now
            audit = WelfareNotificationAudit(
                notification_id=n.id,
                action="NOTIFICATION_READ",
                actor_id=current_user.id,
                previous_status="UNREAD",
                new_status="READ",
                timestamp=now,
            )
            db.add(audit)

        db.commit()
        return len(unreads)

    # =========================================================================
    # AUTOMATIC WORKFLOW HOOKS (Triggered by Authoritative State Transitions)
    # =========================================================================

    @classmethod
    def notify_on_recommendation_accepted(
        cls, db: Session, recommendation: Any, actor_user: User
    ) -> Optional[WelfareNotification]:
        """
        Phase 40 Hook: Creates supportive notification when an authorized reviewer accepts a recommendation.
        """
        if not recommendation or not recommendation.personnel_id:
            return None

        title = "Support Recommendation Available"
        rec_title = recommendation.title or "Welfare Guidance"
        message = (
            f"Your welfare officer has approved support guidance regarding '{rec_title}'. "
            "Please check your welfare resources and follow suggested wellness practices."
        )

        action_url = "/trends"
        return cls.create_notification(
            db=db,
            recipient_personnel_id=recommendation.personnel_id,
            title=title,
            message=message,
            notification_type="SUPPORT_RECOMMENDATION",
            priority="STANDARD",
            source_type="RECOMMENDATION",
            source_id=recommendation.id,
            action_url=action_url,
            created_by=actor_user.id,
        )

    @classmethod
    def notify_on_followup_scheduled(
        cls, db: Session, followup: Any, actor_user: User
    ) -> Optional[WelfareNotification]:
        """
        Phase 41 Hook: Creates follow-up request notification when a review date is scheduled.
        """
        if not followup or not followup.personnel_id:
            return None

        date_str = ""
        if followup.scheduled_at:
            try:
                date_str = f" on {followup.scheduled_at.strftime('%d %b %Y')}"
            except Exception:
                pass

        title = "Welfare Follow-up Scheduled"
        message = (
            f"A welfare follow-up check-in has been scheduled{date_str}. "
            "Your well-being is our priority. Please review your portal to complete the check-in."
        )

        return cls.create_notification(
            db=db,
            recipient_personnel_id=followup.personnel_id,
            title=title,
            message=message,
            notification_type="FOLLOW_UP_REQUEST",
            priority="PRIORITY",
            source_type="FOLLOWUP",
            source_id=followup.id,
            action_url="/check-in",
            created_by=actor_user.id,
        )

    @classmethod
    def notify_on_followup_reminder(
        cls, db: Session, followup: Any, actor_user: User
    ) -> Optional[WelfareNotification]:
        """
        Phase 41 Hook: Creates follow-up reminder notification.
        """
        if not followup or not followup.personnel_id:
            return None

        title = "Follow-up Reminder"
        message = (
            "Friendly reminder: You have a pending welfare follow-up review. "
            "Please take a few moments to complete your check-in."
        )

        return cls.create_notification(
            db=db,
            recipient_personnel_id=followup.personnel_id,
            title=title,
            message=message,
            notification_type="FOLLOW_UP_REMINDER",
            priority="STANDARD",
            source_type="FOLLOWUP",
            source_id=followup.id,
            action_url="/check-in",
            created_by=actor_user.id,
        )

    @classmethod
    def notify_on_case_update(
        cls, db: Session, case: Any, actor_user: User, custom_message: Optional[str] = None
    ) -> Optional[WelfareNotification]:
        """
        Phase 43 Hook: Creates supportive notification when an authorized case update occurs.
        """
        if not case or not case.personnel_id:
            return None

        title = "Welfare Support Update"
        message = (
            custom_message or
            "An update has been logged regarding your welfare support program. "
            "Your unit welfare team is actively monitoring and assisting your recovery."
        )

        return cls.create_notification(
            db=db,
            recipient_personnel_id=case.personnel_id,
            title=title,
            message=message,
            notification_type="CASE_UPDATE",
            priority="STANDARD",
            source_type="CASE",
            source_id=case.id,
            action_url="/check-in",
            created_by=actor_user.id,
        )

    @classmethod
    def notify_on_welfare_request_update(
        cls, db: Session, request: Any, actor_user: User
    ) -> Optional[WelfareNotification]:
        """
        Creates notification when a Jawan's welfare assistance request changes status.
        """
        if not request or not request.personnel_id:
            return None

        status_label = (request.status or "").replace("_", " ").title()
        title = f"Welfare Request {status_label}"
        message = (
            f"Your welfare request (#{request.id}) status has been updated to '{status_label}' "
            "by the authorized unit welfare officer."
        )

        return cls.create_notification(
            db=db,
            recipient_personnel_id=request.personnel_id,
            title=title,
            message=message,
            notification_type="WELFARE_SUPPORT",
            priority="STANDARD",
            source_type="WELFARE_REQUEST",
            source_id=request.id,
            action_url="/",
            created_by=actor_user.id,
        )
