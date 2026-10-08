import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from app.models.user import User, UserRole
from app.models.mock_test import MockTest, TestQuestion, MockTestStatus
from app.core.security import hash_password, create_access_token


def create_test_user(
    db: Session,
    email: str,
    role: UserRole = UserRole.LEARNER,
    first_name: str = "Test",
    last_name: str = "User",
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


def get_auth_headers(user: User) -> dict:
    token = create_access_token(
        subject=user.id,
        claims={"email": user.email, "role": user.role.value},
    )
    return {"Authorization": f"Bearer {token}"}


def test_create_mock_test_by_instructor_success(client: TestClient, db_session: Session):
    """AC-1: Authorized instructor creates a valid mock test successfully."""
    instructor = create_test_user(db_session, "inst_mock@skill2career.com", role=UserRole.INSTRUCTOR)
    headers = get_auth_headers(instructor)

    payload = {
        "title": "Data Structures & Algorithms Mock Test",
        "description": "Comprehensive practice exam covering trees, graphs, and dynamic programming.",
        "category": "Programming",
        "duration_minutes": 60,
        "passing_score": 50,
        "status": "DRAFT",
    }

    response = client.post("/api/v1/mock-tests", json=payload, headers=headers)
    assert response.status_code == 201
    data = response.json()
    assert data["success"] is True
    assert data["data"]["title"] == payload["title"]
    assert data["data"]["category"] == "Programming"
    assert data["data"]["duration_minutes"] == 60
    assert data["data"]["passing_score"] == 50
    assert data["data"]["status"] == "DRAFT"
    assert data["data"]["instructor_id"] == instructor.id


def test_create_mock_test_by_admin_success(client: TestClient, db_session: Session):
    """AC-1: Platform admin creates a mock test successfully."""
    admin = create_test_user(db_session, "admin_mock@skill2career.com", role=UserRole.ADMIN)
    headers = get_auth_headers(admin)

    payload = {
        "title": "Platform Standard Database Assessment",
        "description": "SQL joins, indexing strategies, and normalization principles.",
        "category": "Database",
        "duration_minutes": 45,
        "passing_score": 60,
        "status": "PUBLISHED",
    }

    response = client.post("/api/v1/mock-tests", json=payload, headers=headers)
    assert response.status_code == 201
    assert response.json()["data"]["is_published"] is True


def test_create_mock_test_by_learner_forbidden(client: TestClient, db_session: Session):
    """AC-5: Learner is rejected from creating mock tests."""
    learner = create_test_user(db_session, "learner_mock@skill2career.com", role=UserRole.LEARNER)
    headers = get_auth_headers(learner)

    payload = {
        "title": "Unauthorized Mock Test",
        "category": "Programming",
        "duration_minutes": 30,
        "passing_score": 50,
    }

    response = client.post("/api/v1/mock-tests", json=payload, headers=headers)
    assert response.status_code == 403


def test_create_mock_test_validation_error_on_missing_fields(client: TestClient, db_session: Session):
    """AC-4: Incomplete test data triggers validation failure."""
    instructor = create_test_user(db_session, "inst_val@skill2career.com", role=UserRole.INSTRUCTOR)
    headers = get_auth_headers(instructor)

    payload = {
        "title": "AB",  # Under min length 3
        "category": "P",  # Under min length 2
        "duration_minutes": -5,  # Invalid duration
        "passing_score": 150,  # Over max 100
    }

    response = client.post("/api/v1/mock-tests", json=payload, headers=headers)
    assert response.status_code == 422


def test_add_question_to_mock_test_success(client: TestClient, db_session: Session):
    """AC-2: Questions are associated with the correct test."""
    instructor = create_test_user(db_session, "inst_q@skill2career.com", role=UserRole.INSTRUCTOR)
    headers = get_auth_headers(instructor)

    test = MockTest(
        instructor_id=instructor.id,
        title="Web Security Assessment",
        category="Web Development",
        duration_minutes=30,
        passing_score=50,
        status="DRAFT",
    )
    db_session.add(test)
    db_session.commit()
    db_session.refresh(test)

    q_payload = {
        "question_text": "Which HTTP response header mitigates Cross-Site Scripting (XSS) attacks?",
        "options": [
            "Content-Security-Policy",
            "Access-Control-Allow-Origin",
            "X-Frame-Options",
            "Strict-Transport-Security",
        ],
        "correct_option": "A",
        "marks": 2,
        "explanation": "Content-Security-Policy restricts sources of executable scripts in modern browsers.",
        "order_index": 0,
    }

    response = client.post(f"/api/v1/mock-tests/{test.id}/questions", json=q_payload, headers=headers)
    assert response.status_code == 201
    data = response.json()["data"]
    assert data["question_text"] == q_payload["question_text"]
    assert data["test_id"] == test.id
    assert len(data["options"]) == 4
    assert data["correct_option"] == "A"


def test_add_question_validation_error_few_options(client: TestClient, db_session: Session):
    """AC-4: Question with fewer than 2 options is rejected."""
    instructor = create_test_user(db_session, "inst_opt@skill2career.com", role=UserRole.INSTRUCTOR)
    headers = get_auth_headers(instructor)

    test = MockTest(
        instructor_id=instructor.id,
        title="Testing Options Count",
        category="Programming",
        duration_minutes=30,
        passing_score=50,
        status="DRAFT",
    )
    db_session.add(test)
    db_session.commit()
    db_session.refresh(test)

    q_payload = {
        "question_text": "Is Python interpreted?",
        "options": ["Yes"],
        "correct_option": "Yes",
    }

    response = client.post(f"/api/v1/mock-tests/{test.id}/questions", json=q_payload, headers=headers)
    assert response.status_code in [400, 422]


def test_learner_can_view_published_mock_test(client: TestClient, db_session: Session):
    """AC-3: Published test is discoverable by learners, correct answers masked in preview."""
    instructor = create_test_user(db_session, "inst_pub@skill2career.com", role=UserRole.INSTRUCTOR)
    learner = create_test_user(db_session, "learner_pub@skill2career.com", role=UserRole.LEARNER)

    test = MockTest(
        instructor_id=instructor.id,
        title="Publicly Available Mock Test",
        category="Programming",
        duration_minutes=45,
        passing_score=50,
        status="PUBLISHED",
        is_published=True,
    )
    db_session.add(test)
    db_session.commit()
    db_session.refresh(test)

    q = TestQuestion(
        test_id=test.id,
        question_text="What is 2 + 2?",
        options=["3", "4", "5", "6"],
        correct_option="B",
        explanation="Basic arithmetic.",
    )
    db_session.add(q)
    db_session.commit()

    learner_headers = get_auth_headers(learner)
    response = client.get(f"/api/v1/mock-tests/{test.id}", headers=learner_headers)
    assert response.status_code == 200
    data = response.json()["data"]
    assert data["id"] == test.id
    assert len(data["questions"]) == 1
    # Learner should not see answer key in public test preview
    assert data["questions"][0]["correct_option"] is None


def test_learner_cannot_view_draft_mock_test(client: TestClient, db_session: Session):
    """AC-3, AC-5: Draft test is forbidden for learners."""
    instructor = create_test_user(db_session, "inst_draft@skill2career.com", role=UserRole.INSTRUCTOR)
    learner = create_test_user(db_session, "learner_draft@skill2career.com", role=UserRole.LEARNER)

    test = MockTest(
        instructor_id=instructor.id,
        title="Draft Assessment In Progress",
        category="Database",
        duration_minutes=30,
        passing_score=50,
        status="DRAFT",
        is_published=False,
    )
    db_session.add(test)
    db_session.commit()
    db_session.refresh(test)

    learner_headers = get_auth_headers(learner)
    response = client.get(f"/api/v1/mock-tests/{test.id}", headers=learner_headers)
    assert response.status_code == 403


def test_unauthorized_user_cannot_modify_other_instructor_test(client: TestClient, db_session: Session):
    """AC-5: Another instructor cannot modify tests they do not own."""
    instructor1 = create_test_user(db_session, "inst1@skill2career.com", role=UserRole.INSTRUCTOR)
    instructor2 = create_test_user(db_session, "inst2@skill2career.com", role=UserRole.INSTRUCTOR)

    test = MockTest(
        instructor_id=instructor1.id,
        title="Instructor 1 Unique Test",
        category="Programming",
        duration_minutes=45,
        passing_score=50,
        status="DRAFT",
    )
    db_session.add(test)
    db_session.commit()
    db_session.refresh(test)

    headers2 = get_auth_headers(instructor2)
    update_payload = {"title": "Attempted Hijack"}
    response = client.put(f"/api/v1/mock-tests/{test.id}", json=update_payload, headers=headers2)
    assert response.status_code == 403


def test_author_can_update_mock_test(client: TestClient, db_session: Session):
    """Author successfully updates test metadata."""
    instructor = create_test_user(db_session, "inst_update@skill2career.com", role=UserRole.INSTRUCTOR)
    headers = get_auth_headers(instructor)

    test = MockTest(
        instructor_id=instructor.id,
        title="Initial Title",
        category="Programming",
        duration_minutes=30,
        passing_score=50,
        status="DRAFT",
    )
    db_session.add(test)
    db_session.commit()
    db_session.refresh(test)

    response = client.put(
        f"/api/v1/mock-tests/{test.id}",
        json={"title": "Updated Test Title", "duration_minutes": 50},
        headers=headers,
    )
    assert response.status_code == 200
    assert response.json()["data"]["title"] == "Updated Test Title"
    assert response.json()["data"]["duration_minutes"] == 50


def test_bulk_sync_questions(client: TestClient, db_session: Session):
    """Instructor bulk synchronizes question bank."""
    instructor = create_test_user(db_session, "inst_sync@skill2career.com", role=UserRole.INSTRUCTOR)
    headers = get_auth_headers(instructor)

    test = MockTest(
        instructor_id=instructor.id,
        title="Sync Questions Test",
        category="Programming",
        duration_minutes=30,
        passing_score=50,
        status="DRAFT",
    )
    db_session.add(test)
    db_session.commit()
    db_session.refresh(test)

    sync_payload = {
        "questions": [
            {
                "question_text": "What is 1 + 1?",
                "options": ["1", "2", "3", "4"],
                "correct_option": "B",
                "marks": 1,
                "order_index": 0,
            },
            {
                "question_text": "What is 2 + 2?",
                "options": ["2", "3", "4", "5"],
                "correct_option": "C",
                "marks": 1,
                "order_index": 1,
            },
        ]
    }

    response = client.post(f"/api/v1/mock-tests/{test.id}/questions/sync", json=sync_payload, headers=headers)
    assert response.status_code == 200
    assert len(response.json()["data"]) == 2

    # Check updated total_questions on test
    test_resp = client.get(f"/api/v1/mock-tests/{test.id}", headers=headers)
    assert test_resp.json()["data"]["total_questions"] == 2
