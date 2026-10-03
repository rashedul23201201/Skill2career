from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.dependencies.auth import get_current_user
from app.models.user import User
from app.schemas.auth import ApiResponse
from app.schemas.instructor import (
    InstructorApplicationRequest,
    InstructorProfileUpdateRequest,
    InstructorProfileResponse,
    InstructorDashboardStats,
)
from app.services.instructor_service import InstructorService

router = APIRouter(prefix="/instructors", tags=["Instructor Management"])
instructor_service = InstructorService()


@router.post(
    "/apply",
    response_model=ApiResponse[InstructorProfileResponse],
    status_code=status.HTTP_201_CREATED,
    summary="Submit instructor onboarding application (SKL-52)"
)
def apply_as_instructor(
    payload: InstructorApplicationRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ApiResponse[InstructorProfileResponse]:
    """Submit credentials, academic qualification, and domain expertise to apply for an Instructor account."""
    profile = instructor_service.apply_as_instructor(db, current_user, payload)
    return ApiResponse[InstructorProfileResponse](
        success=True,
        message="Instructor application submitted successfully and is pending administrative review.",
        data=profile
    )


@router.get(
    "/profile",
    response_model=ApiResponse[InstructorProfileResponse],
    status_code=status.HTTP_200_OK,
    summary="Get current user's instructor profile (SKL-52)"
)
def get_instructor_profile(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ApiResponse[InstructorProfileResponse]:
    """Retrieve instructor profile, credentials, and verification status."""
    profile = instructor_service.get_profile(db, current_user)
    return ApiResponse[InstructorProfileResponse](
        success=True,
        message="Instructor profile retrieved successfully",
        data=profile
    )


@router.put(
    "/profile",
    response_model=ApiResponse[InstructorProfileResponse],
    status_code=status.HTTP_200_OK,
    summary="Update current instructor profile (SKL-52)"
)
def update_instructor_profile(
    payload: InstructorProfileUpdateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ApiResponse[InstructorProfileResponse]:
    """Update qualification, expertise domain, bio, and social links."""
    profile = instructor_service.update_profile(db, current_user, payload)
    return ApiResponse[InstructorProfileResponse](
        success=True,
        message="Instructor profile updated successfully",
        data=profile
    )


@router.get(
    "/dashboard-stats",
    response_model=ApiResponse[InstructorDashboardStats],
    status_code=status.HTTP_200_OK,
    summary="Get instructor dashboard telemetry and status (SKL-52)"
)
def get_instructor_dashboard_stats(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ApiResponse[InstructorDashboardStats]:
    """Retrieve instructor metrics: active courses, total learners, mock tests, and status."""
    stats_data = instructor_service.get_dashboard_stats(db, current_user)
    return ApiResponse[InstructorDashboardStats](
        success=True,
        message="Instructor dashboard telemetry retrieved successfully",
        data=stats_data
    )
