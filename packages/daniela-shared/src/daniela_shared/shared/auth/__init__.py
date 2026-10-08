"""Authentication utilities for all aig services."""

import hashlib
import hmac
import json
import time
from dataclasses import dataclass
from typing import Any


@dataclass
class TokenPayload:
    sub: str
    name: str
    tier: str
    exp: float
    iat: float

class JWTHandler:
    """Simple JWT handler without external dependencies."""

    def __init__(self, secret: str):
        self.secret = secret.encode()

    def encode(self, payload: dict[str, Any], expires_in: int = 3600) -> str:
        now = time.time()
        header = json.dumps({"alg": "HS256", "typ": "JWT"}, separators=(",", ":"))
        payload["exp"] = now + expires_in
        payload["iat"] = now
        encoded_header = self._b64url_encode(header.encode())
        encoded_payload = self._b64url_encode(json.dumps(payload, separators=(",", ":")).encode())
        signature = hmac.new(self.secret, f"{encoded_header}.{encoded_payload}".encode(), hashlib.sha256).digest()
        encoded_signature = self._b64url_encode(signature)
        return f"{encoded_header}.{encoded_payload}.{encoded_signature}"

    def decode(self, token: str) -> TokenPayload | None:
        try:
            parts = token.split(".")
            if len(parts) != 3:
                return None
            payload_bytes = self._b64url_decode(parts[1])
            payload = json.loads(payload_bytes)
            if payload.get("exp", 0) < time.time():
                return None
            signature = hmac.new(self.secret, f"{parts[0]}.{parts[1]}".encode(), hashlib.sha256).digest()
            if not hmac.compare_digest(self._b64url_encode(signature), parts[2]):
                return None
            return TokenPayload(**payload)
        except Exception:
            return None

    def _b64url_encode(self, data: bytes) -> str:
        import base64
        return base64.urlsafe_b64encode(data).rstrip(b"=").decode("ascii")

    def _b64url_decode(self, data: str) -> bytes:
        import base64
        padding = 4 - len(data) % 4
        if padding != 4:
            data += "=" * padding
        return base64.urlsafe_b64decode(data)

def create_jwt_handler() -> JWTHandler:
    """Create JWT handler with secret from config."""
    from shared.config import get_jwt_secret
    return JWTHandler(get_jwt_secret())
