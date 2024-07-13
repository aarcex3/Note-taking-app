import pytest
from fastapi.testclient import TestClient

from src.main import app


@pytest.fixture
def client():
    """Create a TestClient instance for the FastAPI app."""
    return TestClient(app)

def test_health_check(client:TestClient):
    """Test the health check endpoint."""
    response = client.get('/health')
    assert response.status_code == 200
    assert response.json() == {"Message": "Service running"}
