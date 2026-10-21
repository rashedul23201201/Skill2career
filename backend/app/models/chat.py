from datetime import datetime, timezone
from typing import Optional, List
from sqlalchemy import String, Boolean, DateTime, ForeignKey, Text, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base


class ChatConversation(Base):
    """Direct chat conversation between a learner and an instructor (SKL-16)."""
    __tablename__ = "chat_conversations"

    id: Mapped[int] = mapped_column(primary_key=True, index=True, autoincrement=True)
    learner_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    instructor_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        server_default=func.now(),
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        server_default=func.now(),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
        index=True,
    )

    __table_args__ = (
        UniqueConstraint(
            "learner_id",
            "instructor_id",
            name="uq_chat_conversations_learner_instructor",
        ),
    )

    # Relationships
    learner = relationship(
        "User",
        foreign_keys=[learner_id],
        backref="learner_chat_conversations",
    )
    instructor = relationship(
        "User",
        foreign_keys=[instructor_id],
        backref="instructor_chat_conversations",
    )
    messages = relationship(
        "ChatMessage",
        back_populates="conversation",
        cascade="all, delete-orphan",
        order_by="ChatMessage.created_at.asc()",
    )

    def __repr__(self) -> str:
        return f"<ChatConversation id={self.id} learner_id={self.learner_id} instructor_id={self.instructor_id}>"


class ChatMessage(Base):
    """Real-time chat message persisted in MySQL (SKL-16)."""
    __tablename__ = "chat_messages"

    id: Mapped[int] = mapped_column(primary_key=True, index=True, autoincrement=True)
    conversation_id: Mapped[int] = mapped_column(
        ForeignKey("chat_conversations.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    sender_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    message_text: Mapped[str] = mapped_column(Text, nullable=False)
    is_read: Mapped[bool] = mapped_column(
        Boolean, default=False, server_default="0", nullable=False, index=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        server_default=func.now(),
        nullable=False,
        index=True,
    )

    # Relationships
    conversation = relationship("ChatConversation", back_populates="messages")
    sender = relationship("User", foreign_keys=[sender_id])

    def __repr__(self) -> str:
        return f"<ChatMessage id={self.id} conversation_id={self.conversation_id} sender_id={self.sender_id} is_read={self.is_read}>"
