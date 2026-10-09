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


def auth_header(user: User) -> dict:
    token = create_access_token(
        subject=user.id,
        claims={"email": user.email, "role": user.role.value},
    )
    return {"Authorization": f"Bearer {token}"}


def create_sample_mock_test_with_topics(db: Session, instructor: User) -> MockTest:
    test = MockTest(
        instructor_id=instructor.id,
        title="Data Structures & Algorithms Assessment",
        description="Assessing BSTs, Graphs, and Sorting with topic tags.",
        category="Programming",
        duration_minutes=60,
        passing_score=50,
        total_questions=3,
        status=MockTestStatus.PUBLISHED.value,
        is_published=True,
    )
    db.add(test)
    db.commit()
    db.refresh(test)

    q1 = TestQuestion(
        test_id=test.id,
        question_text="What is the worst-case time complexity of searching in a balanced BST?",
        options=["O(1)", "O(log n)", "O(n)", "O(n log n)"],
        correct_option="B",
        marks=2,
        explanation="In a balanced BST, lookup operations take O(log n).",
        order_index=1,
        topic="Binary Search Trees",
        difficulty="Easy",
    )
    q2 = TestQuestion(
        test_id=test.id,
        question_text="What is the recursive DFS traversal space complexity on a graph?",
        options=["O(1)", "O(V)", "O(V + E)", "O(E)"],
        correct_option="B",
        marks=2,
        explanation="Recursive DFS uses stack proportional to depth O(V).",
        order_index=2,
        topic="Graph Algorithms",
        difficulty="Medium",
    )
    q3 = TestQuestion(
        test_id=test.id,
        question_text="Which algorithm is an O(n log n) stable sorting algorithm?",
        options=["Quick Sort", "Heap Sort", "Merge Sort", "Selection Sort"],
        correct_option="C",
        marks=3,
        explanation="Merge Sort guarantees O(n log n) stable sort.",
        order_index=3,
        topic="Sorting",
        difficulty="Hard",
    )
    db.add_all([q1, q2, q3])
    db.commit()
    db.refresh(test)
    return test


def test_evaluate_and_get_result_ac1_ac2(client: TestClient, db_session: Session):
    """AC-1 & AC-2: Correct score calculation upon completion and result display."""
    instructor = create_user(db_session, "inst_results1@test.com", role=UserRole.INSTRUCTOR)
    learner = create_user(db_session, "learner_results1@test.com", role=UserRole.LEARNER)
    test = create_sample_mock_test_with_topics(db_session, instructor)

    headers = auth_header(learner)
    start_res = client.post(f"/api/v1/mock-tests/{test.id}/start-attempt", headers=headers)
    assert start_res.status_code == 201
    attempt_id = start_res.json()["data"]["id"]
    questions = start_res.json()["data"]["questions"]
    q1_id, q2_id, q3_id = questions[0]["id"], questions[1]["id"], questions[2]["id"]

    # Answer q1 and q2 correctly (4 marks), q3 incorrectly ('A') -> 4/7 marks = 57.14%
    submit_payload = {
        "answers": {str(q1_id): "B", str(q2_id): "B", str(q3_id): "A"},
    }
    sub_res = client.post(f"/api/v1/attempts/{attempt_id}/submit-answers", json=submit_payload, headers=headers)
    assert sub_res.status_code == 200

    # AC-2: Fetch result details
    res = client.get(f"/api/v1/attempts/{attempt_id}/result", headers=headers)
    assert res.status_code == 200
    data = res.json()["data"]

    # Verify score metrics
    assert data["attempt_id"] == attempt_id
    assert data["test_id"] == test.id
    assert data["total_score"] == 4.0
    assert data["total_marks"] == 7
    assert data["percentage"] == pytest.approx(57.14, 0.01)
    assert data["is_passed"] is True
    assert data["accuracy"] == pytest.approx(66.7, 0.1)


def test_performance_analysis_ac3(client: TestClient, db_session: Session):
    """AC-3: Relevant performance analysis information (topics, difficulty, percentile) is shown."""
    instructor = create_user(db_session, "inst_results2@test.com", role=UserRole.INSTRUCTOR)
    learner = create_user(db_session, "learner_results2@test.com", role=UserRole.LEARNER)
    test = create_sample_mock_test_with_topics(db_session, instructor)

    headers = auth_header(learner)
    start_res = client.post(f"/api/v1/mock-tests/{test.id}/start-attempt", headers=headers)
    attempt_id = start_res.json()["data"]["id"]
    questions = start_res.json()["data"]["questions"]
    q1_id, q2_id, q3_id = questions[0]["id"], questions[1]["id"], questions[2]["id"]

    # Submit all correct answers
    submit_payload = {
        "answers": {str(q1_id): "B", str(q2_id): "B", str(q3_id): "C"},
    }
    client.post(f"/api/v1/attempts/{attempt_id}/submit-answers", json=submit_payload, headers=headers)

    res = client.get(f"/api/v1/attempts/{attempt_id}/result", headers=headers)
    assert res.status_code == 200
    data = res.json()["data"]

    # Topic Breakdown
    topic_names = [t["topic"] for t in data["topic_breakdown"]]
    assert "Binary Search Trees" in topic_names
    assert "Graph Algorithms" in topic_names
    assert "Sorting" in topic_names

    bst_topic = next(t for t in data["topic_breakdown"] if t["topic"] == "Binary Search Trees")
    assert bst_topic["percentage"] == 100.0

    # Difficulty Analysis
    diff_names = [d["difficulty"] for d in data["difficulty_analysis"]]
    assert "Easy" in diff_names
    assert "Medium" in diff_names
    assert "Hard" in diff_names

    # Percentile
    assert "percentile_label" in data
    assert "Top" in data["percentile_label"]

    # Question reviews
    assert len(data["question_reviews"]) == 3
    assert all(qr["is_correct"] is True for qr in data["question_reviews"])


def test_unauthorized_result_access_ac4(client: TestClient, db_session: Session):
    """AC-4: User attempting to access another user's restricted result is denied access (403)."""
    instructor = create_user(db_session, "inst_results3@test.com", role=UserRole.INSTRUCTOR)
    learner1 = create_user(db_session, "learner_one@test.com", role=UserRole.LEARNER)
    learner2 = create_user(db_session, "learner_two@test.com", role=UserRole.LEARNER)
    test = create_sample_mock_test_with_topics(db_session, instructor)

    # Learner 1 takes and completes test
    headers1 = auth_header(learner1)
    start_res = client.post(f"/api/v1/mock-tests/{test.id}/start-attempt", headers=headers1)
    attempt_id = start_res.json()["data"]["id"]
    client.post(f"/api/v1/attempts/{attempt_id}/submit-answers", json={"answers": {}}, headers=headers1)

    # Learner 2 tries to access Learner 1's result
    headers2 = auth_header(learner2)
    res = client.get(f"/api/v1/attempts/{attempt_id}/result", headers=headers2)
    assert res.status_code == 403
    assert "permission" in res.json()["message"].lower()


def test_result_processing_error_cases_ac5(client: TestClient, db_session: Session):
    """AC-5: Appropriate errors for nonexistent attempt or active attempt."""
    instructor = create_user(db_session, "inst_results4@test.com", role=UserRole.INSTRUCTOR)
    learner = create_user(db_session, "learner_results4@test.com", role=UserRole.LEARNER)
    test = create_sample_mock_test_with_topics(db_session, instructor)

    headers = auth_header(learner)

    # 1. Nonexistent attempt ID -> 404
    res_not_found = client.get("/api/v1/attempts/99999/result", headers=headers)
    assert res_not_found.status_code == 404

    # 2. In-progress attempt without submitting -> 400
    start_res = client.post(f"/api/v1/mock-tests/{test.id}/start-attempt", headers=headers)
    active_attempt_id = start_res.json()["data"]["id"]

    res_active = client.get(f"/api/v1/attempts/{active_attempt_id}/result", headers=headers)
    assert res_active.status_code == 400
    assert "in progress" in res_active.json()["message"].lower()


def test_learner_test_history_and_instructor_view(client: TestClient, db_session: Session):
    """Test history endpoints for learner and instructor views."""
    instructor = create_user(db_session, "inst_results5@test.com", role=UserRole.INSTRUCTOR)
    learner = create_user(db_session, "learner_results5@test.com", role=UserRole.LEARNER)
    test = create_sample_mock_test_with_topics(db_session, instructor)

    headers = auth_header(learner)
    start_res = client.post(f"/api/v1/mock-tests/{test.id}/start-attempt", headers=headers)
    attempt_id = start_res.json()["data"]["id"]
    client.post(f"/api/v1/attempts/{attempt_id}/submit-answers", json={"answers": {}}, headers=headers)

    # Learner history via /api/v1/learners/test-history
    res_hist = client.get("/api/v1/learners/test-history", headers=headers)
    assert res_hist.status_code == 200
    assert len(res_hist.json()["data"]) >= 1

    # Learner history via /api/v1/attempts/history
    res_att_hist = client.get("/api/v1/attempts/history", headers=headers)
    assert res_att_hist.status_code == 200
    assert len(res_att_hist.json()["data"]) >= 1

    # Instructor monitoring via /api/v1/mock-tests/{id}/results
    inst_headers = auth_header(instructor)
    res_inst = client.get(f"/api/v1/mock-tests/{test.id}/results", headers=inst_headers)
    assert res_inst.status_code == 200
    assert len(res_inst.json()["data"]) >= 1
