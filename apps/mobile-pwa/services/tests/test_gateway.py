"""Tests for the Termux edge gateway (PC<->Pixel pairing)."""
import hashlib
import hmac
import os
import sys

import pytest
from fastapi.testclient import TestClient

sys.path.insert(0, r"C:\Users\Alejandro\aigestion-universe\apps\mobile-pwa")
os.environ["PIXEL_TOKEN"] = "test-secret-token"

from services.termux_api_gateway import create_app


@pytest.fixture(scope="module")
def client():
    app = create_app()
    with TestClient(app) as c:
        yield c


def test_health(client):
    r = client.get("/health")
    assert r.status_code == 200
    assert r.json()["service"] == "termux-gateway"


def test_pairing_roundtrip(client):
    # 1. Phone requests a challenge
    r = client.post("/api/pair/challenge")
    assert r.status_code == 200
    data = r.json()
    assert "challenge" in data
    assert "pair_code" in data
    assert "-" in data["pair_code"]  # XXX-XXX format

    # 2. PC computes HMAC-SHA256(challenge, PIXEL_TOKEN) and responds
    challenge = data["challenge"]
    expected = hmac.new(
        b"test-secret-token", challenge.encode(), hashlib.sha256
    ).hexdigest()
    r = client.post(
        "/api/pair/verify",
        json={"challenge": challenge, "response": expected},
    )
    assert r.status_code == 200
    assert r.json()["paired"] is True
    assert "device_id" in r.json()


def test_pairing_bad_response(client):
    r = client.post("/api/pair/challenge")
    challenge = r.json()["challenge"]
    r = client.post(
        "/api/pair/verify",
        json={"challenge": challenge, "response": "bad"},
    )
    assert r.status_code == 401


def test_pairing_unknown_challenge(client):
    r = client.post(
        "/api/pair/verify",
        json={"challenge": "unknown", "response": "x"},
    )
    assert r.status_code == 404


def test_pair_status(client):
    r = client.get("/api/pair/status")
    assert r.status_code == 200
    assert "active_sessions" in r.json()


def test_device_endpoints(client):
    for path in (
        "/api/device/info",
        "/api/device/battery",
        "/api/device/network",
        "/api/device/sensors",
        "/api/location",
        "/api/storage",
    ):
        r = client.get(path)
        assert r.status_code == 200, path
