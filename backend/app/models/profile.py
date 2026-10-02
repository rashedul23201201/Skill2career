from datetime import datetime, timezone
from typing import Optional
from sqlalchemy import String, Boolean, DateTime, Integer, ForeignKey, Text, JSON, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database.base import Base


class LearnerProfile(Base):
    """Profile details for Learner users."""
    __tablename__ = "learner_profiles"

    id: Mapped[int] = mapped_column(primary_key=True, index=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), unique=True, nullable=False, index=True)
    phone_number: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    location: Mapped[Optional[str]] = mapped_column(String(150), nullable=True)
    bio: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    target_role: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    primary_track: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    institution: Mapped[Optional[str]] = mapped_column(String(150), nullable=True)
    department: Mapped[Optional[str]] = mapped_column(String(150), nullable=True)
    skills: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    resume_url: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    resume_filename: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    portfolio_links: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    completion_pct: Mapped[int] = mapped_column(Integer, default=25, nullable=False)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), server_default=func.now(), onupdate=lambda: datetime.now(timezone.utc), nullable=False)

    user = relationship("User", back_populates="learner_profile")


class InstructorProfile(Base):
    """Profile details for Instructor users."""
    __tablename__ = "instructor_profiles"

    id: Mapped[int] = mapped_column(primary_key=True, index=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), unique=True, nullable=False, index=True)
    designation: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    institution: Mapped[Optional[str]] = mapped_column(String(150), nullable=True)
    qualification: Mapped[Optional[str]] = mapped_column(String(150), nullable=True)
    expertise_domain: Mapped[Optional[str]] = mapped_column(String(150), nullable=True)
    years_experience: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    certificates: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    intro_video_url: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    bio: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    linkedin_url: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    onboarding_status: Mapped[str] = mapped_column(String(50), default="PENDING_REVIEW", nullable=False)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), server_default=func.now(), onupdate=lambda: datetime.now(timezone.utc), nullable=False)

    user = relationship("User", back_populates="instructor_profile")


class CompanyProfile(Base):
    """Profile and verification details for Company users."""
    __tablename__ = "company_profiles"

    id: Mapped[int] = mapped_column(primary_key=True, index=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), unique=True, nullable=False, index=True)
    company_name: Mapped[str] = mapped_column(String(150), nullable=False)
    industry: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    company_size: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    contact_person: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    contact_phone: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    website_url: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    office_address: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    tagline: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    logo_url: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    banner_url: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    trade_license_url: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    verification_status: Mapped[str] = mapped_column(String(50), default="PENDING", nullable=False)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), server_default=func.now(), onupdate=lambda: datetime.now(timezone.utc), nullable=False)

    user = relationship("User", back_populates="company_profile")
