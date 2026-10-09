import enum
from datetime import datetime, timezone
from typing import Optional, List
from sqlalchemy import String, Boolean, DateTime, Float, Integer, ForeignKey, Text, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database.base import Base


class EnrollmentStatus(str, enum.Enum):
    ACTIVE = "ACTIVE"
    COMPLETED = "COMPLETED"
    DROPPED = "DROPPED"


class CourseEnrollment(Base):
    __tablename__ = "course_enrollments"
    __table_args__ = (
        UniqueConstraint("user_id", "course_id", name="uq_user_course_enrollment"),
    )

    id: Mapped[int] = mapped_column(primary_key=True, index=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    course_id: Mapped[int] = mapped_column(ForeignKey("courses.id", ondelete="CASCADE"), nullable=False, index=True)
    status: Mapped[str] = mapped_column(String(50), default=EnrollmentStatus.ACTIVE.value, nullable=False, index=True)
    progress_percentage: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    completed_lessons_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    last_accessed_lesson_id: Mapped[Optional[int]] = mapped_column(ForeignKey("lessons.id", ondelete="SET NULL"), nullable=True)

    enrolled_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        server_default=func.now(),
        nullable=False,
    )
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
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

    user = relationship("User", foreign_keys=[user_id], backref="enrollments")
    course = relationship("Course", foreign_keys=[course_id], backref="enrollments")
    last_accessed_lesson = relationship("Lesson", foreign_keys=[last_accessed_lesson_id])
    lesson_progresses = relationship("LessonProgress", back_populates="enrollment", cascade="all, delete-orphan")

    def __repr__(self) -> str:
        return f"<CourseEnrollment id={self.id} user_id={self.user_id} course_id={self.course_id} progress={self.progress_percentage}%>"


class LessonProgress(Base):
    __tablename__ = "lesson_progress"
    __table_args__ = (
        UniqueConstraint("user_id", "lesson_id", name="uq_user_lesson_progress"),
    )

    id: Mapped[int] = mapped_column(primary_key=True, index=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    course_id: Mapped[int] = mapped_column(ForeignKey("courses.id", ondelete="CASCADE"), nullable=False, index=True)
    lesson_id: Mapped[int] = mapped_column(ForeignKey("lessons.id", ondelete="CASCADE"), nullable=False, index=True)
    enrollment_id: Mapped[Optional[int]] = mapped_column(ForeignKey("course_enrollments.id", ondelete="CASCADE"), nullable=True, index=True)
    is_completed: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

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

    user = relationship("User", foreign_keys=[user_id])
    course = relationship("Course", foreign_keys=[course_id])
    lesson = relationship("Lesson", foreign_keys=[lesson_id])
    enrollment = relationship("CourseEnrollment", back_populates="lesson_progresses")

    def __repr__(self) -> str:
        return f"<LessonProgress id={self.id} user_id={self.user_id} lesson_id={self.lesson_id} completed={self.is_completed}>"
