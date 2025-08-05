"""
Test the MasterLINC orchestration agent
"""

import pytest
import asyncio
from fastapi.testclient import TestClient
import sys
import os

# Add the project root to the path
sys.path.append(os.path.join(os.path.dirname(__file__), '../../..'))

from agents.masterlinc.main import create_app
from shared.database import DatabaseManager

@pytest.fixture
def client():
    """Create test client"""
    app = create_app()
    DatabaseManager.init_database()
    return TestClient(app.app)

def test_health_check(client):
    """Test health check endpoint"""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert data["agent"] == "masterlinc"
    assert "version" in data
    assert "uptime" in data

def test_root_endpoint(client):
    """Test root endpoint"""
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert data["agent"] == "masterlinc"
    assert data["status"] == "online"

def test_list_agents(client):
    """Test agent listing endpoint"""
    response = client.get("/agents")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    
    # Check if core agents are present
    agent_names = [agent["name"] for agent in data]
    assert "masterlinc" in agent_names
    assert "authlinc" in agent_names
    assert "doctorlinc" in agent_names

def test_system_metrics(client):
    """Test system metrics endpoint"""
    # This would require authentication in real implementation
    # For now, test that the endpoint exists
    response = client.get("/system/metrics")
    # Should return 401/403/422 without authentication
    assert response.status_code in [401, 403, 422]  # Might be 422 for missing dependencies

def test_workflow_route_structure(client):
    """Test workflow routing endpoint structure"""
    # Test without authentication (should fail)
    workflow_data = {
        "user_intent": "I need to see a doctor",
        "context": {},
        "preferred_language": "en",
        "priority": "normal"
    }
    
    response = client.post("/workflow/route", json=workflow_data)
    # Should return 401/403/422 without proper authentication
    assert response.status_code in [401, 403, 422]

if __name__ == "__main__":
    pytest.main([__file__])