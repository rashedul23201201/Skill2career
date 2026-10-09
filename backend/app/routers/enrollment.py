from typing import Optional
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.dependencies.auth import get_current_user
from app.models.user import User
from app.schemas.auth import ApiResponse
from app.schemas.enrollment import (
    EnrollmentResponse,
    EnrollmentStatusResponse,
    LessonCompletionRequest,
    LessonProgressResponse,
    CourseProgressResponse,
    EnrolledCoursesListResponse,
)
from app.services.enrollment_service import EnrollmentService

router = APIRouter(tags=["Course Enrollment & Learning Progress (SKL-54)"])
enrollment_service = EnrollmentService()


@router.post(
    "/courses/{course_id}/enroll",
    response_model=ApiResponse[EnrollmentResponse],
    status_code=status.HTTP_201_CREATED,
    summary="Enroll authenticated user into a course (SKL-54 AC-1)",
)
def enroll_course(
    course_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ApiResponse[EnrollmentResponse]:
    enrollment = enrollment_service.enroll_course(
        db=db, current_user=current_user, course_id=course_id
    )
    return ApiResponse[EnrollmentResponse](
        success=True,
        message="Enrolled in course successfully",
        data=enrollment,
    )


@router.get(
    "/courses/{course_id}/enrollment-status",
    response_model=ApiResponse[EnrollmentStatusResponse],
    status_code=status.HTTP_200_OK,
    summary="Check enrollment status for a course (SKL-54)",
)
def get_enrollment_status(
    course_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ApiResponse[EnrollmentStatusResponse]:
    status_data = enrollment_service.get_enrollment_status(
        db=db, current_user=current_user, course_id=course_id
    )
    return ApiResponse[EnrollmentStatusResponse](
        success=True,
        message="Enrollment status retrieved successfully",
        data=status_data,
    )


@router.get(
    "/courses/{course_id}/progress",
    response_model=ApiResponse[CourseProgressResponse],
    status_code=status.HTTP_200_OK,
    summary="Get learning progress and completion metrics for a course (SKL-54 AC-4)",
)
def get_course_progress(
    course_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ApiResponse[CourseProgressResponse]:
    progress_data = enrollment_service.get_course_progress(
        db=db, current_user=current_user, course_id=course_id
    )
    return ApiResponse[CourseProgressResponse](
        success=True,
        message="Course progress retrieved successfully",
        data=progress_data,
    )


@router.post(
    "/lessons/{lesson_id}/complete",
    response_model=ApiResponse[LessonProgressResponse],
    status_code=status.HTTP_200_OK,
    summary="Toggle lesson completion and recalculate progress percentage (SKL-54 AC-4)",
)
def complete_lesson(
    lesson_id: int,
    request: Optional[LessonCompletionRequest] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ApiResponse[LessonProgressResponse]:
    is_completed = request.is_completed if request else True
    res = enrollment_service.complete_lesson(
        db=db,
        current_user=current_user,
        lesson_id=lesson_id,
        is_completed=is_completed,
    )
    msg = "Lesson marked as completed" if is_completed else "Lesson marked as incomplete"
    return ApiResponse[LessonProgressResponse](
        success=True,
        message=msg,
        data=res,
    )


@router.get(
    "/learners/enrolled-courses",
    response_model=ApiResponse[EnrolledCoursesListResponse],
    status_code=status.HTTP_200_OK,
    summary="Get enrolled courses for learner dashboard (SKL-54 Learners dashboard.png)",
)
@router.get(
    "/courses/enrolled",
    response_model=ApiResponse[EnrolledCoursesListResponse],
    status_code=status.HTTP_200_OK,
    include_in_schema=False,
)
def get_enrolled_courses(
    status_filter: Optional[str] = Query(default=None, alias="status"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ApiResponse[EnrolledCoursesListResponse]:
    enrolled_data = enrollment_service.get_enrolled_courses(
        db=db, current_user=current_user, status=status_filter
    )
    return ApiResponse[EnrolledCoursesListResponse](
        success=True,
        message="Enrolled courses retrieved successfully",
        data=enrolled_data,
    )
