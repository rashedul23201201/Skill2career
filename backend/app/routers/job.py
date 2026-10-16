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
    JobTaxonomiesResponse,
    SavedJobToggleResponse,
)
from app.services.job_service import JobService
from app.services.saved_job_service import SavedJobService

router = APIRouter(prefix="/jobs", tags=["Job & Internship Postings (Recruitment)"])
job_service = JobService()
saved_job_service = SavedJobService()


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
    "/search",
    response_model=ApiResponse[PaginatedJobPostingResponse],
    status_code=status.HTTP_200_OK,
    summary="Search vacancies with full-text indexing, multi-attribute filters, and sorting (SKL-5)",
)
def search_jobs(
    page: int = Query(default=1, ge=1, description="Page number"),
    size: int = Query(default=8, ge=1, le=100, description="Items per page"),
    search: Optional[str] = Query(default=None, description="Keyword search query across title, description, requirements, location, company"),
    posting_type: Optional[str] = Query(default=None, description="Filter by Job or Internship"),
    work_mode: Optional[str] = Query(default=None, description="Filter by On-site, Remote, Hybrid"),
    category: Optional[str] = Query(default=None, description="Filter by category"),
    experience_level: Optional[str] = Query(default=None, description="Filter by seniority level"),
    location: Optional[str] = Query(default=None, description="Filter by location"),
    min_salary: Optional[int] = Query(default=None, ge=0, description="Minimum salary bracket in BDT"),
    max_salary: Optional[int] = Query(default=None, ge=0, description="Maximum salary bracket in BDT"),
    sort_by: Optional[str] = Query(default="recent", description="Sort order: recent, salary_high, deadline"),
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_optional_current_user),
) -> ApiResponse[PaginatedJobPostingResponse]:
    """Search active vacancies from verified corporate companies with debounce support and dynamic sorting (SKL-5)."""
    result = job_service.search_jobs(
        db=db,
        page=page,
        size=size,
        search=search,
        posting_type=posting_type,
        work_mode=work_mode,
        category=category,
        experience_level=experience_level,
        location=location,
        min_salary=min_salary,
        max_salary=max_salary,
        sort_by=sort_by,
        current_user=current_user,
    )
    return ApiResponse[PaginatedJobPostingResponse](
        success=True,
        message="Search results retrieved successfully",
        data=result,
    )


@router.get(
    "/taxonomies",
    response_model=ApiResponse[JobTaxonomiesResponse],
    status_code=status.HTTP_200_OK,
    summary="Fetch filter facets and taxonomies for vacancy search (SKL-5)",
)
def get_taxonomies(
    db: Session = Depends(get_db),
) -> ApiResponse[JobTaxonomiesResponse]:
    """Return available search facets, categories, work modes, and salary bands (SKL-5)."""
    taxonomies = job_service.get_taxonomies(db=db)
    return ApiResponse[JobTaxonomiesResponse](
        success=True,
        message="Job taxonomies retrieved successfully",
        data=JobTaxonomiesResponse(**taxonomies),
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


@router.post(
    "/{job_id}/save",
    response_model=ApiResponse[SavedJobToggleResponse],
    status_code=status.HTTP_200_OK,
    summary="1-click save, unsave, or toggle vacancy bookmark (SKL-6)",
)
def save_job(
    job_id: int,
    action: Optional[str] = Query(default=None, description="Explicit action: 'save', 'unsave', or None for toggle"),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(UserRole.LEARNER, UserRole.ADMIN)),
) -> ApiResponse[SavedJobToggleResponse]:
    """1-click save / bookmark or unsave a job posting for the authenticated learner (SKL-6)."""
    result = saved_job_service.toggle_save_job(
        db=db, job_id=job_id, current_user=current_user, action=action
    )
    return ApiResponse[SavedJobToggleResponse](
        success=True,
        message=result.message,
        data=result,
    )


@router.delete(
    "/{job_id}/save",
    response_model=ApiResponse[SavedJobToggleResponse],
    status_code=status.HTTP_200_OK,
    summary="Remove vacancy from saved list (SKL-6)",
)
def unsave_job(
    job_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(UserRole.LEARNER, UserRole.ADMIN)),
) -> ApiResponse[SavedJobToggleResponse]:
    """Explicitly remove a vacancy from the authenticated learner's saved list (SKL-6)."""
    result = saved_job_service.toggle_save_job(
        db=db, job_id=job_id, current_user=current_user, action="unsave"
    )
    return ApiResponse[SavedJobToggleResponse](
        success=True,
        message=result.message,
        data=result,
    )

