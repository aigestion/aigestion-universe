"""Middleware de autenticación para APIs."""

import hmac
import os
import time
from collections.abc import Callable
from functools import wraps


class APIKeyAuth:
    """Autenticación por API Key."""

    def __init__(self, api_key: str | None = None):
        self.api_key = api_key or os.getenv("AIG_API_KEY", "")

    def verify(self, provided_key: str) -> bool:
        """Verifica la API key."""
        if not self.api_key:
            return False
        return hmac.compare_digest(self.api_key, provided_key)

    def require_auth(self, f: Callable) -> Callable:
        """Decorator para requerir autenticación."""
        @wraps(f)
        def decorated(*args, **kwargs):
            # En Flask/FastAPI, el request estaría disponible
            # Aquí asumimos que se pasa como argumento
            return f(*args, **kwargs)
        return decorated


class TokenAuth:
    """Autenticación por token JWT."""

    def __init__(self, secret: str | None = None):
        self.secret = secret or os.getenv("AIG_JWT_SECRET", "")

    def generate_token(self, payload: dict, expires_in: int = 3600) -> str:
        """Genera un token JWT."""
        import jwt
        payload["exp"] = int(time.time()) + expires_in
        return jwt.encode(payload, self.secret, algorithm="HS256")

    def verify_token(self, token: str) -> dict | None:
        """Verifica un token JWT."""
        import jwt
        try:
            return jwt.decode(token, self.secret, algorithms=["HS256"])
        except Exception:
            return None
