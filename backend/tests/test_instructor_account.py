import pytest
from fastapi.testclient import TestClient


def get_auth_token(client: TestClient, email: str, role: str = "LEARNER") -> str:
    """Helper to register and login a user and return the Bearer access token."""
    reg_payload = {
        "email": email,
        "password": "StrongPassword123!",
        "first_name": "Instructor",
        "last_name": "Candidate",
        "role": role,
    }
    reg_res = client.post("/api/v1/auth/register", json=reg_payload)
    assert reg_res.status_code == 201

    login_res = client.post(
        "/api/v1/auth/login",
        json={"email": email, "password": "StrongPassword123!"}
    )
    assert login_res.status_code == 200
    return login_res.json()["data"]["access_token"]


def test_instructor_application_saves_pending_review(client: TestClient):
    """Test instructor application is saved with PENDING_REVIEW status (SKL-52)."""
    token = get_auth_token(client, "apply_inst1@example.com")
    headers = {"Authorization": f"Bearer {token}"}

    payload = {
        "designation": "Senior Lecturer",
        "institution": "Bangladesh University of Engineering and Technology (BUET)",
        "qualification": "M.Sc. in Computer Science & Engineering",
        "expertise_domain": "Cloud Computing & Distributed Systems",
        "years_experience": "6 years",
        "certificates": ["AWS Certified Solutions Architect", "CKA Kubernetes"],
        "intro_video_url": "https://youtu.be/sample-intro",
        "bio": "Dedicated educator specializing in high-throughput cloud architectures and mentoring.",
        "linkedin_url": "https://linkedin.com/in/buet-lecturer",
    }

    res = client.post("/api/v1/instructors/apply", json=payload, headers=headers)
    assert res.status_code == 201
    data = res.json()["data"]

    assert data["designation"] == payload["designation"]
    assert data["institution"] == payload["institution"]
    assert data["qualification"] == payload["qualification"]
    assert data["expertise_domain"] == payload["expertise_domain"]
    assert data["years_experience"] == payload["years_experience"]
    assert data["onboarding_status"] == "PENDING_REVIEW"
    assert data["email"] == "apply_inst1@example.com"


def test_get_and_update_instructor_profile(client: TestClient):
    """Test fetching and updating an instructor's profile (SKL-52)."""
    token = get_auth_token(client, "update_inst@example.com")
    headers = {"Authorization": f"Bearer {token}"}

    # Initial apply
    apply_payload = {
        "designation": "Lead AI Engineer",
        "institution": "Brain Station 23",
        "qualification": "B.Sc. in CSE",
        "expertise_domain": "Machine Learning & NLP",
        "years_experience": "5 years",
    }
    client.post("/api/v1/instructors/apply", json=apply_payload, headers=headers)

    # Fetch profile
    get_res = client.get("/api/v1/instructors/profile", headers=headers)
    assert get_res.status_code == 200
    assert get_res.json()["data"]["designation"] == "Lead AI Engineer"

    # Update profile
    update_payload = {
        "designation": "Principal AI Architect",
        "bio": "Updated bio with 50+ published deep learning models.",
        "years_experience": "7 years",
    }
    put_res = client.put("/api/v1/instructors/profile", json=update_payload, headers=headers)
    assert put_res.status_code == 200
    updated_data = put_res.json()["data"]
    assert updated_data["designation"] == "Principal AI Architect"
    assert updated_data["bio"] == "Updated bio with 50+ published deep learning models."
    assert updated_data["years_experience"] == "7 years"


def test_admin_approval_promotes_user_and_grants_access(client: TestClient):
    """Test admin approval updates user permissions to access instructor tools (SKL-52 AC)."""
    # 1. Candidate applies
    candidate_token = get_auth_token(client, "candidate_approve@example.com", role="LEARNER")
    candidate_headers = {"Authorization": f"Bearer {candidate_token}"}
    apply_res = client.post(
        "/api/v1/instructors/apply",
        json={
            "designation": "Software Architect",
            "institution": "Chittagong University of Engineering & Technology",
            "qualification": "M.Sc. in Software Engineering",
            "expertise_domain": "Full-Stack Development",
        },
        headers=candidate_headers
    )
    assert apply_res.status_code == 201
    profile_id = apply_res.json()["data"]["id"]

    # 2. Admin logs in
    admin_token = get_auth_token(client, "admin_approver@example.com", role="ADMIN")
    admin_headers = {"Authorization": f"Bearer {admin_token}"}

    # 3. Admin lists pending instructors
    pending_res = client.get("/api/v1/admin/instructors/pending", headers=admin_headers)
    assert pending_res.status_code == 200
    pending_ids = [p["id"] for p in pending_res.json()["data"]]
    assert profile_id in pending_ids

    # 4. Admin approves the instructor application
    approve_res = client.patch(
        f"/api/v1/admin/instructors/{profile_id}/status",
        json={"status": "APPROVED", "reason": "Verified credentials with university registrar."},
        headers=admin_headers
    )
    assert approve_res.status_code == 200
    approved_data = approve_res.json()["data"]
    assert approved_data["onboarding_status"] == "APPROVED"

    # 5. Check candidate user details reflect INSTRUCTOR role & verified status
    user_res = client.get(f"/api/v1/admin/users/{approved_data['user_id']}", headers=admin_headers)
    assert user_res.status_code == 200
    user_data = user_res.json()["data"]
    assert user_data["role"] == "INSTRUCTOR"
    assert user_data["is_verified"] is True


def test_admin_rejection_updates_status(client: TestClient):
    """Test admin rejection updates application status to REJECTED."""
    # Candidate applies
    candidate_token = get_auth_token(client, "candidate_reject@example.com")
    candidate_headers = {"Authorization": f"Bearer {candidate_token}"}
    apply_res = client.post(
        "/api/v1/instructors/apply",
        json={"designation": "Intern", "institution": "College"},
        headers=candidate_headers
    )
    profile_id = apply_res.json()["data"]["id"]

    # Admin rejects
    admin_token = get_auth_token(client, "admin_rejector@example.com", role="ADMIN")
    admin_headers = {"Authorization": f"Bearer {admin_token}"}

    reject_res = client.patch(
        f"/api/v1/admin/instructors/{profile_id}/status",
        json={"status": "REJECTED", "reason": "Requires minimum 3 years of industry experience."},
        headers=admin_headers
    )
    assert reject_res.status_code == 200
    assert reject_res.json()["data"]["onboarding_status"] == "REJECTED"


def test_non_admin_cannot_access_admin_instructor_endpoints(client: TestClient):
    """Test regular learner/instructor is forbidden from reviewing instructor applications."""
    learner_token = get_auth_token(client, "regular_learner_forbidden@example.com")
    headers = {"Authorization": f"Bearer {learner_token}"}

    # Cannot list pending
    r1 = client.get("/api/v1/admin/instructors/pending", headers=headers)
    assert r1.status_code == 403

    # Cannot update status
    r2 = client.patch(
        "/api/v1/admin/instructors/1/status",
        json={"status": "APPROVED"},
        headers=headers
    )
    assert r2.status_code == 403


def test_unauthenticated_access_rejected(client: TestClient):
    """Test unauthenticated calls to instructor endpoints are rejected with 401."""
    assert client.get("/api/v1/instructors/profile").status_code == 401
    assert client.post("/api/v1/instructors/apply", json={}).status_code == 401
    assert client.put("/api/v1/instructors/profile", json={}).status_code == 401
    assert client.get("/api/v1/instructors/dashboard-stats").status_code == 401


def test_instructor_dashboard_stats(client: TestClient):
    """Test instructor telemetry endpoint returns stats structure."""
    token = get_auth_token(client, "dashboard_inst@example.com")
    headers = {"Authorization": f"Bearer {token}"}

    # Submit application
    client.post(
        "/api/v1/instructors/apply",
        json={"designation": "Mentor", "institution": "Online Tech"},
        headers=headers
    )

    res = client.get("/api/v1/instructors/dashboard-stats", headers=headers)
    assert res.status_code == 200
    data = res.json()["data"]
    assert "active_courses" in data
    assert "total_learners" in data
    assert "mock_tests" in data
    assert "upcoming_interviews" in data
    assert data["onboarding_status"] == "PENDING_REVIEW"
