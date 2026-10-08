import enum
from datetime import datetime, timezone
from typing import Optional, List
from sqlalchemy import String, DateTime, Integer, ForeignKey, Text, JSON, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database.base import Base


class JobPostingType(str, enum.Enum):
    """Type of vacancy posting."""
    JOB = "Job"
    INTERNSHIP = "Internship"


class JobWorkMode(str, enum.Enum):
    """Work arrangement model."""
    ON_SITE = "On-site"
    REMOTE = "Remote"
    HYBRID = "Hybrid"


class JobStatus(str, enum.Enum):
    """Lifecycle publishing state of a vacancy."""
    ACTIVE = "ACTIVE"
    DRAFT = "DRAFT"
    CLOSED = "CLOSED"
    ARCHIVED = "ARCHIVED"


class JobExperienceLevel(str, enum.Enum):
    """Required candidate seniority level."""
    ENTRY_LEVEL = "Entry Level"
    JUNIOR = "Junior"
    MID_LEVEL = "Mid Level"
    SENIOR = "Senior"
    INTERNSHIP = "Internship"


class JobPosting(Base):
    """Job and Internship Posting entity for Recruitment Pipeline (SKL-4)."""
    __tablename__ = "job_postings"

    id: Mapped[int] = mapped_column(primary_key=True, index=True, autoincrement=True)
    company_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)

    title: Mapped[str] = mapped_column(String(200), nullable=False, index=True)
    posting_type: Mapped[str] = mapped_column(String(50), default=JobPostingType.JOB.value, nullable=False, index=True)
    work_mode: Mapped[str] = mapped_column(String(50), default=JobWorkMode.ON_SITE.value, nullable=False, index=True)
    location: Mapped[str] = mapped_column(String(150), default="Dhaka", nullable=False, index=True)

    description: Mapped[str] = mapped_column(Text, nullable=False)
    requirements: Mapped[str] = mapped_column(Text, nullable=False)
    skills: Mapped[Optional[list]] = mapped_column(JSON, nullable=True)

    compensation: Mapped[str] = mapped_column(String(100), nullable=False)
    duration: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    experience_level: Mapped[str] = mapped_column(String(50), default=JobExperienceLevel.ENTRY_LEVEL.value, nullable=False)
    category: Mapped[str] = mapped_column(String(100), default="Software Engineering", nullable=False, index=True)

    deadline: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    status: Mapped[str] = mapped_column(String(50), default=JobStatus.ACTIVE.value, nullable=False, index=True)
    applications_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

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
    company = relationship("User", foreign_keys=[company_id], backref="job_postings")

    def __repr__(self) -> str:
        return f"<JobPosting id={self.id} title='{self.title}' status='{self.status}'>"
