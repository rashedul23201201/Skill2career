from fastapi.testclient import TestClient


def test_health_check_endpoint(client: TestClient):
    """Test that the /api/v1/health endpoint responds with 200 OK and expected payload."""
    response = client.get("/api/v1/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert "service" in data
    assert "environment" in data
    assert data["version"] == "1.0.0"
