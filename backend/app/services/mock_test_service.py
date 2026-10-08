import math
from typing import Optional, List
from sqlalchemy.orm import Session

from app.core.exceptions import (
    NotFoundException,
    ForbiddenException,
    BadRequestException,
)
from app.models.user import User, UserRole
from app.models.mock_test import MockTest, TestQuestion, MockTestStatus
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
)


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
