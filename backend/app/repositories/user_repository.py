from datetime import datetime, timedelta, timezone
from typing import Optional
from sqlalchemy import select
from sqlalchemy.orm import Session
from app.core.config import settings
from app.models.user import User, UserRole
from app.models.profile import LearnerProfile, InstructorProfile, CompanyProfile


class UserRepository:
    """Repository handling all database operations for User entity."""

    @staticmethod
    def get_by_id(db: Session, user_id: int) -> Optional[User]:
        """Retrieve a user by primary key ID."""
        statement = select(User).where(User.id == user_id)
        return db.execute(statement).scalar_one_or_none()

    @staticmethod
    def get_by_email(db: Session, email: str) -> Optional[User]:
        """Retrieve a user by email address (case-insensitive)."""
        statement = select(User).where(User.email == email.strip().lower())
        return db.execute(statement).scalar_one_or_none()

    @staticmethod
    def create(db: Session, user: User) -> User:
        """Persist a new user to the database and refresh attributes."""
        db.add(user)
        db.commit()
        db.refresh(user)
        return user

    @staticmethod
    def update(db: Session, user: User) -> User:
        """Save updates to an existing user."""
        db.commit()
        db.refresh(user)
        return user

    @staticmethod
    def record_failed_login(db: Session, user: User) -> int:
        """Increment failed login attempts and lock account if threshold exceeded."""
        user.failed_login_attempts += 1
        if user.failed_login_attempts >= settings.MAX_FAILED_LOGIN_ATTEMPTS:
            user.locked_until = datetime.now(timezone.utc) + timedelta(minutes=settings.ACCOUNT_LOCKOUT_MINUTES)
        db.commit()
        db.refresh(user)
        return user.failed_login_attempts

    @staticmethod
    def reset_failed_logins(db: Session, user: User) -> None:
        """Reset failed login count and clear lockout upon successful login."""
        user.failed_login_attempts = 0
        user.locked_until = None
        db.commit()

    @staticmethod
    def verify_email(db: Session, user: User) -> User:
        """Mark user's email as verified."""
        user.is_verified = True
        db.commit()
        db.refresh(user)
        return user

    @staticmethod
    def update_password(db: Session, user: User, hashed_password: str) -> User:
        """Update user's password hash and reset failed attempts."""
        user.hashed_password = hashed_password
        user.failed_login_attempts = 0
        user.locked_until = None
        db.commit()
        db.refresh(user)
        return user

    @staticmethod
    def create_learner_profile(db: Session, user_id: int, institution: Optional[str] = None, department: Optional[str] = None, target_role: Optional[str] = None) -> LearnerProfile:
        profile = LearnerProfile(
            user_id=user_id,
            institution=institution,
            department=department,
            target_role=target_role,
            completion_pct=25
        )
        db.add(profile)
        db.commit()
        db.refresh(profile)
        return profile

    @staticmethod
    def create_instructor_profile(db: Session, user_id: int, qualification: Optional[str] = None, expertise: Optional[str] = None, years_experience: Optional[str] = None) -> InstructorProfile:
        profile = InstructorProfile(
            user_id=user_id,
            qualification=qualification,
            expertise_domain=expertise,
            years_experience=years_experience,
            onboarding_status="PENDING_REVIEW"
        )
        db.add(profile)
        db.commit()
        db.refresh(profile)
        return profile

    @staticmethod
    def create_company_profile(db: Session, user_id: int, company_name: str, industry: Optional[str] = None, contact_phone: Optional[str] = None, website_url: Optional[str] = None, office_address: Optional[str] = None) -> CompanyProfile:
        profile = CompanyProfile(
            user_id=user_id,
            company_name=company_name,
            industry=industry,
            contact_phone=contact_phone,
            website_url=website_url,
            office_address=office_address,
            verification_status="PENDING"
        )
        db.add(profile)
        db.commit()
        db.refresh(profile)
        return profile
