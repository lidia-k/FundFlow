"""Smoke tests for FastAPI application endpoints."""

from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_root_endpoint_returns_welcome_message():
    response = client.get("/")
    assert response.status_code == 200
    payload = response.json()
    assert payload["message"].startswith("Welcome to")


def test_health_endpoint_reports_healthy_status():
    response = client.get("/api/health")
    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] in {"healthy", "warning"}
    assert "services" in payload


def test_application_health_endpoint_is_minimal():
    response = client.get("/health")
    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "healthy"
    assert payload["service"] == "FundFlow"


def test_api_health_simple_endpoint():
    response = client.get("/api/health/simple")
    assert response.status_code == 200
    payload = response.json()
    assert payload == {"status": "healthy", "service": "fundflow-backend"}
