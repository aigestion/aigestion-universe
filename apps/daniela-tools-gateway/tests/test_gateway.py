"""Tests for the Daniela Tools Gateway (BYOK/MCP, zero markup)."""
import os
import sys

import pytest
from fastapi.testclient import TestClient

sys.path.insert(0, r"C:\Users\Alejandro\aigestion-universe\apps\daniela-tools-gateway")
os.environ.setdefault("OPENAI_API_KEY", "sk-test-dummy")

from services.tools_gateway import create_app


@pytest.fixture(scope="module")
def client():
    app = create_app()
    with TestClient(app) as c:
        yield c


def test_health_zero_markup(client):
    r = client.get("/health")
    assert r.status_code == 200
    assert r.json()["markup"] is False


def test_providers_status(client):
    r = client.get("/providers")
    assert r.status_code == 200
    providers = {p["provider"]: p["configured"] for p in r.json()["providers"]}
    assert providers["openai"] is True
    assert providers["local"] is True  # always "configured" (no key needed)


def test_set_key(client):
    r = client.post("/keys", json={"provider": "anthropic", "key": "sk-ant-test"})
    assert r.status_code == 200
    assert r.json()["configured"] is True

    r = client.post("/keys", json={"provider": "nope", "key": "x"})
    assert r.status_code == 404


def test_tools_list(client):
    r = client.get("/tools")
    assert r.status_code == 200
    names = [t["name"] for t in r.json()["tools"]]
    assert "web_search" in names
    assert "memory_recall" in names


def test_tool_call(client):
    r = client.post(
        "/tools/call",
        json={"name": "memory_recall", "arguments": {"query": "hola"}},
    )
    assert r.status_code == 200
    assert r.json()["result"]["query"] == "hola"


def test_tool_call_unknown(client):
    r = client.post("/tools/call", json={"name": "nope"})
    assert r.status_code == 404


def test_tool_register(client):
    r = client.post(
        "/tools/register",
        json={
            "name": "my_tool",
            "description": "custom",
            "input_schema": {"type": "object"},
        },
    )
    assert r.status_code == 200
    assert r.json()["registered"] == "my_tool"


def test_mcp_list(client):
    r = client.post(
        "/mcp",
        json={"jsonrpc": "2.0", "id": 1, "method": "tools/list"},
    )
    assert r.status_code == 200
    body = r.json()
    assert body["jsonrpc"] == "2.0"
    assert len(body["result"]["tools"]) >= 5


def test_mcp_call(client):
    r = client.post(
        "/mcp",
        json={
            "jsonrpc": "2.0",
            "id": 2,
            "method": "tools/call",
            "params": {"name": "web_search", "arguments": {"query": "x"}},
        },
    )
    assert r.status_code == 200
    assert "content" in r.json()["result"]


def test_mcp_unknown_method(client):
    r = client.post(
        "/mcp",
        json={"jsonrpc": "2.0", "id": 3, "method": "nope"},
    )
    assert r.status_code == 200
    assert "error" in r.json()


def test_chat_bad_provider(client):
    r = client.post(
        "/chat/completions",
        json={"prompt": "hi", "provider": "nope"},
    )
    assert r.status_code == 400


def test_chat_no_live_backend_returns_503(client):
    # No local LLM running and dummy cloud key -> provider unreachable.
    r = client.post("/chat/completions", json={"prompt": "hi"})
    assert r.status_code in (503, 500, 401)


def test_usage_ledger(client):
    r = client.get("/usage")
    assert r.status_code == 200
    data = r.json()
    assert data["markup_applied"] is False
    assert "total_cost_usd" in data
