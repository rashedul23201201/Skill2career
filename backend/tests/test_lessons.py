import io
import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from app.models.user import User, UserRole
from app.models.course import Course, CourseStatus, CourseLevel
from app.core.security import hash_password, create_access_token


def create_test_user(
    db: Session,
    email: str,
    role: UserRole = UserRole.LEARNER,
    first_name: str = "Test",
    last_name: str = "User",
) -> User:
    """Helper to create a user directly in test db."""
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
    """Generate auth headers for test client."""
    token = create_access_token(
        subject=user.id,
        claims={"email": user.email, "role": user.role.value},
    )
    return {"Authorization": f"Bearer {token}"}


def create_test_course(
    db: Session,
    instructor: User,
    title: str = "Data Structures & Algorithms",
    status: CourseStatus = CourseStatus.PUBLISHED,
) -> Course:
    """Helper to create a course directly in test db."""
    course = Course(
        instructor_id=instructor.id,
        title=title,
        description="Comprehensive curriculum for engineering candidates.",
        category="Programming",
        level=CourseLevel.INTERMEDIATE.value,
        price=0.0,
        is_free=True,
        status=status.value,
        duration_weeks=10,
    )
    db.add(course)
    db.commit()
    db.refresh(course)
    return course


def test_create_lesson_by_instructor_success(client: TestClient, db_session: Session):
    """AC-1: Authorized instructor creates a valid lesson successfully."""
    instructor = create_test_user(db_session, "inst_lesson1@skill2career.com", role=UserRole.INSTRUCTOR)
    headers = get_auth_headers(instructor)
    course = create_test_course(db_session, instructor)

    payload = {
        "title": "Trees and Tree Traversal",
        "content_type": "video",
        "video_url": "https://www.youtube.com/embed/dQw4w9WgXcQ",
        "duration_minutes": 32,
        "attachments": [
            {"name": "Lecture Notes.pdf", "size": "2.4 MB · High Yield"},
            {"name": "Previous Questions.pdf", "size": "1.8 MB · Bank & Govt Sets"},
        ],
    }
    response = client.post(f"/api/v1/courses/{course.id}/lessons", json=payload, headers=headers)
    assert response.status_code == 201
    data = response.json()
    assert data["success"] is True
    assert data["data"]["title"] == "Trees and Tree Traversal"
    assert data["data"]["course_id"] == course.id
    assert len(data["data"]["attachments"]) == 2


def test_create_lesson_with_module_association(client: TestClient, db_session: Session):
    """AC-2: Lesson is correctly associated with a curriculum module."""
    instructor = create_test_user(db_session, "inst_mod1@skill2career.com", role=UserRole.INSTRUCTOR)
    headers = get_auth_headers(instructor)
    course = create_test_course(db_session, instructor)

    # 1. Create module
    mod_res = client.post(
        f"/api/v1/courses/{course.id}/modules",
        json={"title": "Module 2: Linear Data Structures", "order_index": 1},
        headers=headers,
    )
    assert mod_res.status_code == 201
    module_id = mod_res.json()["data"]["id"]

    # 2. Create lesson under module
    lesson_res = client.post(
        f"/api/v1/courses/{course.id}/lessons",
        json={
            "title": "Lesson: Linked Lists",
            "module_id": module_id,
            "duration_minutes": 45,
            "content_type": "video",
        },
        headers=headers,
    )
    assert lesson_res.status_code == 201
    assert lesson_res.json()["data"]["module_id"] == module_id


def test_create_lesson_invalid_module_fails(client: TestClient, db_session: Session):
    """AC-2 & AC-4: Lesson creation fails when referencing a module of another course."""
    instructor = create_test_user(db_session, "inst_inv_mod@skill2career.com", role=UserRole.INSTRUCTOR)
    headers = get_auth_headers(instructor)
    course1 = create_test_course(db_session, instructor, title="Course 1")
    course2 = create_test_course(db_session, instructor, title="Course 2")

    # Module created for course2
    mod_res = client.post(
        f"/api/v1/courses/{course2.id}/modules",
        json={"title": "Course 2 Module"},
        headers=headers,
    )
    foreign_module_id = mod_res.json()["data"]["id"]

    # Try attaching to course1
    res = client.post(
        f"/api/v1/courses/{course1.id}/lessons",
        json={"title": "Invalid Lesson", "module_id": foreign_module_id},
        headers=headers,
    )
    assert res.status_code == 400
    assert res.json()["error_code"] == "INVALID_MODULE"


def test_create_lesson_unauthorized_by_different_instructor_fails(client: TestClient, db_session: Session):
    """AC-5: Instructor cannot add lessons to another instructor's course."""
    instructor_a = create_test_user(db_session, "inst_a@skill2career.com", role=UserRole.INSTRUCTOR)
    instructor_b = create_test_user(db_session, "inst_b@skill2career.com", role=UserRole.INSTRUCTOR)
    headers_b = get_auth_headers(instructor_b)
    course_a = create_test_course(db_session, instructor_a)

    response = client.post(
        f"/api/v1/courses/{course_a.id}/lessons",
        json={"title": "Intruder Lesson"},
        headers=headers_b,
    )
    assert response.status_code == 403
    assert response.json()["error_code"] == "LESSON_ACCESS_DENIED"


def test_create_lesson_unauthorized_for_learner(client: TestClient, db_session: Session):
    """AC-5: Learners cannot create lessons."""
    instructor = create_test_user(db_session, "inst_target@skill2career.com", role=UserRole.INSTRUCTOR)
    learner = create_test_user(db_session, "learner_hacker@skill2career.com", role=UserRole.LEARNER)
    headers_learner = get_auth_headers(learner)
    course = create_test_course(db_session, instructor)

    response = client.post(
        f"/api/v1/courses/{course.id}/lessons",
        json={"title": "Learner Injection"},
        headers=headers_learner,
    )
    assert response.status_code == 403


def test_get_lessons_for_published_course_by_learner(client: TestClient, db_session: Session):
    """AC-3: Learner accesses available course lessons and related materials."""
    instructor = create_test_user(db_session, "inst_pub@skill2career.com", role=UserRole.INSTRUCTOR)
    learner = create_test_user(db_session, "learner_viewer@skill2career.com", role=UserRole.LEARNER)
    headers_instructor = get_auth_headers(instructor)
    headers_learner = get_auth_headers(learner)
    course = create_test_course(db_session, instructor, status=CourseStatus.PUBLISHED)

    # Add lesson
    client.post(
        f"/api/v1/courses/{course.id}/lessons",
        json={
            "title": "Trees and Tree Traversal",
            "duration_minutes": 32,
            "attachments": [{"name": "Lecture Notes.pdf", "size": "2.4 MB"}],
        },
        headers=headers_instructor,
    )

    # Learner accesses lessons list
    list_res = client.get(f"/api/v1/courses/{course.id}/lessons", headers=headers_learner)
    assert list_res.status_code == 200
    lessons = list_res.json()["data"]
    assert len(lessons) >= 1
    assert lessons[0]["title"] == "Trees and Tree Traversal"

    # Learner accesses single lesson
    lesson_id = lessons[0]["id"]
    detail_res = client.get(f"/api/v1/lessons/{lesson_id}", headers=headers_learner)
    assert detail_res.status_code == 200
    assert detail_res.json()["data"]["title"] == "Trees and Tree Traversal"
    assert len(detail_res.json()["data"]["attachments"]) == 1


def test_get_draft_lesson_by_learner_fails(client: TestClient, db_session: Session):
    """AC-5: Unpublished draft lesson is inaccessible to learners."""
    instructor = create_test_user(db_session, "inst_draft@skill2career.com", role=UserRole.INSTRUCTOR)
    learner = create_test_user(db_session, "learner_draft@skill2career.com", role=UserRole.LEARNER)
    headers_instructor = get_auth_headers(instructor)
    headers_learner = get_auth_headers(learner)
    course = create_test_course(db_session, instructor, status=CourseStatus.DRAFT)

    create_res = client.post(
        f"/api/v1/courses/{course.id}/lessons",
        json={"title": "Draft Lesson"},
        headers=headers_instructor,
    )
    lesson_id = create_res.json()["data"]["id"]

    # Learner attempts access
    res = client.get(f"/api/v1/lessons/{lesson_id}", headers=headers_learner)
    assert res.status_code == 404


def test_update_lesson_success(client: TestClient, db_session: Session):
    """AC-2: Instructor successfully updates lesson details."""
    instructor = create_test_user(db_session, "inst_upd@skill2career.com", role=UserRole.INSTRUCTOR)
    headers = get_auth_headers(instructor)
    course = create_test_course(db_session, instructor)

    create_res = client.post(
        f"/api/v1/courses/{course.id}/lessons",
        json={"title": "Old Lesson Title", "duration_minutes": 20},
        headers=headers,
    )
    lesson_id = create_res.json()["data"]["id"]

    update_payload = {
        "title": "Updated Trees and Graph Traversals",
        "duration_minutes": 45,
        "video_url": "https://www.youtube.com/embed/newVideo",
    }
    update_res = client.put(f"/api/v1/lessons/{lesson_id}", json=update_payload, headers=headers)
    assert update_res.status_code == 200
    data = update_res.json()["data"]
    assert data["title"] == "Updated Trees and Graph Traversals"
    assert data["duration_minutes"] == 45
    assert data["video_url"] == "https://www.youtube.com/embed/newVideo"


def test_delete_lesson_success(client: TestClient, db_session: Session):
    """AC-5: Instructor deletes an unwanted lesson."""
    instructor = create_test_user(db_session, "inst_del@skill2career.com", role=UserRole.INSTRUCTOR)
    headers = get_auth_headers(instructor)
    course = create_test_course(db_session, instructor)

    create_res = client.post(
        f"/api/v1/courses/{course.id}/lessons",
        json={"title": "Temporary Lesson"},
        headers=headers,
    )
    lesson_id = create_res.json()["data"]["id"]

    del_res = client.delete(f"/api/v1/lessons/{lesson_id}", headers=headers)
    assert del_res.status_code == 200
    assert del_res.json()["data"]["deleted"] is True

    # Check that lesson no longer exists
    get_res = client.get(f"/api/v1/lessons/{lesson_id}", headers=headers)
    assert get_res.status_code == 404


def test_upload_and_download_study_material_success(client: TestClient, db_session: Session):
    """AC-2 & AC-3: Instructor uploads study material PDF, and learner downloads it."""
    instructor = create_test_user(db_session, "inst_mat@skill2career.com", role=UserRole.INSTRUCTOR)
    learner = create_test_user(db_session, "learner_mat@skill2career.com", role=UserRole.LEARNER)
    headers_instructor = get_auth_headers(instructor)
    headers_learner = get_auth_headers(learner)
    course = create_test_course(db_session, instructor, status=CourseStatus.PUBLISHED)

    create_res = client.post(
        f"/api/v1/courses/{course.id}/lessons",
        json={"title": "Lesson with Material"},
        headers=headers_instructor,
    )
    lesson_id = create_res.json()["data"]["id"]

    # 1. Upload mock PDF material
    fake_pdf = io.BytesIO(b"%PDF-1.4 Mock binary PDF content for lecture notes")
    files = {"file": ("Lecture_Notes.pdf", fake_pdf, "application/pdf")}
    upload_res = client.post(
        f"/api/v1/lessons/{lesson_id}/materials",
        files=files,
        headers=headers_instructor,
    )
    assert upload_res.status_code == 201
    upload_data = upload_res.json()["data"]
    assert upload_data["name"] == "Lecture_Notes.pdf"
    filename = upload_data["filename"]

    # 2. Check lesson attachments updated
    lesson_check = client.get(f"/api/v1/lessons/{lesson_id}", headers=headers_learner)
    assert lesson_check.status_code == 200
    attachments = lesson_check.json()["data"]["attachments"]
    assert any(a["name"] == "Lecture_Notes.pdf" for a in attachments)

    # 3. Learner downloads study material
    download_res = client.get(
        f"/api/v1/lessons/{lesson_id}/materials/{filename}/download",
        headers=headers_learner,
    )
    assert download_res.status_code == 200
    assert download_res.content == b"%PDF-1.4 Mock binary PDF content for lecture notes"


def test_upload_study_material_unsupported_format_fails(client: TestClient, db_session: Session):
    """AC-4: Unsupported file formats are rejected with an appropriate error."""
    instructor = create_test_user(db_session, "inst_unsupp@skill2career.com", role=UserRole.INSTRUCTOR)
    headers = get_auth_headers(instructor)
    course = create_test_course(db_session, instructor)

    create_res = client.post(
        f"/api/v1/courses/{course.id}/lessons",
        json={"title": "Format Check Lesson"},
        headers=headers,
    )
    lesson_id = create_res.json()["data"]["id"]

    fake_exe = io.BytesIO(b"MZ executable mock payload")
    files = {"file": ("malware.exe", fake_exe, "application/octet-stream")}
    upload_res = client.post(
        f"/api/v1/lessons/{lesson_id}/materials",
        files=files,
        headers=headers,
    )
    assert upload_res.status_code == 400
    assert upload_res.json()["error_code"] == "UNSUPPORTED_MATERIAL_FORMAT"
