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
    def search_jobs(
        db: Session,
        page: int = 1,
        size: int = 8,
        search: Optional[str] = None,
        posting_type: Optional[str] = None,
        work_mode: Optional[str] = None,
        category: Optional[str] = None,
        experience_level: Optional[str] = None,
        location: Optional[str] = None,
        min_salary: Optional[int] = None,
        max_salary: Optional[int] = None,
        sort_by: Optional[str] = "recent",
        status: Optional[str] = JobStatus.ACTIVE.value,
        enforce_approved_company: bool = True,
    ) -> Tuple[List[JobPosting], int]:
        """Full-text and multi-attribute search with dynamic sorting and verification gating (SKL-5)."""
        statement = select(JobPosting).options(
            joinedload(JobPosting.company).joinedload(User.company_profile),
        )
        count_stmt = select(func.count(JobPosting.id))

        # Join User and CompanyProfile for verification gating and company name search
        statement = statement.join(User, JobPosting.company_id == User.id).outerjoin(
            CompanyProfile, User.id == CompanyProfile.user_id
        )
        count_stmt = count_stmt.join(User, JobPosting.company_id == User.id).outerjoin(
            CompanyProfile, User.id == CompanyProfile.user_id
        )

        # Status filter
        if status:
            statement = statement.where(JobPosting.status == status)
            count_stmt = count_stmt.where(JobPosting.status == status)

        # SKL-5 AC-4: Verified Company Listing Enforcement
        if enforce_approved_company:
            statement = statement.where(
                User.is_active.is_(True),
                func.upper(CompanyProfile.verification_status) == "APPROVED",
            )
            count_stmt = count_stmt.where(
                User.is_active.is_(True),
                func.upper(CompanyProfile.verification_status) == "APPROVED",
            )

        # SKL-5 AC-1: Keyword Search Engine (title, description, requirements, location, category, company_name)
        if search and search.strip():
            term = f"%{search.strip().lower()}%"
            search_clause = or_(
                func.lower(JobPosting.title).like(term),
                func.lower(JobPosting.description).like(term),
                func.lower(JobPosting.requirements).like(term),
                func.lower(JobPosting.location).like(term),
                func.lower(JobPosting.category).like(term),
                func.lower(CompanyProfile.company_name).like(term),
            )
            statement = statement.where(search_clause)
            count_stmt = count_stmt.where(search_clause)

        # SKL-5 AC-2: Multi-Criteria Filter Pipeline
        if posting_type and posting_type.strip().lower() not in ("all", ""):
            statement = statement.where(func.lower(JobPosting.posting_type) == posting_type.strip().lower())
            count_stmt = count_stmt.where(func.lower(JobPosting.posting_type) == posting_type.strip().lower())

        if work_mode and work_mode.strip().lower() not in ("all", ""):
            clean_mode = work_mode.strip().lower().replace("_", "-")
            statement = statement.where(
                or_(
                    func.lower(JobPosting.work_mode) == clean_mode,
                    func.lower(JobPosting.work_mode) == work_mode.strip().lower(),
                )
            )
            count_stmt = count_stmt.where(
                or_(
                    func.lower(JobPosting.work_mode) == clean_mode,
                    func.lower(JobPosting.work_mode) == work_mode.strip().lower(),
                )
            )

        if category and category.strip().lower() not in ("all", ""):
            statement = statement.where(func.lower(JobPosting.category) == category.strip().lower())
            count_stmt = count_stmt.where(func.lower(JobPosting.category) == category.strip().lower())

        if experience_level and experience_level.strip().lower() not in ("all", ""):
            statement = statement.where(func.lower(JobPosting.experience_level) == experience_level.strip().lower())
            count_stmt = count_stmt.where(func.lower(JobPosting.experience_level) == experience_level.strip().lower())

        if location and location.strip().lower() not in ("all", ""):
            loc_term = f"%{location.strip().lower()}%"
            statement = statement.where(func.lower(JobPosting.location).like(loc_term))
            count_stmt = count_stmt.where(func.lower(JobPosting.location).like(loc_term))

        if min_salary is not None and min_salary > 0:
            statement = statement.where(
                or_(
                    JobPosting.salary_max >= min_salary,
                    JobPosting.salary_min >= min_salary,
                )
            )
            count_stmt = count_stmt.where(
                or_(
                    JobPosting.salary_max >= min_salary,
                    JobPosting.salary_min >= min_salary,
                )
            )

        if max_salary is not None and max_salary > 0:
            statement = statement.where(
                or_(
                    JobPosting.salary_min <= max_salary,
                    JobPosting.salary_max <= max_salary,
                )
            )
            count_stmt = count_stmt.where(
                or_(
                    JobPosting.salary_min <= max_salary,
                    JobPosting.salary_max <= max_salary,
                )
            )

        # SKL-5 AC-3: Dynamic Sorting
        sort_mode = (sort_by or "recent").lower().strip()
        if sort_mode == "salary_high":
            statement = statement.order_by(JobPosting.salary_max.desc().nullslast(), JobPosting.id.desc())
        elif sort_mode == "deadline":
            statement = statement.order_by(JobPosting.deadline.asc().nullslast(), JobPosting.id.desc())
        else:  # "recent" or default
            statement = statement.order_by(JobPosting.created_at.desc(), JobPosting.id.desc())

        total = db.execute(count_stmt).scalar() or 0
        offset = max(0, (page - 1) * size)
        statement = statement.offset(offset).limit(size)
        items = list(db.execute(statement).scalars().all())

        return items, total

    @staticmethod
    def get_taxonomies(db: Session) -> dict:
        """Fetch distinct categories, locations, and default filter facets for vacancy exploration (SKL-5)."""
        cat_stmt = select(JobPosting.category).where(JobPosting.status == JobStatus.ACTIVE.value).distinct()
        loc_stmt = select(JobPosting.location).where(JobPosting.status == JobStatus.ACTIVE.value).distinct()

        categories = [c for c in db.execute(cat_stmt).scalars().all() if c]
        locations = [l for l in db.execute(loc_stmt).scalars().all() if l]

        default_categories = ["Software Engineering", "Product Management", "UI/UX Design", "Data & AI", "DevOps & Cloud", "Quality Assurance"]
        default_locations = ["Dhaka", "Chittagong", "Sylhet", "Remote"]

        for d in default_categories:
            if d not in categories:
                categories.append(d)
        for d in default_locations:
            if d not in locations:
                locations.append(d)

        return {
            "posting_types": ["All", "Job", "Internship"],
            "work_modes": ["All", "On-site", "Remote", "Hybrid"],
            "experience_levels": ["All", "Entry Level", "Junior", "Mid Level", "Senior", "Internship"],
            "categories": sorted(categories),
            "locations": sorted(locations),
            "salary_presets": [
                {"label": "Any Salary", "min_salary": None, "max_salary": None},
                {"label": "Under ৳25,000", "min_salary": 0, "max_salary": 25000},
                {"label": "৳25,000 - ৳50,000", "min_salary": 25000, "max_salary": 50000},
                {"label": "৳50,000 - ৳80,000", "min_salary": 50000, "max_salary": 80000},
                {"label": "৳80,000+", "min_salary": 80000, "max_salary": None},
            ],
        }

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
        enforce_approved_company: bool = False,
    ) -> Tuple[List[JobPosting], int]:
        statement = select(JobPosting).options(
            joinedload(JobPosting.company).joinedload(User.company_profile),
        )
        count_stmt = select(func.count(JobPosting.id))

        # Always join User and CompanyProfile when search or verification check needed
        if search or enforce_approved_company:
            statement = statement.join(User, JobPosting.company_id == User.id).outerjoin(
                CompanyProfile, User.id == CompanyProfile.user_id
            )
            count_stmt = count_stmt.join(User, JobPosting.company_id == User.id).outerjoin(
                CompanyProfile, User.id == CompanyProfile.user_id
            )
            if enforce_approved_company:
                statement = statement.where(
                    User.is_active.is_(True),
                    func.upper(CompanyProfile.verification_status) == "APPROVED",
                )
                count_stmt = count_stmt.where(
                    User.is_active.is_(True),
                    func.upper(CompanyProfile.verification_status) == "APPROVED",
                )

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
            search_clause = or_(
                func.lower(JobPosting.title).like(term),
                func.lower(JobPosting.description).like(term),
                func.lower(JobPosting.requirements).like(term),
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
