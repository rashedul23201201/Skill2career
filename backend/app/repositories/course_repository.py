import logging
from typing import Optional, List, Tuple, Dict, Any
from sqlalchemy import select, func, or_
from sqlalchemy.orm import Session, joinedload, selectinload
from app.models.course import Course, CourseModule, Lesson, CourseStatus
from app.models.user import User

logger = logging.getLogger(__name__)


class CourseRepository:
    """Repository managing persistence for Course, CourseModule, and Lesson entities (SKL-53)."""

    @staticmethod
    def create(db: Session, course: Course) -> Course:
        """Persist a new course to the database."""
        db.add(course)
        db.commit()
        db.refresh(course)
        return course

    @staticmethod
    def get_by_id(db: Session, course_id: int) -> Optional[Course]:
        """Fetch course by ID with instructor relationship."""
        stmt = (
            select(Course)
            .options(
                joinedload(Course.instructor).joinedload(User.instructor_profile),
                selectinload(Course.modules).selectinload(CourseModule.lessons),
                selectinload(Course.lessons),
            )
            .where(Course.id == course_id)
        )
        return db.execute(stmt).scalar_one_or_none()

    @staticmethod
    def update(db: Session, course: Course) -> Course:
        """Commit changes to an existing course."""
        db.commit()
        db.refresh(course)
        return course

    @staticmethod
    def delete(db: Session, course: Course) -> None:
        """Permanently delete a course and cascading curriculum."""
        db.delete(course)
        db.commit()

    @staticmethod
    def update_status(db: Session, course: Course, status: str) -> Course:
        """Update publication status of a course."""
        course.status = status
        db.commit()
        db.refresh(course)
        return course

    @staticmethod
    def get_courses_paginated(
        db: Session,
        page: int = 1,
        size: int = 12,
        category: Optional[str] = None,
        level: Optional[str] = None,
        status: Optional[str] = None,
        search: Optional[str] = None,
        instructor_id: Optional[int] = None,
    ) -> Tuple[List[Course], int]:
        """Query courses with pagination, domain filtering, full-text search, and instructor ownership."""
        statement = select(Course).options(
            joinedload(Course.instructor).joinedload(User.instructor_profile),
            selectinload(Course.lessons),
            selectinload(Course.modules),
        )
        count_stmt = select(func.count(Course.id))

        if category and category.lower() != "all":
            statement = statement.where(func.lower(Course.category) == category.strip().lower())
            count_stmt = count_stmt.where(func.lower(Course.category) == category.strip().lower())

        if level:
            statement = statement.where(func.lower(Course.level) == level.strip().lower())
            count_stmt = count_stmt.where(func.lower(Course.level) == level.strip().lower())

        if status:
            statement = statement.where(Course.status == status)
            count_stmt = count_stmt.where(Course.status == status)

        if instructor_id:
            statement = statement.where(Course.instructor_id == instructor_id)
            count_stmt = count_stmt.where(Course.instructor_id == instructor_id)

        if search and search.strip():
            term = f"%{search.strip().lower()}%"
            search_clause = or_(
                func.lower(Course.title).like(term),
                func.lower(Course.description).like(term),
                func.lower(Course.category).like(term),
            )
            statement = statement.where(search_clause)
            count_stmt = count_stmt.where(search_clause)

        total = db.execute(count_stmt).scalar() or 0
        offset = max(0, (page - 1) * size)
        statement = statement.order_by(Course.id.desc()).offset(offset).limit(size)
        items = list(db.execute(statement).scalars().all())

        return items, total

    @staticmethod
    def count_active_courses(db: Session) -> int:
        """Count total published and active courses for telemetry counters."""
        stmt = select(func.count(Course.id)).where(Course.status == CourseStatus.PUBLISHED.value)
        return db.execute(stmt).scalar() or 0

    @staticmethod
    def add_module(db: Session, course_id: int, title: str, order_index: int = 0) -> CourseModule:
        """Add a module to a course."""
        module = CourseModule(course_id=course_id, title=title, order_index=order_index)
        db.add(module)
        db.commit()
        db.refresh(module)
        return module

    @staticmethod
    def add_lesson(
        db: Session,
        course_id: int,
        title: str,
        module_id: Optional[int] = None,
        content_type: str = "video",
        video_url: Optional[str] = None,
        study_material_url: Optional[str] = None,
        attachments: Optional[list] = None,
        duration_minutes: int = 30,
        order_index: int = 0,
    ) -> Lesson:
        """Add a lesson to a course/module."""
        lesson = Lesson(
            course_id=course_id,
            module_id=module_id,
            title=title,
            content_type=content_type,
            video_url=video_url,
            study_material_url=study_material_url,
            attachments=attachments or [],
            duration_minutes=duration_minutes,
            order_index=order_index,
        )
        db.add(lesson)
        db.commit()
        db.refresh(lesson)
        return lesson

    @staticmethod
    def sync_curriculum(db: Session, course: Course, modules_data: List[Dict[str, Any]]) -> Course:
        """Atomically synchronize curriculum tree for Course Management & Curriculum Builder (Course Management.png)."""
        # Clear existing modules and lessons
        for mod in list(course.modules):
            db.delete(mod)
        for les in list(course.lessons):
            db.delete(les)
        db.flush()

        # Rebuild hierarchy
        for mod_idx, mod_dict in enumerate(modules_data):
            module = CourseModule(
                course_id=course.id,
                title=mod_dict.get("title", f"Module {mod_idx + 1}"),
                order_index=mod_dict.get("order_index", mod_idx),
            )
            db.add(module)
            db.flush()

            for les_idx, les_dict in enumerate(mod_dict.get("lessons", [])):
                lesson = Lesson(
                    course_id=course.id,
                    module_id=module.id,
                    title=les_dict.get("title", f"Lesson {les_idx + 1}"),
                    content_type=les_dict.get("content_type", "video"),
                    video_url=les_dict.get("video_url"),
                    study_material_url=les_dict.get("study_material_url"),
                    attachments=les_dict.get("attachments", []),
                    duration_minutes=les_dict.get("duration_minutes", 30),
                    order_index=les_dict.get("order_index", les_idx),
                )
                db.add(lesson)

        db.commit()
        db.refresh(course)
        return course
