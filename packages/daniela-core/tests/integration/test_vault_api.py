"""Integration tests for /api/v1/vault (persistent MemoryVault)."""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest
from fastapi.testclient import TestClient

from daniela_core.api import create_app

if TYPE_CHECKING:
    from pathlib import Path


@pytest.fixture
def client(tmp_path: Path, monkeypatch):
    monkeypatch.setenv("MEMORY_RAG_DB", str(tmp_path / "vault.db"))
    app = create_app()
    with TestClient(app) as c:
        yield c


def test_vault_record_y_recall(client):
    r = client.post(
        "/api/v1/vault/record",
        json={
            "source": "facturas",
            "content": "El proveedor Garcia emitio la factura 4471 en marzo",
        },
    )
    assert r.status_code == 200
    assert r.json()["id"] == 1

    q = client.post("/api/v1/vault/recall", json={"query": "factura Garcia marzo"})
    assert q.status_code == 200
    data = q.json()
    assert data["count"] >= 1
    assert data["memories"][0]["via"] == "directo"


def test_vault_recientes_y_stats(client):
    client.post(
        "/api/v1/vault/record",
        json={"source": "agenda", "content": "Reunion con cliente Miguelito martes manana"},
    )
    rec = client.post("/api/v1/vault/recientes", json={"limite": 10})
    assert rec.status_code == 200
    assert rec.json()["count"] == 1

    st = client.get("/api/v1/vault/stats")
    assert st.status_code == 200
    assert st.json()["docs"] == 1


def test_vault_olvidar(client):
    r = client.post(
        "/api/v1/vault/record",
        json={"source": "t", "content": "Recuerdo temporal para borrar manana"},
    )
    doc_id = r.json()["id"]
    d = client.delete(f"/api/v1/vault/olvidar/{doc_id}")
    assert d.status_code == 200
    assert d.json()["docs"] == 1

    d2 = client.delete("/api/v1/vault/olvidar/9999")
    assert d2.status_code == 404


def test_vault_record_vacio_422(client):
    r = client.post("/api/v1/vault/record", json={"source": "t", "content": "   "})
    assert r.status_code == 422
