"""API integration tests (FastAPI TestClient, full lifespan)."""
import pytest
from fastapi.testclient import TestClient

from daniela_core import create_app


@pytest.fixture(scope="module")
def client():
    app = create_app()
    with TestClient(app) as c:
        yield c


def test_health(client):
    r = client.get("/health")
    assert r.status_code == 200
    assert r.json()["status"] == "healthy"


def test_brain_process(client):
    r = client.post(
        "/api/v1/brain/process",
        json={"input": "hello", "context": {"source": "test"}},
    )
    assert r.status_code == 200
    data = r.json()
    assert data["coherence"] == 4
    assert data["empathy"] == 0.96


def test_memory_roundtrip(client):
    store = client.post(
        "/api/v1/memory/store",
        json={"tier": "episodic", "content": "api test note", "importance": 0.7},
    )
    assert store.status_code == 200

    recall = client.post(
        "/api/v1/memory/recall",
        json={"query": "api test", "limit": 5},
    )
    assert recall.status_code == 200
    assert recall.json()["count"] >= 1


def test_orchestrator_delegate_and_execute(client):
    delegate = client.post(
        "/api/v1/orchestrator/delegate",
        json={"description": "encrypt the vault"},
    )
    assert delegate.status_code == 200
    task_id = delegate.json()["task_id"]

    execute = client.post(f"/api/v1/orchestrator/execute/{task_id}")
    assert execute.status_code == 200


def test_orchestrator_consensus(client):
    r = client.post(
        "/api/v1/orchestrator/consensus",
        json={"proposal": {"action": "deploy"}},
    )
    assert r.status_code == 200
    assert r.json()["accepted"] is True


def test_persona_rename_and_greet(client):
    rename = client.post("/api/v1/persona/rename", json={"name": "Aurora"})
    assert rename.status_code == 200
    assert rename.json()["name"] == "Aurora"

    greet = client.get("/api/v1/persona/greet")
    assert greet.status_code == 200
    assert "Aurora" in greet.json()["greeting"]


def test_life_requires_admin(client):
    r = client.post("/api/v1/life/enable", json={"enabled": True, "admin": False})
    assert r.status_code == 403

    r = client.post("/api/v1/life/enable", json={"enabled": True, "admin": True})
    assert r.status_code == 200
    assert r.json()["enabled"] is True


def test_agents_list(client):
    r = client.get("/api/v1/agents/list")
    assert r.status_code == 200
    assert len(r.json()["agents"]) >= 6


def test_tools_list(client):
    r = client.get("/api/v1/tools/list")
    assert r.status_code == 200
    assert "web_search" in r.json()


def test_voice_synthesize(client):
    r = client.post("/api/v1/voice/synthesize", json={"text": "hello"})
    assert r.status_code == 200
    assert r.json()["text"] == "hello"


def test_admin_audit_and_verify(client):
    r = client.post(
        "/api/v1/admin/audit",
        json={"action": "test", "actor": "pytest"},
    )
    assert r.status_code == 200
    assert "digest" in r.json()

    log = client.get("/api/v1/admin/audit-log")
    assert log.status_code == 200
    assert log.json()["chain_valid"] is True
