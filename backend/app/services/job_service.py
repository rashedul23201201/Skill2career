import logging
import math
from typing import Optional
from sqlalchemy.orm import Session

from app.core.exceptions import (
    NotFoundException,
    ForbiddenException,
)
from app.models.user import User, UserRole
from app.models.job import JobPosting, JobStatus
from app.repositories.job_repository import JobRepository
from app.repositories.audit_log_repository import AuditLogRepository
from app.schemas.job import (
    JobPostingCreateRequest,
    JobPostingUpdateRequest,
    JobPostingResponse,
    PaginatedJobPostingResponse,
)

logger = logging.getLogger(__name__)


class JobService:
    """Service handling recruitment vacancies, candidate discovery, and company posting management (SKL-4)."""

    def __init__(
        self,
        job_repo: JobRepository = JobRepository(),
        audit_repo: AuditLogRepository = AuditLogRepository(),
    ):
        self.job_repo = job_repo
        self.audit_repo = audit_repo

    def _to_job_response(self, job: JobPosting) -> JobPostingResponse:
        company_name = "Hiring Company"
        company_logo_url = None
        company_location = None
        company_industry = None
        company_website = None

        if job.company:
            company_name = f"{job.company.first_name} {job.company.last_name}".strip()
            if hasattr(job.company, "company_profile") and job.company.company_profile:
                profile = job.company.company_profile
                company_name = profile.company_name or company_name
                company_logo_url = profile.logo_url
                company_location = profile.location or profile.office_address
                company_industry = profile.industry
                company_website = profile.website_url

        return JobPostingResponse(
            id=job.id,
            company_id=job.company_id,
            company_name=company_name,
            company_logo_url=company_logo_url,
            company_location=company_location,
            company_industry=company_industry,
            company_website=company_website,
            title=job.title,
            posting_type=job.posting_type,
            work_mode=job.work_mode,
            location=job.location,
            description=job.description,
            requirements=job.requirements,
            skills=job.skills or [],
            compensation=job.compensation,
            duration=job.duration,
            experience_level=job.experience_level,
            category=job.category,
            deadline=job.deadline,
            status=job.status,
            applications_count=job.applications_count,
            created_at=job.created_at,
            updated_at=job.updated_at,
        )

    def create_job(
        self, db: Session, current_user: User, request: JobPostingCreateRequest
    ) -> JobPostingResponse:
        """Create a new job or internship posting (SKL-4 AC-1, AC-2)."""
        if current_user.role not in [UserRole.COMPANY, UserRole.ADMIN]:
            raise ForbiddenException(
                message="Only corporate company accounts or administrators can create vacancies",
                error_code="INSUFFICIENT_ROLE_PERMISSIONS",
            )

        # Gatekeeper: Verification Authorization Check (AC-2)
        if current_user.role == UserRole.COMPANY:
            profile = current_user.company_profile
            is_approved = bool(profile and profile.verification_status == "APPROVED")
            if not current_user.is_verified or not is_approved:
                raise ForbiddenException(
                    message="Your company account is currently pending administrative verification. Job and internship publishing is disabled until verified.",
                    error_code="COMPANY_NOT_VERIFIED",
                )

        new_job = JobPosting(
            company_id=current_user.id,
            title=request.title.strip(),
            posting_type=request.posting_type.value if hasattr(request.posting_type, "value") else request.posting_type,
            work_mode=request.work_mode.value if hasattr(request.work_mode, "value") else request.work_mode,
            location=request.location.strip(),
            description=request.description.strip(),
            requirements=request.requirements.strip(),
            skills=request.skills or [],
            compensation=request.compensation.strip(),
            duration=request.duration.strip() if request.duration else None,
            experience_level=request.experience_level.value if hasattr(request.experience_level, "value") else request.experience_level,
            category=request.category.strip(),
            deadline=request.deadline,
            status=request.status.value if hasattr(request.status, "value") else request.status,
        )

        created = self.job_repo.create(db, new_job)
        logger.info("Company User ID %d created job posting ID %d: '%s'", current_user.id, created.id, created.title)
        return self._to_job_response(created)

    def get_job_by_id(
        self, db: Session, job_id: int, current_user: Optional[User] = None
    ) -> JobPostingResponse:
        """Fetch vacancy details with status visibility checks (SKL-4 AC-4)."""
        job = self.job_repo.get_by_id(db, job_id)
        if not job:
            raise NotFoundException(
                message=f"Job posting with ID {job_id} was not found",
                error_code="JOB_NOT_FOUND",
            )

        # If not ACTIVE, visible only to authoring company recruiter or admin
        if job.status != JobStatus.ACTIVE.value:
            if not current_user or (
                current_user.id != job.company_id and current_user.role != UserRole.ADMIN
            ):
                raise NotFoundException(
                    message=f"Job posting with ID {job_id} is currently unavailable or closed",
                    error_code="JOB_NOT_AVAILABLE",
                )

        return self._to_job_response(job)

    def update_job(
        self, db: Session, job_id: int, current_user: User, request: JobPostingUpdateRequest
    ) -> JobPostingResponse:
        """Update existing job posting metadata (SKL-4 AC-3)."""
        job = self.job_repo.get_by_id(db, job_id)
        if not job:
            raise NotFoundException(
                message=f"Job posting with ID {job_id} was not found",
                error_code="JOB_NOT_FOUND",
            )

        if job.company_id != current_user.id and current_user.role != UserRole.ADMIN:
            raise ForbiddenException(
                message="You do not have permission to modify this job posting",
                error_code="JOB_ACCESS_DENIED",
            )

        if request.title is not None:
            job.title = request.title.strip()
        if request.posting_type is not None:
            job.posting_type = request.posting_type.value if hasattr(request.posting_type, "value") else request.posting_type
        if request.work_mode is not None:
            job.work_mode = request.work_mode.value if hasattr(request.work_mode, "value") else request.work_mode
        if request.location is not None:
            job.location = request.location.strip()
        if request.description is not None:
            job.description = request.description.strip()
        if request.requirements is not None:
            job.requirements = request.requirements.strip()
        if request.skills is not None:
            job.skills = request.skills
        if request.compensation is not None:
            job.compensation = request.compensation.strip()
        if request.duration is not None:
            job.duration = request.duration.strip() if request.duration else None
        if request.experience_level is not None:
            job.experience_level = request.experience_level.value if hasattr(request.experience_level, "value") else request.experience_level
        if request.category is not None:
            job.category = request.category.strip()
        if request.deadline is not None:
            job.deadline = request.deadline
        if request.status is not None:
            job.status = request.status.value if hasattr(request.status, "value") else request.status

        updated = self.job_repo.update(db, job)
        logger.info("Job ID %d updated by User ID %d", job_id, current_user.id)
        return self._to_job_response(updated)

    def delete_job(self, db: Session, job_id: int, current_user: User) -> None:
        """Remove a job posting (SKL-4 AC-5)."""
        job = self.job_repo.get_by_id(db, job_id)
        if not job:
            raise NotFoundException(
                message=f"Job posting with ID {job_id} was not found",
                error_code="JOB_NOT_FOUND",
            )

        if job.company_id != current_user.id and current_user.role != UserRole.ADMIN:
            raise ForbiddenException(
                message="You do not have permission to delete this job posting",
                error_code="JOB_ACCESS_DENIED",
            )

        self.job_repo.delete(db, job)
        logger.info("Job ID %d deleted by User ID %d", job_id, current_user.id)

    def update_job_status(
        self,
        db: Session,
        job_id: int,
        current_user: User,
        status: JobStatus,
        reason: Optional[str] = None,
        ip_address: Optional[str] = None,
    ) -> JobPostingResponse:
        """Manage vacancy lifecycle or apply administrative moderation (SKL-4 AC-3, AC-5)."""
        job = self.job_repo.get_by_id(db, job_id)
        if not job:
            raise NotFoundException(
                message=f"Job posting with ID {job_id} was not found",
                error_code="JOB_NOT_FOUND",
            )

        new_status_str = status.value if hasattr(status, "value") else status
        previous_status = job.status

        if current_user.role == UserRole.ADMIN:
            job = self.job_repo.update_status(db, job, new_status_str)
            self.audit_repo.create(
                db=db,
                admin_id=current_user.id,
                target_user_id=job.company_id,
                action="JOB_STATUS_OVERRIDE",
                details={
                    "job_id": job.id,
                    "job_title": job.title,
                    "previous_status": previous_status,
                    "new_status": new_status_str,
                    "reason": reason or "Administrative vacancy moderation",
                },
                ip_address=ip_address,
            )
            logger.info("Admin ID %d updated Job ID %d status to %s", current_user.id, job_id, new_status_str)
        elif current_user.role == UserRole.COMPANY:
            if job.company_id != current_user.id:
                raise ForbiddenException(
                    message="You do not have permission to modify the status of this job posting",
                    error_code="JOB_ACCESS_DENIED",
                )
            job = self.job_repo.update_status(db, job, new_status_str)
            logger.info("Company ID %d updated Job ID %d status to %s", current_user.id, job_id, new_status_str)
        else:
            raise ForbiddenException(
                message="You do not have permission to alter job lifecycle status",
                error_code="INSUFFICIENT_ROLE_PERMISSIONS",
            )

        return self._to_job_response(job)

    def list_jobs_paginated(
        self,
        db: Session,
        page: int = 1,
        size: int = 10,
        posting_type: Optional[str] = None,
        work_mode: Optional[str] = None,
        category: Optional[str] = None,
        experience_level: Optional[str] = None,
        location: Optional[str] = None,
        search: Optional[str] = None,
        my_jobs: bool = False,
        status: Optional[str] = None,
        current_user: Optional[User] = None,
    ) -> PaginatedJobPostingResponse:
        """Search and filter vacancies for candidate portal or company console (SKL-4 AC-4)."""
        page = max(1, page)
        size = min(100, max(1, size))

        query_company_id: Optional[int] = None
        query_status: Optional[str] = None

        if my_jobs:
            if not current_user:
                raise ForbiddenException(
                    message="Authentication required to view company vacancies",
                    error_code="AUTHENTICATION_REQUIRED",
                )
            query_company_id = current_user.id
            query_status = status
        elif current_user and current_user.role == UserRole.ADMIN and status:
            query_status = status
        else:
            # Public catalog: only ACTIVE vacancies are listed
            query_status = JobStatus.ACTIVE.value

        jobs, total = self.job_repo.get_jobs_paginated(
            db=db,
            page=page,
            size=size,
            posting_type=posting_type,
            work_mode=work_mode,
            category=category,
            experience_level=experience_level,
            location=location,
            status=query_status,
            search=search,
            company_id=query_company_id,
        )

        total_pages = math.ceil(total / size) if size > 0 else 0

        return PaginatedJobPostingResponse(
            items=[self._to_job_response(j) for j in jobs],
            total=total,
            page=page,
            size=size,
            total_pages=total_pages,
        )
