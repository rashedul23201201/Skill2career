import enum
from datetime import datetime, timezone
from typing import Optional, List, Any
from sqlalchemy import String, Boolean, DateTime, Integer, ForeignKey, Text, JSON, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database.base import Base


class InterviewStatus(str, enum.Enum):
    PENDING = "PENDING"
    SCHEDULED = "SCHEDULED"
    RESCHEDULE_REQUESTED = "RESCHEDULE_REQUESTED"
    COMPLETED = "COMPLETED"
    CANCELLED = "CANCELLED"


class InterviewRecommendation(str, enum.Enum):
    STRONG_HIRE = "STRONG_HIRE"
    HIRE = "HIRE"
    NEUTRAL = "NEUTRAL"
    NO_HIRE = "NO_HIRE"


class InterviewRequest(Base):
    __tablename__ = "interview_requests"

    id: Mapped[int] = mapped_column(primary_key=True, index=True, autoincrement=True)
    application_id: Mapped[int] = mapped_column(
        ForeignKey("job_applications.id", ondelete="CASCADE"), nullable=False, index=True
    )
    company_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    candidate_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    job_id: Mapped[int] = mapped_column(
        ForeignKey("job_postings.id", ondelete="CASCADE"), nullable=False, index=True
    )

    interview_type: Mapped[str] = mapped_column(
        String(100), default="Company Interview", nullable=False
    )
    meeting_platform: Mapped[str] = mapped_column(
        String(100), default="Google Meet", nullable=False
    )
    meeting_link: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    location: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    duration_minutes: Mapped[int] = mapped_column(Integer, default=45, nullable=False)
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    status: Mapped[str] = mapped_column(
        String(50), default=InterviewStatus.PENDING.value, nullable=False, index=True
    )

    selected_slot_id: Mapped[Optional[int]] = mapped_column(
        Integer,
        ForeignKey(
            "interview_slots.id",
            ondelete="SET NULL",
            use_alter=True,
            name="fk_interview_requests_selected_slot_id",
        ),
        nullable=True,
    )
    scheduled_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    reschedule_reason: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    rescheduled_by: Mapped[Optional[int]] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    reschedule_preferred_time: Mapped[Optional[str]] = mapped_column(
        String(255), nullable=True
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
    )

    application = relationship("JobApplication", backref="interview_requests")
    company = relationship("User", foreign_keys=[company_id])
    candidate = relationship("User", foreign_keys=[candidate_id], backref="candidate_interviews")
    job = relationship("JobPosting")
    slots: Mapped[List["InterviewSlot"]] = relationship(
        "InterviewSlot",
        foreign_keys="InterviewSlot.interview_request_id",
        back_populates="interview_request",
        cascade="all, delete-orphan",
    )
    selected_slot = relationship(
        "InterviewSlot",
        foreign_keys=[selected_slot_id],
        post_update=True,
    )
    feedbacks: Mapped[List["InterviewFeedback"]] = relationship(
        "InterviewFeedback",
        foreign_keys="InterviewFeedback.interview_id",
        back_populates="interview_request",
        cascade="all, delete-orphan",
    )


class InterviewSlot(Base):
    __tablename__ = "interview_slots"

    id: Mapped[int] = mapped_column(primary_key=True, index=True, autoincrement=True)
    interview_request_id: Mapped[int] = mapped_column(
        ForeignKey("interview_requests.id", ondelete="CASCADE"), nullable=False, index=True
    )
    start_time: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    end_time: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    is_selected: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        server_default=func.now(),
        nullable=False,
    )

    interview_request = relationship(
        "InterviewRequest",
        foreign_keys=[interview_request_id],
        back_populates="slots",
    )


class InterviewFeedback(Base):
    __tablename__ = "interview_feedbacks"

    id: Mapped[int] = mapped_column(primary_key=True, index=True, autoincrement=True)
    interview_id: Mapped[int] = mapped_column(
        ForeignKey("interview_requests.id", ondelete="CASCADE"), nullable=False, index=True
    )
    application_id: Mapped[int] = mapped_column(
        ForeignKey("job_applications.id", ondelete="CASCADE"), nullable=False, index=True
    )
    interviewer_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )

    overall_score: Mapped[int] = mapped_column(Integer, nullable=False)
    technical_score: Mapped[int] = mapped_column(Integer, default=75, nullable=False)
    communication_score: Mapped[int] = mapped_column(Integer, default=75, nullable=False)
    problem_solving_score: Mapped[int] = mapped_column(Integer, default=75, nullable=False)

    recommendation: Mapped[str] = mapped_column(
        String(50), default=InterviewRecommendation.HIRE.value, nullable=False, index=True
    )

    strengths: Mapped[Optional[Any]] = mapped_column(JSON, nullable=True)
    improvement_areas: Mapped[Optional[Any]] = mapped_column(JSON, nullable=True)
    competency_breakdown: Mapped[Optional[Any]] = mapped_column(JSON, nullable=True)

    feedback_notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    internal_notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    suggested_next_action: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)

    is_shared_with_candidate: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    shared_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

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

    interview_request = relationship(
        "InterviewRequest",
        foreign_keys=[interview_id],
        back_populates="feedbacks",
    )
    application = relationship(
        "JobApplication",
        foreign_keys=[application_id],
        backref="interview_feedbacks",
    )
    interviewer = relationship(
        "User",
        foreign_keys=[interviewer_id],
    )
