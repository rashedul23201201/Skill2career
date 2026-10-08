import logging
from typing import Optional, List, Tuple
from sqlalchemy import select, func, or_
from sqlalchemy.orm import Session, joinedload
from app.models.job import JobPosting, JobStatus
from app.models.user import User
from app.models.profile import CompanyProfile

logger = logging.getLogger(__name__)


class JobRepository:
    """Repository managing persistence for JobPosting entities (SKL-4)."""

    @staticmethod
    def create(db: Session, job: JobPosting) -> JobPosting:
        db.add(job)
        db.commit()
        db.refresh(job)
        return job

    @staticmethod
    def get_by_id(db: Session, job_id: int) -> Optional[JobPosting]:
        stmt = (
            select(JobPosting)
            .options(
                joinedload(JobPosting.company).joinedload(User.company_profile),
            )
            .where(JobPosting.id == job_id)
        )
        return db.execute(stmt).scalar_one_or_none()

    @staticmethod
    def update(db: Session, job: JobPosting) -> JobPosting:
        db.commit()
        db.refresh(job)
        return job

    @staticmethod
    def delete(db: Session, job: JobPosting) -> None:
        db.delete(job)
        db.commit()

    @staticmethod
    def update_status(db: Session, job: JobPosting, status: str) -> JobPosting:
        job.status = status
        db.commit()
        db.refresh(job)
        return job

    @staticmethod
    def get_jobs_paginated(
        db: Session,
        page: int = 1,
        size: int = 10,
        posting_type: Optional[str] = None,
        work_mode: Optional[str] = None,
        category: Optional[str] = None,
        experience_level: Optional[str] = None,
        location: Optional[str] = None,
        status: Optional[str] = None,
        search: Optional[str] = None,
        company_id: Optional[int] = None,
    ) -> Tuple[List[JobPosting], int]:
        statement = select(JobPosting).options(
            joinedload(JobPosting.company).joinedload(User.company_profile),
        )
        count_stmt = select(func.count(JobPosting.id))

        if posting_type and posting_type.lower() != "all":
            statement = statement.where(func.lower(JobPosting.posting_type) == posting_type.strip().lower())
            count_stmt = count_stmt.where(func.lower(JobPosting.posting_type) == posting_type.strip().lower())

        if work_mode:
            statement = statement.where(func.lower(JobPosting.work_mode) == work_mode.strip().lower())
            count_stmt = count_stmt.where(func.lower(JobPosting.work_mode) == work_mode.strip().lower())

        if category and category.lower() != "all":
            statement = statement.where(func.lower(JobPosting.category) == category.strip().lower())
            count_stmt = count_stmt.where(func.lower(JobPosting.category) == category.strip().lower())

        if experience_level:
            statement = statement.where(func.lower(JobPosting.experience_level) == experience_level.strip().lower())
            count_stmt = count_stmt.where(func.lower(JobPosting.experience_level) == experience_level.strip().lower())

        if location:
            loc_term = f"%{location.strip().lower()}%"
            statement = statement.where(func.lower(JobPosting.location).like(loc_term))
            count_stmt = count_stmt.where(func.lower(JobPosting.location).like(loc_term))

        if status:
            statement = statement.where(JobPosting.status == status)
            count_stmt = count_stmt.where(JobPosting.status == status)

        if company_id:
            statement = statement.where(JobPosting.company_id == company_id)
            count_stmt = count_stmt.where(JobPosting.company_id == company_id)

        if search and search.strip():
            term = f"%{search.strip().lower()}%"
            statement = statement.outerjoin(User, JobPosting.company_id == User.id).outerjoin(CompanyProfile, User.id == CompanyProfile.user_id)
            count_stmt = count_stmt.outerjoin(User, JobPosting.company_id == User.id).outerjoin(CompanyProfile, User.id == CompanyProfile.user_id)

            search_clause = or_(
                func.lower(JobPosting.title).like(term),
                func.lower(JobPosting.description).like(term),
                func.lower(JobPosting.location).like(term),
                func.lower(JobPosting.category).like(term),
                func.lower(CompanyProfile.company_name).like(term),
            )
            statement = statement.where(search_clause)
            count_stmt = count_stmt.where(search_clause)

        total = db.execute(count_stmt).scalar() or 0
        offset = max(0, (page - 1) * size)
        statement = statement.order_by(JobPosting.id.desc()).offset(offset).limit(size)
        items = list(db.execute(statement).scalars().all())

        return items, total

    @staticmethod
    def count_active_jobs(db: Session, company_id: Optional[int] = None) -> int:
        stmt = select(func.count(JobPosting.id)).where(JobPosting.status == JobStatus.ACTIVE.value)
        if company_id:
            stmt = stmt.where(JobPosting.company_id == company_id)
        return db.execute(stmt).scalar() or 0
