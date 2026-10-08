import enum
from datetime import datetime, timezone
from typing import Optional
from sqlalchemy import String, DateTime, Integer, ForeignKey, Text, Boolean, JSON, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database.base import Base


class QuestionType(str, enum.Enum):
    MULTIPLE_CHOICE = "MULTIPLE_CHOICE"
    NUMERIC = "NUMERIC"
    TEXT = "TEXT"
    YES_NO = "YES_NO"


class DealBreakerRule(str, enum.Enum):
    MANDATORY = "MANDATORY"
    GTE = "GTE"
    LTE = "LTE"
    EQUALS = "EQUALS"
    CONTAINS = "CONTAINS"


class CandidateStatus(str, enum.Enum):
    APPLIED = "APPLIED"
    UNDER_REVIEW = "UNDER_REVIEW"
    SHORTLISTED = "SHORTLISTED"
    DISQUALIFIED = "DISQUALIFIED"


class ScreeningQuestion(Base):
    __tablename__ = "screening_questions"

    id: Mapped[int] = mapped_column(primary_key=True, index=True, autoincrement=True)
    job_id: Mapped[int] = mapped_column(ForeignKey("job_postings.id", ondelete="CASCADE"), nullable=False, index=True)

    question_text: Mapped[str] = mapped_column(String(500), nullable=False)
    question_type: Mapped[str] = mapped_column(String(50), default=QuestionType.TEXT.value, nullable=False)
    options: Mapped[Optional[list]] = mapped_column(JSON, nullable=True)
    expected_answer: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)

    is_required: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    is_deal_breaker: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False, index=True)
    deal_breaker_rule: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    deal_breaker_value: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    deal_breaker_label: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)

    weight: Mapped[int] = mapped_column(Integer, default=10, nullable=False)
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

    job = relationship("JobPosting", backref="screening_questions")


class CandidateEvaluation(Base):
    __tablename__ = "candidate_evaluations"

    id: Mapped[int] = mapped_column(primary_key=True, index=True, autoincrement=True)
    job_id: Mapped[int] = mapped_column(ForeignKey("job_postings.id", ondelete="CASCADE"), nullable=False, index=True)
    candidate_id: Mapped[Optional[int]] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)

    candidate_name: Mapped[str] = mapped_column(String(150), nullable=False, index=True)
    candidate_email: Mapped[str] = mapped_column(String(150), nullable=False)
    candidate_avatar_url: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)

    match_score: Mapped[int] = mapped_column(Integer, default=0, nullable=False, index=True)
    deal_breaker_passed: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False, index=True)
    deal_breaker_failed_reason: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(String(50), default=CandidateStatus.APPLIED.value, nullable=False, index=True)

    answers: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    key_answers_preview: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    resume_url: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    reviewed_by: Mapped[Optional[int]] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    reviewed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

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

    job = relationship("JobPosting", backref="candidate_evaluations")
    candidate = relationship("User", foreign_keys=[candidate_id])
    reviewer = relationship("User", foreign_keys=[reviewed_by])
