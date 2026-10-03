from typing import Optional, List, Tuple
from sqlalchemy import select, func
from sqlalchemy.orm import Session, joinedload
from app.models.profile import InstructorProfile
from app.models.user import User


class InstructorRepository:
    """Data Access Object for Instructor Profiles and Onboarding Applications (SKL-52)."""

    @staticmethod
    def get_by_id(db: Session, profile_id: int) -> Optional[InstructorProfile]:
        """Retrieve an instructor profile by primary key ID, eagerly loading user details."""
        statement = (
            select(InstructorProfile)
            .options(joinedload(InstructorProfile.user))
            .where(InstructorProfile.id == profile_id)
        )
        return db.execute(statement).scalar_one_or_none()

    @staticmethod
    def get_by_user_id(db: Session, user_id: int) -> Optional[InstructorProfile]:
        """Retrieve an instructor profile by user foreign key ID, eagerly loading user details."""
        statement = (
            select(InstructorProfile)
            .options(joinedload(InstructorProfile.user))
            .where(InstructorProfile.user_id == user_id)
        )
        return db.execute(statement).scalar_one_or_none()

    @staticmethod
    def create(db: Session, profile: InstructorProfile) -> InstructorProfile:
        """Persist a new instructor profile to the database."""
        db.add(profile)
        db.commit()
        db.refresh(profile)
        return profile

    @staticmethod
    def update(db: Session, profile: InstructorProfile) -> InstructorProfile:
        """Save updates to an existing instructor profile."""
        db.commit()
        db.refresh(profile)
        return profile

    @staticmethod
    def get_pending_applications(db: Session, skip: int = 0, limit: int = 50) -> List[InstructorProfile]:
        """Retrieve instructor profiles with onboarding_status = 'PENDING_REVIEW'."""
        statement = (
            select(InstructorProfile)
            .options(joinedload(InstructorProfile.user))
            .where(InstructorProfile.onboarding_status == "PENDING_REVIEW")
            .order_by(InstructorProfile.created_at.asc())
            .offset(skip)
            .limit(limit)
        )
        return list(db.execute(statement).scalars().all())

    @staticmethod
    def get_all(
        db: Session,
        status: Optional[str] = None,
        skip: int = 0,
        limit: int = 50
    ) -> Tuple[List[InstructorProfile], int]:
        """Query instructor profiles with optional status filtering and pagination."""
        statement = select(InstructorProfile).options(joinedload(InstructorProfile.user))
        count_stmt = select(func.count(InstructorProfile.id))

        if status:
            statement = statement.where(InstructorProfile.onboarding_status == status)
            count_stmt = count_stmt.where(InstructorProfile.onboarding_status == status)

        total = db.execute(count_stmt).scalar() or 0
        statement = statement.order_by(InstructorProfile.id.desc()).offset(skip).limit(limit)
        items = list(db.execute(statement).scalars().all())
        return items, total
