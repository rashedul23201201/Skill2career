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


def test_create_course_by_instructor_success(client: TestClient, db_session: Session):
    """AC-1: Authorized instructor creates a valid course successfully."""
    instructor = create_test_user(db_session, "inst_1@skill2career.com", role=UserRole.INSTRUCTOR)
    headers = get_auth_headers(instructor)

    payload = {
        "title": "Algorithms & Problem Solving in C++",
        "description": "Master algorithmic complexity, sorting, graphs, and dynamic programming.",
        "category": "Programming",
        "level": "Intermediate",
        "duration_weeks": 10,
        "price": 0.0,
        "is_free": True,
        "status": "DRAFT",
    }
    response = client.post("/api/v1/courses", json=payload, headers=headers)
    assert response.status_code == 201
    data = response.json()
    assert data["success"] is True
    assert data["data"]["title"] == payload["title"]
    assert data["data"]["instructor_id"] == instructor.id
    assert data["data"]["status"] == "DRAFT"
    assert len(data["data"]["modules"]) >= 1


def test_create_course_by_admin_success(client: TestClient, db_session: Session):
    """AC-1: Administrator can also create courses."""
    admin = create_test_user(db_session, "admin_crs@skill2career.com", role=UserRole.ADMIN)
    headers = get_auth_headers(admin)

    payload = {
        "title": "Platform Onboarding: Orientation",
        "description": "Orientation curriculum for new engineers.",
        "category": "Software Engineering",
        "level": "Beginner",
        "duration_weeks": 2,
    }
    response = client.post("/api/v1/courses", json=payload, headers=headers)
    assert response.status_code == 201
    assert response.json()["success"] is True


def test_create_course_unauthorized_for_learner(client: TestClient, db_session: Session):
    """AC-4: Learners attempting to create a course receive HTTP 403 Forbidden."""
    learner = create_test_user(db_session, "learner_crs@skill2career.com", role=UserRole.LEARNER)
    headers = get_auth_headers(learner)

    payload = {
        "title": "Hacker Course",
        "description": "Attempting unauthorized authoring.",
        "category": "Security",
    }
    response = client.post("/api/v1/courses", json=payload, headers=headers)
    assert response.status_code == 403
    assert response.json()["success"] is False
    assert response.json()["error_code"] == "INSUFFICIENT_ROLE_PERMISSIONS"


def test_create_course_unauthenticated_fails(client: TestClient):
    """AC-4: Unauthenticated user receives HTTP 401 Unauthorized."""
    payload = {
        "title": "Anonymous Course",
        "description": "Attempting unauthenticated post.",
        "category": "Testing",
    }
    response = client.post("/api/v1/courses", json=payload)
    assert response.status_code == 401
    assert response.json()["error_code"] == "NOT_AUTHENTICATED"


def test_create_course_validation_error_on_missing_fields(client: TestClient, db_session: Session):
    """AC-3: Validation errors must be shown when required fields are missing."""
    instructor = create_test_user(db_session, "inst_val@skill2career.com", role=UserRole.INSTRUCTOR)
    headers = get_auth_headers(instructor)

    # Missing description and category
    payload = {"title": "No Description"}
    response = client.post("/api/v1/courses", json=payload, headers=headers)
    assert response.status_code == 422


def test_update_course_by_owner_success(client: TestClient, db_session: Session):
    """AC-2: Course owner instructor updates course information successfully."""
    instructor = create_test_user(db_session, "inst_owner@skill2career.com", role=UserRole.INSTRUCTOR)
    headers = get_auth_headers(instructor)

    create_res = client.post(
        "/api/v1/courses",
        json={
            "title": "Original Title",
            "description": "Original course description text.",
            "category": "Database",
        },
        headers=headers,
    )
    course_id = create_res.json()["data"]["id"]

    update_payload = {
        "title": "Updated Title: Advanced PostgreSQL",
        "duration_weeks": 12,
    }
    update_res = client.put(f"/api/v1/courses/{course_id}", json=update_payload, headers=headers)
    assert update_res.status_code == 200
    data = update_res.json()
    assert data["success"] is True
    assert data["data"]["title"] == "Updated Title: Advanced PostgreSQL"
    assert data["data"]["duration_weeks"] == 12


def test_update_course_by_another_instructor_denied(client: TestClient, db_session: Session):
    """AC-4: Instructor B cannot modify course authored by Instructor A."""
    instructor_a = create_test_user(db_session, "inst_a@skill2career.com", role=UserRole.INSTRUCTOR)
    instructor_b = create_test_user(db_session, "inst_b@skill2career.com", role=UserRole.INSTRUCTOR)

    create_res = client.post(
        "/api/v1/courses",
        json={
            "title": "Instructor A Masterclass",
            "description": "Exclusive material by instructor A.",
            "category": "Web Development",
        },
        headers=get_auth_headers(instructor_a),
    )
    course_id = create_res.json()["data"]["id"]

    # Instructor B attempts modification
    mod_res = client.put(
        f"/api/v1/courses/{course_id}",
        json={"title": "Hijacked Course Title"},
        headers=get_auth_headers(instructor_b),
    )
    assert mod_res.status_code == 403
    assert mod_res.json()["error_code"] == "COURSE_ACCESS_DENIED"


def test_update_course_by_admin_permitted(client: TestClient, db_session: Session):
    """AC-2: Platform Admin can modify any course."""
    instructor = create_test_user(db_session, "inst_admin_edit@skill2career.com", role=UserRole.INSTRUCTOR)
    admin = create_test_user(db_session, "admin_editor@skill2career.com", role=UserRole.ADMIN)

    create_res = client.post(
        "/api/v1/courses",
        json={
            "title": "Instructor Course Before Admin Edit",
            "description": "Valid content description here.",
            "category": "Programming",
        },
        headers=get_auth_headers(instructor),
    )
    course_id = create_res.json()["data"]["id"]

    admin_res = client.put(
        f"/api/v1/courses/{course_id}",
        json={"title": "Curated by Admin"},
        headers=get_auth_headers(admin),
    )
    assert admin_res.status_code == 200
    assert admin_res.json()["data"]["title"] == "Curated by Admin"


def test_delete_course_and_cascade(client: TestClient, db_session: Session):
    """AC-5: Removing course deletes it so it is no longer available."""
    instructor = create_test_user(db_session, "inst_del@skill2career.com", role=UserRole.INSTRUCTOR)
    headers = get_auth_headers(instructor)

    create_res = client.post(
        "/api/v1/courses",
        json={
            "title": "Course To Delete",
            "description": "Will be removed shortly.",
            "category": "Testing",
        },
        headers=headers,
    )
    course_id = create_res.json()["data"]["id"]

    del_res = client.delete(f"/api/v1/courses/{course_id}", headers=headers)
    assert del_res.status_code == 200

    # Verify no longer available
    get_res = client.get(f"/api/v1/courses/{course_id}", headers=headers)
    assert get_res.status_code == 404


def test_publish_unpublish_status_flow(client: TestClient, db_session: Session):
    """AC-5: Toggle draft vs published status and check public availability."""
    instructor = create_test_user(db_session, "inst_pub@skill2career.com", role=UserRole.INSTRUCTOR)
    headers = get_auth_headers(instructor)

    # 1. Create in DRAFT
    create_res = client.post(
        "/api/v1/courses",
        json={
            "title": "Draft Machine Learning Course",
            "description": "Neural networks, transformers, and inference.",
            "category": "Programming",
            "status": "DRAFT",
        },
        headers=headers,
    )
    course_id = create_res.json()["data"]["id"]

    # Public anonymous request should not see draft course
    anon_res = client.get(f"/api/v1/courses/{course_id}")
    assert anon_res.status_code == 404

    # 2. Publish course
    pub_res = client.patch(
        f"/api/v1/courses/{course_id}/status",
        json={"status": "PUBLISHED"},
        headers=headers,
    )
    assert pub_res.status_code == 200
    assert pub_res.json()["data"]["status"] == "PUBLISHED"

    # Now anonymous public can view it
    anon_res2 = client.get(f"/api/v1/courses/{course_id}")
    assert anon_res2.status_code == 200
    assert anon_res2.json()["data"]["title"] == "Draft Machine Learning Course"

    # 3. Unpublish course
    unpub_res = client.patch(
        f"/api/v1/courses/{course_id}/status",
        json={"status": "UNPUBLISHED"},
        headers=headers,
    )
    assert unpub_res.status_code == 200
    assert unpub_res.json()["data"]["status"] == "UNPUBLISHED"

    # Anonymous public can no longer see it
    anon_res3 = client.get(f"/api/v1/courses/{course_id}")
    assert anon_res3.status_code == 404


def test_admin_oversight_unpublish_audit_log(client: TestClient, db_session: Session):
    """AC-5: Admin oversight unpublish endpoint creates immutable audit log."""
    instructor = create_test_user(db_session, "inst_audit@skill2career.com", role=UserRole.INSTRUCTOR)
    admin = create_test_user(db_session, "admin_audit_crs@skill2career.com", role=UserRole.ADMIN)

    create_res = client.post(
        "/api/v1/courses",
        json={
            "title": "Policy Violating Course",
            "description": "Contains copyrighted material.",
            "category": "Other",
            "status": "PUBLISHED",
        },
        headers=get_auth_headers(instructor),
    )
    course_id = create_res.json()["data"]["id"]

    # Admin unpublishes with policy violation note
    mod_res = client.patch(
        f"/api/v1/courses/{course_id}/status",
        json={"status": "UNPUBLISHED", "reason": "Copyright violation reported"},
        headers=get_auth_headers(admin),
    )
    assert mod_res.status_code == 200
    assert mod_res.json()["data"]["status"] == "UNPUBLISHED"

    # Verify audit log recorded
    audit_res = client.get("/api/v1/admin/audit-logs", headers=get_auth_headers(admin))
    assert audit_res.status_code == 200
    logs = audit_res.json()["data"]
    override_log = next((l for l in logs if l["action"] == "COURSE_STATUS_OVERRIDE"), None)
    assert override_log is not None
    assert override_log["details"]["reason"] == "Copyright violation reported"


def test_curriculum_sync_builder(client: TestClient, db_session: Session):
    """Curriculum Builder tree saving with modules and nested lessons."""
    instructor = create_test_user(db_session, "inst_curr@skill2career.com", role=UserRole.INSTRUCTOR)
    headers = get_auth_headers(instructor)

    create_res = client.post(
        "/api/v1/courses",
        json={
            "title": "Data Structures & Algorithms in Python",
            "description": "Full curriculum builder test.",
            "category": "Programming",
        },
        headers=headers,
    )
    course_id = create_res.json()["data"]["id"]

    curriculum_payload = {
        "modules": [
            {
                "title": "Module 1: Foundations of Algorithms",
                "order_index": 0,
                "lessons": [
                    {"title": "Lesson: Complexity Basics", "duration_minutes": 30, "content_type": "video"},
                ],
            },
            {
                "title": "Module 2: Linear Data Structures",
                "order_index": 1,
                "lessons": [
                    {"title": "Lesson: Linked Lists", "duration_minutes": 45, "content_type": "video"},
                    {
                        "title": "Binary Trees and Traversal Strategies",
                        "duration_minutes": 45,
                        "content_type": "video",
                        "video_url": "https://www.youtube.com/embed/tree_video",
                        "attachments": [{"name": "Lecture_Notes_Trees.pdf", "size": "2.4 MB"}],
                    },
                ],
            },
        ]
    }

    sync_res = client.put(f"/api/v1/courses/{course_id}/curriculum", json=curriculum_payload, headers=headers)
    assert sync_res.status_code == 200
    data = sync_res.json()["data"]
    assert len(data["modules"]) == 2
    assert data["modules"][0]["title"] == "Module 1: Foundations of Algorithms"
    assert len(data["modules"][1]["lessons"]) == 2
    assert data["modules"][1]["lessons"][1]["title"] == "Binary Trees and Traversal Strategies"
