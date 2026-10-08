#!/usr/bin/env python3
"""
AIGestion Auth System v1.0
============================
Autenticacion y autorizacion completa:
- OAuth2 (Google, GitHub)
- JWT tokens con refresh
- Roles y permisos (RBAC)
- Rate limits por tier
- Session management

Autor: AIGestion Team
"""

from __future__ import annotations

import hashlib
import hmac
import json
import os
import sqlite3
import sys
import time
import uuid
from datetime import datetime, timedelta
from functools import wraps
from typing import Any

# ── Configuracion ─────────────────────────────────────────────

DB_NAME = "auth.db"
JWT_SECRET = os.getenv("AIGESTION_JWT_SECRET") or os.getenv("JWT_SECRET")
if not JWT_SECRET or JWT_SECRET in {
    "change-me-in-production",
    "aigestion-super-secret-key-change-in-production",
    "aig-super-secret-key-change-in-production",
}:
    raise RuntimeError(
        "AIGESTION_JWT_SECRET/JWT_SECRET no definido (o es el default inseguro): define un secreto de alto entropo."
    )
OAUTH_GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID", "")
OAUTH_GOOGLE_CLIENT_SECRET = os.getenv("GOOGLE_CLIENT_SECRET", "")
OAUTH_GITHUB_CLIENT_ID = os.getenv("GITHUB_CLIENT_ID", "")
OAUTH_GITHUB_CLIENT_SECRET = os.getenv("GITHUB_CLIENT_SECRET", "")

# ── Roles y Tiers ─────────────────────────────────────────────

TIERS = {
    "free": {
        "daily_requests": 100,
        "modules": ["content_factory", "sentiment_dashboard", "email_zero_inbox"],
        "api_access": False,
        "support": "community",
        "price_monthly": 0,
    },
    "pro": {
        "daily_requests": 1000,
        "modules": "all",
        "api_access": True,
        "support": "email",
        "price_monthly": 29,
    },
    "enterprise": {
        "daily_requests": -1,  # ilimitado
        "modules": "all",
        "api_access": True,
        "support": "priority",
        "price_monthly": 99,
        "white_label": True,
        "sla": "99.9%",
    },
}

ROLES = {
    "user": ["read_own", "write_own", "use_modules"],
    "admin": ["read_all", "write_all", "manage_users", "manage_billing", "view_analytics"],
    "superadmin": ["*"],
}


# ── Base de Datos ─────────────────────────────────────────────


def init_auth_db() -> None:

    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()

    # Usuarios
    c.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id TEXT PRIMARY KEY,
            email TEXT UNIQUE NOT NULL,
            name TEXT,
            avatar TEXT,
            provider TEXT DEFAULT 'local',
            provider_id TEXT,
            password_hash TEXT,
            tier TEXT DEFAULT 'free',
            role TEXT DEFAULT 'user',
            status TEXT DEFAULT 'active',
            created_at TEXT,
            last_login TEXT,
            api_key TEXT UNIQUE
        )
    """)

    # Refresh tokens
    c.execute("""
        CREATE TABLE IF NOT EXISTS refresh_tokens (
            token TEXT PRIMARY KEY,
            user_id TEXT NOT NULL,
            expires_at TEXT,
            created_at TEXT,
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
    """)

    # Usage tracking
    c.execute("""
        CREATE TABLE IF NOT EXISTS usage_log (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id TEXT NOT NULL,
            endpoint TEXT,
            module TEXT,
            tokens_used INTEGER DEFAULT 0,
            timestamp TEXT,
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
    """)

    # Sessions
    c.execute("""
        CREATE TABLE IF NOT EXISTS sessions (
            id TEXT PRIMARY KEY,
            user_id TEXT NOT NULL,
            ip_address TEXT,
            user_agent TEXT,
            expires_at TEXT,
            created_at TEXT,
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
    """)

    conn.commit()
    conn.close()


init_auth_db()


# ── Utilidades JWT ────────────────────────────────────────────


def _base64url_encode(data: bytes) -> str:
    import base64

    return base64.urlsafe_b64encode(data).rstrip(b"=").decode("ascii")


def _base64url_decode(data: str) -> bytes:
    import base64

    padding = 4 - len(data) % 4
    if padding != 4:
        data += "=" * padding
    return base64.urlsafe_b64decode(data)


def create_jwt(payload: dict[str, Any], expires_in: int = 3600) -> str:

    header = json.dumps({"alg": "HS256", "typ": "JWT"}, separators=(",", ":"))
    payload["jti"] = str(uuid.uuid4())
    payload["exp"] = time.time() + expires_in
    payload["iat"] = time.time()

    enc_header = _base64url_encode(header.encode())
    enc_payload = _base64url_encode(json.dumps(payload, separators=(",", ":")).encode())
    signature = hmac.new(
        JWT_SECRET.encode(), f"{enc_header}.{enc_payload}".encode(), hashlib.sha256
    ).digest()
    enc_sig = _base64url_encode(signature)
    return f"{enc_header}.{enc_payload}.{enc_sig}"


def verify_jwt(token: str) -> dict[str, Any] | None:

    try:
        parts = token.split(".")
        if len(parts) != 3:
            return None
        payload = json.loads(_base64url_decode(parts[1]))
        if payload.get("exp", 0) < time.time():
            return None
        # Verify signature
        sig = hmac.new(
            JWT_SECRET.encode(), f"{parts[0]}.{parts[1]}".encode(), hashlib.sha256
        ).digest()
        if not hmac.compare_digest(_base64url_encode(sig), parts[2]):
            return None
        return payload
    except Exception:
        return None


def hash_password(password: str) -> str:

    salt = os.urandom(32)
    pwdhash = hashlib.pbkdf2_hmac("sha256", password.encode(), salt, 100000)
    return salt.hex() + ":" + pwdhash.hex()


def verify_password(password: str, stored: str) -> bool:

    try:
        salt_hex, hash_hex = stored.split(":")
        salt = bytes.fromhex(salt_hex)
        pwdhash = hashlib.pbkdf2_hmac("sha256", password.encode(), salt, 100000)
        return hmac.compare_digest(pwdhash.hex(), hash_hex)
    except Exception:
        return False


def generate_api_key() -> str:

    return "ag_" + hashlib.sha256(os.urandom(32)).hexdigest()[:24]


def require_auth(f):
    """Flask decorator that enforces JWT authentication on API endpoints.

    Reads the Authorization header (Bearer <token>), verifies the JWT,
    and injects the decoded payload into request.auth_user.
    Returns 401 if missing/invalid.
    """

    @wraps(f)
    def decorated(*args, **kwargs):

        from flask import jsonify, request

        auth_header = request.headers.get("Authorization", "")
        if not auth_header.startswith("Bearer "):
            return jsonify(
                {"error": "Missing or invalid Authorization header", "status": "unauthorized"}
            ), 401
        token = auth_header[7:]
        payload = verify_jwt(token)
        if not payload:
            return jsonify({"error": "Invalid or expired token", "status": "unauthorized"}), 401
        # Inject user info into request for downstream use
        from flask import g

        g.auth_user = payload
        return f(*args, **kwargs)

    return decorated


# ── AuthManager ───────────────────────────────────────────────


class AuthManager:
    """Gestiona autenticacion, autorizacion y sesiones."""

    def __init__(self):
        self.db = DB_NAME

    def _db(self) -> sqlite3.Connection:
        return sqlite3.connect(self.db)

    # ── Registro / Login ──────────────────────────────────────

    def register_local(self, email: str, password: str, name: str = "") -> dict[str, Any]:
        """Registro con email/password local."""
        conn = self._db()
        c = conn.cursor()

        # Verificar si existe
        c.execute("SELECT id FROM users WHERE email = ?", (email,))
        if c.fetchone():
            conn.close()
            return {"success": False, "error": "Email ya registrado"}

        user_id = str(uuid.uuid4())
        now = datetime.now().isoformat()
        api_key = generate_api_key()

        c.execute(
            """
            INSERT INTO users (id, email, name, provider, password_hash, tier, role, status, created_at, api_key)
            VALUES (?, ?, ?, 'local', ?, 'free', 'user', 'active', ?, ?)
        """,
            (user_id, email, name, hash_password(password), now, api_key),
        )
        conn.commit()
        conn.close()

        return {
            "success": True,
            "user_id": user_id,
            "email": email,
            "tier": "free",
            "api_key": api_key,
        }

    def login_local(self, email: str, password: str) -> dict[str, Any]:
        """Login con email/password."""
        conn = self._db()
        c = conn.cursor()
        c.execute(
            "SELECT id, password_hash, name, tier, role, status, api_key FROM users WHERE email = ?",
            (email,),
        )
        row = c.fetchone()
        conn.close()

        if not row:
            return {"success": False, "error": "Credenciales invalidas"}

        user_id, pwd_hash, name, tier, role, status, api_key = row
        if status != "active":
            return {"success": False, "error": "Cuenta suspendida"}
        if not verify_password(password, pwd_hash):
            return {"success": False, "error": "Credenciales invalidas"}

        # Crear tokens
        access_token = create_jwt(
            {"sub": user_id, "email": email, "tier": tier, "role": role}, expires_in=3600
        )
        refresh_token = self._create_refresh_token(user_id)

        self._update_last_login(user_id)

        return {
            "success": True,
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_type": "Bearer",
            "expires_in": 3600,
            "user": {
                "id": user_id,
                "email": email,
                "name": name,
                "tier": tier,
                "role": role,
                "api_key": api_key,
            },
        }

    def oauth_login(
        self, provider: str, provider_id: str, email: str, name: str = "", avatar: str = ""
    ) -> dict[str, Any]:
        """Login/registro via OAuth (Google/GitHub)."""
        conn = self._db()
        c = conn.cursor()

        # Buscar por provider_id
        c.execute(
            "SELECT id, tier, role, status, api_key FROM users WHERE provider = ? AND provider_id = ?",
            (provider, provider_id),
        )
        row = c.fetchone()

        if row:
            user_id, tier, role, status, api_key = row
            if status != "active":
                conn.close()
                return {"success": False, "error": "Cuenta suspendida"}
            # Actualizar info
            c.execute(
                "UPDATE users SET email = ?, name = ?, avatar = ?, last_login = ? WHERE id = ?",
                (email, name, avatar, datetime.now().isoformat(), user_id),
            )
        else:
            # Crear nuevo usuario
            user_id = str(uuid.uuid4())
            tier = "free"
            role = "user"
            api_key = generate_api_key()
            now = datetime.now().isoformat()
            c.execute(
                """
                INSERT INTO users (id, email, name, avatar, provider, provider_id, tier, role, status, created_at, last_login, api_key)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, 'active', ?, ?, ?)
            """,
                (
                    user_id,
                    email,
                    name,
                    avatar,
                    provider,
                    provider_id,
                    tier,
                    role,
                    now,
                    now,
                    api_key,
                ),
            )

        conn.commit()
        conn.close()

        access_token = create_jwt(
            {"sub": user_id, "email": email, "tier": tier, "role": role}, expires_in=3600
        )
        refresh_token = self._create_refresh_token(user_id)

        return {
            "success": True,
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_type": "Bearer",
            "expires_in": 3600,
            "user": {
                "id": user_id,
                "email": email,
                "name": name,
                "tier": tier,
                "role": role,
                "api_key": api_key,
            },
        }

    def refresh_access_token(self, refresh_token: str) -> dict[str, Any]:
        """Renueva access token con refresh token."""
        conn = self._db()
        c = conn.cursor()
        c.execute(
            "SELECT user_id, expires_at FROM refresh_tokens WHERE token = ?", (refresh_token,)
        )
        row = c.fetchone()

        if not row:
            conn.close()
            return {"success": False, "error": "Refresh token invalido"}

        user_id, expires_at = row
        if datetime.fromisoformat(expires_at) < datetime.now():
            c.execute("DELETE FROM refresh_tokens WHERE token = ?", (refresh_token,))
            conn.commit()
            conn.close()
            return {"success": False, "error": "Refresh token expirado"}

        # Obtener info del usuario
        c.execute("SELECT email, tier, role FROM users WHERE id = ?", (user_id,))
        user_row = c.fetchone()
        conn.close()

        if not user_row:
            return {"success": False, "error": "Usuario no encontrado"}

        email, tier, role = user_row
        new_access = create_jwt(
            {"sub": user_id, "email": email, "tier": tier, "role": role}, expires_in=3600
        )

        return {
            "success": True,
            "access_token": new_access,
            "token_type": "Bearer",
            "expires_in": 3600,
        }

    def _create_refresh_token(self, user_id: str) -> str:
        token = str(uuid.uuid4())
        expires = (datetime.now() + timedelta(days=30)).isoformat()
        conn = self._db()
        c = conn.cursor()
        c.execute(
            "INSERT INTO refresh_tokens (token, user_id, expires_at, created_at) VALUES (?, ?, ?, ?)",
            (token, user_id, expires, datetime.now().isoformat()),
        )
        conn.commit()
        conn.close()
        return token

    def _update_last_login(self, user_id: str) -> None:
        conn = self._db()
        c = conn.cursor()
        c.execute(
            "UPDATE users SET last_login = ? WHERE id = ?", (datetime.now().isoformat(), user_id)
        )
        conn.commit()
        conn.close()

    # ── Autorizacion ──────────────────────────────────────────

    def get_user_from_token(self, token: str) -> dict[str, Any] | None:
        """Obtiene usuario desde JWT."""
        payload = verify_jwt(token)
        if not payload:
            return None
        user_id = payload.get("sub")
        conn = self._db()
        c = conn.cursor()
        c.execute(
            "SELECT id, email, name, tier, role, status, api_key FROM users WHERE id = ?",
            (user_id,),
        )
        row = c.fetchone()
        conn.close()
        if not row:
            return None
        return {
            "id": row[0],
            "email": row[1],
            "name": row[2],
            "tier": row[3],
            "role": row[4],
            "status": row[5],
            "api_key": row[6],
        }

    def get_user_from_api_key(self, api_key: str) -> dict[str, Any] | None:
        """Obtiene usuario desde API key."""
        conn = self._db()
        c = conn.cursor()
        c.execute(
            "SELECT id, email, name, tier, role, status FROM users WHERE api_key = ?", (api_key,)
        )
        row = c.fetchone()
        conn.close()
        if not row:
            return None
        return {
            "id": row[0],
            "email": row[1],
            "name": row[2],
            "tier": row[3],
            "role": row[4],
            "status": row[5],
        }

    def check_permission(self, user: dict[str, Any], permission: str) -> bool:
        """Verifica si el usuario tiene un permiso."""
        role = user.get("role", "user")
        perms = ROLES.get(role, [])
        if "*" in perms:
            return True
        return permission in perms

    def can_use_module(self, user: dict[str, Any], module_name: str) -> bool:
        """Verifica si el usuario puede usar un modulo segun su tier."""
        tier_name = user.get("tier", "free")
        tier = TIERS.get(tier_name, TIERS["free"])
        allowed = tier.get("modules", [])
        if allowed == "all":
            return True
        return module_name in allowed

    def get_tier_limits(self, user: dict[str, Any]) -> dict[str, Any]:
        """Obtiene limites del tier del usuario."""
        tier_name = user.get("tier", "free")
        return TIERS.get(tier_name, TIERS["free"])

    # ── Usage Tracking ────────────────────────────────────────

    def log_usage(self, user_id: str, endpoint: str, module: str = "", tokens: int = 0) -> None:
        """Registra uso de la API."""
        conn = self._db()
        c = conn.cursor()
        c.execute(
            """
            INSERT INTO usage_log (user_id, endpoint, module, tokens_used, timestamp)
            VALUES (?, ?, ?, ?, ?)
        """,
            (user_id, endpoint, module, tokens, datetime.now().isoformat()),
        )
        conn.commit()
        conn.close()

    def get_daily_usage(self, user_id: str) -> int:
        """Obtiene requests de hoy."""
        today = datetime.now().strftime("%Y-%m-%d")
        conn = self._db()
        c = conn.cursor()
        c.execute(
            """
            SELECT COUNT(*) FROM usage_log
            WHERE user_id = ? AND timestamp LIKE ?
        """,
            (user_id, f"{today}%"),
        )
        count = c.fetchone()[0]
        conn.close()
        return count

    def check_rate_limit(
        self, user_id: str, tier_name: str = "free"
    ) -> tuple[bool, dict[str, Any]]:
        """Verifica si el usuario ha excedido su limite diario."""
        tier = TIERS.get(tier_name, TIERS["free"])
        daily_limit = tier["daily_requests"]
        if daily_limit == -1:
            return True, {"limit": -1, "used": 0, "remaining": "unlimited"}

        used = self.get_daily_usage(user_id)
        remaining = max(0, daily_limit - used)
        return used < daily_limit, {"limit": daily_limit, "used": used, "remaining": remaining}

    # ── Administracion ────────────────────────────────────────

    def list_users(self, limit: int = 100) -> list[dict[str, Any]]:
        """Lista usuarios (admin only)."""
        conn = self._db()
        c = conn.cursor()
        c.execute(
            """
            SELECT id, email, name, provider, tier, role, status, created_at, last_login
            FROM users ORDER BY created_at DESC LIMIT ?
        """,
            (limit,),
        )
        rows = c.fetchall()
        conn.close()
        return [
            {
                "id": r[0],
                "email": r[1],
                "name": r[2],
                "provider": r[3],
                "tier": r[4],
                "role": r[5],
                "status": r[6],
                "created_at": r[7],
                "last_login": r[8],
            }
            for r in rows
        ]

    def update_user_tier(self, user_id: str, new_tier: str) -> bool:
        """Actualiza tier de usuario."""
        if new_tier not in TIERS:
            return False
        conn = self._db()
        c = conn.cursor()
        c.execute("UPDATE users SET tier = ? WHERE id = ?", (new_tier, user_id))
        conn.commit()
        conn.close()
        return True

    def suspend_user(self, user_id: str) -> bool:
        """Suspende un usuario."""
        conn = self._db()
        c = conn.cursor()
        c.execute("UPDATE users SET status = 'suspended' WHERE id = ?", (user_id,))
        conn.commit()
        conn.close()
        return True

    def get_user_stats(self, user_id: str) -> dict[str, Any]:
        """Estadisticas de un usuario."""
        conn = self._db()
        c = conn.cursor()

        # Total requests
        c.execute("SELECT COUNT(*) FROM usage_log WHERE user_id = ?", (user_id,))
        total = c.fetchone()[0]

        # Requests hoy
        today = datetime.now().strftime("%Y-%m-%d")
        c.execute(
            "SELECT COUNT(*) FROM usage_log WHERE user_id = ? AND timestamp LIKE ?",
            (user_id, f"{today}%"),
        )
        today_count = c.fetchone()[0]

        # Modulos mas usados
        c.execute(
            """
            SELECT module, COUNT(*) as count FROM usage_log
            WHERE user_id = ? GROUP BY module ORDER BY count DESC LIMIT 5
        """,
            (user_id,),
        )
        modules = [{"module": r[0] or "unknown", "count": r[1]} for r in c.fetchall()]

        conn.close()
        return {"total_requests": total, "today_requests": today_count, "top_modules": modules}


# ═══════════════════════════════════════════════════════════════
# CLI
# ═══════════════════════════════════════════════════════════════


def main() -> int:
    import argparse

    parser = argparse.ArgumentParser(description="AIGestion Auth System")
    parser.add_argument(
        "--register", nargs=2, metavar=("EMAIL", "PASSWORD"), help="Registrar usuario"
    )
    parser.add_argument("--login", nargs=2, metavar=("EMAIL", "PASSWORD"), help="Login usuario")
    parser.add_argument("--list-users", action="store_true", help="Listar usuarios")
    parser.add_argument("--stats", metavar="USER_ID", help="Estadisticas de usuario")
    parser.add_argument("--set-tier", nargs=2, metavar=("USER_ID", "TIER"), help="Cambiar tier")

    args = parser.parse_args()

    auth = AuthManager()

    if args.register:
        result = auth.register_local(args.register[0], args.register[1])
        print(json.dumps(result, indent=2, ensure_ascii=False))

    if args.login:
        result = auth.login_local(args.login[0], args.login[1])
        print(json.dumps(result, indent=2, ensure_ascii=False))

    if args.list_users:
        users = auth.list_users()
        print(json.dumps(users, indent=2, ensure_ascii=False))

    if args.stats:
        stats = auth.get_user_stats(args.stats)
        print(json.dumps(stats, indent=2, ensure_ascii=False))

    if args.set_tier:
        ok = auth.update_user_tier(args.set_tier[0], args.set_tier[1])
        print(f"Tier actualizado: {ok}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
