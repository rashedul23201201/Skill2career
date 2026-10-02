from fastapi.testclient import TestClient


def test_register_user_success(client: TestClient):
    """Test successful user registration."""
    payload = {
        "email": "testuser@example.com",
        "password": "Password123!",
        "first_name": "Rahim",
        "last_name": "Uddin",
        "role": "LEARNER"
    }
    response = client.post("/api/v1/auth/register", json=payload)
    assert response.status_code == 201
    data = response.json()
    assert data["success"] is True
    assert data["data"]["email"] == "testuser@example.com"
    assert data["data"]["first_name"] == "Rahim"
    assert data["data"]["last_name"] == "Uddin"
    assert data["data"]["role"] == "LEARNER"
    assert "hashed_password" not in data["data"]


def test_register_duplicate_email_fails(client: TestClient):
    """Test that registering duplicate email returns 409 Conflict."""
    payload = {
        "email": "duplicate@example.com",
        "password": "Password123!",
        "first_name": "Karim",
        "last_name": "Chowdhury",
        "role": "INSTRUCTOR"
    }
    # First registration
    res1 = client.post("/api/v1/auth/register", json=payload)
    assert res1.status_code == 201

    # Second registration with same email
    res2 = client.post("/api/v1/auth/register", json=payload)
    assert res2.status_code == 409
    data = res2.json()
    assert data["success"] is False
    assert data["error_code"] == "EMAIL_ALREADY_EXISTS"


def test_login_and_access_me_profile(client: TestClient):
    """Test full authentication flow: register -> login -> access /auth/me."""
    register_payload = {
        "email": "flowuser@example.com",
        "password": "SecurePassword999",
        "first_name": "Fatima",
        "last_name": "Begum",
        "role": "COMPANY"
    }
    reg_res = client.post("/api/v1/auth/register", json=register_payload)
    assert reg_res.status_code == 201

    # Login
    login_payload = {
        "email": "flowuser@example.com",
        "password": "SecurePassword999"
    }
    login_res = client.post("/api/v1/auth/login", json=login_payload)
    assert login_res.status_code == 200
    login_data = login_res.json()
    assert login_data["success"] is True
    token = login_data["data"]["access_token"]
    assert token

    # Access /auth/me with Bearer token
    headers = {"Authorization": f"Bearer {token}"}
    me_res = client.get("/api/v1/auth/me", headers=headers)
    assert me_res.status_code == 200
    me_data = me_res.json()
    assert me_data["success"] is True
    assert me_data["data"]["email"] == "flowuser@example.com"
    assert me_data["data"]["role"] == "COMPANY"


def test_login_invalid_password(client: TestClient):
    """Test login with incorrect credentials returns 401 Unauthorized."""
    payload = {
        "email": "wrongpass@example.com",
        "password": "CorrectPassword123",
        "first_name": "Anis",
        "last_name": "Haque"
    }
    client.post("/api/v1/auth/register", json=payload)

    # Attempt login with wrong password
    bad_login = {
        "email": "wrongpass@example.com",
        "password": "IncorrectPassword"
    }
    res = client.post("/api/v1/auth/login", json=bad_login)
    assert res.status_code == 401
    assert res.json()["error_code"] == "INVALID_CREDENTIALS"


def test_me_without_token_fails(client: TestClient):
    """Test accessing protected /auth/me without token returns 401."""
    res = client.get("/api/v1/auth/me")
    assert res.status_code == 401
    assert res.json()["error_code"] == "NOT_AUTHENTICATED"
