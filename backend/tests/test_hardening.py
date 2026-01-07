from fastapi.testclient import TestClient
from backend.app.main import app
from backend.app.config import settings
import pytest

client = TestClient(app)

def test_health_public():
    # Health check should be public
    response = client.get("/health")
    assert response.status_code == 200

def test_passcode_protection():
    # Temporarily set passcode for testing
    original_passcode = settings.API_PASSCODE
    settings.API_PASSCODE = "secret123"
    
    try:
        # Request without passcode
        response = client.get("/jobs")
        assert response.status_code == 403
        assert response.json()["detail"] == "Invalid or missing passcode"
        
        # Request with wrong passcode
        response = client.get("/jobs", headers={"X-Passcode": "wrong"})
        assert response.status_code == 403
        
        # Request with correct passcode
        response = client.get("/jobs", headers={"X-Passcode": "secret123"})
        # 200 (or other success/database error if not mocked, but we just care about middleware)
        assert response.status_code != 403
        
    finally:
        settings.API_PASSCODE = original_passcode

def test_root_public():
    response = client.get("/")
    assert response.status_code == 200
