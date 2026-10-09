import json
from typing import Optional
from fastapi import APIRouter, Depends, Query, Request, UploadFile, File, Form, status
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.dependencies.auth import get_current_user, require_role
from app.models.user import User, UserRole
from app.schemas.auth import ApiResponse
from app.schemas.application import (
    ApplicationCreateRequest,
    ApplicationStatusUpdateRequest,
    JobApplicationResponse,
    PaginatedApplicationResponse,
    ApplicationCheckResponse,
)
from app.services.application_service import ApplicationService

router = APIRouter(tags=["Job Applications & Tracking (SKL-7)"])
application_service = ApplicationService()


@router.post(
    "/jobs/{job_id}/apply",
    response_model=ApiResponse[JobApplicationResponse],
    status_code=status.HTTP_201_CREATED,
    summary="Submit job application with resume & screening answers (SKL-7 AC-1, AC-2)",
)
async def apply_to_job(
    job_id: int,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ApiResponse[JobApplicationResponse]:
    content_type = request.headers.get("content-type", "")
    resume_file: Optional[UploadFile] = None
    app_request: ApplicationCreateRequest

    if "multipart/form-data" in content_type:
        form = await request.form()
        resume_file = form.get("resume_file")
        if resume_file and not hasattr(resume_file, "file"):
            resume_file = None

        cover_letter = form.get("cover_letter")
        use_profile_resume_val = form.get("use_profile_resume")
        use_profile_resume = (
            str(use_profile_resume_val).lower() in ("true", "1", "yes")
            if use_profile_resume_val is not None
            else False
        )
        resume_url = form.get("resume_url")
        resume_filename = form.get("resume_filename")

        raw_answers = form.get("screening_answers")
        screening_answers = {}
        if raw_answers:
            if isinstance(raw_answers, str):
                try:
                    screening_answers = json.loads(raw_answers)
                except Exception:
                    screening_answers = {}
            elif isinstance(raw_answers, dict):
                screening_answers = raw_answers

        app_request = ApplicationCreateRequest(
            resume_url=str(resume_url) if resume_url else None,
            resume_filename=str(resume_filename) if resume_filename else None,
            cover_letter=str(cover_letter) if cover_letter else None,
            screening_answers=screening_answers,
            use_profile_resume=use_profile_resume,
        )
    else:
        body = await request.json()
        app_request = ApplicationCreateRequest(**body)

    created = application_service.apply_for_job(
        db=db,
        current_user=current_user,
        job_id=job_id,
        request=app_request,
        resume_file=resume_file,
    )
    return ApiResponse[JobApplicationResponse](
        success=True,
        message="Application submitted successfully",
        data=created,
    )


@router.get(
    "/learners/applications",
    response_model=ApiResponse[PaginatedApplicationResponse],
    status_code=status.HTTP_200_OK,
    summary="Get candidate applications tracking list (SKL-7 AC-3)",
)
@router.get(
    "/applications/my-applications",
    response_model=ApiResponse[PaginatedApplicationResponse],
    status_code=status.HTTP_200_OK,
    include_in_schema=False,
)
def get_learner_applications(
    status: Optional[str] = Query(default=None, description="Filter by status stage"),
    page: int = Query(default=1, ge=1),
    size: int = Query(default=10, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ApiResponse[PaginatedApplicationResponse]:
    result = application_service.get_learner_applications(
        db=db,
        current_user=current_user,
        status=status,
        page=page,
        size=size,
    )
    return ApiResponse[PaginatedApplicationResponse](
        success=True,
        message="Applications retrieved successfully",
        data=result,
    )


@router.get(
    "/applications/check/{job_id}",
    response_model=ApiResponse[ApplicationCheckResponse],
    status_code=status.HTTP_200_OK,
    summary="Check if user already applied to job",
)
def check_job_application(
    job_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ApiResponse[ApplicationCheckResponse]:
    result = application_service.check_application_status(
        db=db, current_user=current_user, job_id=job_id
    )
    return ApiResponse[ApplicationCheckResponse](
        success=True,
        message="Application status checked",
        data=result,
    )


@router.get(
    "/applications/{application_id}",
    response_model=ApiResponse[JobApplicationResponse],
    status_code=status.HTTP_200_OK,
    summary="Get application details",
)
def get_application(
    application_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ApiResponse[JobApplicationResponse]:
    result = application_service.get_application_by_id(
        db=db, current_user=current_user, application_id=application_id
    )
    return ApiResponse[JobApplicationResponse](
        success=True,
        message="Application details retrieved",
        data=result,
    )


@router.delete(
    "/applications/{application_id}/withdraw",
    response_model=ApiResponse[JobApplicationResponse],
    status_code=status.HTTP_200_OK,
    summary="Candidate withdraws application (SKL-7 AC-5)",
)
@router.post(
    "/applications/{application_id}/withdraw",
    response_model=ApiResponse[JobApplicationResponse],
    status_code=status.HTTP_200_OK,
    include_in_schema=False,
)
def withdraw_application(
    application_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ApiResponse[JobApplicationResponse]:
    result = application_service.withdraw_application(
        db=db, current_user=current_user, application_id=application_id
    )
    return ApiResponse[JobApplicationResponse](
        success=True,
        message="Application withdrawn successfully",
        data=result,
    )


@router.patch(
    "/applications/{application_id}/status",
    response_model=ApiResponse[JobApplicationResponse],
    status_code=status.HTTP_200_OK,
    summary="Recruiter updates candidate application pipeline stage (SKL-7 AC-4)",
)
def update_application_status(
    application_id: int,
    request: ApplicationStatusUpdateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ApiResponse[JobApplicationResponse]:
    result = application_service.update_application_status(
        db=db,
        current_user=current_user,
        application_id=application_id,
        request=request,
    )
    return ApiResponse[JobApplicationResponse](
        success=True,
        message="Application status updated successfully",
        data=result,
    )


@router.get(
    "/jobs/{job_id}/applications",
    response_model=ApiResponse[PaginatedApplicationResponse],
    status_code=status.HTTP_200_OK,
    summary="Get all applications for a job posting (Company/Admin)",
)
def get_job_applications(
    job_id: int,
    status: Optional[str] = Query(default=None),
    page: int = Query(default=1, ge=1),
    size: int = Query(default=10, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ApiResponse[PaginatedApplicationResponse]:
    result = application_service.get_job_applications(
        db=db,
        current_user=current_user,
        job_id=job_id,
        status=status,
        page=page,
        size=size,
    )
    return ApiResponse[PaginatedApplicationResponse](
        success=True,
        message="Job applications retrieved successfully",
        data=result,
    )
