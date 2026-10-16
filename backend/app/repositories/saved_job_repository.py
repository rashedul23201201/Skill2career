import logging
from typing import Optional, List, Set
from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload

from app.models.job import SavedJob, JobPosting
from app.models.user import User

logger = logging.getLogger(__name__)


class SavedJobRepository:
    """Repository handling database operations for the SavedJob entity (SKL-6)."""

    @staticmethod
    def get_by_id(db: Session, saved_job_id: int) -> Optional[SavedJob]:
        """Fetch a saved job record by primary key with related job and company."""
        stmt = (
            select(SavedJob)
            .options(
                joinedload(SavedJob.job)
                .joinedload(JobPosting.company)
                .joinedload(User.company_profile)
            )
            .where(SavedJob.id == saved_job_id)
        )
        return db.execute(stmt).scalar_one_or_none()

    @staticmethod
    def get_by_learner_and_job(db: Session, learner_id: int, job_id: int) -> Optional[SavedJob]:
        """Fetch saved job record by composite (learner_id, job_id) key."""
        stmt = (
            select(SavedJob)
            .options(
                joinedload(SavedJob.job)
                .joinedload(JobPosting.company)
                .joinedload(User.company_profile)
            )
            .where(SavedJob.learner_id == learner_id, SavedJob.job_id == job_id)
        )
        return db.execute(stmt).scalar_one_or_none()

    @staticmethod
    def create(db: Session, learner_id: int, job_id: int) -> SavedJob:
        """Create and persist a new SavedJob record."""
        saved = SavedJob(learner_id=learner_id, job_id=job_id)
        db.add(saved)
        db.commit()
        db.refresh(saved)
        return saved

    @staticmethod
    def delete(db: Session, saved_job: SavedJob) -> None:
        """Remove a SavedJob record from the database."""
        db.delete(saved_job)
        db.commit()

    @staticmethod
    def list_by_learner(db: Session, learner_id: int) -> List[SavedJob]:
        """List all saved vacancies for a specific learner, ordered by most recently saved."""
        stmt = (
            select(SavedJob)
            .options(
                joinedload(SavedJob.job)
                .joinedload(JobPosting.company)
                .joinedload(User.company_profile)
            )
            .where(SavedJob.learner_id == learner_id)
            .order_by(SavedJob.saved_at.desc())
        )
        return list(db.execute(stmt).scalars().all())

    @staticmethod
    def get_saved_job_ids(db: Session, learner_id: int) -> Set[int]:
        """Retrieve set of job IDs currently bookmarked by the learner."""
        stmt = select(SavedJob.job_id).where(SavedJob.learner_id == learner_id)
        return set(db.execute(stmt).scalars().all())
