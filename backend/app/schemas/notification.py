from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field, ConfigDict


class NotificationResponse(BaseModel):
    """Schema for individual user notification (SKL-17)."""
    id: int
    recipient_id: int
    event_type: str
    title: str
    message: str
    link_url: Optional[str] = None
    is_read: bool
    email_sent: bool
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class NotificationListResponse(BaseModel):
    """Schema for paginated notifications list with unread counter (SKL-17 AC-2, AC-5)."""
    items: List[NotificationResponse]
    total: int
    page: int
    size: int
    unread_count: int


class NotificationUnreadCountResponse(BaseModel):
    """Schema for quick unread counter badge."""
    unread_count: int


class NotificationCreateRequest(BaseModel):
    """Internal/Administrative creation schema for generating notifications."""
    recipient_id: int = Field(..., gt=0, description="Recipient user ID")
    event_type: str = Field(..., min_length=1, max_length=50, description="Event classification")
    title: str = Field(..., min_length=1, max_length=150, description="Notification title")
    message: str = Field(..., min_length=1, description="Notification body content")
    link_url: Optional[str] = Field(default=None, max_length=255, description="Deep link target path")
    send_email: bool = Field(default=False, description="Whether to attempt high priority email dispatch")

    model_config = ConfigDict(extra="ignore")


class NotificationMarkReadResponse(BaseModel):
    """Schema returned after marking notification(s) as read."""
    id: Optional[int] = None
    is_read: bool = True
    updated_count: int = 1
    unread_count: int = 0
