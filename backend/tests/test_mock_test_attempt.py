import pytest
from datetime import datetime, timedelta, timezone
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.models.user import User, UserRole
from app.models.mock_test import MockTest, TestQuestion, MockTestStatus, TestAttempt, TestAttemptStatus
from app.core.security import hash_password, create_access_token


def create_user(
    db: Session,
    email: str,
    role: UserRole = UserRole.LEARNER,
    first_name: str = "Test",
    last_name: str = "Learner",
) -> User:
    user = User(
        email=email,
        hashed_password=hash_password("Password123!"),
        role=role,
        first_name=first_name,
        last_name=last_name,
        is_active=True,
        is_verified=True,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def auth_header(user: User) -> dict:
    token = create_access_token(
        subject=user.id,
        claims={"email": user.email, "role": user.role.value},
    )
    return {"Authorization": f"Bearer {token}"}


def create_sample_mock_test(db: Session, instructor: User, is_published: bool = True) -> MockTest:
    test = MockTest(
        instructor_id=instructor.id,
        title="Python Data Structures Assessment",
        description="Assessing lists, dicts, BSTs, and time complexities.",
        category="Programming",
        duration_minutes=30,
        passing_score=50,
        total_questions=2,
        status=MockTestStatus.PUBLISHED.value if is_published else MockTestStatus.DRAFT.value,
        is_published=is_published,
    )
    db.add(test)
    db.commit()
    db.refresh(test)

    q1 = TestQuestion(
        test_id=test.id,
        question_text="What is the worst-case search time complexity in an unbalanced BST?",
        options=["O(1)", "O(log n)", "O(n)", "O(n log n)"],
        correct_option="C",
        marks=2,
        explanation="An unbalanced BST can degenerate into a linked list giving O(n) search.",
        order_index=1,
    )
    q2 = TestQuestion(
        test_id=test.id,
        question_text="Which Python data structure is implemented using a hash table?",
        options=["list", "tuple", "dict", "str"],
        correct_option="C",
        marks=2,
        explanation="Python dictionaries and sets are implemented as hash tables.",
        order_index=2,
    )
    db.add_all([q1, q2])
    db.commit()
    db.refresh(test)
    return test


def test_start_attempt_success(client: TestClient, db_session: Session):
    """AC-1: Learner starts an available test; new attempt and timer begin."""
    instructor = create_user(db_session, "inst_attempt1@test.com", role=UserRole.INSTRUCTOR)
    learner = create_user(db_session, "learner_attempt1@test.com", role=UserRole.LEARNER)
    test = create_sample_mock_test(db_session, instructor, is_published=True)

    headers = auth_header(learner)
    res = client.post(f"/api/v1/mock-tests/{test.id}/start-attempt", headers=headers)
    assert res.status_code == 201
    data = res.json()["data"]
    assert data["test_id"] == test.id
    assert data["learner_id"] == learner.id
    assert data["status"] == "ACTIVE"
    assert data["duration_minutes"] == 30
    assert data["remaining_seconds"] == 1800
    assert len(data["questions"]) == 2
    # Verify answers are hidden to prevent cheating
    for q in data["questions"]:
        assert q["correct_option"] is None
        assert q["explanation"] is None


def test_start_attempt_unavailable_fails(client: TestClient, db_session: Session):
    """AC-5: Starting an attempt on an unpublished test is denied."""
    instructor = create_user(db_session, "inst_attempt2@test.com", role=UserRole.INSTRUCTOR)
    learner = create_user(db_session, "learner_attempt2@test.com", role=UserRole.LEARNER)
    draft_test = create_sample_mock_test(db_session, instructor, is_published=False)

    headers = auth_header(learner)
    res = client.post(f"/api/v1/mock-tests/{draft_test.id}/start-attempt", headers=headers)
    assert res.status_code == 403


def test_save_intermediate_answers(client: TestClient, db_session: Session):
    """AC-2: Given active test, learner answers questions and answers are recorded."""
    instructor = create_user(db_session, "inst_attempt3@test.com", role=UserRole.INSTRUCTOR)
    learner = create_user(db_session, "learner_attempt3@test.com", role=UserRole.LEARNER)
    test = create_sample_mock_test(db_session, instructor, is_published=True)

    headers = auth_header(learner)
    start_res = client.post(f"/api/v1/mock-tests/{test.id}/start-attempt", headers=headers)
    attempt_id = start_res.json()["data"]["id"]
    questions = start_res.json()["data"]["questions"]
    q1_id = questions[0]["id"]

    # Record answer for question 1 and mark for review
    save_payload = {
        "answers": {str(q1_id): "C"},
        "marked_for_review": [q1_id],
    }
    save_res = client.put(f"/api/v1/attempts/{attempt_id}/answers", json=save_payload, headers=headers)
    assert save_res.status_code == 200
    saved_data = save_res.json()["data"]
    assert saved_data["answers"][str(q1_id)] == "C"
    assert q1_id in saved_data["marked_for_review"]

    # Reload attempt session to ensure state was persisted
    get_res = client.get(f"/api/v1/attempts/{attempt_id}", headers=headers)
    assert get_res.status_code == 200
    assert get_res.json()["data"]["answers"][str(q1_id)] == "C"


def test_submit_attempt_manual_success(client: TestClient, db_session: Session):
    """AC-4: Learner submits before time expires; attempt is completed with grade."""
    instructor = create_user(db_session, "inst_attempt4@test.com", role=UserRole.INSTRUCTOR)
    learner = create_user(db_session, "learner_attempt4@test.com", role=UserRole.LEARNER)
    test = create_sample_mock_test(db_session, instructor, is_published=True)

    headers = auth_header(learner)
    start_res = client.post(f"/api/v1/mock-tests/{test.id}/start-attempt", headers=headers)
    attempt_id = start_res.json()["data"]["id"]
    questions = start_res.json()["data"]["questions"]
    q1_id = questions[0]["id"]
    q2_id = questions[1]["id"]

    # Submit with both correct answers (q1: C, q2: C) -> 4/4 = 100%
    submit_payload = {
        "answers": {str(q1_id): "C", str(q2_id): "C"},
        "marked_for_review": [],
    }
    sub_res = client.post(f"/api/v1/attempts/{attempt_id}/submit-answers", json=submit_payload, headers=headers)
    assert sub_res.status_code == 200
    sub_data = sub_res.json()["data"]
    assert sub_data["status"] == "SUBMITTED"
    assert sub_data["score"] == 4.0
    assert sub_data["total_marks"] == 4
    assert sub_data["percentage"] == 100.0
    assert sub_data["is_passed"] is True
    assert sub_data["submitted_at"] is not None


def test_expired_attempt_auto_submits(client: TestClient, db_session: Session):
    """AC-3: When timer reaches zero / expires, attempt is submitted automatically."""
    instructor = create_user(db_session, "inst_attempt5@test.com", role=UserRole.INSTRUCTOR)
    learner = create_user(db_session, "learner_attempt5@test.com", role=UserRole.LEARNER)
    test = create_sample_mock_test(db_session, instructor, is_published=True)

    # Directly create an attempt that started 40 minutes ago (limit is 30 mins)
    past_time = datetime.now(timezone.utc) - timedelta(minutes=40)
    questions = test.questions
    q1 = questions[0]
    expired_attempt = TestAttempt(
        test_id=test.id,
        learner_id=learner.id,
        started_at=past_time,
        status=TestAttemptStatus.ACTIVE.value,
        answers={str(q1.id): "C"},
        marked_for_review=[],
    )
    db_session.add(expired_attempt)
    db_session.commit()
    db_session.refresh(expired_attempt)

    headers = auth_header(learner)
    # Fetching or saving answers on expired attempt triggers auto-submit
    res = client.get(f"/api/v1/attempts/{expired_attempt.id}", headers=headers)
    assert res.status_code == 200
    assert res.json()["data"]["status"] == "EXPIRED"
    assert res.json()["data"]["remaining_seconds"] == 0
