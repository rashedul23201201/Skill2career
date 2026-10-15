import pytest
from datetime import datetime, timezone
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.models.user import User, UserRole
from app.models.course import Course, CourseStatus, CourseLevel, CourseModule, Lesson
from app.models.mock_test import MockTest, MockTestStatus, TestQuestion
from app.models.moderation import ModerationStatus, ContentType, ModerationAction, ContentModerationLog
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


def get_headers(user: User) -> dict:
    token = create_access_token(
        subject=user.id,
        claims={"email": user.email, "role": user.role.value if hasattr(user.role, "value") else str(user.role)},
    )
    return {"Authorization": f"Bearer {token}"}


def test_admin_rbac_protection(client: TestClient, db_session: Session):
    """Ensure non-admin users cannot access administrative moderation routes (SKL-25)."""
    learner = create_user(db_session, "learner_mod@example.com", UserRole.LEARNER)
    instructor = create_user(db_session, "inst_mod@example.com", UserRole.INSTRUCTOR)

    learner_headers = get_headers(learner)
    inst_headers = get_headers(instructor)

    # Learner should be denied
    resp1 = client.get("/api/v1/admin/moderation/pending", headers=learner_headers)
    assert resp1.status_code == 403

    # Instructor should be denied admin moderation endpoints
    resp2 = client.get("/api/v1/admin/moderation/pending", headers=inst_headers)
    assert resp2.status_code == 403

    # Unauthenticated should be denied
    resp3 = client.get("/api/v1/admin/moderation/pending")
    assert resp3.status_code == 401


def test_moderation_queue_and_stats(client: TestClient, db_session: Session):
    """Verify pending moderation queue and overview metric counters (SKL-25)."""
    admin = create_user(db_session, "admin_mod@example.com", UserRole.ADMIN)
    instructor = create_user(db_session, "inst2_mod@example.com", UserRole.INSTRUCTOR)
    admin_headers = get_headers(admin)

    # Create a pending course
    course = Course(
        instructor_id=instructor.id,
        title="Python Deep Dive",
        description="Comprehensive course on Python",
        category="Development",
        level="Intermediate",
        price=49.99,
        is_free=False,
        status="PUBLISHED",
        moderation_status=ModerationStatus.PENDING_REVIEW.value,
    )
    db_session.add(course)

    # Create a pending mock test
    test = MockTest(
        instructor_id=instructor.id,
        title="Python Certification Practice",
        description="Assess Python proficiency",
        category="Development",
        duration_minutes=45,
        passing_score=70,
        status="PUBLISHED",
        is_published=True,
        moderation_status=ModerationStatus.PENDING_REVIEW.value,
    )
    db_session.add(test)
    db_session.commit()

    # Query pending moderation queue
    resp = client.get("/api/v1/admin/moderation/pending", headers=admin_headers)
    assert resp.status_code == 200
    data = resp.json()["data"]
    assert data["total_pending"] >= 2
    assert any(c["id"] == course.id for c in data["courses"])
    assert any(t["id"] == test.id for t in data["mock_tests"])

    # Query moderation stats
    stats_resp = client.get("/api/v1/admin/moderation/stats", headers=admin_headers)
    assert stats_resp.status_code == 200
    stats = stats_resp.json()["data"]
    assert stats["pending_courses"] >= 1
    assert stats["pending_tests"] >= 1
    assert stats["total_pending"] >= 2


def test_course_and_mock_test_preview(client: TestClient, db_session: Session):
    """Verify detailed admin preview drawer payloads for inspection (SKL-25)."""
    admin = create_user(db_session, "admin_preview@example.com", UserRole.ADMIN)
    instructor = create_user(db_session, "inst_preview@example.com", UserRole.INSTRUCTOR)
    admin_headers = get_headers(admin)

    # Course with modules and lessons
    course = Course(
        instructor_id=instructor.id,
        title="Fullstack React & Node",
        description="Learn fullstack engineering",
        category="Web Development",
        level="All Levels",
        status="PUBLISHED",
        moderation_status=ModerationStatus.PENDING_REVIEW.value,
    )
    db_session.add(course)
    db_session.commit()
    db_session.refresh(course)

    module = CourseModule(course_id=course.id, title="Module 1: Introduction", order_index=0)
    db_session.add(module)
    db_session.commit()
    db_session.refresh(module)

    lesson = Lesson(
        course_id=course.id,
        module_id=module.id,
        title="Welcome to the course",
        content_type="video",
        duration_minutes=10,
        order_index=0,
    )
    db_session.add(lesson)

    # Mock test with questions
    mock_test = MockTest(
        instructor_id=instructor.id,
        title="React Core Concepts",
        description="Core React MCQs",
        category="Web Development",
        duration_minutes=30,
        passing_score=80,
        status="PUBLISHED",
        is_published=True,
        moderation_status=ModerationStatus.PENDING_REVIEW.value,
    )
    db_session.add(mock_test)
    db_session.commit()
    db_session.refresh(mock_test)

    question = TestQuestion(
        test_id=mock_test.id,
        question_text="What hook is used for side effects?",
        options=["useState", "useEffect", "useMemo", "useCallback"],
        correct_option="B",
        marks=2,
        explanation="useEffect is specifically designated for managing lifecycle side effects.",
        order_index=0,
    )
    db_session.add(question)
    db_session.commit()

    # Course preview check
    c_resp = client.get(f"/api/v1/admin/moderation/courses/{course.id}/preview", headers=admin_headers)
    assert c_resp.status_code == 200
    c_data = c_resp.json()["data"]
    assert c_data["id"] == course.id
    assert len(c_data["modules"]) == 1
    assert len(c_data["modules"][0]["lessons"]) == 1
    assert c_data["modules"][0]["lessons"][0]["title"] == "Welcome to the course"

    # Mock test preview check
    t_resp = client.get(f"/api/v1/admin/moderation/mock-tests/{mock_test.id}/preview", headers=admin_headers)
    assert t_resp.status_code == 200
    t_data = t_resp.json()["data"]
    assert t_data["id"] == mock_test.id
    assert len(t_data["questions"]) == 1
    assert t_data["questions"][0]["correct_option"] == "B"
    assert "useEffect is specifically" in t_data["questions"][0]["explanation"]


def test_approve_and_restrict_course(client: TestClient, db_session: Session):
    """Verify course approval, restriction, catalog exclusion, and audit trail (SKL-25)."""
    admin = create_user(db_session, "admin_approve@example.com", UserRole.ADMIN)
    instructor = create_user(db_session, "inst_approve@example.com", UserRole.INSTRUCTOR)
    learner = create_user(db_session, "learner_catalog@example.com", UserRole.LEARNER)

    admin_headers = get_headers(admin)
    learner_headers = get_headers(learner)

    course = Course(
        instructor_id=instructor.id,
        title="Machine Learning Foundations",
        description="Intro to ML algorithms",
        category="Data Science",
        level="Intermediate",
        status="PUBLISHED",
        moderation_status=ModerationStatus.PENDING_REVIEW.value,
    )
    db_session.add(course)
    db_session.commit()
    db_session.refresh(course)

    # 1. While PENDING_REVIEW, public learner should NOT find it in /courses
    cat_resp = client.get("/api/v1/courses", headers=learner_headers)
    assert cat_resp.status_code == 200
    course_ids = [c["id"] for c in cat_resp.json()["data"]["items"]]
    assert course.id not in course_ids

    # 2. While PENDING_REVIEW, learner accessing course details gets 404
    detail_resp = client.get(f"/api/v1/courses/{course.id}", headers=learner_headers)
    assert detail_resp.status_code == 404

    # 3. Admin approves course
    approve_resp = client.post(
        f"/api/v1/admin/moderation/courses/{course.id}/approve",
        headers=admin_headers,
        json={"notes": "High quality curriculum aligned with our standards"},
    )
    assert approve_resp.status_code == 200
    app_data = approve_resp.json()["data"]
    assert app_data["moderation_status"] == ModerationStatus.APPROVED.value
    assert app_data["moderated_by"] == admin.id

    # 4. Now learner CAN find it in /courses
    cat_resp2 = client.get("/api/v1/courses", headers=learner_headers)
    assert cat_resp2.status_code == 200
    course_ids2 = [c["id"] for c in cat_resp2.json()["data"]["items"]]
    assert course.id in course_ids2

    # 5. Now learner can view details
    detail_resp2 = client.get(f"/api/v1/courses/{course.id}", headers=learner_headers)
    assert detail_resp2.status_code == 200
    assert detail_resp2.json()["data"]["title"] == "Machine Learning Foundations"

    # 6. Admin restricts course (requires non-empty reason)
    bad_restrict = client.post(
        f"/api/v1/admin/moderation/courses/{course.id}/restrict",
        headers=admin_headers,
        json={"reason": ""},
    )
    assert bad_restrict.status_code == 400

    restrict_resp = client.post(
        f"/api/v1/admin/moderation/courses/{course.id}/restrict",
        headers=admin_headers,
        json={"reason": "Contains copyrighted material in lecture slides"},
    )
    assert restrict_resp.status_code == 200
    res_data = restrict_resp.json()["data"]
    assert res_data["moderation_status"] == ModerationStatus.RESTRICTED.value

    # 7. Restricted course is immediately hidden from catalog and learner GET
    cat_resp3 = client.get("/api/v1/courses", headers=learner_headers)
    assert course.id not in [c["id"] for c in cat_resp3.json()["data"]["items"]]

    detail_resp3 = client.get(f"/api/v1/courses/{course.id}", headers=learner_headers)
    assert detail_resp3.status_code == 404

    # But authoring instructor and admin can still view it
    inst_headers = get_headers(instructor)
    inst_view = client.get(f"/api/v1/courses/{course.id}", headers=inst_headers)
    assert inst_view.status_code == 200

    admin_view = client.get(f"/api/v1/courses/{course.id}", headers=admin_headers)
    assert admin_view.status_code == 200


def test_approve_and_restrict_mock_test(client: TestClient, db_session: Session):
    """Verify mock test moderation lifecycle and catalog filtering (SKL-25)."""
    admin = create_user(db_session, "admin_test_mod@example.com", UserRole.ADMIN)
    instructor = create_user(db_session, "inst_test_mod@example.com", UserRole.INSTRUCTOR)
    learner = create_user(db_session, "learner_test_mod@example.com", UserRole.LEARNER)

    admin_headers = get_headers(admin)
    learner_headers = get_headers(learner)

    mock_test = MockTest(
        instructor_id=instructor.id,
        title="Docker and Containers",
        description="Containerization basics",
        category="DevOps",
        duration_minutes=25,
        passing_score=75,
        status="PUBLISHED",
        is_published=True,
        moderation_status=ModerationStatus.PENDING_REVIEW.value,
    )
    db_session.add(mock_test)
    db_session.commit()
    db_session.refresh(mock_test)

    # 1. Pending test excluded from learner catalog
    tests_resp = client.get("/api/v1/mock-tests", headers=learner_headers)
    assert tests_resp.status_code == 200
    test_ids = [t["id"] for t in tests_resp.json()["data"]["items"]]
    assert mock_test.id not in test_ids

    # 2. Admin approves mock test
    app_resp = client.post(
        f"/api/v1/admin/moderation/mock-tests/{mock_test.id}/approve",
        headers=admin_headers,
        json={"notes": "Valid questions verified"},
    )
    assert app_resp.status_code == 200
    assert app_resp.json()["data"]["moderation_status"] == ModerationStatus.APPROVED.value

    # 3. Approved test is now in learner catalog
    tests_resp2 = client.get("/api/v1/mock-tests", headers=learner_headers)
    test_ids2 = [t["id"] for t in tests_resp2.json()["data"]["items"]]
    assert mock_test.id in test_ids2

    # 4. Admin restricts mock test
    rest_resp = client.post(
        f"/api/v1/admin/moderation/mock-tests/{mock_test.id}/restrict",
        headers=admin_headers,
        json={"reason": "Contains inaccurate test answers in section 2"},
    )
    assert rest_resp.status_code == 200
    assert rest_resp.json()["data"]["moderation_status"] == ModerationStatus.RESTRICTED.value

    # 5. Restricted test is hidden from learner catalog and blocked from single GET
    tests_resp3 = client.get("/api/v1/mock-tests", headers=learner_headers)
    assert mock_test.id not in [t["id"] for t in tests_resp3.json()["data"]["items"]]

    get_resp = client.get(f"/api/v1/mock-tests/{mock_test.id}", headers=learner_headers)
    assert get_resp.status_code == 403


def test_submit_for_review_flow(client: TestClient, db_session: Session):
    """Verify instructor can submit authored content for moderation review (SKL-25)."""
    instructor1 = create_user(db_session, "inst1_submit@example.com", UserRole.INSTRUCTOR)
    instructor2 = create_user(db_session, "inst2_submit@example.com", UserRole.INSTRUCTOR)

    h1 = get_headers(instructor1)
    h2 = get_headers(instructor2)

    course = Course(
        instructor_id=instructor1.id,
        title="Draft Course",
        description="Work in progress",
        category="Design",
        level="Beginner",
        status="DRAFT",
        moderation_status=ModerationStatus.DRAFT.value,
    )
    db_session.add(course)
    db_session.commit()
    db_session.refresh(course)

    # Instructor 2 cannot submit Instructor 1's course
    forbidden_resp = client.post(f"/api/v1/courses/{course.id}/submit-review", headers=h2)
    assert forbidden_resp.status_code == 403

    # Instructor 1 submits their course for review
    sub_resp = client.post(f"/api/v1/courses/{course.id}/submit-review", headers=h1)
    assert sub_resp.status_code == 200
    assert sub_resp.json()["data"]["moderation_status"] == ModerationStatus.PENDING_REVIEW.value

    # Repeat for mock test
    test = MockTest(
        instructor_id=instructor1.id,
        title="Draft Test",
        description="Draft test description",
        category="Design",
        duration_minutes=30,
        passing_score=60,
        status="DRAFT",
        is_published=False,
        moderation_status=ModerationStatus.DRAFT.value,
    )
    db_session.add(test)
    db_session.commit()
    db_session.refresh(test)

    sub_test_resp = client.post(f"/api/v1/mock-tests/{test.id}/submit-review", headers=h1)
    assert sub_test_resp.status_code == 200
    assert sub_test_resp.json()["data"]["moderation_status"] == ModerationStatus.PENDING_REVIEW.value


def test_moderation_logs_and_item_filtering(client: TestClient, db_session: Session):
    """Verify audit logs and item list filtering by status and content type (SKL-25)."""
    admin = create_user(db_session, "admin_audit@example.com", UserRole.ADMIN)
    admin_headers = get_headers(admin)

    # Fetch logs
    log_resp = client.get("/api/v1/admin/moderation/logs", headers=admin_headers)
    assert log_resp.status_code == 200
    assert isinstance(log_resp.json()["data"], list)

    # Filter items by status
    items_resp = client.get(
        "/api/v1/admin/moderation/items?status=PENDING_REVIEW&content_type=COURSE",
        headers=admin_headers,
    )
    assert items_resp.status_code == 200
    items = items_resp.json()["data"]
    for it in items:
        assert it["content_type"] == ContentType.COURSE.value
        assert it["moderation_status"] == ModerationStatus.PENDING_REVIEW.value
