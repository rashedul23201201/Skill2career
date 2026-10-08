from typing import Optional, List
from fastapi import APIRouter, Depends, Query, Request, status, UploadFile, File
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.dependencies.auth import get_current_user, get_optional_current_user, require_role
from app.models.user import User, UserRole
from app.schemas.auth import ApiResponse
from app.schemas.course import (
    CourseCreateRequest,
    CourseUpdateRequest,
    CourseStatusUpdateRequest,
    CourseResponse,
    CourseDetailResponse,
    CurriculumSyncRequest,
    PaginatedCourseResponse,
    LessonCreateRequest,
    LessonUpdateRequest,
    LessonSchema,
    StudyMaterialUploadResponse,
    CourseModuleCreateRequest,
    CourseModuleUpdateRequest,
    CourseModuleSchema,
)
from app.services.course_service import CourseService

router = APIRouter(prefix="/courses", tags=["Course Management (LMS)"])
course_service = CourseService()


@router.post(
    "",
    response_model=ApiResponse[CourseDetailResponse],
    status_code=status.HTTP_201_CREATED,
    summary="Create a new course (SKL-53 AC-1)",
)
def create_course(
    request: CourseCreateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(UserRole.INSTRUCTOR, UserRole.ADMIN)),
) -> ApiResponse[CourseDetailResponse]:
    """Author a new course curriculum container. Only Instructors and Admins are permitted."""
    created = course_service.create_course(db=db, current_user=current_user, request=request)
    return ApiResponse[CourseDetailResponse](
        success=True,
        message="Course created successfully",
        data=created,
    )


@router.get(
    "",
    response_model=ApiResponse[PaginatedCourseResponse],
    status_code=status.HTTP_200_OK,
    summary="Explore courses or list instructor courses (SKL-53 Courses.png)",
)
def list_courses(
    page: int = Query(default=1, ge=1, description="Page number"),
    size: int = Query(default=12, ge=1, le=100, description="Items per page"),
    category: Optional[str] = Query(default=None, description="Domain category filter"),
    level: Optional[str] = Query(default=None, description="Proficiency level filter"),
    search: Optional[str] = Query(default=None, description="Search term for course title or summary"),
    my_courses: bool = Query(default=False, description="Filter only courses authored by current user"),
    status_filter: Optional[str] = Query(default=None, alias="status", description="Filter by status (Admin/Instructor only)"),
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_optional_current_user),
) -> ApiResponse[PaginatedCourseResponse]:
    """Retrieve paginated courses for public exploration catalog or instructor dashboard."""
    result = course_service.list_courses_paginated(
        db=db,
        page=page,
        size=size,
        category=category,
        level=level,
        search=search,
        my_courses=my_courses,
        status=status_filter,
        current_user=current_user,
    )
    return ApiResponse[PaginatedCourseResponse](
        success=True,
        message="Courses retrieved successfully",
        data=result,
    )


@router.get(
    "/{course_id}",
    response_model=ApiResponse[CourseDetailResponse],
    status_code=status.HTTP_200_OK,
    summary="Get course details and curriculum outline (SKL-53)",
)
def get_course(
    course_id: int,
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_optional_current_user),
) -> ApiResponse[CourseDetailResponse]:
    """Fetch complete course details, syllabus modules, and lesson outline."""
    course = course_service.get_course_by_id(db=db, course_id=course_id, current_user=current_user)
    return ApiResponse[CourseDetailResponse](
        success=True,
        message="Course details retrieved successfully",
        data=course,
    )


@router.put(
    "/{course_id}",
    response_model=ApiResponse[CourseDetailResponse],
    status_code=status.HTTP_200_OK,
    summary="Update course metadata (SKL-53 AC-2)",
)
def update_course(
    course_id: int,
    request: CourseUpdateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ApiResponse[CourseDetailResponse]:
    """Modify course details. Permitted only for authoring instructor or admin."""
    updated = course_service.update_course(
        db=db, course_id=course_id, current_user=current_user, request=request
    )
    return ApiResponse[CourseDetailResponse](
        success=True,
        message="Course updated successfully",
        data=updated,
    )


@router.delete(
    "/{course_id}",
    response_model=ApiResponse[dict],
    status_code=status.HTTP_200_OK,
    summary="Remove a course (SKL-53 AC-5)",
)
def delete_course(
    course_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ApiResponse[dict]:
    """Delete a course and all child lessons. Permitted only for authoring instructor or admin."""
    course_service.delete_course(db=db, course_id=course_id, current_user=current_user)
    return ApiResponse[dict](
        success=True,
        message="Course deleted successfully",
        data={"course_id": course_id},
    )


@router.patch(
    "/{course_id}/status",
    response_model=ApiResponse[CourseDetailResponse],
    status_code=status.HTTP_200_OK,
    summary="Publish, unpublish, or administratively moderate course status (SKL-53 AC-5)",
)
def update_course_status(
    course_id: int,
    request_data: CourseStatusUpdateRequest,
    http_req: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ApiResponse[CourseDetailResponse]:
    """Toggle course publication status or apply administrative moderation."""
    client_ip = http_req.client.host if http_req.client else "unknown"
    updated = course_service.update_course_status(
        db=db,
        course_id=course_id,
        current_user=current_user,
        status=request_data.status,
        reason=request_data.reason,
        ip_address=client_ip,
    )
    return ApiResponse[CourseDetailResponse](
        success=True,
        message=f"Course status updated to {request_data.status.value}",
        data=updated,
    )


@router.put(
    "/{course_id}/curriculum",
    response_model=ApiResponse[CourseDetailResponse],
    status_code=status.HTTP_200_OK,
    summary="Save entire curriculum outline with modules and lessons (Course Management.png)",
)
def sync_curriculum(
    course_id: int,
    curriculum: CurriculumSyncRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ApiResponse[CourseDetailResponse]:
    """Save modules and lesson tree for Curriculum Builder."""
    updated = course_service.sync_curriculum(
        db=db, course_id=course_id, current_user=current_user, request=curriculum
    )
    return ApiResponse[CourseDetailResponse](
        success=True,
        message="Curriculum synchronized successfully",
        data=updated,
    )


@router.post(
    "/{course_id}/lessons",
    response_model=ApiResponse[LessonSchema],
    status_code=status.HTTP_201_CREATED,
    summary="Create a new lesson in a course (SKL-55 AC-1)",
)
def create_lesson(
    course_id: int,
    request: LessonCreateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ApiResponse[LessonSchema]:
    """Create a new lesson and attach study material to a course. Permitted only for authoring instructor or admin."""
    created = course_service.create_lesson(
        db=db, course_id=course_id, current_user=current_user, request=request
    )
    return ApiResponse[LessonSchema](
        success=True,
        message="Lesson created successfully",
        data=created,
    )


@router.get(
    "/{course_id}/lessons",
    response_model=ApiResponse[List[LessonSchema]],
    status_code=status.HTTP_200_OK,
    summary="List all lessons for an available course (SKL-55 AC-3)",
)
def list_lessons(
    course_id: int,
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_optional_current_user),
) -> ApiResponse[List[LessonSchema]]:
    """Retrieve all lessons and study materials for an available course."""
    lessons = course_service.get_lessons_for_course(
        db=db, course_id=course_id, current_user=current_user
    )
    return ApiResponse[List[LessonSchema]](
        success=True,
        message="Lessons retrieved successfully",
        data=lessons,
    )


@router.get(
    "/{course_id}/lessons/{lesson_id}",
    response_model=ApiResponse[LessonSchema],
    status_code=status.HTTP_200_OK,
    summary="Get lesson details and study materials (SKL-55 AC-3)",
)
def get_course_lesson(
    course_id: int,
    lesson_id: int,
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_optional_current_user),
) -> ApiResponse[LessonSchema]:
    """Retrieve single lesson details with video link and study material attachments."""
    lesson = course_service.get_lesson_by_id(
        db=db, lesson_id=lesson_id, current_user=current_user
    )
    return ApiResponse[LessonSchema](
        success=True,
        message="Lesson retrieved successfully",
        data=lesson,
    )


@router.put(
    "/{course_id}/lessons/{lesson_id}",
    response_model=ApiResponse[LessonSchema],
    status_code=status.HTTP_200_OK,
    summary="Update lesson details and materials (SKL-55 AC-2)",
)
def update_course_lesson(
    course_id: int,
    lesson_id: int,
    request: LessonUpdateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ApiResponse[LessonSchema]:
    """Update lesson metadata, video URL, or study material attachments."""
    updated = course_service.update_lesson(
        db=db, lesson_id=lesson_id, current_user=current_user, request=request
    )
    return ApiResponse[LessonSchema](
        success=True,
        message="Lesson updated successfully",
        data=updated,
    )


@router.delete(
    "/{course_id}/lessons/{lesson_id}",
    response_model=ApiResponse[dict],
    status_code=status.HTTP_200_OK,
    summary="Delete a lesson (SKL-55 AC-5)",
)
def delete_course_lesson(
    course_id: int,
    lesson_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ApiResponse[dict]:
    """Delete a lesson. Permitted only for authoring instructor or admin."""
    result = course_service.delete_lesson(
        db=db, lesson_id=lesson_id, current_user=current_user
    )
    return ApiResponse[dict](
        success=True,
        message="Lesson deleted successfully",
        data=result,
    )


@router.post(
    "/{course_id}/lessons/{lesson_id}/materials",
    response_model=ApiResponse[StudyMaterialUploadResponse],
    status_code=status.HTTP_201_CREATED,
    summary="Upload study material document to a lesson (SKL-55 AC-2)",
)
def upload_course_lesson_material(
    course_id: int,
    lesson_id: int,
    file: UploadFile = File(..., description="Study material file (PDF, DOCX, PPTX, TXT, ZIP, max 25MB)"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ApiResponse[StudyMaterialUploadResponse]:
    """Upload and attach study material document (e.g. PDF lecture notes) to a lesson."""
    result = course_service.upload_lesson_material(
        db=db, lesson_id=lesson_id, current_user=current_user, file=file
    )
    return ApiResponse[StudyMaterialUploadResponse](
        success=True,
        message=result.message,
        data=result,
    )


@router.post(
    "/{course_id}/modules",
    response_model=ApiResponse[CourseModuleSchema],
    status_code=status.HTTP_201_CREATED,
    summary="Create a new module in a course",
)
def create_module(
    course_id: int,
    request: CourseModuleCreateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ApiResponse[CourseModuleSchema]:
    """Add a new module to group lessons within a course."""
    created = course_service.create_module(
        db=db, course_id=course_id, current_user=current_user, request=request
    )
    return ApiResponse[CourseModuleSchema](
        success=True,
        message="Module created successfully",
        data=created,
    )


@router.put(
    "/modules/{module_id}",
    response_model=ApiResponse[CourseModuleSchema],
    status_code=status.HTTP_200_OK,
    summary="Update module title or ordering",
)
def update_module(
    module_id: int,
    request: CourseModuleUpdateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ApiResponse[CourseModuleSchema]:
    """Update curriculum module title or ordering."""
    updated = course_service.update_module(
        db=db, module_id=module_id, current_user=current_user, request=request
    )
    return ApiResponse[CourseModuleSchema](
        success=True,
        message="Module updated successfully",
        data=updated,
    )


@router.delete(
    "/modules/{module_id}",
    response_model=ApiResponse[dict],
    status_code=status.HTTP_200_OK,
    summary="Delete a curriculum module",
)
def delete_module(
    module_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ApiResponse[dict]:
    """Delete a curriculum module and its contents."""
    result = course_service.delete_module(
        db=db, module_id=module_id, current_user=current_user
    )
    return ApiResponse[dict](
        success=True,
        message="Module deleted successfully",
        data=result,
    )

