from datetime import datetime, timedelta, timezone
from typing import Optional, List, Tuple, Dict, Any
from sqlalchemy import select, func, or_
from sqlalchemy.orm import Session
from app.core.config import settings
from app.models.user import User, UserRole
from app.models.profile import LearnerProfile, InstructorProfile, CompanyProfile


class UserRepository:
    """Repository handling all database operations for User entity and administrative queries (SKL-50/SKL-24)."""

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
    def update_status(db: Session, user: User, is_active: bool) -> User:
        """Update a user's active/deactivated status."""
        user.is_active = is_active
        db.commit()
        db.refresh(user)
        return user

    @staticmethod
    def update_role(db: Session, user: User, new_role: UserRole) -> User:
        """Update a user's role in the system."""
        user.role = new_role
        db.commit()
        db.refresh(user)
        return user

    @staticmethod
    def get_users_paginated(
        db: Session,
        page: int = 1,
        size: int = 20,
        role: Optional[UserRole] = None,
        is_active: Optional[bool] = None,
        is_verified: Optional[bool] = None,
        search: Optional[str] = None
    ) -> Tuple[List[User], int]:
        """Query users with pagination, filters (role, is_active, is_verified), and search (email, first_name, last_name)."""
        statement = select(User)
        count_stmt = select(func.count(User.id))

        if role is not None:
            statement = statement.where(User.role == role)
            count_stmt = count_stmt.where(User.role == role)

        if is_active is not None:
            statement = statement.where(User.is_active == is_active)
            count_stmt = count_stmt.where(User.is_active == is_active)

        if is_verified is not None:
            statement = statement.where(User.is_verified == is_verified)
            count_stmt = count_stmt.where(User.is_verified == is_verified)

        if search and search.strip():
            term = f"%{search.strip().lower()}%"
            search_clause = or_(
                func.lower(User.email).like(term),
                func.lower(User.first_name).like(term),
                func.lower(User.last_name).like(term),
            )
            statement = statement.where(search_clause)
            count_stmt = count_stmt.where(search_clause)

        total = db.execute(count_stmt).scalar() or 0
        offset = max(0, (page - 1) * size)
        statement = statement.order_by(User.id.desc()).offset(offset).limit(size)
        items = list(db.execute(statement).scalars().all())

        return items, total

    @staticmethod
    def get_overview_stats(db: Session) -> Dict[str, Any]:
        """Calculate system overview metrics for Admin Dashboard."""
        total_users = db.execute(select(func.count(User.id))).scalar() or 0
        total_companies = db.execute(select(func.count(User.id)).where(User.role == UserRole.COMPANY)).scalar() or 0
        
        # Pending company verification approvals & instructor onboarding
        try:
            pending_companies = db.execute(
                select(func.count(CompanyProfile.id)).where(CompanyProfile.verification_status == "PENDING")
            ).scalar() or 0
        except Exception:
            pending_companies = 0

        try:
            pending_instructors = db.execute(
                select(func.count(InstructorProfile.id)).where(InstructorProfile.onboarding_status == "PENDING_REVIEW")
            ).scalar() or 0
        except Exception:
            pending_instructors = 0

        pending_approvals = pending_companies + pending_instructors
        active_courses = 0

        active_users = db.execute(select(func.count(User.id)).where(User.is_active == True)).scalar() or 0
        inactive_users = total_users - active_users

        learners = db.execute(select(func.count(User.id)).where(User.role == UserRole.LEARNER)).scalar() or 0
        instructors = db.execute(select(func.count(User.id)).where(User.role == UserRole.INSTRUCTOR)).scalar() or 0
        admins = db.execute(select(func.count(User.id)).where(User.role == UserRole.ADMIN)).scalar() or 0

        return {
            "total_users": total_users,
            "total_companies": total_companies,
            "active_courses": active_courses,
            "pending_approvals": pending_approvals,
            "active_users": active_users,
            "inactive_users": inactive_users,
            "role_breakdown": {
                "LEARNER": learners,
                "INSTRUCTOR": instructors,
                "COMPANY": total_companies,
                "ADMIN": admins,
            }
        }

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
