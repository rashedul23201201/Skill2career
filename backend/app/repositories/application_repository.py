from datetime import datetime, timezone
from typing import Optional, List, Tuple, Dict
from sqlalchemy import select, func, and_
from sqlalchemy.orm import Session, joinedload
from app.models.application import JobApplication, ApplicationStatus
from app.models.job import JobPosting
from app.models.user import User
from app.models.profile import CompanyProfile, LearnerProfile


class ApplicationRepository:
    @staticmethod
    def create(db: Session, application: JobApplication) -> JobApplication:
        db.add(application)
        db.commit()
        db.refresh(application)
        return application

    @staticmethod
    def get_by_id(db: Session, application_id: int) -> Optional[JobApplication]:
        stmt = (
            select(JobApplication)
            .options(
                joinedload(JobApplication.job).joinedload(JobPosting.company).joinedload(User.company_profile),
                joinedload(JobApplication.learner).joinedload(User.learner_profile),
            )
            .where(JobApplication.id == application_id)
        )
        return db.execute(stmt).scalar_one_or_none()

    @staticmethod
    def get_by_job_and_learner(
        db: Session, job_id: int, learner_id: int, include_withdrawn: bool = False
    ) -> Optional[JobApplication]:
        stmt = select(JobApplication).where(
            JobApplication.job_id == job_id,
            JobApplication.learner_id == learner_id,
        )
        if not include_withdrawn:
            stmt = stmt.where(JobApplication.status != ApplicationStatus.WITHDRAWN.value)
        stmt = stmt.order_by(JobApplication.created_at.desc())
        return db.execute(stmt).scalars().first()

    @staticmethod
    def get_by_learner_paginated(
        db: Session,
        learner_id: int,
        status: Optional[str] = None,
        page: int = 1,
        size: int = 10,
    ) -> Tuple[List[JobApplication], int, Dict[str, int]]:
        base_query = (
            select(JobApplication)
            .options(
                joinedload(JobApplication.job).joinedload(JobPosting.company).joinedload(User.company_profile),
                joinedload(JobApplication.learner).joinedload(User.learner_profile),
            )
            .where(JobApplication.learner_id == learner_id)
        )

        all_for_learner = (
            db.execute(select(JobApplication.status).where(JobApplication.learner_id == learner_id))
            .scalars()
            .all()
        )

        counts = {
            "total": len(all_for_learner),
            "submitted": 0,
            "under_review": 0,
            "shortlisted": 0,
            "interview": 0,
            "offered": 0,
            "withdrawn": 0,
            "rejected": 0,
            "active": 0,
        }
        for st in all_for_learner:
            s_upper = st.upper() if st else ""
            if s_upper == ApplicationStatus.SUBMITTED.value:
                counts["submitted"] += 1
                counts["active"] += 1
            elif s_upper == ApplicationStatus.UNDER_REVIEW.value:
                counts["under_review"] += 1
                counts["active"] += 1
            elif s_upper == ApplicationStatus.SHORTLISTED.value:
                counts["shortlisted"] += 1
                counts["active"] += 1
            elif s_upper == ApplicationStatus.INTERVIEW_SCHEDULED.value:
                counts["interview"] += 1
                counts["active"] += 1
            elif s_upper == ApplicationStatus.OFFERED.value:
                counts["offered"] += 1
                counts["active"] += 1
            elif s_upper == ApplicationStatus.WITHDRAWN.value:
                counts["withdrawn"] += 1
            elif s_upper == ApplicationStatus.REJECTED.value:
                counts["rejected"] += 1

        if status:
            base_query = base_query.where(JobApplication.status == status.upper())

        count_stmt = select(func.count(JobApplication.id)).where(JobApplication.learner_id == learner_id)
        if status:
            count_stmt = count_stmt.where(JobApplication.status == status.upper())
        total = db.execute(count_stmt).scalar() or 0

        items_stmt = (
            base_query.order_by(JobApplication.applied_at.desc())
            .offset((page - 1) * size)
            .limit(size)
        )
        items = list(db.execute(items_stmt).scalars().all())

        return items, total, counts

    @staticmethod
    def get_by_job_paginated(
        db: Session,
        job_id: int,
        status: Optional[str] = None,
        page: int = 1,
        size: int = 10,
    ) -> Tuple[List[JobApplication], int]:
        query = (
            select(JobApplication)
            .options(
                joinedload(JobApplication.job).joinedload(JobPosting.company).joinedload(User.company_profile),
                joinedload(JobApplication.learner).joinedload(User.learner_profile),
            )
            .where(JobApplication.job_id == job_id)
        )

        if status:
            query = query.where(JobApplication.status == status.upper())

        count_stmt = select(func.count(JobApplication.id)).where(JobApplication.job_id == job_id)
        if status:
            count_stmt = count_stmt.where(JobApplication.status == status.upper())
        total = db.execute(count_stmt).scalar() or 0

        items_stmt = (
            query.order_by(JobApplication.applied_at.desc())
            .offset((page - 1) * size)
            .limit(size)
        )
        items = list(db.execute(items_stmt).scalars().all())

        return items, total

    @staticmethod
    def update(db: Session, application: JobApplication) -> JobApplication:
        application.updated_at = datetime.now(timezone.utc)
        db.commit()
        db.refresh(application)
        return application

    @staticmethod
    def delete(db: Session, application: JobApplication) -> None:
        db.delete(application)
        db.commit()
