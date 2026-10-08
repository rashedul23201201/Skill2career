import pytest
from datetime import datetime, timezone, timedelta
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from app.models.user import User, UserRole
from app.models.profile import CompanyProfile
from app.models.job import JobPosting, JobStatus, JobPostingType, JobWorkMode
from app.core.security import hash_password, create_access_token


def create_test_company(
    db: Session,
    email: str,
    company_name: str = "Test Technologies Ltd.",
    verification_status: str = "APPROVED",
    is_verified: bool = True,
) -> User:
    """Helper to create a company user with profile directly in test db."""
    user = User(
        email=email,
        hashed_password=hash_password("Password123!"),
        role=UserRole.COMPANY,
        first_name="Recruiter",
        last_name="Lead",
        is_active=True,
        is_verified=is_verified,
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    profile = CompanyProfile(
        user_id=user.id,
        company_name=company_name,
        verification_status=verification_status,
        location="Dhaka, Bangladesh",
        industry="Software & IT",
    )
    db.add(profile)
    db.commit()
    db.refresh(user)
    return user


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


def test_create_job_by_verified_company_success(client: TestClient, db_session: Session):
    """AC-1: Authorized and verified company creates a valid job posting successfully."""
    company = create_test_company(db_session, "corp_verified_1@skill2career.com", "Brain Station 23")
    headers = get_auth_headers(company)

    payload = {
        "title": "Junior Software Developer",
        "posting_type": "Job",
        "work_mode": "On-site",
        "location": "Dhaka",
        "description": "Develop and maintain robust web APIs in modern frameworks.",
        "requirements": "Solid understanding of OOP, Data Structures, and SQL.",
        "skills": ["Java", "Python", "SQL"],
        "compensation": "৳35K – ৳50K",
        "experience_level": "Entry Level",
        "category": "Software Engineering",
        "status": "ACTIVE",
    }
    response = client.post("/api/v1/jobs", json=payload, headers=headers)
    assert response.status_code == 201
    data = response.json()
    assert data["success"] is True
    assert data["data"]["title"] == payload["title"]
    assert data["data"]["company_name"] == "Brain Station 23"
    assert data["data"]["status"] == "ACTIVE"
    assert data["data"]["skills"] == ["Java", "Python", "SQL"]


def test_create_job_unverified_company_fails(client: TestClient, db_session: Session):
    """AC-2: Unverified company attempting to publish a vacancy is blocked with COMPANY_NOT_VERIFIED."""
    unverified_company = create_test_company(
        db_session,
        "corp_pending@skill2career.com",
        "Pending StartUp Ltd.",
        verification_status="PENDING",
        is_verified=False,
    )
    headers = get_auth_headers(unverified_company)

    payload = {
        "title": "Backend Intern",
        "posting_type": "Internship",
        "work_mode": "Remote",
        "location": "Dhaka",
        "description": "Looking for enthusiastic interns to join backend engineering.",
        "requirements": "Basic programming knowledge.",
        "compensation": "৳15K / month",
    }
    response = client.post("/api/v1/jobs", json=payload, headers=headers)
    assert response.status_code == 403
    data = response.json()
    assert data["success"] is False
    assert data["error_code"] == "COMPANY_NOT_VERIFIED"


def test_create_job_unauthorized_for_learner(client: TestClient, db_session: Session):
    """Learners attempting to publish a vacancy receive HTTP 403 Forbidden."""
    learner = create_test_user(db_session, "learner_hiring@skill2career.com", role=UserRole.LEARNER)
    headers = get_auth_headers(learner)

    payload = {
        "title": "Unauthorized Vacancy",
        "posting_type": "Job",
        "description": "Learner attempting to post.",
        "requirements": "None",
        "compensation": "৳50K",
    }
    response = client.post("/api/v1/jobs", json=payload, headers=headers)
    assert response.status_code == 403
    assert response.json()["error_code"] == "INSUFFICIENT_ROLE_PERMISSIONS"


def test_create_job_validation_error_on_missing_fields(client: TestClient, db_session: Session):
    """Field validation error on missing required fields."""
    company = create_test_company(db_session, "corp_val@skill2career.com")
    headers = get_auth_headers(company)

    # Missing requirements and compensation
    payload = {
        "title": "Incomplete Job",
        "description": "Missing other mandatory fields.",
    }
    response = client.post("/api/v1/jobs", json=payload, headers=headers)
    assert response.status_code == 422


def test_update_job_by_owner_company_success(client: TestClient, db_session: Session):
    """AC-3: Vacancy author updates details and extends application deadline."""
    company = create_test_company(db_session, "corp_owner_edit@skill2career.com")
    headers = get_auth_headers(company)

    create_res = client.post(
        "/api/v1/jobs",
        json={
            "title": "Software Engineer",
            "posting_type": "Job",
            "work_mode": "Hybrid",
            "location": "Dhaka",
            "description": "Original description of software engineer.",
            "requirements": "Original requirements.",
            "compensation": "৳40K – ৳60K",
        },
        headers=headers,
    )
    job_id = create_res.json()["data"]["id"]

    new_deadline = (datetime.now(timezone.utc) + timedelta(days=30)).isoformat()
    update_res = client.put(
        f"/api/v1/jobs/{job_id}",
        json={
            "title": "Senior Software Engineer",
            "compensation": "৳80K – ৳110K",
            "deadline": new_deadline,
        },
        headers=headers,
    )
    assert update_res.status_code == 200
    data = update_res.json()["data"]
    assert data["title"] == "Senior Software Engineer"
    assert data["compensation"] == "৳80K – ৳110K"


def test_update_job_by_another_company_denied(client: TestClient, db_session: Session):
    """Company B cannot modify vacancy authored by Company A."""
    company_a = create_test_company(db_session, "corp_a@skill2career.com", "Company Alpha")
    company_b = create_test_company(db_session, "corp_b@skill2career.com", "Company Beta")

    create_res = client.post(
        "/api/v1/jobs",
        json={
            "title": "Company Alpha Vacancy",
            "description": "Exclusive role at company Alpha.",
            "requirements": "Solid engineering skills.",
            "compensation": "৳60K",
        },
        headers=get_auth_headers(company_a),
    )
    job_id = create_res.json()["data"]["id"]

    mod_res = client.put(
        f"/api/v1/jobs/{job_id}",
        json={"title": "Hijacked Vacancy Title"},
        headers=get_auth_headers(company_b),
    )
    assert mod_res.status_code == 403
    assert mod_res.json()["error_code"] == "JOB_ACCESS_DENIED"


def test_toggle_job_status_flow(client: TestClient, db_session: Session):
    """AC-3: Listing lifecycle management (ACTIVE / CLOSED / DRAFT) and candidate visibility."""
    company = create_test_company(db_session, "corp_lifecycle@skill2career.com")
    headers = get_auth_headers(company)

    # 1. Create job in DRAFT
    create_res = client.post(
        "/api/v1/jobs",
        json={
            "title": "Draft QA Engineer",
            "description": "Quality assurance and test automation.",
            "requirements": "Manual and automated testing.",
            "compensation": "৳30K",
            "status": "DRAFT",
        },
        headers=headers,
    )
    job_id = create_res.json()["data"]["id"]

    # Public candidate should not see draft job
    anon_res = client.get(f"/api/v1/jobs/{job_id}")
    assert anon_res.status_code == 404

    # 2. Activate job
    act_res = client.patch(
        f"/api/v1/jobs/{job_id}/status",
        json={"status": "ACTIVE"},
        headers=headers,
    )
    assert act_res.status_code == 200
    assert act_res.json()["data"]["status"] == "ACTIVE"

    # Now public candidate can view it
    anon_res2 = client.get(f"/api/v1/jobs/{job_id}")
    assert anon_res2.status_code == 200
    assert anon_res2.json()["data"]["title"] == "Draft QA Engineer"

    # 3. Close job
    close_res = client.patch(
        f"/api/v1/jobs/{job_id}/status",
        json={"status": "CLOSED"},
        headers=headers,
    )
    assert close_res.status_code == 200
    assert close_res.json()["data"]["status"] == "CLOSED"

    # Closed job is no longer available to public
    anon_res3 = client.get(f"/api/v1/jobs/{job_id}")
    assert anon_res3.status_code == 404


def test_learner_discovery_and_filtering(client: TestClient, db_session: Session):
    """AC-4: Learners discover active jobs with role type, keywords, and work mode filters."""
    company = create_test_company(db_session, "corp_filter_discovery@skill2career.com", "Filter Tech Ltd")
    headers = get_auth_headers(company)

    # Post a Full-time Job
    client.post(
        "/api/v1/jobs",
        json={
            "title": "DevOps Engineer",
            "posting_type": "Job",
            "work_mode": "Remote",
            "location": "Remote",
            "description": "Kubernetes and CI/CD pipelines.",
            "requirements": "Docker, Kubernetes, AWS.",
            "compensation": "৳90K",
            "status": "ACTIVE",
        },
        headers=headers,
    )

    # Post an Internship
    client.post(
        "/api/v1/jobs",
        json={
            "title": "Mobile App Intern",
            "posting_type": "Internship",
            "work_mode": "On-site",
            "location": "Dhaka",
            "description": "Flutter mobile application development.",
            "requirements": "Dart, Flutter widgets.",
            "compensation": "৳20K / month",
            "status": "ACTIVE",
        },
        headers=headers,
    )

    # Filter by Internship
    res_intern = client.get("/api/v1/jobs?posting_type=Internship")
    assert res_intern.status_code == 200
    items_intern = res_intern.json()["data"]["items"]
    assert any(j["title"] == "Mobile App Intern" for j in items_intern)
    assert all(j["posting_type"] == "Internship" for j in items_intern)

    # Filter by search keyword
    res_search = client.get("/api/v1/jobs?search=DevOps")
    assert res_search.status_code == 200
    items_search = res_search.json()["data"]["items"]
    assert any("DevOps" in j["title"] for j in items_search)


def test_admin_moderation_unpublish_audit_log(client: TestClient, db_session: Session):
    """AC-5: Admin oversight unpublishes policy-violating job and records audit log."""
    company = create_test_company(db_session, "corp_violating@skill2career.com")
    admin = create_test_user(db_session, "admin_jobs_audit@skill2career.com", role=UserRole.ADMIN)

    create_res = client.post(
        "/api/v1/jobs",
        json={
            "title": "Spam / Misleading Job Post",
            "description": "Violation of recruitment guidelines.",
            "requirements": "Unrealistic requirements.",
            "compensation": "৳100K",
            "status": "ACTIVE",
        },
        headers=get_auth_headers(company),
    )
    job_id = create_res.json()["data"]["id"]

    # Admin closes / unpublishes job with moderation note
    mod_res = client.patch(
        f"/api/v1/jobs/{job_id}/status",
        json={"status": "CLOSED", "reason": "Policy violation: Misleading compensation bracket"},
        headers=get_auth_headers(admin),
    )
    assert mod_res.status_code == 200
    assert mod_res.json()["data"]["status"] == "CLOSED"

    # Verify audit log recorded
    audit_res = client.get("/api/v1/admin/audit-logs", headers=get_auth_headers(admin))
    assert audit_res.status_code == 200
    logs = audit_res.json()["data"]
    override_log = next((l for l in logs if l["action"] == "JOB_STATUS_OVERRIDE"), None)
    assert override_log is not None
    assert override_log["details"]["reason"] == "Policy violation: Misleading compensation bracket"
