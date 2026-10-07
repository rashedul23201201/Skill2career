import pytest
from fastapi.testclient import TestClient


def get_user_token(client: TestClient, email: str, role: str = "COMPANY", company_name: str = "Acme Corp") -> str:
    """Helper to register and login a user and return the Bearer access token."""
    reg_payload = {
        "email": email,
        "password": "StrongPassword123!",
        "first_name": "Rahim",
        "last_name": "Chowdhury",
        "role": role,
        "company_name": company_name,
        "industry": "Software Engineering",
        "contact_phone": "+8801700000000",
        "website_url": "https://acme-bangladesh.com",
        "office_address": "Gulshan-1, Dhaka-1212",
    }
    reg_res = client.post("/api/v1/auth/register", json=reg_payload)
    assert reg_res.status_code == 201

    login_res = client.post(
        "/api/v1/auth/login",
        json={"email": email, "password": "StrongPassword123!"}
    )
    assert login_res.status_code == 200
    return login_res.json()["data"]["access_token"]


def test_company_registration_defaults_to_unverified(client: TestClient):
    """Test newly registered company account has is_verified=False and status=PENDING (SKL-2)."""
    token = get_user_token(client, "acme_new@example.com", role="COMPANY")
    headers = {"Authorization": f"Bearer {token}"}

    res = client.get("/api/v1/companies/verification-status", headers=headers)
    assert res.status_code == 200
    data = res.json()["data"]

    assert data["is_verified"] is False
    assert data["verification_status"] == "PENDING"
    assert data["company_name"] == "Acme Corp"


def test_unverified_company_job_posting_forbidden(client: TestClient):
    """Test unverified company calling job publishing endpoint receives HTTP 403 Forbidden with COMPANY_NOT_VERIFIED (SKL-2)."""
    token = get_user_token(client, "unverified_corp@example.com", role="COMPANY")
    headers = {"Authorization": f"Bearer {token}"}

    job_payload = {
        "title": "Senior Backend Engineer",
        "description": "Looking for FastAPI and SQLAlchemy experts in Dhaka.",
        "job_type": "Full-time",
        "location": "Dhaka, Bangladesh",
        "salary_range": "100k - 150k BDT"
    }

    res = client.post("/api/v1/companies/jobs", json=job_payload, headers=headers)
    assert res.status_code == 403
    error_json = res.json()
    assert error_json["error_code"] == "COMPANY_NOT_VERIFIED"
    assert "pending administrative verification" in error_json["message"]


def test_submit_company_verification_dossier(client: TestClient):
    """Test company can submit official trade license and credentials dossier (SKL-2)."""
    token = get_user_token(client, "techcorp@example.com", role="COMPANY", company_name="TechCorp BD")
    headers = {"Authorization": f"Bearer {token}"}

    submit_payload = {
        "company_name": "TechCorp Bangladesh Ltd.",
        "trade_license_url": "https://storage.skill2career.com/licenses/techcorp_trade_lic_2026.pdf",
        "registration_number": "TRAD/DNCC/098765/2026",
        "industry": "Information Technology",
        "location": "Dhaka, Bangladesh",
        "company_size": "51-200",
        "website_url": "https://techcorp-bd.com",
        "office_address": "Level 7, BDBL Bhaban, Karwan Bazar, Dhaka",
        "contact_person": "Tanvir Ahmed, HR Director",
        "contact_phone": "+8801811223344",
        "description": "Enterprise cloud consultancy and FinTech solutions in Bangladesh.",
    }

    res = client.post("/api/v1/companies/verification-request", json=submit_payload, headers=headers)
    assert res.status_code == 200
    data = res.json()["data"]

    assert data["company_name"] == "TechCorp Bangladesh Ltd."
    assert data["trade_license_url"] == "https://storage.skill2career.com/licenses/techcorp_trade_lic_2026.pdf"
    assert data["registration_number"] == "TRAD/DNCC/098765/2026"
    assert data["verification_status"] == "PENDING"
    assert data["is_verified"] is False


def test_submit_verification_missing_trade_license_fails(client: TestClient):
    """Test submitting verification without trade license URL fails with HTTP 422 or 400."""
    token = get_user_token(client, "nolicense@example.com", role="COMPANY")
    headers = {"Authorization": f"Bearer {token}"}

    res = client.post("/api/v1/companies/verification-request", json={"company_name": "No License Inc."}, headers=headers)
    assert res.status_code == 422  # Pydantic validation failure


def test_admin_view_pending_verifications(client: TestClient):
    """Test admin can view list of pending company verification dossiers (SKL-2)."""
    admin_token = get_user_token(client, "admin_approver@example.com", role="ADMIN")
    comp_token = get_user_token(client, "pending_sub@example.com", role="COMPANY", company_name="Pending Submission Ltd")

    # Submit dossier as company
    client.post(
        "/api/v1/companies/verification-request",
        json={
            "trade_license_url": "https://storage.skill2career.com/licenses/pending_sub.pdf",
            "registration_number": "REG-889900",
        },
        headers={"Authorization": f"Bearer {comp_token}"}
    )

    # Admin fetches pending list
    res = client.get("/api/v1/admin/companies/pending-verifications", headers={"Authorization": f"Bearer {admin_token}"})
    assert res.status_code == 200
    pending_list = res.json()["data"]
    assert isinstance(pending_list, list)
    matching = [c for c in pending_list if c["company_name"] == "Pending Submission Ltd"]
    assert len(matching) == 1
    assert matching[0]["trade_license_url"] == "https://storage.skill2career.com/licenses/pending_sub.pdf"
    assert matching[0]["registration_number"] == "REG-889900"


def test_admin_approve_company_unlocks_job_posting(client: TestClient):
    """Full lifecycle: Unverified company submits dossier -> Admin approves -> is_verified=True -> Job posting succeeds (SKL-2)."""
    admin_token = get_user_token(client, "super_admin@example.com", role="ADMIN")
    comp_token = get_user_token(client, "hired_today@example.com", role="COMPANY", company_name="Hired Today Ltd")

    comp_headers = {"Authorization": f"Bearer {comp_token}"}
    admin_headers = {"Authorization": f"Bearer {admin_token}"}

    # 1. Company submits verification dossier
    sub_res = client.post(
        "/api/v1/companies/verification-request",
        json={
            "trade_license_url": "https://storage.skill2career.com/licenses/hired_today.pdf",
            "registration_number": "TRAD-776655",
            "website_url": "https://hiredtoday.com.bd",
        },
        headers=comp_headers
    )
    assert sub_res.status_code == 200
    company_id = sub_res.json()["data"]["company_id"]

    # 2. Before approval: Job creation must be rejected
    job_payload = {
        "title": "Full Stack React Developer",
        "description": "Looking for frontend and backend React/FastAPI engineers.",
    }
    blocked_job = client.post("/api/v1/companies/jobs", json=job_payload, headers=comp_headers)
    assert blocked_job.status_code == 403
    assert blocked_job.json()["error_code"] == "COMPANY_NOT_VERIFIED"

    # 3. Admin approves verification
    approval_res = client.post(
        f"/api/v1/admin/companies/{company_id}/verify",
        json={"action": "APPROVE", "notes": "Trade license and BIN certificate vetted and approved."},
        headers=admin_headers
    )
    assert approval_res.status_code == 200
    appr_data = approval_res.json()["data"]
    assert appr_data["verification_status"] == "APPROVED"
    assert appr_data["is_verified"] is True
    assert appr_data["verified_at"] is not None

    # 4. Status reflects approved
    status_res = client.get("/api/v1/companies/verification-status", headers=comp_headers)
    assert status_res.status_code == 200
    assert status_res.json()["data"]["verification_status"] == "APPROVED"
    assert status_res.json()["data"]["is_verified"] is True

    # 5. Now company calls job publishing endpoint -> SUCCESS!
    job_success = client.post("/api/v1/companies/jobs", json=job_payload, headers=comp_headers)
    assert job_success.status_code == 201
    assert job_success.json()["success"] is True
    assert job_success.json()["data"]["is_published"] is True
    assert job_success.json()["data"]["title"] == "Full Stack React Developer"


def test_admin_reject_company_records_reason(client: TestClient):
    """Test admin rejection updates status to REJECTED, preserves is_verified=False, and stores feedback notes (SKL-2)."""
    admin_token = get_user_token(client, "admin_reviewer@example.com", role="ADMIN")
    comp_token = get_user_token(client, "fake_company@example.com", role="COMPANY", company_name="Suspicious Corp")

    comp_headers = {"Authorization": f"Bearer {comp_token}"}
    admin_headers = {"Authorization": f"Bearer {admin_token}"}

    # Submit dossier
    sub_res = client.post(
        "/api/v1/companies/verification-request",
        json={
            "trade_license_url": "https://invalid-link.example.com/expired_lic.pdf",
            "registration_number": "INVALID-000",
        },
        headers=comp_headers
    )
    company_id = sub_res.json()["data"]["company_id"]

    # Admin rejects
    reject_res = client.post(
        f"/api/v1/admin/companies/{company_id}/verify",
        json={"action": "REJECT", "notes": "Trade license document is expired. Please submit current FY2026 renewal."},
        headers=admin_headers
    )
    assert reject_res.status_code == 200
    rej_data = reject_res.json()["data"]
    assert rej_data["verification_status"] == "REJECTED"
    assert rej_data["is_verified"] is False
    assert rej_data["verification_notes"] == "Trade license document is expired. Please submit current FY2026 renewal."

    # Company checks status
    comp_status = client.get("/api/v1/companies/verification-status", headers=comp_headers)
    assert comp_status.json()["data"]["verification_status"] == "REJECTED"
    assert comp_status.json()["data"]["verification_notes"] == "Trade license document is expired. Please submit current FY2026 renewal."

    # Job posting remains blocked
    job_blocked = client.post(
        "/api/v1/companies/jobs",
        json={"title": "Dev", "description": "Short job description for testing."},
        headers=comp_headers
    )
    assert job_blocked.status_code == 403
    assert job_blocked.json()["error_code"] == "COMPANY_NOT_VERIFIED"


def test_non_company_access_to_verification_endpoints_forbidden(client: TestClient):
    """Test Learner or Instructor cannot access company verification endpoints."""
    learner_token = get_user_token(client, "learner_trying_comp@example.com", role="LEARNER")
    headers = {"Authorization": f"Bearer {learner_token}"}

    r1 = client.get("/api/v1/companies/verification-status", headers=headers)
    assert r1.status_code == 403

    r2 = client.post("/api/v1/companies/verification-request", json={"trade_license_url": "https://test.com/lic.pdf"}, headers=headers)
    assert r2.status_code == 403


def test_non_admin_access_to_admin_verification_forbidden(client: TestClient):
    """Test Company or Learner cannot access admin verification review endpoints."""
    comp_token = get_user_token(client, "regular_company@example.com", role="COMPANY")
    headers = {"Authorization": f"Bearer {comp_token}"}

    r1 = client.get("/api/v1/admin/companies/pending-verifications", headers=headers)
    assert r1.status_code == 403

    r2 = client.post("/api/v1/admin/companies/1/verify", json={"action": "APPROVE"}, headers=headers)
    assert r2.status_code == 403
