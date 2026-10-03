import io
import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.core.security import hash_password, create_access_token
from app.models.user import User, UserRole
from app.models.profile import CompanyProfile
from app.models.audit_log import AuditLog


@pytest.fixture
def company_user(db_session: Session) -> User:
    """Fixture providing a test company user with initial CompanyProfile."""
    user = User(
        email="talent@brainstation23.com",
        hashed_password=hash_password("CompanyPass123!"),
        role=UserRole.COMPANY,
        first_name="Brain Station 23",
        last_name="",
        is_active=True,
        is_verified=False,
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)

    profile = CompanyProfile(
        user_id=user.id,
        company_name="Brain Station 23",
        industry="Software & IT Services",
        company_size="500+",
        contact_person="Muktadir Rahman",
        contact_phone="+8801700000000",
        website_url="https://brainstation-23.com",
        office_address="8th Floor, Plot 2, Mirpur 14, Dhaka, Bangladesh",
        tagline="Global Digital Solutions Partner",
        description="Pioneering software development company in Bangladesh delivering enterprise systems.",
        logo_url=None,
        banner_url=None,
        social_links={
            "linkedin": "https://linkedin.com/company/brainstation23",
            "facebook": "https://facebook.com/brainstation23",
            "github": "https://github.com/brainstation-23",
        },
        trade_license_url="https://storage.skill2career.com/licenses/bs23_license.pdf",
        verification_status="PENDING",
    )
    db_session.add(profile)
    db_session.commit()
    db_session.refresh(profile)

    return user


@pytest.fixture
def company_auth_headers(company_user: User) -> dict:
    """Generate authorization headers for company user."""
    token = create_access_token(
        subject=company_user.id,
        claims={"email": company_user.email, "role": company_user.role.value}
    )
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def learner_auth_headers(db_session: Session) -> dict:
    """Fixture providing a learner token."""
    user = User(
        email="learner.test@aust.edu",
        hashed_password=hash_password("LearnerPass123!"),
        role=UserRole.LEARNER,
        first_name="Rahim",
        last_name="Uddin",
        is_active=True,
        is_verified=True,
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)

    token = create_access_token(
        subject=user.id,
        claims={"email": user.email, "role": user.role.value}
    )
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def admin_auth_headers(db_session: Session) -> dict:
    """Fixture providing an admin token."""
    user = User(
        email="admin.security@skill2career.com",
        hashed_password=hash_password("AdminPass123!"),
        role=UserRole.ADMIN,
        first_name="Asif",
        last_name="Admin",
        is_active=True,
        is_verified=True,
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)

    token = create_access_token(
        subject=user.id,
        claims={"email": user.email, "role": user.role.value}
    )
    return {"Authorization": f"Bearer {token}"}


def test_get_company_profile_initial(client: TestClient, company_auth_headers: dict, company_user: User):
    """Test retrieving authenticated company's own complete profile (SKL-3)."""
    response = client.get("/api/v1/companies/profile/me", headers=company_auth_headers)
    assert response.status_code == 200
    res_data = response.json()
    assert res_data["success"] is True
    assert res_data["data"]["company_name"] == "Brain Station 23"
    assert res_data["data"]["email"] == company_user.email
    assert res_data["data"]["verification_status"] == "PENDING"
    assert res_data["data"]["contact_person"] == "Muktadir Rahman"
    assert res_data["data"]["social_links"]["linkedin"] == "https://linkedin.com/company/brainstation23"


def test_update_company_profile_success(client: TestClient, company_auth_headers: dict, db_session: Session, company_user: User):
    """Test updating company profile fields updates MySQL record and returns updated profile (SKL-3 Testing Criteria)."""
    payload = {
        "company_name": "Brain Station 23 Limited",
        "tagline": "Empowering Next-Gen Enterprise Engineering",
        "description": "Top-tier custom software development agency with 700+ engineers.",
        "industry": "Enterprise Software & Cloud Engineering",
        "company_size": "500+",
        "contact_person": "Lam-Yea Chowdhury",
        "contact_phone": "+8801811223344",
        "website_url": "https://www.brainstation-23.com",
        "office_address": "8th Floor, Mirpur 14, Dhaka 1206",
        "social_links": {
            "linkedin": "https://www.linkedin.com/company/brainstation-23",
            "github": "https://github.com/brain-station-23",
            "twitter": "https://x.com/brainstation23",
            "facebook": "https://facebook.com/brainstation23",
        }
    }

    response = client.put("/api/v1/companies/profile/me", json=payload, headers=company_auth_headers)
    assert response.status_code == 200
    res_data = response.json()
    assert res_data["success"] is True
    assert res_data["data"]["company_name"] == "Brain Station 23 Limited"
    assert res_data["data"]["tagline"] == "Empowering Next-Gen Enterprise Engineering"
    assert res_data["data"]["contact_person"] == "Lam-Yea Chowdhury"
    assert res_data["data"]["social_links"]["github"] == "https://github.com/brain-station-23"

    # Verify database persistence
    db_profile = db_session.query(CompanyProfile).filter(CompanyProfile.user_id == company_user.id).first()
    assert db_profile is not None
    assert db_profile.company_name == "Brain Station 23 Limited"
    assert db_profile.contact_person == "Lam-Yea Chowdhury"
    assert db_profile.social_links["twitter"] == "https://x.com/brainstation23"


def test_update_company_profile_invalid_url_fails(client: TestClient, company_auth_headers: dict):
    """Test that invalid website URL or social URI syntax returns HTTP 422 validation error (Strict URL Validation)."""
    payload = {
        "website_url": "not-a-valid-http-or-https-url",
    }
    response = client.put("/api/v1/companies/profile/me", json=payload, headers=company_auth_headers)
    assert response.status_code == 422
    assert response.json()["error_code"] == "VALIDATION_ERROR"

    payload_social = {
        "social_links": {
            "linkedin": "javascript:alert(1)"
        }
    }
    response_social = client.put("/api/v1/companies/profile/me", json=payload_social, headers=company_auth_headers)
    assert response_social.status_code == 422
    assert response_social.json()["error_code"] == "VALIDATION_ERROR"


def test_upload_company_logo_png_success(client: TestClient, company_auth_headers: dict, db_session: Session, company_user: User):
    """Test uploading valid PNG logo image (magic bytes \\x89PNG\\r\\n\\x1a\\n) succeeds."""
    png_bytes = b"\x89PNG\r\n\x1a\n" + b"\x00" * 200  # Valid PNG header
    files = {"file": ("company_logo.png", io.BytesIO(png_bytes), "image/png")}

    response = client.post("/api/v1/companies/profile/logo", files=files, headers=company_auth_headers)
    assert response.status_code == 200
    res_data = response.json()
    assert res_data["success"] is True
    assert "/api/v1/companies/assets/logo/" in res_data["data"]["asset_url"]

    # Verify DB updated
    db_profile = db_session.query(CompanyProfile).filter(CompanyProfile.user_id == company_user.id).first()
    assert db_profile.logo_url == res_data["data"]["asset_url"]


def test_upload_company_logo_invalid_mime_type_fails(client: TestClient, company_auth_headers: dict):
    """Test that uploading invalid image MIME type returns HTTP 400 Bad Request (SKL-3 Testing Criteria)."""
    fake_doc = b"%PDF-1.4 Fake PDF file"
    files = {"file": ("malicious.pdf", io.BytesIO(fake_doc), "application/pdf")}

    response = client.post("/api/v1/companies/profile/logo", files=files, headers=company_auth_headers)
    assert response.status_code == 400
    res_data = response.json()
    assert res_data["success"] is False
    assert res_data["error_code"] in {"INVALID_MIME_TYPE", "INVALID_FILE_EXTENSION"}


def test_upload_company_logo_invalid_magic_bytes_fails(client: TestClient, company_auth_headers: dict):
    """Test uploading file with .png extension but spoofed text contents fails deep magic inspection."""
    corrupted_data = b"Plain text disguised as image"
    files = {"file": ("fake_image.png", io.BytesIO(corrupted_data), "image/png")}

    response = client.post("/api/v1/companies/profile/logo", files=files, headers=company_auth_headers)
    assert response.status_code == 400
    res_data = response.json()
    assert res_data["success"] is False
    assert res_data["error_code"] == "INVALID_IMAGE_HEADER"


def test_upload_company_logo_size_limit_fails(client: TestClient, company_auth_headers: dict):
    """Test that image exceeding 5MB returns HTTP 400 Bad Request."""
    large_data = b"\x89PNG\r\n\x1a\n" + (b"0" * (5 * 1024 * 1024 + 500))  # > 5MB
    files = {"file": ("huge_logo.png", io.BytesIO(large_data), "image/png")}

    response = client.post("/api/v1/companies/profile/logo", files=files, headers=company_auth_headers)
    assert response.status_code == 400
    res_data = response.json()
    assert res_data["error_code"] == "FILE_TOO_LARGE"


def test_upload_company_banner_success(client: TestClient, company_auth_headers: dict, db_session: Session, company_user: User):
    """Test uploading valid JPEG cover banner succeeds."""
    jpeg_bytes = b"\xff\xd8\xff\xe0\x00\x10JFIF" + b"\x00" * 300
    files = {"file": ("banner.jpg", io.BytesIO(jpeg_bytes), "image/jpeg")}

    response = client.post("/api/v1/companies/profile/banner", files=files, headers=company_auth_headers)
    assert response.status_code == 200
    res_data = response.json()
    assert res_data["success"] is True
    assert "/api/v1/companies/assets/banner/" in res_data["data"]["asset_url"]

    db_profile = db_session.query(CompanyProfile).filter(CompanyProfile.user_id == company_user.id).first()
    assert db_profile.banner_url == res_data["data"]["asset_url"]


def test_upload_company_banner_invalid_mime_fails(client: TestClient, company_auth_headers: dict):
    """Test uploading invalid MIME type for banner returns 400."""
    fake_exe = b"MZ\x90\x00" + b"\x00" * 100
    files = {"file": ("banner.exe", io.BytesIO(fake_exe), "application/octet-stream")}

    response = client.post("/api/v1/companies/profile/banner", files=files, headers=company_auth_headers)
    assert response.status_code == 400


def test_serve_company_asset_endpoint(client: TestClient, company_auth_headers: dict):
    """Test downloading uploaded branding asset returns correct image stream."""
    png_bytes = b"\x89PNG\r\n\x1a\n" + b"\x00" * 200
    files = {"file": ("brand_logo.png", io.BytesIO(png_bytes), "image/png")}

    upload_res = client.post("/api/v1/companies/profile/logo", files=files, headers=company_auth_headers)
    assert upload_res.status_code == 200
    asset_url = upload_res.json()["data"]["asset_url"]

    # Now download asset
    get_res = client.get(asset_url)
    assert get_res.status_code == 200
    assert get_res.headers["content-type"] == "image/png"
    assert get_res.content.startswith(b"\x89PNG\r\n\x1a\n")


def test_public_company_profile_endpoint_sanitized(client: TestClient, company_user: User):
    """
    Test public profile endpoint returns sanitized company details without exposing internal contact information (SKL-3 Testing Criteria).
    """
    company_profile = company_user.company_profile
    assert company_profile is not None

    response = client.get(f"/api/v1/companies/{company_profile.id}/public")
    assert response.status_code == 200
    res_data = response.json()
    assert res_data["success"] is True
    data = res_data["data"]

    # Public branding info must be present
    assert data["id"] == company_profile.id
    assert data["company_name"] == "Brain Station 23"
    assert data["industry"] == "Software & IT Services"
    assert data["company_size"] == "500+"
    assert data["tagline"] == "Global Digital Solutions Partner"
    assert data["website_url"] == "https://brainstation-23.com"
    assert data["social_links"]["linkedin"] == "https://linkedin.com/company/brainstation23"
    assert "active_jobs" in data
    assert isinstance(data["active_jobs"], list)

    # CRITICAL: Sensitive internal contact details MUST NOT be exposed!
    assert "contact_person" not in data
    assert "contact_phone" not in data
    assert "trade_license_url" not in data
    assert "user_id" not in data
    assert "email" not in data


def test_public_company_profile_not_found(client: TestClient):
    """Test requesting non-existent company ID returns HTTP 404."""
    response = client.get("/api/v1/companies/99999/public")
    assert response.status_code == 404
    res_data = response.json()
    assert res_data["success"] is False
    assert res_data["error_code"] == "COMPANY_NOT_FOUND"


def test_admin_content_moderation_approve(client: TestClient, admin_auth_headers: dict, company_user: User, db_session: Session):
    """Test admin content moderation approving company and recording audit log (SKL-3 / SKL-50)."""
    company_profile = company_user.company_profile
    payload = {
        "action": "APPROVE",
        "notes": "Verified official trade license and corporate domain. Approved for job publishing.",
        "verification_status": "APPROVED",
        "is_verified": True,
    }

    response = client.patch(
        f"/api/v1/admin/companies/{company_profile.id}/moderate",
        json=payload,
        headers=admin_auth_headers
    )
    assert response.status_code == 200
    res_data = response.json()
    assert res_data["success"] is True
    assert res_data["data"]["verification_status"] == "APPROVED"
    assert res_data["data"]["is_verified"] is True

    # Verify audit log was created
    audit_record = (
        db_session.query(AuditLog)
        .filter(AuditLog.target_user_id == company_user.id)
        .order_by(AuditLog.id.desc())
        .first()
    )
    assert audit_record is not None
    assert audit_record.action == "COMPANY_APPROVE"
    assert audit_record.details["company_id"] == company_profile.id


def test_admin_content_moderation_reject(client: TestClient, admin_auth_headers: dict, company_user: User):
    """Test admin rejecting company verification."""
    company_profile = company_user.company_profile
    payload = {
        "action": "REJECT",
        "notes": "Trade license document is expired. Please re-submit a valid license.",
        "verification_status": "REJECTED",
    }

    response = client.patch(
        f"/api/v1/admin/companies/{company_profile.id}/moderate",
        json=payload,
        headers=admin_auth_headers
    )
    assert response.status_code == 200
    res_data = response.json()
    assert res_data["data"]["verification_status"] == "REJECTED"


def test_non_admin_cannot_moderate_company(client: TestClient, company_auth_headers: dict, learner_auth_headers: dict, company_user: User):
    """Test non-admin roles cannot access the moderation endpoint (HTTP 403 Forbidden)."""
    company_profile = company_user.company_profile
    payload = {"action": "APPROVE"}

    # Company user trying to moderate themselves
    res_company = client.patch(
        f"/api/v1/admin/companies/{company_profile.id}/moderate",
        json=payload,
        headers=company_auth_headers
    )
    assert res_company.status_code == 403

    # Learner user trying to moderate company
    res_learner = client.patch(
        f"/api/v1/admin/companies/{company_profile.id}/moderate",
        json=payload,
        headers=learner_auth_headers
    )
    assert res_learner.status_code == 403


def test_unauthenticated_company_profile_me_fails(client: TestClient):
    """Test unauthenticated request to /profile/me returns HTTP 401."""
    response = client.get("/api/v1/companies/profile/me")
    assert response.status_code == 401


def test_learner_access_to_company_profile_me_forbidden(client: TestClient, learner_auth_headers: dict):
    """Test learner role accessing company profile/me returns HTTP 403 Forbidden."""
    response = client.get("/api/v1/companies/profile/me", headers=learner_auth_headers)
    assert response.status_code == 403
