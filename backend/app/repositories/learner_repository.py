from typing import Optional, List, Dict, Any
from sqlalchemy import select
from sqlalchemy.orm import Session
from app.models.profile import LearnerProfile


class LearnerRepository:
    """Repository handling database operations for the LearnerProfile entity (SKL-51)."""

    @staticmethod
    def get_by_user_id(db: Session, user_id: int) -> Optional[LearnerProfile]:
        """Retrieve learner profile by user ID."""
        statement = select(LearnerProfile).where(LearnerProfile.user_id == user_id)
        return db.execute(statement).scalar_one_or_none()

    @staticmethod
    def create(
        db: Session,
        user_id: int,
        phone_number: Optional[str] = None,
        location: Optional[str] = None,
        bio: Optional[str] = None,
        target_role: Optional[str] = None,
        primary_track: Optional[str] = None,
        institution: Optional[str] = None,
        department: Optional[str] = None,
        skills: Optional[List[str]] = None,
        portfolio_links: Optional[Dict[str, Any]] = None,
        resume_url: Optional[str] = None,
        resume_filename: Optional[str] = None,
        completion_pct: int = 25,
    ) -> LearnerProfile:
        """Create and persist a new LearnerProfile record."""
        profile = LearnerProfile(
            user_id=user_id,
            phone_number=phone_number,
            location=location,
            bio=bio,
            target_role=target_role,
            primary_track=primary_track,
            institution=institution,
            department=department,
            skills={"items": skills} if isinstance(skills, list) else skills,
            portfolio_links=portfolio_links or {},
            resume_url=resume_url,
            resume_filename=resume_filename,
            completion_pct=completion_pct,
        )
        db.add(profile)
        db.commit()
        db.refresh(profile)
        return profile

    @staticmethod
    def update(db: Session, profile: LearnerProfile) -> LearnerProfile:
        """Persist updates to an existing LearnerProfile."""
        db.commit()
        db.refresh(profile)
        return profile

    @staticmethod
    def update_resume(
        db: Session,
        profile: LearnerProfile,
        resume_url: Optional[str],
        resume_filename: Optional[str]
    ) -> LearnerProfile:
        """Update resume attachment fields and persist."""
        profile.resume_url = resume_url
        profile.resume_filename = resume_filename
        db.commit()
        db.refresh(profile)
        return profile
