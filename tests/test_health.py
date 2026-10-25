"""Exercise the public HTTP contract through the actual ASGI application."""

from fastapi.testclient import TestClient

from app.main import app


def test_health_contract():
    with TestClient(app) as client:
        response = client.get("/health")
    assert response.status_code == 200
    assert response.headers["content-type"] == "application/json"
    assert response.json() == {"status": "ok"}


def test_unknown_route_returns_404():
    with TestClient(app) as client:
        assert client.get("/unknown").status_code == 404


def test_health_rejects_mutation():
    with TestClient(app) as client:
        assert client.post("/health").status_code == 405
