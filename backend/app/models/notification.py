from datetime import datetime, timezone
from typing import Optional
from sqlalchemy import String, Boolean, DateTime, ForeignKey, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base


class Notification(Base):
    """Notification model for cross-module alerts, in-app drawer, and email logs (SKL-17)."""
    __tablename__ = "notifications"

    id: Mapped[int] = mapped_column(primary_key=True, index=True, autoincrement=True)
    recipient_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    event_type: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    title: Mapped[str] = mapped_column(String(150), nullable=False)
    message: Mapped[str] = mapped_column(Text, nullable=False)
    link_url: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    is_read: Mapped[bool] = mapped_column(
        Boolean, default=False, server_default="0", nullable=False, index=True
    )
    email_sent: Mapped[bool] = mapped_column(
        Boolean, default=False, server_default="0", nullable=False
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        server_default=func.now(),
        nullable=False,
        index=True,
    )

    # Relationships
    recipient = relationship(
        "User",
        foreign_keys=[recipient_id],
        backref="notifications",
    )

    def __repr__(self) -> str:
        return f"<Notification id={self.id} recipient_id={self.recipient_id} event_type='{self.event_type}' is_read={self.is_read}>"
