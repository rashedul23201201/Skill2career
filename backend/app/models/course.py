import enum
from datetime import datetime, timezone
from typing import Optional, List
from sqlalchemy import String, Boolean, DateTime, Float, Integer, ForeignKey, Text, JSON, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database.base import Base


class CourseLevel(str, enum.Enum):
    """Course proficiency difficulty level."""
    BEGINNER = "Beginner"
    INTERMEDIATE = "Intermediate"
    ADVANCED = "Advanced"


class CourseStatus(str, enum.Enum):
    """Lifecycle publishing state of a course."""
    DRAFT = "DRAFT"
    PUBLISHED = "PUBLISHED"
    UNPUBLISHED = "UNPUBLISHED"
    ARCHIVED = "ARCHIVED"


class Course(Base):
    """Course entity for LMS Module (SKL-53)."""
    __tablename__ = "courses"

    id: Mapped[int] = mapped_column(primary_key=True, index=True, autoincrement=True)
    instructor_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    
    title: Mapped[str] = mapped_column(String(200), nullable=False, index=True)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    category: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    level: Mapped[str] = mapped_column(String(50), default=CourseLevel.BEGINNER.value, nullable=False)
    
    price: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    is_free: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    status: Mapped[str] = mapped_column(String(50), default=CourseStatus.DRAFT.value, nullable=False, index=True)
    
    thumbnail_url: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    duration_weeks: Mapped[int] = mapped_column(Integer, default=8, nullable=False)
    
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

    # Relationships
    instructor = relationship("User", foreign_keys=[instructor_id], backref="courses")
    modules = relationship("CourseModule", back_populates="course", cascade="all, delete-orphan", order_by="CourseModule.order_index")
    lessons = relationship("Lesson", back_populates="course", cascade="all, delete-orphan", order_by="Lesson.order_index")

    def __repr__(self) -> str:
        return f"<Course id={self.id} title='{self.title}' status='{self.status}'>"


class CourseModule(Base):
    """Curriculum Module grouping lessons within a Course (SKL-53)."""
    __tablename__ = "course_modules"

    id: Mapped[int] = mapped_column(primary_key=True, index=True, autoincrement=True)
    course_id: Mapped[int] = mapped_column(ForeignKey("courses.id", ondelete="CASCADE"), nullable=False, index=True)
    
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    order_index: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

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

    # Relationships
    course = relationship("Course", back_populates="modules")
    lessons = relationship("Lesson", back_populates="module", cascade="all, delete-orphan", order_by="Lesson.order_index")

    def __repr__(self) -> str:
        return f"<CourseModule id={self.id} title='{self.title}' course_id={self.course_id}>"


class Lesson(Base):
    """Lesson and Study Material unit within a Course / Module (SKL-53 / SKL-55)."""
    __tablename__ = "lessons"

    id: Mapped[int] = mapped_column(primary_key=True, index=True, autoincrement=True)
    course_id: Mapped[int] = mapped_column(ForeignKey("courses.id", ondelete="CASCADE"), nullable=False, index=True)
    module_id: Mapped[Optional[int]] = mapped_column(ForeignKey("course_modules.id", ondelete="CASCADE"), nullable=True, index=True)
    
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    content_type: Mapped[str] = mapped_column(String(50), default="video", nullable=False)  # video, reading, quiz
    video_url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    study_material_url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    attachments: Mapped[Optional[list]] = mapped_column(JSON, nullable=True)
    duration_minutes: Mapped[int] = mapped_column(Integer, default=30, nullable=False)
    order_index: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

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

    # Relationships
    course = relationship("Course", back_populates="lessons")
    module = relationship("CourseModule", back_populates="lessons")

    def __repr__(self) -> str:
        return f"<Lesson id={self.id} title='{self.title}' course_id={self.course_id}>"
