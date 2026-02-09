"""Authentication API tests."""
import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_health_check():
    """Test health check endpoint."""
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"


def test_register_user():
    """Test user registration."""
    response = client.post(
        "/api/auth/register",
        json={"username": "testuser", "password": "testpass123"}
    )
    assert response.status_code == 201
    data = response.json()
    assert data["username"] == "testuser"
    assert "id" in data
    assert "password_hash" not in response.text


def test_register_duplicate_user():
    """Test duplicate user registration fails."""
    # First registration
    client.post(
        "/api/auth/register",
        json={"username": "dupuser", "password": "testpass123"}
    )
    # Duplicate
    response = client.post(
        "/api/auth/register",
        json={"username": "dupuser", "password": "testpass123"}
    )
    assert response.status_code == 400
    assert "already registered" in response.json()["detail"]


def test_login_success():
    """Test successful login."""
    # Create user first
    client.post(
        "/api/auth/register",
        json={"loginuser", "password": "loginpass123"}
    )
    # Login
    response = client.post(
        "/api/auth/login",
        data={"username": "loginuser", "password": "loginpass123"}
    )
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"


def test_login_wrong_password():
    """Test login with wrong password fails."""
    client.post(
        "/api/auth/register",
        json={"wrongpass", "password": "correctpass"}
    )
    response = client.post(
        "/api/auth/login",
        data={"username": "wrongpass", "password": "wrongpass"}
    )
    assert response.status_code == 401
