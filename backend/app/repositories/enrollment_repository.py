from datetime import datetime, timezone
from typing import Optional, List
from sqlalchemy import select, func
from sqlalchemy.orm import Session, joinedload, selectinload
from app.models.enrollment import CourseEnrollment, LessonProgress, EnrollmentStatus
from app.models.course import Course, Lesson
from app.models.user import User


class EnrollmentRepository:
    """Repository handling database operations for course enrollments and lesson progress (SKL-54)."""

    @staticmethod
    def get_enrollment(db: Session, user_id: int, course_id: int) -> Optional[CourseEnrollment]:
        stmt = (
            select(CourseEnrollment)
            .options(
                joinedload(CourseEnrollment.course).joinedload(Course.instructor).joinedload(User.instructor_profile),
                joinedload(CourseEnrollment.last_accessed_lesson),
            )
            .where(
                CourseEnrollment.user_id == user_id,
                CourseEnrollment.course_id == course_id,
            )
        )
        return db.execute(stmt).scalar_one_or_none()

    @staticmethod
    def create_enrollment(db: Session, enrollment: CourseEnrollment) -> CourseEnrollment:
        db.add(enrollment)
        db.commit()
        db.refresh(enrollment)
        return enrollment

    @staticmethod
    def get_enrolled_courses(
        db: Session, user_id: int, status: Optional[str] = None
    ) -> List[CourseEnrollment]:
        stmt = (
            select(CourseEnrollment)
            .options(
                joinedload(CourseEnrollment.course).joinedload(Course.instructor).joinedload(User.instructor_profile),
                joinedload(CourseEnrollment.course).selectinload(Course.lessons),
                joinedload(CourseEnrollment.last_accessed_lesson),
            )
            .where(CourseEnrollment.user_id == user_id)
        )
        if status:
            stmt = stmt.where(CourseEnrollment.status == status)
        stmt = stmt.order_by(CourseEnrollment.updated_at.desc())
        return list(db.execute(stmt).scalars().all())

    @staticmethod
    def get_lesson_progress(db: Session, user_id: int, lesson_id: int) -> Optional[LessonProgress]:
        stmt = select(LessonProgress).where(
            LessonProgress.user_id == user_id,
            LessonProgress.lesson_id == lesson_id,
        )
        return db.execute(stmt).scalar_one_or_none()

    @staticmethod
    def set_lesson_progress(
        db: Session,
        user_id: int,
        course_id: int,
        lesson_id: int,
        enrollment_id: Optional[int],
        is_completed: bool = True,
    ) -> LessonProgress:
        progress = EnrollmentRepository.get_lesson_progress(db, user_id, lesson_id)
        now = datetime.now(timezone.utc)
        if progress:
            progress.is_completed = is_completed
            progress.completed_at = now if is_completed else None
            progress.updated_at = now
        else:
            progress = LessonProgress(
                user_id=user_id,
                course_id=course_id,
                lesson_id=lesson_id,
                enrollment_id=enrollment_id,
                is_completed=is_completed,
                completed_at=now if is_completed else None,
            )
            db.add(progress)
        db.commit()
        db.refresh(progress)
        return progress

    @staticmethod
    def get_completed_lesson_ids_for_course(
        db: Session, user_id: int, course_id: int
    ) -> List[int]:
        stmt = select(LessonProgress.lesson_id).where(
            LessonProgress.user_id == user_id,
            LessonProgress.course_id == course_id,
            LessonProgress.is_completed.is_(True),
        )
        return list(db.execute(stmt).scalars().all())

    @staticmethod
    def count_total_lessons_in_course(db: Session, course_id: int) -> int:
        stmt = select(func.count(Lesson.id)).where(Lesson.course_id == course_id)
        return db.execute(stmt).scalar() or 0

    @staticmethod
    def count_completed_lessons(db: Session, user_id: int, course_id: int) -> int:
        stmt = select(func.count(LessonProgress.id)).where(
            LessonProgress.user_id == user_id,
            LessonProgress.course_id == course_id,
            LessonProgress.is_completed.is_(True),
        )
        return db.execute(stmt).scalar() or 0

    @staticmethod
    def update_enrollment_progress(
        db: Session,
        enrollment: CourseEnrollment,
        progress_pct: float,
        completed_count: int,
        last_lesson_id: Optional[int] = None,
        is_completed: bool = False,
    ) -> CourseEnrollment:
        enrollment.progress_percentage = progress_pct
        enrollment.completed_lessons_count = completed_count
        if last_lesson_id:
            enrollment.last_accessed_lesson_id = last_lesson_id
        if is_completed:
            enrollment.status = EnrollmentStatus.COMPLETED.value
            enrollment.completed_at = datetime.now(timezone.utc)
        else:
            enrollment.status = EnrollmentStatus.ACTIVE.value
            enrollment.completed_at = None
        db.commit()
        db.refresh(enrollment)
        return enrollment

    @staticmethod
    def count_user_enrollments(db: Session, user_id: int) -> int:
        stmt = select(func.count(CourseEnrollment.id)).where(CourseEnrollment.user_id == user_id)
        return db.execute(stmt).scalar() or 0

    @staticmethod
    def get_user_average_progress(db: Session, user_id: int) -> float:
        stmt = select(func.avg(CourseEnrollment.progress_percentage)).where(
            CourseEnrollment.user_id == user_id
        )
        avg_val = db.execute(stmt).scalar()
        return round(float(avg_val), 1) if avg_val is not None else 0.0
