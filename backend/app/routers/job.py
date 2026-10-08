from typing import Optional
from fastapi import APIRouter, Depends, Query, Request, status
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.dependencies.auth import get_current_user, get_optional_current_user, require_role
from app.models.user import User, UserRole
from app.schemas.auth import ApiResponse
from app.schemas.job import (
    JobPostingCreateRequest,
    JobPostingUpdateRequest,
    JobPostingStatusUpdateRequest,
    JobPostingResponse,
    PaginatedJobPostingResponse,
)
from app.services.job_service import JobService

router = APIRouter(prefix="/jobs", tags=["Job & Internship Postings (Recruitment)"])
job_service = JobService()


@router.post(
    "",
    response_model=ApiResponse[JobPostingResponse],
    status_code=status.HTTP_201_CREATED,
    summary="Create a new job or internship vacancy (SKL-4 AC-1, AC-2)",
)
def create_job(
    request: JobPostingCreateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(UserRole.COMPANY, UserRole.ADMIN)),
) -> ApiResponse[JobPostingResponse]:
    """Publish a new vacancy listing. Permitted only for verified corporate companies or administrators."""
    created = job_service.create_job(db=db, current_user=current_user, request=request)
    return ApiResponse[JobPostingResponse](
        success=True,
        message="Job posting created successfully",
        data=created,
    )


@router.get(
    "",
    response_model=ApiResponse[PaginatedJobPostingResponse],
    status_code=status.HTTP_200_OK,
    summary="Explore vacancies or list company postings (SKL-4 AC-4, Jobs and internships.png)",
)
def list_jobs(
    page: int = Query(default=1, ge=1, description="Page number"),
    size: int = Query(default=10, ge=1, le=100, description="Items per page"),
    posting_type: Optional[str] = Query(default=None, description="Filter by Job or Internship"),
    work_mode: Optional[str] = Query(default=None, description="Filter by On-site, Remote, Hybrid"),
    category: Optional[str] = Query(default=None, description="Filter by domain category"),
    experience_level: Optional[str] = Query(default=None, description="Filter by seniority level"),
    location: Optional[str] = Query(default=None, description="Location search query"),
    search: Optional[str] = Query(default=None, description="Keyword search query"),
    my_jobs: bool = Query(default=False, description="Filter only postings authored by current company"),
    status_filter: Optional[str] = Query(default=None, alias="status", description="Status filter"),
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_optional_current_user),
) -> ApiResponse[PaginatedJobPostingResponse]:
    """Search and filter vacancies for candidate exploration or recruiter console."""
    result = job_service.list_jobs_paginated(
        db=db,
        page=page,
        size=size,
        posting_type=posting_type,
        work_mode=work_mode,
        category=category,
        experience_level=experience_level,
        location=location,
        search=search,
        my_jobs=my_jobs,
        status=status_filter,
        current_user=current_user,
    )
    return ApiResponse[PaginatedJobPostingResponse](
        success=True,
        message="Job postings retrieved successfully",
        data=result,
    )


@router.get(
    "/{job_id}",
    response_model=ApiResponse[JobPostingResponse],
    status_code=status.HTTP_200_OK,
    summary="Get job posting details (SKL-4)",
)
def get_job(
    job_id: int,
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_optional_current_user),
) -> ApiResponse[JobPostingResponse]:
    """Fetch complete vacancy details, requirements, and hiring company profile."""
    job = job_service.get_job_by_id(db=db, job_id=job_id, current_user=current_user)
    return ApiResponse[JobPostingResponse](
        success=True,
        message="Job posting details retrieved successfully",
        data=job,
    )


@router.put(
    "/{job_id}",
    response_model=ApiResponse[JobPostingResponse],
    status_code=status.HTTP_200_OK,
    summary="Update job posting metadata (SKL-4 AC-3)",
)
def update_job(
    job_id: int,
    request: JobPostingUpdateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ApiResponse[JobPostingResponse]:
    """Modify job posting details. Permitted only for authoring company recruiter or admin."""
    updated = job_service.update_job(
        db=db, job_id=job_id, current_user=current_user, request=request
    )
    return ApiResponse[JobPostingResponse](
        success=True,
        message="Job posting updated successfully",
        data=updated,
    )


@router.delete(
    "/{job_id}",
    response_model=ApiResponse[dict],
    status_code=status.HTTP_200_OK,
    summary="Remove a job posting (SKL-4 AC-5)",
)
def delete_job(
    job_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ApiResponse[dict]:
    """Permanently delete a vacancy. Permitted only for authoring company recruiter or admin."""
    job_service.delete_job(db=db, job_id=job_id, current_user=current_user)
    return ApiResponse[dict](
        success=True,
        message="Job posting deleted successfully",
        data={"job_id": job_id},
    )


@router.patch(
    "/{job_id}/status",
    response_model=ApiResponse[JobPostingResponse],
    status_code=status.HTTP_200_OK,
    summary="Toggle job posting lifecycle or apply admin moderation (SKL-4 AC-3, AC-5)",
)
def update_job_status(
    job_id: int,
    request_data: JobPostingStatusUpdateRequest,
    http_req: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ApiResponse[JobPostingResponse]:
    """Toggle listing status (ACTIVE / CLOSED / DRAFT) or apply administrative moderation."""
    client_ip = http_req.client.host if http_req.client else "unknown"
    updated = job_service.update_job_status(
        db=db,
        job_id=job_id,
        current_user=current_user,
        status=request_data.status,
        reason=request_data.reason,
        ip_address=client_ip,
    )
    return ApiResponse[JobPostingResponse](
        success=True,
        message=f"Job posting status updated to {request_data.status.value}",
        data=updated,
    )
