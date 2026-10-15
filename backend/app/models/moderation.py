import enum
from datetime import datetime, timezone
from typing import Optional
from sqlalchemy import String, DateTime, Integer, ForeignKey, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database.base import Base


class ModerationStatus(str, enum.Enum):
    """Moderation status of content (SKL-25)."""
    DRAFT = "DRAFT"
    PENDING_REVIEW = "PENDING_REVIEW"
    APPROVED = "APPROVED"
    RESTRICTED = "RESTRICTED"


class ContentType(str, enum.Enum):
    """Types of moderatable content items."""
    COURSE = "COURSE"
    LESSON = "LESSON"
    MOCK_TEST = "MOCK_TEST"


class ModerationAction(str, enum.Enum):
    """Actions recorded in content moderation audit trail."""
    APPROVE = "APPROVE"
    RESTRICT = "RESTRICT"
    SUBMIT_REVIEW = "SUBMIT_REVIEW"
    STATUS_RESET = "STATUS_RESET"


class ContentModerationLog(Base):
    """Administrative audit trail for course and mock test moderation decisions (SKL-25)."""
    __tablename__ = "content_moderation_logs"

    id: Mapped[int] = mapped_column(primary_key=True, index=True, autoincrement=True)
    content_type: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    content_id: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    admin_id: Mapped[Optional[int]] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)
    action: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    reason: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        server_default=func.now(),
        nullable=False,
        index=True,
    )

    admin = relationship("User", foreign_keys=[admin_id])

    def __repr__(self) -> str:
        return f"<ContentModerationLog id={self.id} type={self.content_type} content_id={self.content_id} action={self.action}>"
