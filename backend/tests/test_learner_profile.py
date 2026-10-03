import io
import pytest
from fastapi.testclient import TestClient


def get_auth_token(client: TestClient, email: str, role: str = "LEARNER") -> str:
    """Helper to register and login a user and return the Bearer access token."""
    reg_payload = {
        "email": email,
        "password": "StrongPassword123!",
        "first_name": "Test",
        "last_name": "Learner",
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


def test_get_learner_profile_initial(client: TestClient):
    """Test retrieving profile initializes default record with completion breakdown."""
    token = get_auth_token(client, "initial_learner@example.com")
    headers = {"Authorization": f"Bearer {token}"}

    res = client.get("/api/v1/learners/profile", headers=headers)
    assert res.status_code == 200
    data = res.json()["data"]

    assert data["email"] == "initial_learner@example.com"
    assert data["first_name"] == "Test"
    assert data["last_name"] == "Learner"
    assert data["role"] == "LEARNER"
    assert "completion_breakdown" in data
    assert data["completion_pct"] == 0  # No phone, location, institution, or skills yet


def test_learner_profile_completion_dynamic_rubric(client: TestClient):
    """Test profile completion updates dynamically across all 4 tiers (SKL-51)."""
    token = get_auth_token(client, "rubric_learner@example.com")
    headers = {"Authorization": f"Bearer {token}"}

    # Step 0: Initial profile is 0%
    r0 = client.get("/api/v1/learners/profile", headers=headers)
    assert r0.json()["data"]["completion_pct"] == 0

    # Step 1: Add phone and location -> Basic Info complete (25%)
    r1 = client.put(
        "/api/v1/learners/profile",
        json={"phone_number": "01712345678", "location": "Dhaka, Bangladesh"},
        headers=headers,
    )
    assert r1.status_code == 200
    assert r1.json()["data"]["completion_pct"] == 25
    assert r1.json()["data"]["completion_breakdown"]["basic_info"]["is_complete"] is True
    assert r1.json()["data"]["completion_breakdown"]["education"]["is_complete"] is False

    # Step 2: Add education -> 50%
    r2 = client.put(
        "/api/v1/learners/profile",
        json={
            "institution": "University of Asia Pacific",
            "department": "Computer Science & Engineering",
        },
        headers=headers,
    )
    assert r2.status_code == 200
    assert r2.json()["data"]["completion_pct"] == 50
    assert r2.json()["data"]["completion_breakdown"]["education"]["is_complete"] is True

    # Step 3: Add career track and at least 3 skills -> 75%
    r3 = client.put(
        "/api/v1/learners/profile",
        json={
            "target_role": "Junior Backend Developer",
            "primary_track": "Python & Cloud Engineering",
            "skills": ["Python", "FastAPI", "PostgreSQL"],
        },
        headers=headers,
    )
    assert r3.status_code == 200
    assert r3.json()["data"]["completion_pct"] == 75
    assert r3.json()["data"]["completion_breakdown"]["career_skills"]["is_complete"] is True
    assert len(r3.json()["data"]["skills"]) == 3

    # Step 4: Upload valid PDF resume -> 100%
    fake_pdf = b"%PDF-1.4\n1 0 obj\n<<>>\nendobj\ntrailer\n<<>>\n%%EOF"
    r4 = client.post(
        "/api/v1/learners/resume",
        files={"file": ("saif_cv.pdf", io.BytesIO(fake_pdf), "application/pdf")},
        headers=headers,
    )
    assert r4.status_code == 200
    assert r4.json()["data"]["completion_pct"] == 100
    assert r4.json()["data"]["completion_breakdown"]["resume"]["is_complete"] is True

    # Verify GET returns updated profile at 100%
    final_get = client.get("/api/v1/learners/profile", headers=headers)
    assert final_get.json()["data"]["completion_pct"] == 100
    assert final_get.json()["data"]["resume_filename"] == "saif_cv.pdf"


def test_update_profile_all_fields(client: TestClient):
    """Test updating all profile attributes including bio and portfolio links."""
    token = get_auth_token(client, "full_profile@example.com")
    headers = {"Authorization": f"Bearer {token}"}

    update_payload = {
        "phone_number": "+8801811223344",
        "location": "Chittagong, Bangladesh",
        "bio": "Aspiring software engineer passionate about scalable backend microservices.",
        "target_role": "Backend Engineer",
        "primary_track": "Backend Engineering",
        "institution": "BUET",
        "department": "CSE",
        "skills": ["FastAPI", "Docker", "Python", "Redis", "MySQL"],
        "portfolio_links": {
            "github_url": "https://github.com/saif-dev",
            "linkedin_url": "https://linkedin.com/in/saif-dev",
            "portfolio_url": "https://saif-dev.me",
        }
    }

    res = client.put("/api/v1/learners/profile", json=update_payload, headers=headers)
    assert res.status_code == 200
    data = res.json()["data"]

    assert data["phone_number"] == "+8801811223344"
    assert data["location"] == "Chittagong, Bangladesh"
    assert "scalable backend" in data["bio"]
    assert data["target_role"] == "Backend Engineer"
    assert data["institution"] == "BUET"
    assert len(data["skills"]) == 5
    assert data["portfolio_links"]["github_url"] == "https://github.com/saif-dev"
    assert data["completion_pct"] == 75  # Resume not yet uploaded


def test_upload_resume_docx_success(client: TestClient):
    """Test uploading a valid Word document (.docx) with PKZip magic bytes."""
    token = get_auth_token(client, "docx_learner@example.com")
    headers = {"Authorization": f"Bearer {token}"}

    # Standard PKZip header for docx
    fake_docx = b"PK\x03\x04\x14\x00\x06\x00" + b"\x00" * 100
    res = client.post(
        "/api/v1/learners/resume",
        files={"file": ("curriculum_vitae.docx", io.BytesIO(fake_docx), "application/vnd.openxmlformats-officedocument.wordprocessingml.document")},
        headers=headers,
    )
    assert res.status_code == 200
    data = res.json()["data"]
    assert data["resume_filename"] == "curriculum_vitae.docx"
    assert "resume_url" in data


def test_upload_resume_invalid_extension_fails(client: TestClient):
    """Test uploading invalid file extension (e.g. .png, .txt) returns 400 Bad Request."""
    token = get_auth_token(client, "bad_ext@example.com")
    headers = {"Authorization": f"Bearer {token}"}

    res = client.post(
        "/api/v1/learners/resume",
        files={"file": ("photo.png", io.BytesIO(b"\x89PNG\r\n\x1a\n"), "image/png")},
        headers=headers,
    )
    assert res.status_code == 400
    assert res.json()["error_code"] == "INVALID_FILE_EXTENSION"


def test_upload_resume_invalid_magic_bytes_fails(client: TestClient):
    """Test uploading file with .pdf extension but fake/non-PDF header returns 400 Bad Request."""
    token = get_auth_token(client, "bad_header@example.com")
    headers = {"Authorization": f"Bearer {token}"}

    fake_text_as_pdf = b"This is just a plain text file pretending to be a PDF"
    res = client.post(
        "/api/v1/learners/resume",
        files={"file": ("fake.pdf", io.BytesIO(fake_text_as_pdf), "application/pdf")},
        headers=headers,
    )
    assert res.status_code == 400
    assert res.json()["error_code"] == "INVALID_FILE_HEADER"


def test_upload_resume_exceeds_size_limit_fails(client: TestClient):
    """Test uploading file larger than 5MB returns 400 Bad Request."""
    token = get_auth_token(client, "large_file@example.com")
    headers = {"Authorization": f"Bearer {token}"}

    large_content = b"%PDF-1.4\n" + (b"0" * (5 * 1024 * 1024 + 100))
    res = client.post(
        "/api/v1/learners/resume",
        files={"file": ("too_large.pdf", io.BytesIO(large_content), "application/pdf")},
        headers=headers,
    )
    assert res.status_code == 400
    assert res.json()["error_code"] == "FILE_TOO_LARGE"


def test_download_and_delete_resume(client: TestClient):
    """Test downloading uploaded resume and subsequently deleting it."""
    token = get_auth_token(client, "download_test@example.com")
    headers = {"Authorization": f"Bearer {token}"}

    pdf_bytes = b"%PDF-1.5 test resume document contents %%EOF"
    upload_res = client.post(
        "/api/v1/learners/resume",
        files={"file": ("my_resume.pdf", io.BytesIO(pdf_bytes), "application/pdf")},
        headers=headers,
    )
    assert upload_res.status_code == 200

    # Test download
    dl_res = client.get("/api/v1/learners/resume/download", headers=headers)
    assert dl_res.status_code == 200
    assert dl_res.content == pdf_bytes

    # Test delete resume
    del_res = client.delete("/api/v1/learners/resume", headers=headers)
    assert del_res.status_code == 200
    del_data = del_res.json()["data"]
    assert del_data["resume_url"] is None
    assert del_data["resume_filename"] is None
    assert del_data["completion_breakdown"]["resume"]["is_complete"] is False

    # Second download should now return 404
    dl_res2 = client.get("/api/v1/learners/resume/download", headers=headers)
    assert dl_res2.status_code == 404


def test_unauthenticated_access_rejected(client: TestClient):
    """Test unauthenticated request to /api/v1/learners/profile returns 401."""
    res = client.get("/api/v1/learners/profile")
    assert res.status_code == 401


def test_company_role_access_forbidden(client: TestClient):
    """Test company role calling learner profile returns 403 Forbidden."""
    token = get_auth_token(client, "company_access@example.com", role="COMPANY")
    headers = {"Authorization": f"Bearer {token}"}

    res = client.get("/api/v1/learners/profile", headers=headers)
    assert res.status_code == 403
    assert res.json()["error_code"] == "INSUFFICIENT_ROLE_PERMISSIONS"
