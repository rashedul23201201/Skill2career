from typing import Optional, List, Tuple
from sqlalchemy import select, func, or_
from sqlalchemy.orm import Session, joinedload
from app.models.mock_test import (
    MockTest,
    TestQuestion,
    MockTestStatus,
    TestAttempt,
    TestAttemptStatus,
    TestResult,
)
from app.models.user import User


class MockTestRepository:
    """Repository managing database persistence for MockTest and TestQuestion entities (SKL-56)."""

    @staticmethod
    def create_test(db: Session, test: MockTest) -> MockTest:
        db.add(test)
        db.commit()
        db.refresh(test)
        return test

    @staticmethod
    def get_by_id(db: Session, test_id: int) -> Optional[MockTest]:
        stmt = (
            select(MockTest)
            .options(
                joinedload(MockTest.instructor),
                joinedload(MockTest.questions),
            )
            .where(MockTest.id == test_id)
        )
        return db.execute(stmt).unique().scalar_one_or_none()

    @staticmethod
    def update_test(db: Session, test: MockTest) -> MockTest:
        db.commit()
        db.refresh(test)
        return test

    @staticmethod
    def delete_test(db: Session, test: MockTest) -> None:
        db.delete(test)
        db.commit()

    @staticmethod
    def update_status(db: Session, test: MockTest, status: str, is_published: bool) -> MockTest:
        test.status = status
        test.is_published = is_published
        db.commit()
        db.refresh(test)
        return test

    @staticmethod
    def get_tests_paginated(
        db: Session,
        page: int = 1,
        size: int = 10,
        category: Optional[str] = None,
        search: Optional[str] = None,
        instructor_id: Optional[int] = None,
        status: Optional[str] = None,
        is_published_only: bool = True,
    ) -> Tuple[List[MockTest], int]:
        base_stmt = select(MockTest).options(joinedload(MockTest.instructor))

        if is_published_only:
            base_stmt = base_stmt.where(MockTest.status == MockTestStatus.PUBLISHED.value)
        elif status:
            base_stmt = base_stmt.where(MockTest.status == status)

        if instructor_id:
            base_stmt = base_stmt.where(MockTest.instructor_id == instructor_id)

        if category and category.lower() != "all":
            base_stmt = base_stmt.where(func.lower(MockTest.category) == category.lower())

        if search and search.strip():
            term = f"%{search.strip().lower()}%"
            base_stmt = base_stmt.where(
                or_(
                    func.lower(MockTest.title).like(term),
                    func.lower(MockTest.description).like(term),
                    func.lower(MockTest.category).like(term),
                )
            )

        count_stmt = select(func.count()).select_from(base_stmt.subquery())
        total = db.execute(count_stmt).scalar() or 0

        offset = (page - 1) * size
        stmt = base_stmt.order_by(MockTest.id.desc()).offset(offset).limit(size)
        items = list(db.execute(stmt).unique().scalars().all())

        return items, total

    @staticmethod
    def create_question(db: Session, question: TestQuestion) -> TestQuestion:
        db.add(question)
        db.commit()
        db.refresh(question)
        return question

    @staticmethod
    def get_question_by_id(db: Session, question_id: int) -> Optional[TestQuestion]:
        stmt = select(TestQuestion).where(TestQuestion.id == question_id)
        return db.execute(stmt).scalar_one_or_none()

    @staticmethod
    def get_questions_by_test_id(db: Session, test_id: int) -> List[TestQuestion]:
        stmt = (
            select(TestQuestion)
            .where(TestQuestion.test_id == test_id)
            .order_by(TestQuestion.order_index.asc(), TestQuestion.id.asc())
        )
        return list(db.execute(stmt).scalars().all())

    @staticmethod
    def update_question(db: Session, question: TestQuestion) -> TestQuestion:
        db.commit()
        db.refresh(question)
        return question

    @staticmethod
    def delete_question(db: Session, question: TestQuestion) -> None:
        db.delete(question)
        db.commit()

    @staticmethod
    def sync_questions(db: Session, test: MockTest, questions_data: List[dict]) -> List[TestQuestion]:
        for q in test.questions:
            db.delete(q)
        db.flush()

        created_questions = []
        for idx, q_dict in enumerate(questions_data):
            q = TestQuestion(
                test_id=test.id,
                question_text=q_dict["question_text"],
                options=q_dict["options"],
                correct_option=q_dict["correct_option"],
                marks=q_dict.get("marks", 1),
                explanation=q_dict.get("explanation"),
                order_index=q_dict.get("order_index", idx),
                topic=q_dict.get("topic"),
                difficulty=q_dict.get("difficulty"),
            )
            db.add(q)
            created_questions.append(q)

        test.total_questions = len(created_questions)
        db.commit()
        db.refresh(test)
        return created_questions

    @staticmethod
    def create_attempt(db: Session, attempt: TestAttempt) -> TestAttempt:
        db.add(attempt)
        db.commit()
        db.refresh(attempt)
        return attempt

    @staticmethod
    def get_attempt_by_id(db: Session, attempt_id: int) -> Optional[TestAttempt]:
        stmt = (
            select(TestAttempt)
            .options(
                joinedload(TestAttempt.test),
                joinedload(TestAttempt.learner),
                joinedload(TestAttempt.result),
            )
            .where(TestAttempt.id == attempt_id)
        )
        return db.execute(stmt).unique().scalar_one_or_none()

    @staticmethod
    def get_active_attempt_for_learner(db: Session, test_id: int, learner_id: int) -> Optional[TestAttempt]:
        stmt = (
            select(TestAttempt)
            .options(joinedload(TestAttempt.test))
            .where(
                TestAttempt.test_id == test_id,
                TestAttempt.learner_id == learner_id,
                TestAttempt.status == TestAttemptStatus.ACTIVE.value,
            )
            .order_by(TestAttempt.id.desc())
        )
        return db.execute(stmt).scalars().first()

    @staticmethod
    def get_attempts_by_learner(
        db: Session, learner_id: int, test_id: Optional[int] = None
    ) -> List[TestAttempt]:
        stmt = (
            select(TestAttempt)
            .options(joinedload(TestAttempt.test), joinedload(TestAttempt.result))
            .where(TestAttempt.learner_id == learner_id)
        )
        if test_id:
            stmt = stmt.where(TestAttempt.test_id == test_id)
        stmt = stmt.order_by(TestAttempt.id.desc())
        return list(db.execute(stmt).unique().scalars().all())

    @staticmethod
    def update_attempt(db: Session, attempt: TestAttempt) -> TestAttempt:
        db.commit()
        db.refresh(attempt)
        return attempt

    @staticmethod
    def create_result(db: Session, result: TestResult) -> TestResult:
        db.add(result)
        db.commit()
        db.refresh(result)
        return result

    @staticmethod
    def get_result_by_attempt_id(db: Session, attempt_id: int) -> Optional[TestResult]:
        stmt = (
            select(TestResult)
            .options(
                joinedload(TestResult.attempt).joinedload(TestAttempt.test),
                joinedload(TestResult.attempt).joinedload(TestAttempt.learner),
            )
            .where(TestResult.attempt_id == attempt_id)
        )
        return db.execute(stmt).unique().scalar_one_or_none()

    @staticmethod
    def get_submitted_attempts_by_test(db: Session, test_id: int) -> List[TestAttempt]:
        stmt = (
            select(TestAttempt)
            .where(
                TestAttempt.test_id == test_id,
                TestAttempt.status.in_([TestAttemptStatus.SUBMITTED.value, TestAttemptStatus.EXPIRED.value]),
            )
            .order_by(TestAttempt.score.desc())
        )
        return list(db.execute(stmt).scalars().all())

    @staticmethod
    def get_results_by_test_id(db: Session, test_id: int) -> List[TestResult]:
        stmt = (
            select(TestResult)
            .join(TestAttempt, TestResult.attempt_id == TestAttempt.id)
            .options(
                joinedload(TestResult.attempt).joinedload(TestAttempt.test),
                joinedload(TestResult.attempt).joinedload(TestAttempt.learner),
            )
            .where(TestAttempt.test_id == test_id)
            .order_by(TestResult.percentage.desc())
        )
        return list(db.execute(stmt).unique().scalars().all())


