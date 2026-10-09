import logging
from typing import Optional, List
from sqlalchemy.orm import Session

from app.core.exceptions import (
    NotFoundException,
    BadRequestException,
    ForbiddenException,
)
from app.models.user import User, UserRole
from app.models.course import Course, Lesson, CourseStatus
from app.models.enrollment import CourseEnrollment, LessonProgress, EnrollmentStatus
from app.repositories.course_repository import CourseRepository
from app.repositories.enrollment_repository import EnrollmentRepository
from app.schemas.enrollment import (
    EnrollmentResponse,
    EnrollmentStatusResponse,
    LessonProgressResponse,
    CourseProgressResponse,
    EnrolledCourseItem,
    EnrolledCoursesListResponse,
)

logger = logging.getLogger(__name__)


class EnrollmentService:
    """Business logic for course enrollment and learning progress tracking (SKL-54)."""

    def __init__(
        self,
        enrollment_repo: EnrollmentRepository = EnrollmentRepository(),
        course_repo: CourseRepository = CourseRepository(),
    ):
        self.enrollment_repo = enrollment_repo
        self.course_repo = course_repo

    def enroll_course(
        self, db: Session, current_user: User, course_id: int
    ) -> EnrollmentResponse:
        course = self.course_repo.get_by_id(db, course_id)
        if not course:
            raise NotFoundException(message="Course not found", error_code="COURSE_NOT_FOUND")

        # Verify course is available for enrollment
        is_owner = course.instructor_id == current_user.id
        is_admin = current_user.role == UserRole.ADMIN
        if course.status != CourseStatus.PUBLISHED.value and not (is_owner or is_admin):
            raise BadRequestException(
                message="Course is not currently available for enrollment",
                error_code="COURSE_UNAVAILABLE",
            )

        # Prevent duplicate enrollment (AC-2)
        existing = self.enrollment_repo.get_enrollment(db, current_user.id, course_id)
        if existing:
            raise BadRequestException(
                message="Learner is already enrolled in this course",
                error_code="ALREADY_ENROLLED",
            )

        total_lessons = self.enrollment_repo.count_total_lessons_in_course(db, course_id)

        enrollment = CourseEnrollment(
            user_id=current_user.id,
            course_id=course_id,
            status=EnrollmentStatus.ACTIVE.value,
            progress_percentage=0.0,
            completed_lessons_count=0,
        )
        saved = self.enrollment_repo.create_enrollment(db, enrollment)

        instructor_name = (
            f"{course.instructor.first_name} {course.instructor.last_name}"
            if course.instructor
            else None
        )

        return EnrollmentResponse(
            id=saved.id,
            user_id=saved.user_id,
            course_id=saved.course_id,
            status=saved.status,
            progress_percentage=saved.progress_percentage,
            completed_lessons_count=saved.completed_lessons_count,
            last_accessed_lesson_id=saved.last_accessed_lesson_id,
            enrolled_at=saved.enrolled_at,
            completed_at=saved.completed_at,
            course_title=course.title,
            course_thumbnail_url=course.thumbnail_url,
            instructor_name=instructor_name,
            total_lessons=total_lessons,
        )

    def get_enrollment_status(
        self, db: Session, current_user: User, course_id: int
    ) -> EnrollmentStatusResponse:
        course = self.course_repo.get_by_id(db, course_id)
        if not course:
            raise NotFoundException(message="Course not found", error_code="COURSE_NOT_FOUND")

        enrollment = self.enrollment_repo.get_enrollment(db, current_user.id, course_id)
        if not enrollment:
            return EnrollmentStatusResponse(is_enrolled=False, enrollment=None)

        total_lessons = self.enrollment_repo.count_total_lessons_in_course(db, course_id)
        instructor_name = (
            f"{course.instructor.first_name} {course.instructor.last_name}"
            if course.instructor
            else None
        )

        return EnrollmentStatusResponse(
            is_enrolled=True,
            enrollment=EnrollmentResponse(
                id=enrollment.id,
                user_id=enrollment.user_id,
                course_id=enrollment.course_id,
                status=enrollment.status,
                progress_percentage=enrollment.progress_percentage,
                completed_lessons_count=enrollment.completed_lessons_count,
                last_accessed_lesson_id=enrollment.last_accessed_lesson_id,
                enrolled_at=enrollment.enrolled_at,
                completed_at=enrollment.completed_at,
                course_title=course.title,
                course_thumbnail_url=course.thumbnail_url,
                instructor_name=instructor_name,
                total_lessons=total_lessons,
            ),
        )

    def get_course_progress(
        self, db: Session, current_user: User, course_id: int
    ) -> CourseProgressResponse:
        course = self.course_repo.get_by_id(db, course_id)
        if not course:
            raise NotFoundException(message="Course not found", error_code="COURSE_NOT_FOUND")

        enrollment = self.enrollment_repo.get_enrollment(db, current_user.id, course_id)
        total_lessons = self.enrollment_repo.count_total_lessons_in_course(db, course_id)
        completed_ids = self.enrollment_repo.get_completed_lesson_ids_for_course(
            db, current_user.id, course_id
        )
        completed_count = len(completed_ids)
        remaining = max(0, total_lessons - completed_count)
        progress_pct = (
            round((completed_count / total_lessons) * 100.0, 1) if total_lessons > 0 else 0.0
        )

        return CourseProgressResponse(
            course_id=course.id,
            course_title=course.title,
            total_lessons=total_lessons,
            completed_lessons=completed_count,
            remaining_lessons=remaining,
            progress_percentage=progress_pct,
            completed_lesson_ids=completed_ids,
            is_enrolled=enrollment is not None,
            last_accessed_lesson_id=enrollment.last_accessed_lesson_id if enrollment else None,
            status=enrollment.status if enrollment else "UNENROLLED",
        )

    def complete_lesson(
        self, db: Session, current_user: User, lesson_id: int, is_completed: bool = True
    ) -> LessonProgressResponse:
        lesson = self.course_repo.get_lesson_by_id(db, lesson_id)
        if not lesson:
            raise NotFoundException(message="Lesson not found", error_code="LESSON_NOT_FOUND")

        course_id = lesson.course_id
        enrollment = self.enrollment_repo.get_enrollment(db, current_user.id, course_id)
        if not enrollment:
            raise ForbiddenException(
                message="You must be enrolled in the course to complete lessons",
                error_code="NOT_ENROLLED",
            )

        # Record progress for the lesson
        progress = self.enrollment_repo.set_lesson_progress(
            db=db,
            user_id=current_user.id,
            course_id=course_id,
            lesson_id=lesson_id,
            enrollment_id=enrollment.id,
            is_completed=is_completed,
        )

        # Recalculate dynamic course progress percentage
        total_lessons = self.enrollment_repo.count_total_lessons_in_course(db, course_id)
        completed_lessons = self.enrollment_repo.count_completed_lessons(
            db, current_user.id, course_id
        )
        progress_pct = (
            round((completed_lessons / total_lessons) * 100.0, 1) if total_lessons > 0 else 0.0
        )
        is_course_completed = total_lessons > 0 and completed_lessons >= total_lessons

        self.enrollment_repo.update_enrollment_progress(
            db=db,
            enrollment=enrollment,
            progress_pct=progress_pct,
            completed_count=completed_lessons,
            last_lesson_id=lesson_id,
            is_completed=is_course_completed,
        )

        return LessonProgressResponse(
            lesson_id=lesson_id,
            course_id=course_id,
            is_completed=progress.is_completed,
            completed_at=progress.completed_at,
            course_progress_percentage=progress_pct,
            completed_lessons_count=completed_lessons,
            total_lessons=total_lessons,
        )

    def get_enrolled_courses(
        self, db: Session, current_user: User, status: Optional[str] = None
    ) -> EnrolledCoursesListResponse:
        enrollments = self.enrollment_repo.get_enrolled_courses(
            db, current_user.id, status=status
        )

        items = []
        for enr in enrollments:
            crs = enr.course
            instructor_name = (
                f"{crs.instructor.first_name} {crs.instructor.last_name}"
                if crs.instructor
                else "Senior Instructor"
            )
            total = len(crs.lessons) if crs.lessons else self.enrollment_repo.count_total_lessons_in_course(db, crs.id)
            items.append(
                EnrolledCourseItem(
                    enrollment_id=enr.id,
                    course_id=crs.id,
                    title=crs.title,
                    description=crs.description,
                    category=crs.category,
                    level=crs.level,
                    thumbnail_url=crs.thumbnail_url,
                    duration_weeks=crs.duration_weeks,
                    instructor_name=instructor_name,
                    total_lessons=total,
                    completed_lessons=enr.completed_lessons_count,
                    progress_percentage=enr.progress_percentage,
                    status=enr.status,
                    enrolled_at=enr.enrolled_at,
                    completed_at=enr.completed_at,
                    last_accessed_lesson_id=enr.last_accessed_lesson_id,
                )
            )

        avg = self.enrollment_repo.get_user_average_progress(db, current_user.id)
        return EnrolledCoursesListResponse(
            items=items,
            total=len(items),
            average_progress=avg,
        )
