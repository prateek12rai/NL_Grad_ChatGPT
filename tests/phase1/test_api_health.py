"""Phase 1.5.2 — FastAPI health endpoint."""

from fastapi.testclient import TestClient

from api.main import app


def test_health_returns_ok(tmp_chroma_path):
    client = TestClient(app)
    response = client.get("/health")
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "ok"
    assert body["chroma"] == "reachable"


def test_openapi_schema_available():
    client = TestClient(app)
    response = client.get("/openapi.json")
    assert response.status_code == 200
    schema = response.json()
    assert schema["info"]["title"] == "India Medical RAG API"
