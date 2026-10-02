from fastapi.testclient import TestClient


def test_register_user_success(client: TestClient):
    """Test successful user registration with verification token (AC-1)."""
    payload = {
        "email": "rashedul_test@example.com",
        "password": "Password123!",
        "first_name": "Rashedul",
        "last_name": "Islam",
        "role": "LEARNER",
        "institution": "University of Asia Pacific",
        "department": "Computer Science & Engineering",
        "target_role": "Junior Software Developer"
    }
    response = client.post("/api/v1/auth/register", json=payload)
    assert response.status_code == 201
    data = response.json()
    assert data["success"] is True
    assert data["data"]["user"]["email"] == "rashedul_test@example.com"
    assert data["data"]["user"]["role"] == "LEARNER"
    assert data["data"]["user"]["is_verified"] is False
    assert "verification_token" in data["data"]
    assert data["data"]["verification_token"] is not None


def test_register_duplicate_email_fails(client: TestClient):
    """Test that duplicate email registration returns 409 Conflict."""
    payload = {
        "email": "duplicate@example.com",
        "password": "Password123!",
        "first_name": "Karim",
        "last_name": "Chowdhury",
        "role": "INSTRUCTOR",
        "qualification": "M.Sc. in CSE"
    }
    res1 = client.post("/api/v1/auth/register", json=payload)
    assert res1.status_code == 201

    res2 = client.post("/api/v1/auth/register", json=payload)
    assert res2.status_code == 409
    assert res2.json()["error_code"] == "EMAIL_ALREADY_EXISTS"


def test_login_and_access_me_profile(client: TestClient):
    """Test full login flow returning access token and refresh token (AC-2)."""
    reg_payload = {
        "email": "company_login@example.com",
        "password": "SecurePassword999",
        "first_name": "Brain",
        "last_name": "Station",
        "role": "COMPANY",
        "company_name": "Brain Station 23",
        "industry": "Software Technology"
    }
    reg_res = client.post("/api/v1/auth/register", json=reg_payload)
    assert reg_res.status_code == 201

    login_payload = {
        "email": "company_login@example.com",
        "password": "SecurePassword999",
        "remember_me": True
    }
    login_res = client.post("/api/v1/auth/login", json=login_payload)
    assert login_res.status_code == 200
    login_data = login_res.json()["data"]
    assert "access_token" in login_data
    assert "refresh_token" in login_data
    assert login_data["user"]["role"] == "COMPANY"

    # Access /auth/me with Bearer token
    headers = {"Authorization": f"Bearer {login_data['access_token']}"}
    me_res = client.get("/api/v1/auth/me", headers=headers)
    assert me_res.status_code == 200
    assert me_res.json()["data"]["email"] == "company_login@example.com"


def test_refresh_token_rotation(client: TestClient):
    """Test refresh token exchange and rotation."""
    reg = client.post("/api/v1/auth/register", json={
        "email": "refresh_user@example.com",
        "password": "Password123!",
        "first_name": "Asif",
        "last_name": "Ahmed",
        "role": "LEARNER"
    })
    assert reg.status_code == 201

    login_res = client.post("/api/v1/auth/login", json={
        "email": "refresh_user@example.com",
        "password": "Password123!"
    })
    initial_refresh = login_res.json()["data"]["refresh_token"]

    # Exchange refresh token
    refresh_res = client.post("/api/v1/auth/refresh", json={"refresh_token": initial_refresh})
    assert refresh_res.status_code == 200
    refresh_data = refresh_res.json()["data"]
    new_refresh = refresh_data["refresh_token"]
    assert new_refresh != initial_refresh

    # Using the old revoked refresh token must now fail
    old_res = client.post("/api/v1/auth/refresh", json={"refresh_token": initial_refresh})
    assert old_res.status_code == 401
    assert old_res.json()["error_code"] == "INVALID_REFRESH_TOKEN"


def test_login_failed_attempts_lockout(client: TestClient):
    """Test that 5 consecutive failed login attempts trigger account lockout (AC-3)."""
    email = "lockout_test@example.com"
    client.post("/api/v1/auth/register", json={
        "email": email,
        "password": "CorrectPassword123",
        "first_name": "Test",
        "last_name": "Lockout"
    })

    # 4 failed attempts should return 401
    for i in range(4):
        res = client.post("/api/v1/auth/login", json={"email": email, "password": f"WrongPass{i}"})
        assert res.status_code == 401
        assert res.json()["error_code"] == "INVALID_CREDENTIALS"

    # 5th failed attempt should trigger lockout (HTTP 429)
    res5 = client.post("/api/v1/auth/login", json={"email": email, "password": "WrongPassword5"})
    assert res5.status_code == 429
    assert res5.json()["error_code"] == "ACCOUNT_LOCKED"

    # Even with correct password, account remains locked
    res_locked = client.post("/api/v1/auth/login", json={"email": email, "password": "CorrectPassword123"})
    assert res_locked.status_code == 429
    assert res_locked.json()["error_code"] == "ACCOUNT_LOCKED"


def test_password_reset_workflow(client: TestClient):
    """Test full forgot-password and reset-password workflow (AC-4)."""
    email = "reset_user@example.com"
    client.post("/api/v1/auth/register", json={
        "email": email,
        "password": "OldPassword123!",
        "first_name": "Reset",
        "last_name": "Candidate"
    })

    # Step 1: Request password reset
    forgot_res = client.post("/api/v1/auth/forgot-password", json={"email": email})
    assert forgot_res.status_code == 200
    reset_token = forgot_res.json()["data"]["reset_token"]
    assert reset_token is not None

    # Step 2: Reset password
    reset_res = client.post("/api/v1/auth/reset-password", json={
        "token": reset_token,
        "new_password": "NewSecurePassword456!"
    })
    assert reset_res.status_code == 200

    # Step 3: Old password should no longer work
    old_login = client.post("/api/v1/auth/login", json={"email": email, "password": "OldPassword123!"})
    assert old_login.status_code == 401

    # Step 4: New password should log in successfully
    new_login = client.post("/api/v1/auth/login", json={"email": email, "password": "NewSecurePassword456!"})
    assert new_login.status_code == 200


def test_email_verification_workflow(client: TestClient):
    """Test email verification flow (AC-1)."""
    email = "verify_user@example.com"
    reg_res = client.post("/api/v1/auth/register", json={
        "email": email,
        "password": "Password123!",
        "first_name": "Verif",
        "last_name": "User"
    })
    token = reg_res.json()["data"]["verification_token"]

    verify_res = client.post("/api/v1/auth/verify-email", json={"token": token})
    assert verify_res.status_code == 200
    assert verify_res.json()["data"]["is_verified"] is True
