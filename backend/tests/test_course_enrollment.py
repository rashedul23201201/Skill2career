import pytest
from datetime import datetime, timezone
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.models.user import User, UserRole
from app.models.course import Course, CourseModule, Lesson, CourseStatus
from app.models.enrollment import CourseEnrollment, LessonProgress, EnrollmentStatus
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


def create_sample_course_with_lessons(
    db: Session,
    instructor: User,
    status: str = CourseStatus.PUBLISHED.value,
    lessons_count: int = 2,
) -> Course:
    course = Course(
        instructor_id=instructor.id,
        title="Test Data Structures & Algorithms",
        description="Comprehensive course on linear and nonlinear data structures.",
        category="Programming",
        level="Intermediate",
        price=0.0,
        is_free=True,
        status=status,
        duration_weeks=8,
    )
    db.add(course)
    db.commit()
    db.refresh(course)

    mod = CourseModule(
        course_id=course.id,
        title="Module 1: Foundations",
        order_index=1,
    )
    db.add(mod)
    db.commit()
    db.refresh(mod)

    for i in range(1, lessons_count + 1):
        lesson = Lesson(
            course_id=course.id,
            module_id=mod.id,
            title=f"Lesson {i}: Core Concepts",
            content_type="video",
            video_url="https://youtube.com/embed/test",
            duration_minutes=30,
            order_index=i,
        )
        db.add(lesson)

    db.commit()
    db.refresh(course)
    return course


def test_enroll_course_success(client: TestClient, db_session: Session):
    """AC-1: Learner enrolls in an available course; enrollment is recorded with 0% initial progress."""
    instructor = create_user(db_session, "inst_enr1@test.com", role=UserRole.INSTRUCTOR)
    learner = create_user(db_session, "learner_enr1@test.com", role=UserRole.LEARNER)
    course = create_sample_course_with_lessons(db_session, instructor, lessons_count=2)

    headers = auth_header(learner)
    res = client.post(f"/api/v1/courses/{course.id}/enroll", headers=headers)
    assert res.status_code == 201
    data = res.json()["data"]
    assert data["course_id"] == course.id
    assert data["user_id"] == learner.id
    assert data["status"] == "ACTIVE"
    assert data["progress_percentage"] == 0.0
    assert data["completed_lessons_count"] == 0
    assert data["total_lessons"] == 2


def test_enroll_course_duplicate_rejected(client: TestClient, db_session: Session):
    """AC-2: Duplicate enrollment attempt is rejected with 400 Bad Request."""
    instructor = create_user(db_session, "inst_enr2@test.com", role=UserRole.INSTRUCTOR)
    learner = create_user(db_session, "learner_enr2@test.com", role=UserRole.LEARNER)
    course = create_sample_course_with_lessons(db_session, instructor, lessons_count=2)

    headers = auth_header(learner)
    res1 = client.post(f"/api/v1/courses/{course.id}/enroll", headers=headers)
    assert res1.status_code == 201

    res2 = client.post(f"/api/v1/courses/{course.id}/enroll", headers=headers)
    assert res2.status_code == 400
    assert res2.json()["error_code"] == "ALREADY_ENROLLED"


def test_enroll_nonexistent_course_fails(client: TestClient, db_session: Session):
    """AC-5: Enrolling in a nonexistent course returns 404 Not Found."""
    learner = create_user(db_session, "learner_enr3@test.com", role=UserRole.LEARNER)
    headers = auth_header(learner)

    res = client.post("/api/v1/courses/99999/enroll", headers=headers)
    assert res.status_code == 404
    assert res.json()["error_code"] == "COURSE_NOT_FOUND"


def test_enroll_unpublished_course_fails(client: TestClient, db_session: Session):
    """AC-5: Enrolling in an unpublished (DRAFT) course is prohibited."""
    instructor = create_user(db_session, "inst_enr4@test.com", role=UserRole.INSTRUCTOR)
    learner = create_user(db_session, "learner_enr4@test.com", role=UserRole.LEARNER)
    draft_course = create_sample_course_with_lessons(
        db_session, instructor, status=CourseStatus.DRAFT.value, lessons_count=2
    )

    headers = auth_header(learner)
    res = client.post(f"/api/v1/courses/{draft_course.id}/enroll", headers=headers)
    assert res.status_code == 400
    assert res.json()["error_code"] == "COURSE_UNAVAILABLE"


def test_enroll_unauthenticated_fails(client: TestClient, db_session: Session):
    """AC-5: Unauthenticated enrollment requests return 401 Unauthorized."""
    instructor = create_user(db_session, "inst_enr5@test.com", role=UserRole.INSTRUCTOR)
    course = create_sample_course_with_lessons(db_session, instructor, lessons_count=2)

    res = client.post(f"/api/v1/courses/{course.id}/enroll")
    assert res.status_code == 401


def test_get_enrollment_status_and_progress(client: TestClient, db_session: Session):
    """AC-3: Valid enrollment allows checking status and viewing progress metrics."""
    instructor = create_user(db_session, "inst_enr6@test.com", role=UserRole.INSTRUCTOR)
    learner = create_user(db_session, "learner_enr6@test.com", role=UserRole.LEARNER)
    course = create_sample_course_with_lessons(db_session, instructor, lessons_count=3)
    headers = auth_header(learner)

    # Before enrollment
    status_res1 = client.get(f"/api/v1/courses/{course.id}/enrollment-status", headers=headers)
    assert status_res1.status_code == 200
    assert status_res1.json()["data"]["is_enrolled"] is False

    # Enroll
    client.post(f"/api/v1/courses/{course.id}/enroll", headers=headers)

    # After enrollment
    status_res2 = client.get(f"/api/v1/courses/{course.id}/enrollment-status", headers=headers)
    assert status_res2.status_code == 200
    assert status_res2.json()["data"]["is_enrolled"] is True

    progress_res = client.get(f"/api/v1/courses/{course.id}/progress", headers=headers)
    assert progress_res.status_code == 200
    p_data = progress_res.json()["data"]
    assert p_data["total_lessons"] == 3
    assert p_data["completed_lessons"] == 0
    assert p_data["remaining_lessons"] == 3
    assert p_data["progress_percentage"] == 0.0


def test_complete_lesson_progress_tracking(client: TestClient, db_session: Session):
    """AC-4: Completing lessons dynamically recalculates progress percentage."""
    instructor = create_user(db_session, "inst_enr7@test.com", role=UserRole.INSTRUCTOR)
    learner = create_user(db_session, "learner_enr7@test.com", role=UserRole.LEARNER)
    course = create_sample_course_with_lessons(db_session, instructor, lessons_count=2)
    headers = auth_header(learner)

    # Enroll
    client.post(f"/api/v1/courses/{course.id}/enroll", headers=headers)

    lessons = course.lessons
    lesson1 = lessons[0]
    lesson2 = lessons[1]

    # Complete lesson 1 -> 50%
    res1 = client.post(
        f"/api/v1/lessons/{lesson1.id}/complete",
        json={"is_completed": True},
        headers=headers,
    )
    assert res1.status_code == 200
    data1 = res1.json()["data"]
    assert data1["lesson_id"] == lesson1.id
    assert data1["is_completed"] is True
    assert data1["completed_lessons_count"] == 1
    assert data1["course_progress_percentage"] == 50.0

    # Complete lesson 2 -> 100%
    res2 = client.post(
        f"/api/v1/lessons/{lesson2.id}/complete",
        json={"is_completed": True},
        headers=headers,
    )
    assert res2.status_code == 200
    data2 = res2.json()["data"]
    assert data2["completed_lessons_count"] == 2
    assert data2["course_progress_percentage"] == 100.0

    # Verify overall course progress endpoint
    prog_res = client.get(f"/api/v1/courses/{course.id}/progress", headers=headers)
    p_data = prog_res.json()["data"]
    assert p_data["progress_percentage"] == 100.0
    assert p_data["status"] == "COMPLETED"
    assert lesson1.id in p_data["completed_lesson_ids"]
    assert lesson2.id in p_data["completed_lesson_ids"]


def test_toggle_lesson_incomplete(client: TestClient, db_session: Session):
    """AC-4: Unmarking a lesson as incomplete decreases progress percentage."""
    instructor = create_user(db_session, "inst_enr8@test.com", role=UserRole.INSTRUCTOR)
    learner = create_user(db_session, "learner_enr8@test.com", role=UserRole.LEARNER)
    course = create_sample_course_with_lessons(db_session, instructor, lessons_count=2)
    headers = auth_header(learner)

    client.post(f"/api/v1/courses/{course.id}/enroll", headers=headers)
    lesson1 = course.lessons[0]

    # Mark complete
    client.post(
        f"/api/v1/lessons/{lesson1.id}/complete",
        json={"is_completed": True},
        headers=headers,
    )

    # Unmark complete
    res = client.post(
        f"/api/v1/lessons/{lesson1.id}/complete",
        json={"is_completed": False},
        headers=headers,
    )
    assert res.status_code == 200
    assert res.json()["data"]["is_completed"] is False
    assert res.json()["data"]["course_progress_percentage"] == 0.0


def test_complete_lesson_not_enrolled_fails(client: TestClient, db_session: Session):
    """AC-5: Non-enrolled learner cannot record progress on course lessons."""
    instructor = create_user(db_session, "inst_enr9@test.com", role=UserRole.INSTRUCTOR)
    learner = create_user(db_session, "learner_enr9@test.com", role=UserRole.LEARNER)
    course = create_sample_course_with_lessons(db_session, instructor, lessons_count=1)
    headers = auth_header(learner)

    lesson = course.lessons[0]
    res = client.post(
        f"/api/v1/lessons/{lesson.id}/complete",
        json={"is_completed": True},
        headers=headers,
    )
    assert res.status_code == 403
    assert res.json()["error_code"] == "NOT_ENROLLED"


def test_get_enrolled_courses_list(client: TestClient, db_session: Session):
    """SKL-54 / Learners dashboard.png: Learner retrieves list of enrolled courses."""
    instructor = create_user(db_session, "inst_enr10@test.com", role=UserRole.INSTRUCTOR)
    learner = create_user(db_session, "learner_enr10@test.com", role=UserRole.LEARNER)
    c1 = create_sample_course_with_lessons(db_session, instructor, lessons_count=2)
    c2 = create_sample_course_with_lessons(db_session, instructor, lessons_count=4)
    headers = auth_header(learner)

    # Enroll in both
    client.post(f"/api/v1/courses/{c1.id}/enroll", headers=headers)
    client.post(f"/api/v1/courses/{c2.id}/enroll", headers=headers)

    # Complete 1 lesson in c1 (50%)
    client.post(
        f"/api/v1/lessons/{c1.lessons[0].id}/complete",
        json={"is_completed": True},
        headers=headers,
    )

    res = client.get("/api/v1/learners/enrolled-courses", headers=headers)
    assert res.status_code == 200
    data = res.json()["data"]
    assert data["total"] == 2
    assert len(data["items"]) == 2
    assert data["average_progress"] == 25.0  # (50 + 0) / 2
