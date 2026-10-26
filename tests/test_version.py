"""Verify the version visible to users of the running API."""

from fastapi.testclient import TestClient

from app.main import app


def test_version_contract():
    with TestClient(app) as client:
        response = client.get("/version")
    assert response.status_code == 200
    assert response.headers["content-type"] == "application/json"
    assert response.json() == {"version": "0.2.0"}
    assert response.json()["version"] == app.version
