from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field, field_validator
import html

VALID_NOTIFICATION_TYPES = {
    "WELFARE_SUPPORT",
    "FOLLOW_UP_REQUEST",
    "FOLLOW_UP_REMINDER",
    "SUPPORT_RECOMMENDATION",
    "DUTY_SUPPORT_REVIEW",
    "RECOVERY_SUPPORT",
    "CASE_UPDATE",
    "WELFARE_MESSAGE",
}

VALID_PRIORITIES = {"INFO", "STANDARD", "PRIORITY", "URGENT"}

VALID_STATUSES = {"UNREAD", "READ", "ACKNOWLEDGED", "DISMISSED"}


class WelfareNotificationOut(BaseModel):
    id: int
    recipient_personnel_id: int
    recipient_personnel_code: Optional[str] = None
    recipient_name: Optional[str] = None
    notification_type: str
    title: str
    message: str
    source_type: Optional[str] = None
    source_id: Optional[int] = None
    priority: str
    action_url: Optional[str] = None
    status: str
    created_at: datetime
    read_at: Optional[datetime] = None
    acknowledged_at: Optional[datetime] = None
    created_by: Optional[int] = None
    creator_username: Optional[str] = None

    class Config:
        from_attributes = True


class CommanderNotificationSendRequest(BaseModel):
    recipient_personnel_id: int = Field(..., description="ID of recipient personnel in scope")
    notification_type: str = Field(default="WELFARE_SUPPORT", description="Type of support notification")
    title: str = Field(..., min_length=3, max_length=200, description="Supportive notification title")
    message: str = Field(..., min_length=5, max_length=1000, description="Supportive, non-stigmatizing message content")
    priority: Optional[str] = Field(default="STANDARD", description="Notification priority level")
    action_url: Optional[str] = Field(default=None, max_length=256, description="Optional relative action deep link")
    source_type: Optional[str] = Field(default="COMMANDER_ACTION", description="Workflow source type")
    source_id: Optional[int] = Field(default=None, description="Linked entity ID")

    @field_validator("notification_type")
    @classmethod
    def validate_type(cls, v: str) -> str:
        clean = (v or "").strip().upper()
        if clean not in VALID_NOTIFICATION_TYPES:
            raise ValueError(f"Invalid notification_type '{v}'. Allowed: {sorted(list(VALID_NOTIFICATION_TYPES))}")
        return clean

    @field_validator("priority")
    @classmethod
    def validate_priority(cls, v: Optional[str]) -> str:
        if not v:
            return "STANDARD"
        clean = v.strip().upper()
        if clean not in VALID_PRIORITIES:
            raise ValueError(f"Invalid priority '{v}'. Allowed: {sorted(list(VALID_PRIORITIES))}")
        return clean

    @field_validator("title", "message")
    @classmethod
    def sanitize_text(cls, v: str) -> str:
        if not v:
            return ""
        # Strip script tags or obvious html injections
        cleaned = html.escape(v.strip())
        return cleaned


class NotificationListResponse(BaseModel):
    total: int
    unread_count: int
    notifications: List[WelfareNotificationOut]


class UnreadCountResponse(BaseModel):
    unread_count: int
