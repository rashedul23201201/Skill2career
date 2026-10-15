import logging
from typing import Optional, List, Tuple
from sqlalchemy import select, func, desc
from sqlalchemy.orm import Session, joinedload, selectinload
from app.models.course import Course, CourseModule, Lesson
from app.models.mock_test import MockTest, TestQuestion
from app.models.moderation import ContentModerationLog, ModerationStatus, ContentType
from app.models.user import User

logger = logging.getLogger(__name__)


class ModerationRepository:
    """Repository managing queries and mutations for Content Moderation (SKL-25)."""

    @staticmethod
    def get_pending_courses(db: Session) -> List[Course]:
        """Fetch all courses currently awaiting administrative moderation."""
        stmt = (
            select(Course)
            .options(
                joinedload(Course.instructor).joinedload(User.instructor_profile),
                selectinload(Course.modules).selectinload(CourseModule.lessons),
                selectinload(Course.lessons),
            )
            .where(Course.moderation_status == ModerationStatus.PENDING_REVIEW.value)
            .order_by(desc(Course.updated_at))
        )
        return list(db.execute(stmt).scalars().unique().all())

    @staticmethod
    def get_pending_mock_tests(db: Session) -> List[MockTest]:
        """Fetch all mock tests currently awaiting administrative moderation."""
        stmt = (
            select(MockTest)
            .options(
                joinedload(MockTest.instructor),
                selectinload(MockTest.questions),
            )
            .where(MockTest.moderation_status == ModerationStatus.PENDING_REVIEW.value)
            .order_by(desc(MockTest.updated_at))
        )
        return list(db.execute(stmt).scalars().unique().all())

    @staticmethod
    def get_courses_by_moderation_status(db: Session, status: Optional[str] = None) -> List[Course]:
        """Fetch courses filtered by moderation status."""
        stmt = (
            select(Course)
            .options(
                joinedload(Course.instructor).joinedload(User.instructor_profile),
                selectinload(Course.modules).selectinload(CourseModule.lessons),
                selectinload(Course.lessons),
            )
        )
        if status:
            stmt = stmt.where(Course.moderation_status == status)
        stmt = stmt.order_by(desc(Course.updated_at))
        return list(db.execute(stmt).scalars().unique().all())

    @staticmethod
    def get_mock_tests_by_moderation_status(db: Session, status: Optional[str] = None) -> List[MockTest]:
        """Fetch mock tests filtered by moderation status."""
        stmt = (
            select(MockTest)
            .options(
                joinedload(MockTest.instructor),
                selectinload(MockTest.questions),
            )
        )
        if status:
            stmt = stmt.where(MockTest.moderation_status == status)
        stmt = stmt.order_by(desc(MockTest.updated_at))
        return list(db.execute(stmt).scalars().unique().all())

    @staticmethod
    def get_course_by_id(db: Session, course_id: int) -> Optional[Course]:
        """Fetch course by ID with complete relations for inspection."""
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
    def get_mock_test_by_id(db: Session, test_id: int) -> Optional[MockTest]:
        """Fetch mock test by ID with questions and author for inspection."""
        stmt = (
            select(MockTest)
            .options(
                joinedload(MockTest.instructor),
                selectinload(MockTest.questions),
            )
            .where(MockTest.id == test_id)
        )
        return db.execute(stmt).scalar_one_or_none()

    @staticmethod
    def create_log(db: Session, log: ContentModerationLog) -> ContentModerationLog:
        """Persist a content moderation audit event."""
        db.add(log)
        db.commit()
        db.refresh(log)
        return log

    @staticmethod
    def get_logs(db: Session, limit: int = 50, content_type: Optional[str] = None) -> List[ContentModerationLog]:
        """Retrieve recent content moderation audit logs."""
        stmt = (
            select(ContentModerationLog)
            .options(joinedload(ContentModerationLog.admin))
            .order_by(desc(ContentModerationLog.created_at))
            .limit(limit)
        )
        if content_type:
            stmt = stmt.where(ContentModerationLog.content_type == content_type)
        return list(db.execute(stmt).scalars().all())

    @staticmethod
    def get_counts(db: Session) -> dict:
        """Calculate counts across moderation states."""
        pending_courses = db.scalar(
            select(func.count(Course.id)).where(Course.moderation_status == ModerationStatus.PENDING_REVIEW.value)
        ) or 0
        pending_tests = db.scalar(
            select(func.count(MockTest.id)).where(MockTest.moderation_status == ModerationStatus.PENDING_REVIEW.value)
        ) or 0
        approved_courses = db.scalar(
            select(func.count(Course.id)).where(Course.moderation_status == ModerationStatus.APPROVED.value)
        ) or 0
        approved_tests = db.scalar(
            select(func.count(MockTest.id)).where(MockTest.moderation_status == ModerationStatus.APPROVED.value)
        ) or 0
        restricted_courses = db.scalar(
            select(func.count(Course.id)).where(Course.moderation_status == ModerationStatus.RESTRICTED.value)
        ) or 0
        restricted_tests = db.scalar(
            select(func.count(MockTest.id)).where(MockTest.moderation_status == ModerationStatus.RESTRICTED.value)
        ) or 0

        return {
            "pending_courses": pending_courses,
            "pending_tests": pending_tests,
            "total_pending": pending_courses + pending_tests,
            "approved_courses": approved_courses,
            "approved_tests": approved_tests,
            "total_approved": approved_courses + approved_tests,
            "restricted_courses": restricted_courses,
            "restricted_tests": restricted_tests,
            "total_restricted": restricted_courses + restricted_tests,
        }
