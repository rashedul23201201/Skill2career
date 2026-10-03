import enum
from datetime import datetime, timezone
from typing import Optional, List
from sqlalchemy import String, Boolean, DateTime, Enum, Integer, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database.base import Base


class UserRole(str, enum.Enum):
    """Enumeration of system user roles."""
    LEARNER = "LEARNER"
    INSTRUCTOR = "INSTRUCTOR"
    COMPANY = "COMPANY"
    ADMIN = "ADMIN"


class User(Base):
    """Foundational User model for SKILL2CAREER ecosystem."""
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True, index=True, autoincrement=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)
    role: Mapped[UserRole] = mapped_column(
        Enum(UserRole, name="user_roles", native_enum=False, length=50),
        default=UserRole.LEARNER,
        nullable=False,
        index=True
    )
    first_name: Mapped[str] = mapped_column(String(100), nullable=False)
    last_name: Mapped[str] = mapped_column(String(100), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    is_verified: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    # Security & Brute-Force Rate Limiting (SKL-49)
    failed_login_attempts: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    locked_until: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        server_default=func.now(),
        nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        server_default=func.now(),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False
    )

    # Security token relationships (SKL-49)
    refresh_tokens = relationship("RefreshToken", back_populates="user", cascade="all, delete-orphan")
    password_resets = relationship("PasswordResetToken", back_populates="user", cascade="all, delete-orphan")
    email_verifications = relationship("EmailVerificationToken", back_populates="user", cascade="all, delete-orphan")

    # Profile relationships
    learner_profile = relationship("LearnerProfile", back_populates="user", uselist=False, cascade="all, delete-orphan")
    instructor_profile = relationship("InstructorProfile", back_populates="user", uselist=False, cascade="all, delete-orphan")
    company_profile = relationship("CompanyProfile", back_populates="user", uselist=False, cascade="all, delete-orphan", foreign_keys="CompanyProfile.user_id")

    def __repr__(self) -> str:
        return f"<User id={self.id} email='{self.email}' role='{self.role}'>"
