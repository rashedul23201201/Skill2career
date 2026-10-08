import math
from datetime import datetime, timedelta, timezone
from typing import Optional, List
from sqlalchemy.orm import Session

from app.core.exceptions import (
    NotFoundException,
    ForbiddenException,
    BadRequestException,
)
from app.models.user import User, UserRole
from app.models.mock_test import (
    MockTest,
    TestQuestion,
    MockTestStatus,
    TestAttempt,
    TestAttemptStatus,
)
from app.repositories.mock_test_repository import MockTestRepository
from app.repositories.audit_log_repository import AuditLogRepository
from app.schemas.mock_test import (
    MockTestCreateRequest,
    MockTestUpdateRequest,
    MockTestResponse,
    MockTestDetailResponse,
    TestQuestionCreate,
    TestQuestionUpdate,
    TestQuestionResponse,
    PaginatedMockTestResponse,
    TestAttemptStartResponse,
    TestAttemptSaveAnswersRequest,
    TestAttemptSubmitRequest,
    TestAttemptResponse,
)


def _ensure_utc(dt: Optional[datetime]) -> datetime:
    if dt is None:
        return datetime.now(timezone.utc)
    if dt.tzinfo is None:
        return dt.replace(tzinfo=timezone.utc)
    return dt


class MockTestService:

    """Service handling Mock Test creation, question bank builder, and test discovery (SKL-56)."""

    def __init__(
        self,
        mock_test_repo: MockTestRepository = MockTestRepository(),
        audit_repo: AuditLogRepository = AuditLogRepository(),
    ):
        self.mock_test_repo = mock_test_repo
        self.audit_repo = audit_repo

    def _to_test_response(self, test: MockTest) -> MockTestResponse:
        instructor_name = "Instructor"
        if test.instructor:
            instructor_name = f"{test.instructor.first_name} {test.instructor.last_name}".strip()

        return MockTestResponse(
            id=test.id,
            instructor_id=test.instructor_id,
            instructor_name=instructor_name,
            title=test.title,
            description=test.description,
            category=test.category,
            duration_minutes=test.duration_minutes,
            passing_score=test.passing_score,
            total_questions=test.total_questions or len(test.questions or []),
            status=test.status,
            is_published=test.is_published,
            created_at=test.created_at,
            updated_at=test.updated_at,
        )

    def _to_question_response(self, q: TestQuestion, hide_answers: bool = False) -> TestQuestionResponse:
        return TestQuestionResponse(
            id=q.id,
            test_id=q.test_id,
            question_text=q.question_text,
            options=q.options,
            correct_option=None if hide_answers else q.correct_option,
            marks=q.marks,
            explanation=None if hide_answers else q.explanation,
            order_index=q.order_index,
            created_at=q.created_at,
            updated_at=q.updated_at,
        )

    def _to_attempt_response(self, attempt: TestAttempt) -> TestAttemptResponse:
        test_title = attempt.test.title if attempt.test else None
        category = attempt.test.category if attempt.test else None
        duration = attempt.test.duration_minutes if attempt.test else None
        passing = attempt.test.passing_score if attempt.test else None
        total_q = attempt.test.total_questions if attempt.test else None

        return TestAttemptResponse(
            id=attempt.id,
            test_id=attempt.test_id,
            learner_id=attempt.learner_id,
            started_at=attempt.started_at,
            submitted_at=attempt.submitted_at,
            status=attempt.status,
            score=attempt.score,
            total_marks=attempt.total_marks,
            percentage=attempt.percentage,
            is_passed=attempt.is_passed,
            time_taken_seconds=attempt.time_taken_seconds,
            answers=attempt.answers or {},
            marked_for_review=attempt.marked_for_review or [],
            test_title=test_title,
            category=category,
            duration_minutes=duration,
            passing_score=passing,
            total_questions=total_q,
        )

    def _to_attempt_start_response(
        self, test: MockTest, attempt: TestAttempt, remaining_seconds: int
    ) -> TestAttemptStartResponse:
        duration_seconds = test.duration_minutes * 60
        started_at = _ensure_utc(attempt.started_at)
        expires_at = started_at + timedelta(seconds=duration_seconds)
        questions = [self._to_question_response(q, hide_answers=True) for q in test.questions]

        return TestAttemptStartResponse(
            id=attempt.id,
            test_id=test.id,
            learner_id=attempt.learner_id,
            started_at=started_at,
            expires_at=expires_at,
            duration_minutes=test.duration_minutes,
            duration_seconds=duration_seconds,
            remaining_seconds=max(0, remaining_seconds),
            status=attempt.status,
            answers=attempt.answers or {},
            marked_for_review=attempt.marked_for_review or [],
            test_title=test.title,
            category=test.category,
            total_questions=test.total_questions or len(questions),
            passing_score=test.passing_score,
            questions=questions,
        )


    def _verify_management_access(self, test: MockTest, user: User) -> None:
        if user.role == UserRole.ADMIN:
            return
        if user.role == UserRole.INSTRUCTOR and test.instructor_id == user.id:
            return
        raise ForbiddenException("You do not have permission to manage this mock test")

    def create_mock_test(
        self, db: Session, current_user: User, request: MockTestCreateRequest
    ) -> MockTestResponse:
        if current_user.role not in [UserRole.INSTRUCTOR, UserRole.ADMIN]:
            raise ForbiddenException("Only instructors or administrators can create mock tests")

        is_published = (request.status == MockTestStatus.PUBLISHED)

        test = MockTest(
            instructor_id=current_user.id,
            title=request.title.strip(),
            description=request.description.strip() if request.description else None,
            category=request.category.strip(),
            duration_minutes=request.duration_minutes,
            passing_score=request.passing_score,
            total_questions=0,
            status=request.status.value,
            is_published=is_published,
        )
        created = self.mock_test_repo.create_test(db, test)

        self.audit_repo.create(
            db=db,
            action="MOCK_TEST_CREATE",
            admin_id=current_user.id if current_user.role == UserRole.ADMIN else None,
            target_user_id=current_user.id,
            details={"mock_test_id": created.id, "title": created.title},
        )

        return self._to_test_response(created)

    def get_mock_test_by_id(
        self, db: Session, test_id: int, current_user: Optional[User] = None
    ) -> MockTestDetailResponse:
        test = self.mock_test_repo.get_by_id(db, test_id)
        if not test:
            raise NotFoundException("Mock test not found")

        is_manager = current_user and (
            current_user.role == UserRole.ADMIN
            or (current_user.role == UserRole.INSTRUCTOR and test.instructor_id == current_user.id)
        )

        if not test.is_published and not is_manager:
            raise ForbiddenException("This mock test is not published yet")

        hide_answers = not is_manager
        base_resp = self._to_test_response(test)
        questions = [self._to_question_response(q, hide_answers=hide_answers) for q in test.questions]

        return MockTestDetailResponse(
            **base_resp.model_dump(),
            questions=questions,
        )

    def list_mock_tests_paginated(
        self,
        db: Session,
        page: int = 1,
        size: int = 10,
        category: Optional[str] = None,
        search: Optional[str] = None,
        my_tests: bool = False,
        status: Optional[str] = None,
        current_user: Optional[User] = None,
    ) -> PaginatedMockTestResponse:
        is_published_only = True
        instructor_id = None

        if my_tests and current_user and current_user.role in [UserRole.INSTRUCTOR, UserRole.ADMIN]:
            is_published_only = False
            instructor_id = current_user.id
        elif current_user and current_user.role == UserRole.ADMIN and status:
            is_published_only = False

        items, total = self.mock_test_repo.get_tests_paginated(
            db=db,
            page=page,
            size=size,
            category=category,
            search=search,
            instructor_id=instructor_id,
            status=status,
            is_published_only=is_published_only,
        )

        total_pages = math.ceil(total / size) if total > 0 else 1
        return PaginatedMockTestResponse(
            items=[self._to_test_response(t) for t in items],
            total=total,
            page=page,
            size=size,
            total_pages=total_pages,
        )

    def update_mock_test(
        self, db: Session, test_id: int, current_user: User, request: MockTestUpdateRequest
    ) -> MockTestResponse:
        test = self.mock_test_repo.get_by_id(db, test_id)
        if not test:
            raise NotFoundException("Mock test not found")

        self._verify_management_access(test, current_user)

        if request.title is not None:
            test.title = request.title.strip()
        if request.description is not None:
            test.description = request.description.strip() if request.description else None
        if request.category is not None:
            test.category = request.category.strip()
        if request.duration_minutes is not None:
            test.duration_minutes = request.duration_minutes
        if request.passing_score is not None:
            test.passing_score = request.passing_score
        if request.status is not None:
            test.status = request.status.value
            test.is_published = (request.status == MockTestStatus.PUBLISHED)

        updated = self.mock_test_repo.update_test(db, test)
        return self._to_test_response(updated)

    def delete_mock_test(self, db: Session, test_id: int, current_user: User) -> None:
        test = self.mock_test_repo.get_by_id(db, test_id)
        if not test:
            raise NotFoundException("Mock test not found")

        self._verify_management_access(test, current_user)
        self.mock_test_repo.delete_test(db, test)

    def update_mock_test_status(
        self, db: Session, test_id: int, current_user: User, status: MockTestStatus
    ) -> MockTestResponse:
        test = self.mock_test_repo.get_by_id(db, test_id)
        if not test:
            raise NotFoundException("Mock test not found")

        self._verify_management_access(test, current_user)
        is_published = (status == MockTestStatus.PUBLISHED)
        updated = self.mock_test_repo.update_status(db, test, status.value, is_published)
        return self._to_test_response(updated)

    def add_question(
        self, db: Session, test_id: int, current_user: User, request: TestQuestionCreate
    ) -> TestQuestionResponse:
        test = self.mock_test_repo.get_by_id(db, test_id)
        if not test:
            raise NotFoundException("Mock test not found")

        self._verify_management_access(test, current_user)

        if not request.options or len(request.options) < 2:
            raise BadRequestException("A question must have at least 2 options")

        question = TestQuestion(
            test_id=test.id,
            question_text=request.question_text.strip(),
            options=request.options,
            correct_option=request.correct_option.strip(),
            marks=request.marks,
            explanation=request.explanation.strip() if request.explanation else None,
            order_index=request.order_index,
        )
        created = self.mock_test_repo.create_question(db, question)

        test.total_questions = len(test.questions)
        self.mock_test_repo.update_test(db, test)

        return self._to_question_response(created)

    def get_test_questions(
        self, db: Session, test_id: int, current_user: Optional[User] = None
    ) -> List[TestQuestionResponse]:
        test = self.mock_test_repo.get_by_id(db, test_id)
        if not test:
            raise NotFoundException("Mock test not found")

        is_manager = current_user and (
            current_user.role == UserRole.ADMIN
            or (current_user.role == UserRole.INSTRUCTOR and test.instructor_id == current_user.id)
        )

        if not test.is_published and not is_manager:
            raise ForbiddenException("This mock test is not published yet")

        questions = self.mock_test_repo.get_questions_by_test_id(db, test_id)
        return [self._to_question_response(q, hide_answers=not is_manager) for q in questions]

    def update_question(
        self,
        db: Session,
        test_id: int,
        question_id: int,
        current_user: User,
        request: TestQuestionUpdate,
    ) -> TestQuestionResponse:
        test = self.mock_test_repo.get_by_id(db, test_id)
        if not test:
            raise NotFoundException("Mock test not found")

        self._verify_management_access(test, current_user)

        question = self.mock_test_repo.get_question_by_id(db, question_id)
        if not question or question.test_id != test_id:
            raise NotFoundException("Question not found in this mock test")

        if request.question_text is not None:
            question.question_text = request.question_text.strip()
        if request.options is not None:
            if len(request.options) < 2:
                raise BadRequestException("A question must have at least 2 options")
            question.options = request.options
        if request.correct_option is not None:
            question.correct_option = request.correct_option.strip()
        if request.marks is not None:
            question.marks = request.marks
        if request.explanation is not None:
            question.explanation = request.explanation.strip() if request.explanation else None
        if request.order_index is not None:
            question.order_index = request.order_index

        updated = self.mock_test_repo.update_question(db, question)
        return self._to_question_response(updated)

    def delete_question(
        self, db: Session, test_id: int, question_id: int, current_user: User
    ) -> None:
        test = self.mock_test_repo.get_by_id(db, test_id)
        if not test:
            raise NotFoundException("Mock test not found")

        self._verify_management_access(test, current_user)

        question = self.mock_test_repo.get_question_by_id(db, question_id)
        if not question or question.test_id != test_id:
            raise NotFoundException("Question not found in this mock test")

        self.mock_test_repo.delete_question(db, question)
        test.total_questions = max(0, len(test.questions) - 1)
        self.mock_test_repo.update_test(db, test)

    def sync_questions(
        self,
        db: Session,
        test_id: int,
        current_user: User,
        questions_data: List[TestQuestionCreate],
    ) -> List[TestQuestionResponse]:
        test = self.mock_test_repo.get_by_id(db, test_id)
        if not test:
            raise NotFoundException("Mock test not found")

        self._verify_management_access(test, current_user)

        raw_dicts = [q.model_dump() for q in questions_data]
        created = self.mock_test_repo.sync_questions(db, test, raw_dicts)
        return [self._to_question_response(q) for q in created]

    def start_attempt(self, db: Session, test_id: int, current_user: User) -> TestAttemptStartResponse:
        test = self.mock_test_repo.get_by_id(db, test_id)
        if not test:
            raise NotFoundException("Mock test not found")

        is_manager = (
            current_user.role == UserRole.ADMIN
            or (current_user.role == UserRole.INSTRUCTOR and test.instructor_id == current_user.id)
        )
        if not test.is_published and not is_manager:
            raise ForbiddenException("This mock test is not published yet")

        now = datetime.now(timezone.utc)

        active_attempt = self.mock_test_repo.get_active_attempt_for_learner(db, test.id, current_user.id)
        if active_attempt:
            active_started = _ensure_utc(active_attempt.started_at)
            elapsed = (now - active_started).total_seconds()
            total_duration = test.duration_minutes * 60
            remaining = int(total_duration - elapsed)
            if remaining <= 0:
                self.submit_attempt_answers(
                    db=db,
                    attempt_id=active_attempt.id,
                    current_user=current_user,
                    request=None,
                    is_auto_expired=True,
                )
            else:
                return self._to_attempt_start_response(test, active_attempt, remaining_seconds=remaining)

        new_attempt = TestAttempt(
            test_id=test.id,
            learner_id=current_user.id,
            started_at=now,
            status=TestAttemptStatus.ACTIVE.value,
            answers={},
            marked_for_review=[],
            score=0.0,
            total_marks=0,
            percentage=0.0,
            is_passed=False,
            time_taken_seconds=0,
        )
        created_attempt = self.mock_test_repo.create_attempt(db, new_attempt)

        self.audit_repo.create(
            db=db,
            action="MOCK_TEST_ATTEMPT_START",
            admin_id=current_user.id if current_user.role == UserRole.ADMIN else None,
            target_user_id=current_user.id,
            details={"attempt_id": created_attempt.id, "test_id": test.id, "title": test.title},
        )

        return self._to_attempt_start_response(
            test, created_attempt, remaining_seconds=test.duration_minutes * 60
        )

    def get_attempt(
        self, db: Session, attempt_id: int, current_user: User
    ) -> TestAttemptStartResponse:
        attempt = self.mock_test_repo.get_attempt_by_id(db, attempt_id)
        if not attempt:
            raise NotFoundException("Test attempt not found")

        if attempt.learner_id != current_user.id and current_user.role != UserRole.ADMIN:
            raise ForbiddenException("You do not have permission to view this test attempt")

        now = datetime.now(timezone.utc)
        test = attempt.test
        total_duration = test.duration_minutes * 60
        attempt_started = _ensure_utc(attempt.started_at)
        elapsed = (now - attempt_started).total_seconds()
        remaining = int(total_duration - elapsed)

        if attempt.status == TestAttemptStatus.ACTIVE.value and remaining <= 0:
            self.submit_attempt_answers(
                db=db,
                attempt_id=attempt.id,
                current_user=current_user,
                request=None,
                is_auto_expired=True,
            )
            attempt = self.mock_test_repo.get_attempt_by_id(db, attempt_id)
            remaining = 0

        return self._to_attempt_start_response(
            test, attempt, remaining_seconds=max(0, remaining)
        )

    def save_attempt_answers(
        self,
        db: Session,
        attempt_id: int,
        current_user: User,
        request: TestAttemptSaveAnswersRequest,
    ) -> TestAttemptResponse:
        attempt = self.mock_test_repo.get_attempt_by_id(db, attempt_id)
        if not attempt:
            raise NotFoundException("Test attempt not found")

        if attempt.learner_id != current_user.id and current_user.role != UserRole.ADMIN:
            raise ForbiddenException("You do not have permission to modify this test attempt")

        if attempt.status != TestAttemptStatus.ACTIVE.value:
            raise BadRequestException("Cannot update answers for an inactive or submitted test attempt")

        now = datetime.now(timezone.utc)
        attempt_started = _ensure_utc(attempt.started_at)
        elapsed = (now - attempt_started).total_seconds()
        if elapsed > attempt.test.duration_minutes * 60:
            return self.submit_attempt_answers(
                db=db,
                attempt_id=attempt.id,
                current_user=current_user,
                request=TestAttemptSubmitRequest(
                    answers=request.answers,
                    marked_for_review=request.marked_for_review,
                ),
                is_auto_expired=True,
            )

        attempt.answers = request.answers or {}
        attempt.marked_for_review = request.marked_for_review or []
        updated = self.mock_test_repo.update_attempt(db, attempt)
        return self._to_attempt_response(updated)

    def submit_attempt_answers(
        self,
        db: Session,
        attempt_id: int,
        current_user: User,
        request: Optional[TestAttemptSubmitRequest] = None,
        is_auto_expired: bool = False,
    ) -> TestAttemptResponse:
        attempt = self.mock_test_repo.get_attempt_by_id(db, attempt_id)
        if not attempt:
            raise NotFoundException("Test attempt not found")

        if attempt.learner_id != current_user.id and current_user.role != UserRole.ADMIN:
            raise ForbiddenException("You do not have permission to submit this test attempt")

        if attempt.status in [TestAttemptStatus.SUBMITTED.value, TestAttemptStatus.EXPIRED.value]:
            return self._to_attempt_response(attempt)

        answers = dict(attempt.answers or {})
        if request and request.answers:
            answers.update(request.answers)
        marked_for_review = (
            request.marked_for_review
            if request and request.marked_for_review is not None
            else (attempt.marked_for_review or [])
        )

        questions = self.mock_test_repo.get_questions_by_test_id(db, attempt.test_id)
        total_marks = sum(q.marks for q in questions)
        score = 0.0

        for q in questions:
            qid_str = str(q.id)
            given_answer = answers.get(qid_str) or answers.get(q.id)
            if (
                given_answer
                and str(given_answer).strip().upper() == str(q.correct_option).strip().upper()
            ):
                score += q.marks

        percentage = round((score / total_marks * 100), 2) if total_marks > 0 else 0.0
        is_passed = percentage >= attempt.test.passing_score

        now = datetime.now(timezone.utc)
        duration_limit = attempt.test.duration_minutes * 60
        attempt_started = _ensure_utc(attempt.started_at)
        elapsed = int((now - attempt_started).total_seconds())
        time_taken = max(0, min(elapsed, duration_limit))


        attempt.answers = answers
        attempt.marked_for_review = marked_for_review
        attempt.score = score
        attempt.total_marks = total_marks
        attempt.percentage = percentage
        attempt.is_passed = is_passed
        attempt.time_taken_seconds = time_taken
        attempt.submitted_at = now
        attempt.status = (
            TestAttemptStatus.EXPIRED.value if is_auto_expired else TestAttemptStatus.SUBMITTED.value
        )

        updated = self.mock_test_repo.update_attempt(db, attempt)

        self.audit_repo.create(
            db=db,
            action="MOCK_TEST_ATTEMPT_SUBMIT",
            admin_id=current_user.id if current_user.role == UserRole.ADMIN else None,
            target_user_id=current_user.id,
            details={
                "attempt_id": updated.id,
                "test_id": attempt.test_id,
                "score": score,
                "total_marks": total_marks,
                "percentage": percentage,
                "is_passed": is_passed,
                "is_auto_expired": is_auto_expired,
            },
        )

        return self._to_attempt_response(updated)

    def get_learner_attempts(
        self, db: Session, current_user: User, test_id: Optional[int] = None
    ) -> List[TestAttemptResponse]:
        attempts = self.mock_test_repo.get_attempts_by_learner(
            db=db, learner_id=current_user.id, test_id=test_id
        )
        return [self._to_attempt_response(a) for a in attempts]

