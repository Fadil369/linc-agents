"""
Test the AuthLINC authentication agent
"""

import pytest
from fastapi.testclient import TestClient
import sys
import os

# Add the project root to the path
sys.path.append(os.path.join(os.path.dirname(__file__), '../../..'))

from agents.authlinc.main import create_app
from shared.database import DatabaseManager

@pytest.fixture
def client():
    """Create test client"""
    app = create_app()
    DatabaseManager.init_database()
    return TestClient(app.app)

@pytest.fixture
def test_user_data():
    """Test user registration data"""
    import time
    timestamp = int(time.time())
    return {
        "username": f"testuser_{timestamp}",
        "email": f"test_{timestamp}@example.com",
        "password": "testpassword123",
        "full_name": "Test User",
        "arabic_name": "مستخدم تجريبي",
        "role": "patient",
        "preferred_language": "en",
        "phone": "+966501234567"
    }

def test_health_check(client):
    """Test health check endpoint"""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert data["agent"] == "authlinc"

def test_user_registration(client, test_user_data):
    """Test user registration"""
    response = client.post("/auth/register", json=test_user_data)
    if response.status_code != 200:
        print(f"Response status: {response.status_code}")
        print(f"Response content: {response.text}")
    assert response.status_code == 200
    
    data = response.json()
    assert data["username"] == test_user_data["username"]
    assert data["email"] == test_user_data["email"]
    assert data["full_name"] == test_user_data["full_name"]
    assert data["role"] == test_user_data["role"]
    assert "id" in data
    assert "created_at" in data

def test_user_login(client, test_user_data):
    """Test user login"""
    # First register a user
    client.post("/auth/register", json=test_user_data)
    
    # Then try to login
    login_data = {
        "username": test_user_data["username"],
        "password": test_user_data["password"],
        "agent_name": "test"
    }
    
    response = client.post("/auth/login", json=login_data)
    assert response.status_code == 200
    
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"
    assert "user" in data
    assert "permissions" in data
    assert data["user"]["username"] == test_user_data["username"]

def test_invalid_login(client):
    """Test login with invalid credentials"""
    login_data = {
        "username": "nonexistent",
        "password": "wrongpassword",
        "agent_name": "test"
    }
    
    response = client.post("/auth/login", json=login_data)
    assert response.status_code == 401

def test_duplicate_registration(client):
    """Test registration with duplicate username/email"""
    import time
    timestamp = int(time.time())
    
    test_data = {
        "username": f"duplicate_{timestamp}",
        "email": f"duplicate_{timestamp}@example.com",
        "password": "testpassword123",
        "full_name": "Duplicate User",
        "role": "patient"
    }
    
    # Register user first time
    response1 = client.post("/auth/register", json=test_data)
    assert response1.status_code == 200
    
    # Try to register again with same data
    response2 = client.post("/auth/register", json=test_data)
    assert response2.status_code == 400

def test_token_verification(client, test_user_data):
    """Test token verification"""
    # Register and login user
    client.post("/auth/register", json=test_user_data)
    
    login_data = {
        "username": test_user_data["username"],
        "password": test_user_data["password"],
        "agent_name": "test"
    }
    
    login_response = client.post("/auth/login", json=login_data)
    token = login_response.json()["access_token"]
    
    # Verify token
    headers = {"Authorization": f"Bearer {token}"}
    response = client.post("/auth/verify-token", headers=headers)
    assert response.status_code == 200
    
    data = response.json()
    assert data["valid"] is True
    assert data["username"] == test_user_data["username"]

def test_get_current_user(client, test_user_data):
    """Test getting current user info"""
    # Register and login user
    client.post("/auth/register", json=test_user_data)
    
    login_data = {
        "username": test_user_data["username"],
        "password": test_user_data["password"],
        "agent_name": "test"
    }
    
    login_response = client.post("/auth/login", json=login_data)
    token = login_response.json()["access_token"]
    
    # Get user info
    headers = {"Authorization": f"Bearer {token}"}
    response = client.get("/auth/me", headers=headers)
    assert response.status_code == 200
    
    data = response.json()
    assert data["username"] == test_user_data["username"]
    assert data["email"] == test_user_data["email"]

def test_invalid_token(client):
    """Test with invalid token"""
    headers = {"Authorization": "Bearer invalid_token"}
    response = client.get("/auth/me", headers=headers)
    assert response.status_code == 401

if __name__ == "__main__":
    pytest.main([__file__])