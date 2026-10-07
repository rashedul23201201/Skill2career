import logging
import math
from typing import Optional, List, Dict, Any
from sqlalchemy.orm import Session

from app.core.exceptions import (
    NotFoundException,
    ForbiddenException,
    BadRequestException,
)
from app.models.user import User, UserRole
from app.models.course import Course, CourseModule, Lesson, CourseStatus, CourseLevel
from app.repositories.course_repository import CourseRepository
from app.repositories.audit_log_repository import AuditLogRepository
from app.schemas.course import (
    CourseCreateRequest,
    CourseUpdateRequest,
    CourseResponse,
    CourseDetailResponse,
    CourseModuleSchema,
    LessonSchema,
    CurriculumSyncRequest,
    PaginatedCourseResponse,
)

logger = logging.getLogger(__name__)


class CourseService:
    """Service handling LMS course authoring, discovery, curriculum hierarchies, and administration (SKL-53)."""

    def __init__(
        self,
        course_repo: CourseRepository = CourseRepository(),
        audit_repo: AuditLogRepository = AuditLogRepository(),
    ):
        self.course_repo = course_repo
        self.audit_repo = audit_repo

    def _to_course_response(self, course: Course) -> CourseResponse:
        """Helper to transform Course ORM into standard CourseResponse."""
        instructor_name = "Instructor"
        instructor_designation = "Course Instructor"
        if course.instructor:
            instructor_name = f"{course.instructor.first_name} {course.instructor.last_name}".strip()
            if hasattr(course.instructor, "instructor_profile") and course.instructor.instructor_profile:
                instructor_designation = course.instructor.instructor_profile.designation or course.instructor.instructor_profile.qualification or "Instructor"

        lessons_count = len(course.lessons) if course.lessons else 0
        modules_count = len(course.modules) if course.modules else 0

        return CourseResponse(
            id=course.id,
            instructor_id=course.instructor_id,
            instructor_name=instructor_name,
            instructor_designation=instructor_designation,
            title=course.title,
            description=course.description,
            category=course.category,
            level=course.level,
            price=course.price,
            is_free=course.is_free,
            status=course.status,
            thumbnail_url=course.thumbnail_url,
            duration_weeks=course.duration_weeks,
            lessons_count=lessons_count,
            modules_count=modules_count,
            created_at=course.created_at,
            updated_at=course.updated_at,
        )

    def _to_course_detail_response(self, course: Course) -> CourseDetailResponse:
        """Helper to transform Course ORM into CourseDetailResponse with full curriculum tree."""
        base_res = self._to_course_response(course)
        
        # Serialize modules and nested lessons
        modules_list: List[CourseModuleSchema] = []
        for mod in (course.modules or []):
            mod_lessons = [
                LessonSchema.model_validate(les) for les in (mod.lessons or [])
            ]
            modules_list.append(
                CourseModuleSchema(
                    id=mod.id,
                    course_id=mod.course_id,
                    title=mod.title,
                    order_index=mod.order_index,
                    lessons=mod_lessons,
                    created_at=mod.created_at,
                    updated_at=mod.updated_at,
                )
            )

        all_lessons = [
            LessonSchema.model_validate(les) for les in (course.lessons or [])
        ]

        return CourseDetailResponse(
            **base_res.model_dump(),
            modules=modules_list,
            lessons=all_lessons,
        )

    def create_course(self, db: Session, current_user: User, request: CourseCreateRequest) -> CourseDetailResponse:
        """Author a new course with instructor ownership (SKL-53 AC-1)."""
        if current_user.role not in [UserRole.INSTRUCTOR, UserRole.ADMIN]:
            raise ForbiddenException(
                message="Only approved instructors or administrators can create courses",
                error_code="INSUFFICIENT_COURSE_PERMISSIONS",
            )

        new_course = Course(
            instructor_id=current_user.id,
            title=request.title.strip(),
            description=request.description.strip(),
            category=request.category.strip(),
            level=request.level.value if hasattr(request.level, "value") else request.level,
            price=request.price,
            is_free=request.is_free,
            status=request.status.value if hasattr(request.status, "value") else request.status,
            thumbnail_url=request.thumbnail_url,
            duration_weeks=request.duration_weeks,
        )
        created = self.course_repo.create(db, new_course)

        # Create initial default module and lesson for immediate curriculum building experience
        default_module = self.course_repo.add_module(
            db, course_id=created.id, title="Module 1: Getting Started", order_index=0
        )
        self.course_repo.add_lesson(
            db,
            course_id=created.id,
            module_id=default_module.id,
            title="Introduction to Course",
            content_type="video",
            duration_minutes=15,
            order_index=0,
        )

        db.refresh(created)
        logger.info("User ID %d created new course ID %d: '%s'", current_user.id, created.id, created.title)
        return self._to_course_detail_response(created)

    def get_course_by_id(self, db: Session, course_id: int, current_user: Optional[User] = None) -> CourseDetailResponse:
        """Fetch course details with syllabus and security checks for drafts (SKL-53)."""
        course = self.course_repo.get_by_id(db, course_id)
        if not course:
            raise NotFoundException(
                message=f"Course with ID {course_id} was not found",
                error_code="COURSE_NOT_FOUND",
            )

        # If not published, only the authoring instructor or platform admin can view it
        if course.status != CourseStatus.PUBLISHED.value:
            if not current_user or (
                current_user.id != course.instructor_id and current_user.role != UserRole.ADMIN
            ):
                raise NotFoundException(
                    message=f"Course with ID {course_id} is currently unavailable or unpublished",
                    error_code="COURSE_NOT_AVAILABLE",
                )

        return self._to_course_detail_response(course)

    def update_course(
        self, db: Session, course_id: int, current_user: User, request: CourseUpdateRequest
    ) -> CourseDetailResponse:
        """Update existing course metadata (SKL-53 AC-2)."""
        course = self.course_repo.get_by_id(db, course_id)
        if not course:
            raise NotFoundException(
                message=f"Course with ID {course_id} was not found",
                error_code="COURSE_NOT_FOUND",
            )

        # Guard: ownership check
        if course.instructor_id != current_user.id and current_user.role != UserRole.ADMIN:
            raise ForbiddenException(
                message="You do not have permission to modify this course",
                error_code="COURSE_ACCESS_DENIED",
            )

        if request.title is not None:
            course.title = request.title.strip()
        if request.description is not None:
            course.description = request.description.strip()
        if request.category is not None:
            course.category = request.category.strip()
        if request.level is not None:
            course.level = request.level.value if hasattr(request.level, "value") else request.level
        if request.price is not None:
            course.price = request.price
        if request.is_free is not None:
            course.is_free = request.is_free
        if request.duration_weeks is not None:
            course.duration_weeks = request.duration_weeks
        if request.thumbnail_url is not None:
            course.thumbnail_url = request.thumbnail_url
        if request.status is not None:
            course.status = request.status.value if hasattr(request.status, "value") else request.status

        updated = self.course_repo.update(db, course)
        logger.info("Course ID %d updated by User ID %d", course_id, current_user.id)
        return self._to_course_detail_response(updated)

    def delete_course(self, db: Session, course_id: int, current_user: User) -> None:
        """Remove a course and all associated lessons (SKL-53 AC-5)."""
        course = self.course_repo.get_by_id(db, course_id)
        if not course:
            raise NotFoundException(
                message=f"Course with ID {course_id} was not found",
                error_code="COURSE_NOT_FOUND",
            )

        # Guard: ownership check
        if course.instructor_id != current_user.id and current_user.role != UserRole.ADMIN:
            raise ForbiddenException(
                message="You do not have permission to delete this course",
                error_code="COURSE_ACCESS_DENIED",
            )

        self.course_repo.delete(db, course)
        logger.info("Course ID %d deleted by User ID %d", course_id, current_user.id)

    def update_course_status(
        self,
        db: Session,
        course_id: int,
        current_user: User,
        status: CourseStatus,
        reason: Optional[str] = None,
        ip_address: Optional[str] = None,
    ) -> CourseDetailResponse:
        """Publish, unpublish, or administratively moderate a course (SKL-53 AC-5)."""
        course = self.course_repo.get_by_id(db, course_id)
        if not course:
            raise NotFoundException(
                message=f"Course with ID {course_id} was not found",
                error_code="COURSE_NOT_FOUND",
            )

        new_status_str = status.value if hasattr(status, "value") else status
        previous_status = course.status

        # Permission logic
        if current_user.role == UserRole.ADMIN:
            # Admin oversight: unpublish / moderate policy-violating course
            course = self.course_repo.update_status(db, course, new_status_str)
            self.audit_repo.create(
                db=db,
                admin_id=current_user.id,
                target_user_id=course.instructor_id,
                action="COURSE_STATUS_OVERRIDE",
                details={
                    "course_id": course.id,
                    "course_title": course.title,
                    "previous_status": previous_status,
                    "new_status": new_status_str,
                    "reason": reason or "Administrative content moderation",
                },
                ip_address=ip_address,
            )
            logger.info("Admin ID %d updated Course ID %d status to %s", current_user.id, course_id, new_status_str)
        elif current_user.role == UserRole.INSTRUCTOR:
            if course.instructor_id != current_user.id:
                raise ForbiddenException(
                    message="You do not have permission to modify the status of this course",
                    error_code="COURSE_ACCESS_DENIED",
                )
            course = self.course_repo.update_status(db, course, new_status_str)
            logger.info("Instructor ID %d updated Course ID %d status to %s", current_user.id, course_id, new_status_str)
        else:
            raise ForbiddenException(
                message="You do not have permission to alter course lifecycle status",
                error_code="INSUFFICIENT_COURSE_PERMISSIONS",
            )

        return self._to_course_detail_response(course)

    def list_courses_paginated(
        self,
        db: Session,
        page: int = 1,
        size: int = 12,
        category: Optional[str] = None,
        level: Optional[str] = None,
        search: Optional[str] = None,
        my_courses: bool = False,
        status: Optional[str] = None,
        current_user: Optional[User] = None,
    ) -> PaginatedCourseResponse:
        """Retrieve paginated courses for public catalog, instructor portal, or admin governance (Courses.png)."""
        page = max(1, page)
        size = min(100, max(1, size))

        query_instructor_id: Optional[int] = None
        query_status: Optional[str] = None

        if my_courses:
            if not current_user:
                raise ForbiddenException(
                    message="Authentication required to view authored courses",
                    error_code="AUTHENTICATION_REQUIRED",
                )
            query_instructor_id = current_user.id
            query_status = status  # May be None to see all statuses of their own courses
        elif current_user and current_user.role == UserRole.ADMIN:
            query_status = status  # Admin can filter by status or see all
        else:
            # Public catalog: only PUBLISHED courses are visible
            query_status = CourseStatus.PUBLISHED.value

        courses, total = self.course_repo.get_courses_paginated(
            db=db,
            page=page,
            size=size,
            category=category,
            level=level,
            status=query_status,
            search=search,
            instructor_id=query_instructor_id,
        )

        total_pages = math.ceil(total / size) if size > 0 else 0

        return PaginatedCourseResponse(
            items=[self._to_course_response(c) for c in courses],
            total=total,
            page=page,
            size=size,
            total_pages=total_pages,
        )

    def sync_curriculum(
        self, db: Session, course_id: int, current_user: User, request: CurriculumSyncRequest
    ) -> CourseDetailResponse:
        """Batch save and synchronize entire curriculum tree for Curriculum Builder (Course Management.png)."""
        course = self.course_repo.get_by_id(db, course_id)
        if not course:
            raise NotFoundException(
                message=f"Course with ID {course_id} was not found",
                error_code="COURSE_NOT_FOUND",
            )

        if course.instructor_id != current_user.id and current_user.role != UserRole.ADMIN:
            raise ForbiddenException(
                message="You do not have permission to edit this curriculum",
                error_code="COURSE_ACCESS_DENIED",
            )

        modules_data = [m.model_dump() for m in request.modules]
        updated_course = self.course_repo.sync_curriculum(db, course, modules_data)
        return self._to_course_detail_response(updated_course)
