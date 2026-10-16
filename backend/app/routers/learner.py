from typing import List, Optional
from fastapi import APIRouter, Depends, UploadFile, File, Query, status
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.dependencies.auth import require_role
from app.models.user import User, UserRole
from app.schemas.auth import ApiResponse
from app.schemas.learner import (
    LearnerProfileUpdateRequest,
    LearnerProfileResponse,
    ResumeUploadResponse,
)
from app.schemas.mock_test import TestResultResponse
from app.schemas.job import SavedJobItemResponse, RecommendedJobResponse
from app.services.learner_service import LearnerService
from app.services.mock_test_service import MockTestService
from app.services.saved_job_service import SavedJobService

router = APIRouter(prefix="/learners", tags=["Learner Profile Management"])
learner_service = LearnerService()
mock_test_service = MockTestService()
saved_job_service = SavedJobService()


@router.get(
    "/profile",
    response_model=ApiResponse[LearnerProfileResponse],
    status_code=status.HTTP_200_OK,
    summary="Get authenticated learner's complete profile with completion breakdown (SKL-51)"
)
@router.get(
    "/profile/me",
    response_model=ApiResponse[LearnerProfileResponse],
    status_code=status.HTTP_200_OK,
    include_in_schema=False
)
def get_learner_profile(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(UserRole.LEARNER, UserRole.ADMIN)),
) -> ApiResponse[LearnerProfileResponse]:
    """Retrieve own learner profile containing basic information, educational history, tagged skills, and completion breakdown."""
    profile_data = learner_service.get_profile(db=db, user=current_user)
    return ApiResponse[LearnerProfileResponse](
        success=True,
        message="Learner profile retrieved successfully",
        data=profile_data,
    )


@router.put(
    "/profile",
    response_model=ApiResponse[LearnerProfileResponse],
    status_code=status.HTTP_200_OK,
    summary="Update learner profile details and recalculate completion score (SKL-51)"
)
@router.put(
    "/profile/me",
    response_model=ApiResponse[LearnerProfileResponse],
    status_code=status.HTTP_200_OK,
    include_in_schema=False
)
def update_learner_profile(
    payload: LearnerProfileUpdateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(UserRole.LEARNER, UserRole.ADMIN)),
) -> ApiResponse[LearnerProfileResponse]:
    """Update profile fields, recalculate dynamic completion percentage, and return the updated profile."""
    updated_profile = learner_service.update_profile(
        db=db,
        user=current_user,
        payload=payload,
    )
    return ApiResponse[LearnerProfileResponse](
        success=True,
        message="Learner profile updated successfully",
        data=updated_profile,
    )


@router.post(
    "/resume",
    response_model=ApiResponse[ResumeUploadResponse],
    status_code=status.HTTP_200_OK,
    summary="Upload curriculum vitae (CV) or resume file (PDF/DOCX, max 5MB) (SKL-51)"
)
def upload_resume(
    file: UploadFile = File(..., description="Resume document in PDF or DOCX format (max 5MB)"),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(UserRole.LEARNER, UserRole.ADMIN)),
) -> ApiResponse[ResumeUploadResponse]:
    """Upload resume document with MIME inspection, size restriction, and dynamic profile completion calculation."""
    result = learner_service.upload_resume(db=db, user=current_user, file=file)
    return ApiResponse[ResumeUploadResponse](
        success=True,
        message=result.message,
        data=result,
    )


@router.get(
    "/resume/download",
    status_code=status.HTTP_200_OK,
    summary="Download or view authenticated learner's uploaded resume (SKL-51)"
)
def download_resume(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(UserRole.LEARNER, UserRole.ADMIN)),
) -> FileResponse:
    """Download the current uploaded resume document for the authenticated learner."""
    return learner_service.download_resume(db=db, user=current_user)


@router.delete(
    "/resume",
    response_model=ApiResponse[LearnerProfileResponse],
    status_code=status.HTTP_200_OK,
    summary="Delete uploaded resume and recalculate profile completion (SKL-51)"
)
def delete_resume(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(UserRole.LEARNER, UserRole.ADMIN)),
) -> ApiResponse[LearnerProfileResponse]:
    """Remove attached resume document and recalculate completion score."""
    updated_profile = learner_service.delete_resume(db=db, user=current_user)
    return ApiResponse[LearnerProfileResponse](
        success=True,
        message="Resume removed successfully",
        data=updated_profile,
    )


@router.get(
    "/test-history",
    response_model=ApiResponse[List[TestResultResponse]],
    status_code=status.HTTP_200_OK,
    summary="Get authenticated learner test history with performance analysis (SKL-58)",
)
def get_learner_test_history(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(UserRole.LEARNER, UserRole.ADMIN)),
) -> ApiResponse[List[TestResultResponse]]:
    history = mock_test_service.get_learner_test_history(db=db, current_user=current_user)
    return ApiResponse[List[TestResultResponse]](
        success=True,
        message="Learner test history retrieved successfully",
        data=history,
    )


@router.get(
    "/saved-jobs",
    response_model=ApiResponse[List[SavedJobItemResponse]],
    status_code=status.HTTP_200_OK,
    summary="Get authenticated learner's saved vacancies collection (SKL-6)",
)
def get_saved_jobs(
    status_filter: Optional[str] = Query(default=None, alias="status", description="Filter by status: active, closed, expired, or all"),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(UserRole.LEARNER, UserRole.ADMIN)),
) -> ApiResponse[List[SavedJobItemResponse]]:
    """Retrieve all bookmarked vacancies with real-time status reflection (Active, Closed, Expired)."""
    saved_jobs = saved_job_service.get_saved_jobs(
        db=db, current_user=current_user, status_filter=status_filter
    )
    return ApiResponse[List[SavedJobItemResponse]](
        success=True,
        message="Saved vacancies retrieved successfully",
        data=saved_jobs,
    )


@router.delete(
    "/saved-jobs/{id}",
    response_model=ApiResponse[dict],
    status_code=status.HTTP_200_OK,
    summary="Remove a saved vacancy by saved_job_id or job_id (SKL-6)",
)
def delete_saved_job(
    id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(UserRole.LEARNER, UserRole.ADMIN)),
) -> ApiResponse[dict]:
    """Remove a bookmarked vacancy from the learner's saved collection."""
    result = saved_job_service.delete_saved_job(
        db=db, current_user=current_user, target_id=id
    )
    return ApiResponse[dict](
        success=True,
        message=result.get("message", "Saved job removed successfully"),
        data=result,
    )


@router.get(
    "/recommended-jobs",
    response_model=ApiResponse[List[RecommendedJobResponse]],
    status_code=status.HTTP_200_OK,
    summary="Get profile-based smart vacancy recommendations (SKL-6)",
)
def get_recommended_jobs(
    limit: int = Query(default=10, ge=1, le=50, description="Max recommendations to return"),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(UserRole.LEARNER, UserRole.ADMIN)),
) -> ApiResponse[List[RecommendedJobResponse]]:
    """Smart recommendation engine matching learner profile skills & target role against active vacancies."""
    recommendations = saved_job_service.get_recommended_jobs(
        db=db, current_user=current_user, limit=limit
    )
    return ApiResponse[List[RecommendedJobResponse]](
        success=True,
        message="Personalized job recommendations retrieved successfully",
        data=recommendations,
    )


