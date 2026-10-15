import logging
from datetime import datetime, timezone
from typing import Optional, List, Dict, Any
from sqlalchemy.orm import Session

from app.core.exceptions import NotFoundException, ForbiddenException, BadRequestException
from app.models.user import User, UserRole
from app.models.course import Course, CourseStatus
from app.models.mock_test import MockTest, MockTestStatus
from app.models.moderation import (
    ModerationStatus,
    ContentType,
    ModerationAction,
    ContentModerationLog,
)
from app.repositories.moderation_repository import ModerationRepository
from app.schemas.moderation import (
    ModerationItemResponse,
    PendingModerationResponse,
    ContentModerationLogResponse,
)

logger = logging.getLogger(__name__)


class ModerationService:
    """Service orchestrating Course & Content Moderation workflow (SKL-25)."""

    def __init__(self, moderation_repo: ModerationRepository = ModerationRepository()):
        self.repo = moderation_repo

    @staticmethod
    def _course_to_item(course: Course) -> ModerationItemResponse:
        instructor_name = "Instructor"
        instructor_email = None
        if course.instructor:
            instructor_name = f"{course.instructor.first_name} {course.instructor.last_name}".strip()
            instructor_email = course.instructor.email

        moderator_name = None
        if getattr(course, "moderator", None):
            moderator_name = f"{course.moderator.first_name} {course.moderator.last_name}".strip()

        return ModerationItemResponse(
            id=course.id,
            content_type=ContentType.COURSE.value,
            title=course.title,
            category=course.category,
            instructor_id=course.instructor_id,
            instructor_name=instructor_name,
            instructor_email=instructor_email,
            status=course.status,
            moderation_status=getattr(course, "moderation_status", ModerationStatus.APPROVED.value) or ModerationStatus.APPROVED.value,
            moderation_notes=getattr(course, "moderation_notes", None),
            moderated_by=getattr(course, "moderated_by", None),
            moderator_name=moderator_name,
            moderated_at=getattr(course, "moderated_at", None),
            created_at=course.created_at,
            updated_at=course.updated_at,
            details={
                "price": float(course.price) if course.price is not None else 0.0,
                "is_free": course.is_free,
                "level": course.level,
                "duration_weeks": course.duration_weeks,
                "modules_count": len(course.modules) if course.modules else 0,
                "lessons_count": len(course.lessons) if course.lessons else 0,
            },
        )

    @staticmethod
    def _mock_test_to_item(test: MockTest) -> ModerationItemResponse:
        instructor_name = "Instructor"
        instructor_email = None
        if test.instructor:
            instructor_name = f"{test.instructor.first_name} {test.instructor.last_name}".strip()
            instructor_email = test.instructor.email

        moderator_name = None
        if getattr(test, "moderator", None):
            moderator_name = f"{test.moderator.first_name} {test.moderator.last_name}".strip()

        return ModerationItemResponse(
            id=test.id,
            content_type=ContentType.MOCK_TEST.value,
            title=test.title,
            category=test.category,
            instructor_id=test.instructor_id,
            instructor_name=instructor_name,
            instructor_email=instructor_email,
            status=test.status,
            moderation_status=getattr(test, "moderation_status", ModerationStatus.APPROVED.value) or ModerationStatus.APPROVED.value,
            moderation_notes=getattr(test, "moderation_notes", None),
            moderated_by=getattr(test, "moderated_by", None),
            moderator_name=moderator_name,
            moderated_at=getattr(test, "moderated_at", None),
            created_at=test.created_at,
            updated_at=test.updated_at,
            details={
                "duration_minutes": test.duration_minutes,
                "passing_score": test.passing_score,
                "questions_count": len(test.questions) if test.questions else (test.total_questions or 0),
            },
        )

    def get_pending_moderation(self, db: Session) -> PendingModerationResponse:
        """Fetch all courses and mock tests awaiting moderation review."""
        courses = self.repo.get_pending_courses(db)
        tests = self.repo.get_pending_mock_tests(db)

        course_items = [self._course_to_item(c) for c in courses]
        test_items = [self._mock_test_to_item(t) for t in tests]

        return PendingModerationResponse(
            courses=course_items,
            mock_tests=test_items,
            total_pending=len(course_items) + len(test_items),
        )

    def get_all_moderation_items(
        self, db: Session, status: Optional[str] = None, content_type: Optional[str] = None
    ) -> List[ModerationItemResponse]:
        """Fetch all items across moderation states with optional filtering."""
        items: List[ModerationItemResponse] = []

        if not content_type or content_type.upper() == ContentType.COURSE.value:
            courses = self.repo.get_courses_by_moderation_status(db, status=status)
            items.extend([self._course_to_item(c) for c in courses])

        if not content_type or content_type.upper() == ContentType.MOCK_TEST.value:
            tests = self.repo.get_mock_tests_by_moderation_status(db, status=status)
            items.extend([self._mock_test_to_item(t) for t in tests])

        items.sort(key=lambda x: x.updated_at, reverse=True)
        return items

    def get_moderation_stats(self, db: Session) -> Dict[str, Any]:
        """Calculate aggregate count metrics for dashboard overview."""
        return self.repo.get_counts(db)

    def get_course_preview(self, db: Session, course_id: int) -> Dict[str, Any]:
        """Detailed payload for admin drawer to inspect course curriculum and metadata."""
        course = self.repo.get_course_by_id(db, course_id)
        if not course:
            raise NotFoundException(f"Course with ID {course_id} was not found")

        modules = []
        for mod in (course.modules or []):
            lessons = []
            for les in (mod.lessons or []):
                lessons.append({
                    "id": les.id,
                    "title": les.title,
                    "content_type": les.content_type,
                    "duration_minutes": les.duration_minutes,
                    "order_index": les.order_index,
                    "is_preview": getattr(les, "is_preview", False),
                    "moderation_status": getattr(les, "moderation_status", "APPROVED"),
                })
            modules.append({
                "id": mod.id,
                "title": mod.title,
                "order_index": mod.order_index,
                "lessons": lessons,
            })

        instructor_info = {
            "id": course.instructor.id if course.instructor else course.instructor_id,
            "name": f"{course.instructor.first_name} {course.instructor.last_name}".strip() if course.instructor else "Unknown",
            "email": course.instructor.email if course.instructor else None,
            "designation": getattr(course.instructor.instructor_profile, "designation", "Instructor") if course.instructor and hasattr(course.instructor, "instructor_profile") and course.instructor.instructor_profile else "Instructor",
        }

        return {
            "id": course.id,
            "content_type": ContentType.COURSE.value,
            "title": course.title,
            "description": course.description,
            "category": course.category,
            "level": course.level,
            "price": float(course.price) if course.price is not None else 0.0,
            "is_free": course.is_free,
            "duration_weeks": course.duration_weeks,
            "thumbnail_url": course.thumbnail_url,
            "status": course.status,
            "moderation_status": getattr(course, "moderation_status", ModerationStatus.APPROVED.value),
            "moderation_notes": getattr(course, "moderation_notes", None),
            "moderated_by": getattr(course, "moderated_by", None),
            "moderated_at": getattr(course, "moderated_at", None),
            "created_at": course.created_at,
            "updated_at": course.updated_at,
            "instructor": instructor_info,
            "modules": modules,
        }

    def get_mock_test_preview(self, db: Session, test_id: int) -> Dict[str, Any]:
        """Detailed payload for admin drawer to inspect mock test questions and answer keys."""
        test = self.repo.get_mock_test_by_id(db, test_id)
        if not test:
            raise NotFoundException(f"Mock test with ID {test_id} was not found")

        questions = []
        for q in (test.questions or []):
            questions.append({
                "id": q.id,
                "question_text": q.question_text,
                "options": q.options,
                "correct_option": q.correct_option,
                "marks": q.marks,
                "explanation": q.explanation,
                "order_index": q.order_index,
                "topic": q.topic,
                "difficulty": q.difficulty,
            })

        instructor_info = {
            "id": test.instructor.id if test.instructor else test.instructor_id,
            "name": f"{test.instructor.first_name} {test.instructor.last_name}".strip() if test.instructor else "Unknown",
            "email": test.instructor.email if test.instructor else None,
        }

        return {
            "id": test.id,
            "content_type": ContentType.MOCK_TEST.value,
            "title": test.title,
            "description": test.description,
            "category": test.category,
            "duration_minutes": test.duration_minutes,
            "passing_score": test.passing_score,
            "total_questions": test.total_questions or len(questions),
            "status": test.status,
            "is_published": test.is_published,
            "moderation_status": getattr(test, "moderation_status", ModerationStatus.APPROVED.value),
            "moderation_notes": getattr(test, "moderation_notes", None),
            "moderated_by": getattr(test, "moderated_by", None),
            "moderated_at": getattr(test, "moderated_at", None),
            "created_at": test.created_at,
            "updated_at": test.updated_at,
            "instructor": instructor_info,
            "questions": questions,
        }

    def approve_course(
        self, db: Session, course_id: int, admin_user: User, notes: Optional[str] = None
    ) -> ModerationItemResponse:
        """Approve a course for publication to the public catalog (SKL-25)."""
        course = self.repo.get_course_by_id(db, course_id)
        if not course:
            raise NotFoundException(f"Course with ID {course_id} was not found")

        now = datetime.now(timezone.utc)
        course.moderation_status = ModerationStatus.APPROVED.value
        course.moderated_by = admin_user.id
        course.moderated_at = now
        course.moderation_notes = notes

        # If lessons exist, ensure their status is approved as well
        if course.lessons:
            for les in course.lessons:
                les.moderation_status = ModerationStatus.APPROVED.value

        db.commit()
        db.refresh(course)

        # Audit log
        log = ContentModerationLog(
            content_type=ContentType.COURSE.value,
            content_id=course.id,
            admin_id=admin_user.id,
            action=ModerationAction.APPROVE.value,
            reason=notes or "Approved by administrator for catalog distribution",
            created_at=now,
        )
        self.repo.create_log(db, log)
        logger.info("Admin ID %d approved course ID %d: '%s'", admin_user.id, course.id, course.title)

        return self._course_to_item(course)

    def restrict_course(
        self, db: Session, course_id: int, admin_user: User, reason: str
    ) -> ModerationItemResponse:
        """Restrict/delist a policy-violating course from the public catalog (SKL-25)."""
        if not reason or not reason.strip():
            raise BadRequestException("A valid justification or violation reason is required to restrict content")

        course = self.repo.get_course_by_id(db, course_id)
        if not course:
            raise NotFoundException(f"Course with ID {course_id} was not found")

        now = datetime.now(timezone.utc)
        course.moderation_status = ModerationStatus.RESTRICTED.value
        course.moderated_by = admin_user.id
        course.moderated_at = now
        course.moderation_notes = reason.strip()

        db.commit()
        db.refresh(course)

        # Audit log
        log = ContentModerationLog(
            content_type=ContentType.COURSE.value,
            content_id=course.id,
            admin_id=admin_user.id,
            action=ModerationAction.RESTRICT.value,
            reason=reason.strip(),
            created_at=now,
        )
        self.repo.create_log(db, log)
        logger.info("Admin ID %d restricted course ID %d: reason='%s'", admin_user.id, course.id, reason)

        return self._course_to_item(course)

    def approve_mock_test(
        self, db: Session, test_id: int, admin_user: User, notes: Optional[str] = None
    ) -> ModerationItemResponse:
        """Approve a mock test for publication in assessment catalog (SKL-25)."""
        test = self.repo.get_mock_test_by_id(db, test_id)
        if not test:
            raise NotFoundException(f"Mock test with ID {test_id} was not found")

        now = datetime.now(timezone.utc)
        test.moderation_status = ModerationStatus.APPROVED.value
        test.moderated_by = admin_user.id
        test.moderated_at = now
        test.moderation_notes = notes

        db.commit()
        db.refresh(test)

        # Audit log
        log = ContentModerationLog(
            content_type=ContentType.MOCK_TEST.value,
            content_id=test.id,
            admin_id=admin_user.id,
            action=ModerationAction.APPROVE.value,
            reason=notes or "Approved by administrator for assessment catalog",
            created_at=now,
        )
        self.repo.create_log(db, log)
        logger.info("Admin ID %d approved mock test ID %d: '%s'", admin_user.id, test.id, test.title)

        return self._mock_test_to_item(test)

    def restrict_mock_test(
        self, db: Session, test_id: int, admin_user: User, reason: str
    ) -> ModerationItemResponse:
        """Restrict/delist a mock test from the public assessment catalog (SKL-25)."""
        if not reason or not reason.strip():
            raise BadRequestException("A valid justification or violation reason is required to restrict content")

        test = self.repo.get_mock_test_by_id(db, test_id)
        if not test:
            raise NotFoundException(f"Mock test with ID {test_id} was not found")

        now = datetime.now(timezone.utc)
        test.moderation_status = ModerationStatus.RESTRICTED.value
        test.moderated_by = admin_user.id
        test.moderated_at = now
        test.moderation_notes = reason.strip()

        db.commit()
        db.refresh(test)

        # Audit log
        log = ContentModerationLog(
            content_type=ContentType.MOCK_TEST.value,
            content_id=test.id,
            admin_id=admin_user.id,
            action=ModerationAction.RESTRICT.value,
            reason=reason.strip(),
            created_at=now,
        )
        self.repo.create_log(db, log)
        logger.info("Admin ID %d restricted mock test ID %d: reason='%s'", admin_user.id, test.id, reason)

        return self._mock_test_to_item(test)

    def submit_course_for_review(
        self, db: Session, course_id: int, current_user: User
    ) -> ModerationItemResponse:
        """Author submits course for administrative content review (SKL-25)."""
        course = self.repo.get_course_by_id(db, course_id)
        if not course:
            raise NotFoundException(f"Course with ID {course_id} was not found")

        if course.instructor_id != current_user.id and current_user.role != UserRole.ADMIN:
            raise ForbiddenException("You do not have permission to submit this course for review")

        now = datetime.now(timezone.utc)
        course.moderation_status = ModerationStatus.PENDING_REVIEW.value
        db.commit()
        db.refresh(course)

        log = ContentModerationLog(
            content_type=ContentType.COURSE.value,
            content_id=course.id,
            admin_id=None,
            action=ModerationAction.SUBMIT_REVIEW.value,
            reason=f"Submitted for review by instructor '{current_user.first_name} {current_user.last_name}'",
            created_at=now,
        )
        self.repo.create_log(db, log)
        logger.info("User ID %d submitted Course ID %d for moderation review", current_user.id, course.id)

        return self._course_to_item(course)

    def submit_mock_test_for_review(
        self, db: Session, test_id: int, current_user: User
    ) -> ModerationItemResponse:
        """Author submits mock test for administrative content review (SKL-25)."""
        test = self.repo.get_mock_test_by_id(db, test_id)
        if not test:
            raise NotFoundException(f"Mock test with ID {test_id} was not found")

        if test.instructor_id != current_user.id and current_user.role != UserRole.ADMIN:
            raise ForbiddenException("You do not have permission to submit this mock test for review")

        now = datetime.now(timezone.utc)
        test.moderation_status = ModerationStatus.PENDING_REVIEW.value
        db.commit()
        db.refresh(test)

        log = ContentModerationLog(
            content_type=ContentType.MOCK_TEST.value,
            content_id=test.id,
            admin_id=None,
            action=ModerationAction.SUBMIT_REVIEW.value,
            reason=f"Submitted for review by instructor '{current_user.first_name} {current_user.last_name}'",
            created_at=now,
        )
        self.repo.create_log(db, log)
        logger.info("User ID %d submitted Mock Test ID %d for moderation review", current_user.id, test.id)

        return self._mock_test_to_item(test)

    def get_moderation_logs(
        self, db: Session, limit: int = 50, content_type: Optional[str] = None
    ) -> List[ContentModerationLogResponse]:
        """Fetch chronological audit history of administrative moderation actions."""
        logs = self.repo.get_logs(db, limit=limit, content_type=content_type)
        res = []
        for l in logs:
            admin_name = f"{l.admin.first_name} {l.admin.last_name}".strip() if l.admin else "System/Author"
            res.append(
                ContentModerationLogResponse(
                    id=l.id,
                    content_type=l.content_type,
                    content_id=l.content_id,
                    admin_id=l.admin_id,
                    admin_name=admin_name,
                    action=l.action,
                    reason=l.reason,
                    created_at=l.created_at,
                )
            )
        return res
