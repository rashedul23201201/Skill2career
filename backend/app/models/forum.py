from datetime import datetime, timezone
from typing import Optional, List
from sqlalchemy import String, Boolean, DateTime, Integer, ForeignKey, Text, func, Index
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database.base import Base


class ForumCategory(Base):
    __tablename__ = "forum_categories"

    id: Mapped[int] = mapped_column(primary_key=True, index=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(100), unique=True, nullable=False, index=True)
    slug: Mapped[str] = mapped_column(String(100), unique=True, nullable=False, index=True)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    icon: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    order_index: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        server_default=func.now(),
        nullable=False,
    )

    posts = relationship("ForumPost", back_populates="category", cascade="all, delete-orphan")

    def __repr__(self) -> str:
        return f"<ForumCategory id={self.id} name='{self.name}'>"


class ForumPost(Base):
    __tablename__ = "forum_posts"

    id: Mapped[int] = mapped_column(primary_key=True, index=True, autoincrement=True)
    category_id: Mapped[int] = mapped_column(ForeignKey("forum_categories.id", ondelete="CASCADE"), nullable=False, index=True)
    author_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)

    title: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    content: Mapped[str] = mapped_column(Text, nullable=False)

    views_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    likes_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    replies_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    has_instructor_reply: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False, index=True)
    instructor_reply_name: Mapped[Optional[str]] = mapped_column(String(150), nullable=True)
    is_pinned: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    is_locked: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

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
    )

    category = relationship("ForumCategory", back_populates="posts")
    author = relationship("User", foreign_keys=[author_id], backref="forum_posts")
    comments = relationship("ForumComment", back_populates="post", cascade="all, delete-orphan", order_by="ForumComment.created_at.asc()")
    likes = relationship("ForumLike", back_populates="post", cascade="all, delete-orphan")
    reports = relationship("ForumReport", back_populates="post", cascade="all, delete-orphan")

    def __repr__(self) -> str:
        return f"<ForumPost id={self.id} title='{self.title}'>"


class ForumComment(Base):
    __tablename__ = "forum_comments"

    id: Mapped[int] = mapped_column(primary_key=True, index=True, autoincrement=True)
    post_id: Mapped[int] = mapped_column(ForeignKey("forum_posts.id", ondelete="CASCADE"), nullable=False, index=True)
    author_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    parent_id: Mapped[Optional[int]] = mapped_column(ForeignKey("forum_comments.id", ondelete="CASCADE"), nullable=True, index=True)

    content: Mapped[str] = mapped_column(Text, nullable=False)
    is_instructor_reply: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    likes_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

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
    )

    post = relationship("ForumPost", back_populates="comments")
    author = relationship("User", foreign_keys=[author_id], backref="forum_comments")
    parent = relationship("ForumComment", remote_side=[id], backref="replies")
    likes = relationship("ForumLike", back_populates="comment", cascade="all, delete-orphan")
    reports = relationship("ForumReport", back_populates="comment", cascade="all, delete-orphan")

    def __repr__(self) -> str:
        return f"<ForumComment id={self.id} post_id={self.post_id}>"


class ForumLike(Base):
    __tablename__ = "forum_likes"

    id: Mapped[int] = mapped_column(primary_key=True, index=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    post_id: Mapped[Optional[int]] = mapped_column(ForeignKey("forum_posts.id", ondelete="CASCADE"), nullable=True, index=True)
    comment_id: Mapped[Optional[int]] = mapped_column(ForeignKey("forum_comments.id", ondelete="CASCADE"), nullable=True, index=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        server_default=func.now(),
        nullable=False,
    )

    user = relationship("User", foreign_keys=[user_id])
    post = relationship("ForumPost", back_populates="likes")
    comment = relationship("ForumComment", back_populates="likes")

    __table_args__ = (
        Index("idx_user_post_like", "user_id", "post_id"),
        Index("idx_user_comment_like", "user_id", "comment_id"),
    )


class ForumReport(Base):
    __tablename__ = "forum_reports"

    id: Mapped[int] = mapped_column(primary_key=True, index=True, autoincrement=True)
    reporter_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    post_id: Mapped[Optional[int]] = mapped_column(ForeignKey("forum_posts.id", ondelete="CASCADE"), nullable=True, index=True)
    comment_id: Mapped[Optional[int]] = mapped_column(ForeignKey("forum_comments.id", ondelete="CASCADE"), nullable=True, index=True)

    reason: Mapped[str] = mapped_column(String(100), nullable=False)
    details: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(String(50), default="PENDING", nullable=False, index=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        server_default=func.now(),
        nullable=False,
    )

    reporter = relationship("User", foreign_keys=[reporter_id])
    post = relationship("ForumPost", back_populates="reports")
    comment = relationship("ForumComment", back_populates="reports")

    def __repr__(self) -> str:
        return f"<ForumReport id={self.id} reason='{self.reason}' status='{self.status}'>"
