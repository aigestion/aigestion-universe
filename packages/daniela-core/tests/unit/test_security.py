"""Unit tests for SecurityEngine."""
import pytest

from security import SecurityEngine


@pytest.fixture
def sec():
    return SecurityEngine()


def test_encrypt_decrypt_roundtrip(sec):
    blob = sec.encrypt("hello world")
    assert blob["algorithm"] == "AES-256-GCM"
    assert sec.decrypt(blob) == "hello world"


def test_ciphertext_is_randomized(sec):
    a = sec.encrypt("same")
    b = sec.encrypt("same")
    assert a["ciphertext"] != b["ciphertext"]  # fresh nonce each time


def test_challenge_response(sec):
    challenge = sec.challenge()
    secret = "shared-secret"
    # Simulate the phone side: HMAC-SHA256(challenge, secret)
    import hashlib
    import hmac
    response = hmac.new(secret.encode(), challenge.encode(), hashlib.sha256).hexdigest()
    assert sec.verify_response(challenge, response, secret) is True
    assert sec.verify_response(challenge, "wrong", secret) is False


def test_audit_chain(sec):
    e1 = sec.audit("login", "admin")
    e2 = sec.audit("rename", "admin")
    assert e2.seq == e1.seq + 1
    assert e2.digest != e1.digest
    assert sec.verify_chain() is True
    assert len(sec.audit_log()) == 2


def test_redact(sec):
    dirty = "key=supersecret Authorization: Bearer abc123.def456"
    clean = sec.redact(dirty)
    assert "supersecret" not in clean
    assert "abc123" not in clean
    assert "REDACTED" in clean
