"""
Security Engine - Defense in depth for Daniela Core.

- AES-256-GCM authenticated encryption (FIPS 140-3 aligned)
- HMAC-SHA256 challenge-response pairing (PC <-> Pixel)
- Merkle-style audit log (append-only, tamper-evident)
- Input sanitization and secrets redaction
"""
from __future__ import annotations

import hashlib
import hmac
import json
import os
import secrets
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any

from cryptography.hazmat.primitives.ciphers.aead import AESGCM


@dataclass
class AuditEntry:
    seq: int
    timestamp: str
    action: str
    actor: str
    digest: str = ""
    extra: dict[str, Any] = field(default_factory=dict)


class SecurityEngine:
    """Encryption, pairing, audit logging, and redaction."""

    def __init__(self) -> None:
        self._key = AESGCM.generate_key(bit_length=256)
        self._aesgcm = AESGCM(self._key)
        self._audit: list[AuditEntry] = []
        self._seq = 0
        self._chain = hashlib.sha256(b"genesis").hexdigest()

    async def initialize(self) -> None:
        pass

    async def shutdown(self) -> None:
        self._audit.clear()

    def encrypt(self, plaintext: str, *, aad: bytes | None = None) -> dict[str, str]:
        nonce = os.urandom(12)
        ct = self._aesgcm.encrypt(nonce, plaintext.encode(), aad)
        return {
            "nonce": nonce.hex(),
            "ciphertext": ct.hex(),
            "algorithm": "AES-256-GCM",
        }

    def decrypt(self, blob: dict[str, str], *, aad: bytes | None = None) -> str:
        nonce = bytes.fromhex(blob["nonce"])
        ct = bytes.fromhex(blob["ciphertext"])
        return self._aesgcm.decrypt(nonce, ct, aad).decode()

    def challenge(self) -> str:
        return secrets.token_hex(32)

    def verify_response(self, challenge: str, response: str, secret: str) -> bool:
        expected = hmac.new(secret.encode(), challenge.encode(), hashlib.sha256).hexdigest()
        return hmac.compare_digest(expected, response)

    def audit(self, action: str, actor: str = "system", *, extra: dict[str, Any] | None = None) -> AuditEntry:
        self._seq += 1
        extra = extra or {}
        payload = json.dumps({"seq": self._seq, "action": action, "actor": actor, "extra": extra}, sort_keys=True)
        self._chain = hashlib.sha256((self._chain + payload).encode()).hexdigest()
        entry = AuditEntry(
            seq=self._seq,
            timestamp=datetime.utcnow().isoformat(),
            action=action,
            actor=actor,
            digest=self._chain,
            extra=extra,
        )
        self._audit.append(entry)
        return entry

    def audit_log(self) -> list[dict[str, Any]]:
        return [
            {"seq": e.seq, "timestamp": e.timestamp, "action": e.action,
             "actor": e.actor, "digest": e.digest, "extra": e.extra}
            for e in self._audit
        ]

    def verify_chain(self) -> bool:
        chain = hashlib.sha256(b"genesis").hexdigest()
        for e in self._audit:
            payload = json.dumps(
                {"seq": e.seq, "action": e.action, "actor": e.actor, "extra": e.extra},
                sort_keys=True,
            )
            chain = hashlib.sha256((chain + payload).encode()).hexdigest()
        return chain == self._chain

    @staticmethod
    def redact(text: str, secrets: list[str] | None = None) -> str:
        """Redact known secret patterns and bearer tokens."""
        import re
        rules = [
            (r"(?i)\b(api[_-]?key|token|secret|password|key)\b(\s*[:=]\s*)[^\s]+",
             r"\1\2***REDACTED***"),
            (r"Bearer\s+[A-Za-z0-9\-._~+/]+=*",
             "Bearer ***REDACTED***"),
        ]
        out = text
        for pattern, replacement in rules:
            out = re.sub(pattern, replacement, out)
        return out
