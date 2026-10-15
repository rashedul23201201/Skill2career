from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field, ConfigDict
from app.models.moderation import ModerationStatus, ContentType, ModerationAction


class ModerationDecisionRequest(BaseModel):
    """Payload for administrative approval or restriction of content (SKL-25)."""
    reason: Optional[str] = Field(default=None, description="Detailed rationale for restriction or audit notes")
    notes: Optional[str] = Field(default=None, description="Administrative remarks or feedback")

    model_config = ConfigDict(extra="ignore")


class ContentModerationLogResponse(BaseModel):
    """Schema representing an administrative audit log entry for content moderation (SKL-25)."""
    id: int
    content_type: str
    content_id: int
    admin_id: Optional[int] = None
    admin_name: Optional[str] = None
    action: str
    reason: Optional[str] = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ModerationItemResponse(BaseModel):
    """Schema representing a moderatable entity (Course or Mock Test) in the Admin Moderation Tab."""
    id: int
    content_type: str  # "COURSE" or "MOCK_TEST"
    title: str
    category: str
    instructor_id: int
    instructor_name: str
    instructor_email: Optional[str] = None
    status: str  # CourseStatus or MockTestStatus (DRAFT, PUBLISHED, etc.)
    moderation_status: str  # DRAFT, PENDING_REVIEW, APPROVED, RESTRICTED
    moderation_notes: Optional[str] = None
    moderated_by: Optional[int] = None
    moderator_name: Optional[str] = None
    moderated_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime
    details: Dict[str, Any] = {}

    model_config = ConfigDict(from_attributes=True)


class PendingModerationResponse(BaseModel):
    """Aggregated response for administrative review queue."""
    courses: List[ModerationItemResponse] = []
    mock_tests: List[ModerationItemResponse] = []
    total_pending: int = 0
