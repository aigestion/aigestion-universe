"""Tests for the Daniela Sandbox (isolated execution)."""
import sys

import pytest
from fastapi.testclient import TestClient

sys.path.insert(0, r"C:\Users\Alejandro\aigestion-universe\apps\daniela-sandbox")

from services.sandbox import create_app


@pytest.fixture(scope="module")
def client():
    app = create_app()
    with TestClient(app) as c:
        yield c


def test_health(client):
    r = client.get("/health")
    assert r.status_code == 200
    executors = r.json()["executors"]
    assert executors["process"]["available"] is True


def test_exec_echo(client):
    r = client.post(
        "/exec",
        json={"command": "echo hello", "backend": "process", "timeout_s": 10},
    )
    assert r.status_code == 200
    data = r.json()
    assert data["ok"] is True
    assert data["exit_code"] == 0
    assert "hello" in data["stdout"]
    assert data["audit_seq"] >= 1


def test_exec_timeout(client):
    r = client.post(
        "/exec",
        json={
            "command": 'python -c "import time; time.sleep(10)"',
            "backend": "process",
            "timeout_s": 1,
        },
    )
    assert r.status_code == 200
    data = r.json()
    assert data["timed_out"] is True


def test_python_endpoint(client):
    r = client.post("/python", json={"code": "print(40 + 2)"})
    assert r.status_code == 200
    assert r.json()["stdout"].strip() == "42"


def test_redaction_in_audit(client):
    client.post(
        "/exec",
        json={
            "command": "export API_KEY=supersecret123",
            "backend": "process",
            "timeout_s": 5,
        },
    )
    r = client.get("/audit", params={"limit": 5})
    assert r.status_code == 200
    commands = [e["command"] for e in r.json()["entries"]]
    assert not any("supersecret123" in c for c in commands)
    assert any("REDACTED" in c for c in commands)


def test_audit_verify(client):
    r = client.get("/audit/verify")
    assert r.status_code == 200
    assert r.json()["valid"] is True
