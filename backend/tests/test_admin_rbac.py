import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from app.models.user import User, UserRole
from app.core.security import hash_password, create_access_token


def create_test_user(
    db: Session,
    email: str,
    role: UserRole = UserRole.LEARNER,
    first_name: str = "Test",
    last_name: str = "User",
    is_active: bool = True,
    is_verified: bool = True
) -> User:
    """Helper to create a user directly in test db."""
    user = User(
        email=email,
        hashed_password=hash_password("Password123!"),
        role=role,
        first_name=first_name,
        last_name=last_name,
        is_active=is_active,
        is_verified=is_verified
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def get_auth_headers(user: User) -> dict:
    """Generate auth headers for test client."""
    token = create_access_token(
        subject=user.id,
        claims={"email": user.email, "role": user.role.value}
    )
    return {"Authorization": f"Bearer {token}"}


def test_non_admin_access_forbidden(client: TestClient, db_session: Session):
    """Testing Criteria: Non-admin requesting /api/v1/admin/users receives HTTP 403 Forbidden (SKL-50)."""
    learner = create_test_user(db_session, "learner_access@example.com", role=UserRole.LEARNER)
    headers = get_auth_headers(learner)

    response = client.get("/api/v1/admin/users", headers=headers)
    assert response.status_code == 403
    data = response.json()
    assert data["success"] is False
    assert data["error_code"] == "INSUFFICIENT_ROLE_PERMISSIONS"


def test_unauthenticated_admin_access_unauthorized(client: TestClient):
    """Test unauthenticated request to admin route receives HTTP 401 Unauthorized."""
    response = client.get("/api/v1/admin/users")
    assert response.status_code == 401
    assert response.json()["error_code"] == "NOT_AUTHENTICATED"


def test_admin_get_overview_stats(client: TestClient, db_session: Session):
    """Test admin successfully retrieves platform overview metrics."""
    admin = create_test_user(db_session, "admin_stats@example.com", role=UserRole.ADMIN)
    create_test_user(db_session, "company1@example.com", role=UserRole.COMPANY)
    create_test_user(db_session, "learner1@example.com", role=UserRole.LEARNER)
    headers = get_auth_headers(admin)

    response = client.get("/api/v1/admin/overview-stats", headers=headers)
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    stats = data["data"]
    assert stats["total_users"] >= 3
    assert stats["total_companies"] >= 1
    assert "role_breakdown" in stats
    assert stats["role_breakdown"]["ADMIN"] >= 1


def test_admin_get_users_paginated_and_filtered(client: TestClient, db_session: Session):
    """Test admin user filtering by role and search query (SKL-24)."""
    admin = create_test_user(db_session, "admin_users@example.com", role=UserRole.ADMIN)
    create_test_user(db_session, "rahim.learner@example.com", role=UserRole.LEARNER, first_name="Rahim", last_name="Ahmed")
    create_test_user(db_session, "karim.instructor@example.com", role=UserRole.INSTRUCTOR, first_name="Karim", last_name="Khan")
    headers = get_auth_headers(admin)

    # 1. Search by name "Rahim"
    res1 = client.get("/api/v1/admin/users?search=Rahim", headers=headers)
    assert res1.status_code == 200
    data1 = res1.json()["data"]
    assert data1["total"] == 1
    assert data1["items"][0]["email"] == "rahim.learner@example.com"

    # 2. Filter by role "INSTRUCTOR"
    res2 = client.get("/api/v1/admin/users?role=INSTRUCTOR", headers=headers)
    assert res2.status_code == 200
    data2 = res2.json()["data"]
    assert any(u["email"] == "karim.instructor@example.com" for u in data2["items"])
    assert all(u["role"] == "INSTRUCTOR" for u in data2["items"])


def test_deactivate_user_invalidates_session(client: TestClient, db_session: Session):
    """Testing Criteria: Deactivating user ID X prevents user ID X from calling /api/v1/auth/me on subsequent requests (SKL-50)."""
    admin = create_test_user(db_session, "admin_deactivate@example.com", role=UserRole.ADMIN)
    target_user = create_test_user(db_session, "target_to_deactivate@example.com", role=UserRole.LEARNER)

    # Target user generates headers and verifies initial access
    user_headers = get_auth_headers(target_user)
    initial_me = client.get("/api/v1/auth/me", headers=user_headers)
    assert initial_me.status_code == 200
    assert initial_me.json()["data"]["is_active"] is True

    # Admin deactivates target user
    admin_headers = get_auth_headers(admin)
    deactivate_res = client.patch(
        f"/api/v1/admin/users/{target_user.id}/status",
        headers=admin_headers,
        json={"is_active": False, "reason": "Terms of service violation"}
    )
    assert deactivate_res.status_code == 200
    assert deactivate_res.json()["data"]["is_active"] is False

    # Target user calls /api/v1/auth/me again using their active token
    subsequent_me = client.get("/api/v1/auth/me", headers=user_headers)
    assert subsequent_me.status_code == 403
    assert subsequent_me.json()["error_code"] == "ACCOUNT_INACTIVE"


def test_update_user_role_invalidates_stale_token_session(client: TestClient, db_session: Session):
    """Testing Criteria: Updating a user's role immediately takes effect and invalidates stale session tokens (SKL-50)."""
    admin = create_test_user(db_session, "admin_role_updater@example.com", role=UserRole.ADMIN)
    target_user = create_test_user(db_session, "target_role_user@example.com", role=UserRole.LEARNER)

    # Token issued with LEARNER role in claims
    stale_headers = get_auth_headers(target_user)

    # Admin promotes target user to INSTRUCTOR
    admin_headers = get_auth_headers(admin)
    promote_res = client.patch(
        f"/api/v1/admin/users/{target_user.id}/role",
        headers=admin_headers,
        json={"role": "INSTRUCTOR", "reason": "Passed instructor credential audit"}
    )
    assert promote_res.status_code == 200
    assert promote_res.json()["data"]["role"] == "INSTRUCTOR"

    # Request with stale token containing old 'LEARNER' claim is rejected
    check_me = client.get("/api/v1/auth/me", headers=stale_headers)
    assert check_me.status_code == 401
    assert check_me.json()["error_code"] == "SESSION_ROLE_REVOKED"


def test_admin_cannot_deactivate_or_demote_self(client: TestClient, db_session: Session):
    """Ensure safety constraint preventing admin self-lockout."""
    admin = create_test_user(db_session, "admin_self_check@example.com", role=UserRole.ADMIN)
    admin_headers = get_auth_headers(admin)

    # Cannot deactivate self
    deact_res = client.patch(
        f"/api/v1/admin/users/{admin.id}/status",
        headers=admin_headers,
        json={"is_active": False}
    )
    assert deact_res.status_code == 400
    assert deact_res.json()["error_code"] == "CANNOT_DEACTIVATE_SELF"

    # Cannot demote self
    demote_res = client.patch(
        f"/api/v1/admin/users/{admin.id}/role",
        headers=admin_headers,
        json={"role": "LEARNER"}
    )
    assert demote_res.status_code == 400
    assert demote_res.json()["error_code"] == "CANNOT_DEMOTE_SELF"


def test_audit_logs_recorded_and_fetched(client: TestClient, db_session: Session):
    """Test that audit log entries are generated upon administrative changes and can be fetched."""
    admin = create_test_user(db_session, "admin_auditor@example.com", role=UserRole.ADMIN)
    user = create_test_user(db_session, "user_audit_subject@example.com", role=UserRole.LEARNER)
    admin_headers = get_auth_headers(admin)

    # Trigger a status update
    client.patch(
        f"/api/v1/admin/users/{user.id}/status",
        headers=admin_headers,
        json={"is_active": False, "reason": "Suspicious login pattern"}
    )

    # Fetch audit logs
    logs_res = client.get("/api/v1/admin/audit-logs", headers=admin_headers)
    assert logs_res.status_code == 200
    logs = logs_res.json()["data"]
    assert len(logs) >= 1
    recent_log = logs[0]
    assert recent_log["action"] == "STATUS_UPDATE"
    assert recent_log["admin_id"] == admin.id
    assert recent_log["target_user_id"] == user.id
    assert recent_log["details"]["new_is_active"] is False
