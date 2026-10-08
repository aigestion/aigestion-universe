"""Advanced Authentication Engine - Ideas 1-10."""

from __future__ import annotations

import base64
import hashlib
import hmac
import math
import secrets
import time
from collections import defaultdict
from datetime import UTC, datetime
from typing import Any
from urllib.parse import urlencode

# ---------------------------------------------------------------------------
# 1. OAuth2 Provider (Authorization Code Flow)
# ---------------------------------------------------------------------------

class OAuth2Provider:
    """Full OAuth2 authorization code flow with PKCE support."""

    def __init__(self, client_id: str, client_secret: str, redirect_uri: str):
        self.client_id = client_id
        self.client_secret = client_secret
        self.redirect_uri = redirect_uri
        self._authorization_codes: dict[str, dict[str, Any]] = {}
        self._tokens: dict[str, dict[str, Any]] = {}
        self._refresh_tokens: dict[str, dict[str, Any]] = {}

    def create_authorization_url(
        self,
        state: str | None = None,
        code_challenge: str | None = None,
        code_challenge_method: str = "S256",
        scope: str = "openid profile email",
    ) -> tuple[str, str]:
        state = state or secrets.token_urlsafe(32)
        params: dict[str, str] = {
            "response_type": "code",
            "client_id": self.client_id,
            "redirect_uri": self.redirect_uri,
            "state": state,
            "scope": scope,
        }
        if code_challenge:
            params["code_challenge"] = code_challenge
            params["code_challenge_method"] = code_challenge_method
        return f"/authorize?{urlencode(params)}", state

    def generate_authorization_code(
        self,
        user_id: str,
        scope: str = "openid profile email",
        code_challenge: str | None = None,
    ) -> str:
        code = secrets.token_urlsafe(48)
        self._authorization_codes[code] = {
            "user_id": user_id,
            "scope": scope,
            "code_challenge": code_challenge,
            "created_at": time.time(),
            "ttl": 600,
            "used": False,
        }
        return code

    def exchange_code_for_token(
        self,
        code: str,
        code_verifier: str | None = None,
    ) -> dict[str, Any] | None:
        entry = self._authorization_codes.get(code)
        if not entry or entry["used"]:
            return None
        if time.time() - entry["created_at"] > entry["ttl"]:
            return None
        if entry["code_challenge"] and code_verifier:
            expected = base64.urlsafe_b64encode(
                hashlib.sha256(code_verifier.encode()).digest()
            ).rstrip(b"=").decode()
            if not hmac.compare_digest(expected, entry["code_challenge"]):
                return None
        entry["used"] = True
        access_token = secrets.token_urlsafe(64)
        refresh_token = secrets.token_urlsafe(64)
        now = time.time()
        self._tokens[access_token] = {
            "user_id": entry["user_id"],
            "scope": entry["scope"],
            "created_at": now,
            "expires_at": now + 3600,
        }
        self._refresh_tokens[refresh_token] = {
            "user_id": entry["user_id"],
            "scope": entry["scope"],
            "created_at": now,
            "expires_at": now + 86400 * 30,
        }
        return {
            "access_token": access_token,
            "token_type": "Bearer",
            "expires_in": 3600,
            "refresh_token": refresh_token,
            "scope": entry["scope"],
        }

    def refresh_access_token(self, refresh_token: str) -> dict[str, Any] | None:
        entry = self._refresh_tokens.get(refresh_token)
        if not entry or time.time() > entry["expires_at"]:
            return None
        access_token = secrets.token_urlsafe(64)
        now = time.time()
        self._tokens[access_token] = {
            "user_id": entry["user_id"],
            "scope": entry["scope"],
            "created_at": now,
            "expires_at": now + 3600,
        }
        return {
            "access_token": access_token,
            "token_type": "Bearer",
            "expires_in": 3600,
            "scope": entry["scope"],
        }

    def validate_token(self, access_token: str) -> dict[str, Any] | None:
        entry = self._tokens.get(access_token)
        if not entry or time.time() > entry["expires_at"]:
            return None
        return {"user_id": entry["user_id"], "scope": entry["scope"]}


# ---------------------------------------------------------------------------
# 2. SAML SSO Integration
# ---------------------------------------------------------------------------

class SAMLSSO:
    """SAML 2.0 SSO integration stub."""

    def __init__(self, entity_id: str, sso_url: str, certificate: str):
        self.entity_id = entity_id
        self.sso_url = sso_url
        self.certificate = certificate
        self._assertions: dict[str, dict[str, Any]] = {}

    def create_authn_request(self, relay_state: str = "") -> dict[str, str]:
        request_id = f"_id{secrets.token_hex(16)}"
        issue_instant = datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")
        xml = (
            f'<samlp:AuthnRequest xmlns:samlp="urn:oasis:names:tc:SAML:2.0:protocol"'
            f' ID="{request_id}" IssueInstant="{issue_instant}"'
            f' AssertionConsumerServiceURL="{self.sso_url}"'
            f' ProtocolBinding="urn:oasis:names:tc:SAML:2.0:bindings:HTTP-POST">'
            f"<saml:Issuer xmlns:saml='urn:oasis:names:tc:SAML:2.0:assertion'>"
            f"{self.entity_id}</saml:Issuer>"
            f"</samlp:AuthnRequest>"
        )
        encoded = base64.b64encode(xml.encode()).decode()
        return {"SAMLRequest": encoded, "RelayState": relay_state}

    def validate_assertion(
        self, saml_response_b64: str, expected_audience: str
    ) -> dict[str, Any] | None:
        try:
            xml = base64.b64decode(saml_response_b64).decode()
        except Exception:
            return None
        assertion_id = f"_assertion{secrets.token_hex(8)}"
        self._assertions[assertion_id] = {
            "raw": xml,
            "validated_at": time.time(),
            "audience": expected_audience,
        }
        return {"valid": True, "assertion_id": assertion_id, "audience": expected_audience}

    def get_metadata(self) -> str:
        return (
            f'<EntityDescriptor entityID="{self.entity_id}">'
            f'<SPSSODescriptor>'
            f"<AssertionConsumerService Binding='urn:oasis:names:tc:SAML:2.0:bindings:HTTP-POST' "
            f"Location='{self.sso_url}' index='1'/>"
            f"</SPSSODescriptor>"
            f"</EntityDescriptor>"
        )


# ---------------------------------------------------------------------------
# 3. Multi-Factor Authentication (TOTP)
# ---------------------------------------------------------------------------

class TOTPAuth:
    """Time-based One-Time Password authentication."""

    def __init__(self, secret_key: str | None = None):
        # 2026-10-04 (S5): antes la semilla por defecto era la del RFC
        # (`JBSWY3DPEHPK3PXP`, publica) -> cualquiera calculaba el TOTP.
        # Ahora: sin semilla no hay TOTP; si no se provee, se genera una
        # aleatoria por instancia (20 bytes -> b32).
        if secret_key is None:
            secret_key = base64.b32encode(secrets.token_bytes(20)).decode("ascii")
        self.secret_key = secret_key
        self.digits = 6
        self.period = 30
        self._backup_codes: dict[str, list[str]] = {}

    def _hmac_hotp(self, key: bytes, counter: int) -> bytes:
        counter_bytes = counter.to_bytes(8, "big")
        return hmac.new(key, counter_bytes, hashlib.sha1).digest()

    def generate_totp(self, time_step: int | None = None) -> str:
        if time_step is None:
            time_step = int(time.time()) // self.period
        key = base64.b32decode(self.secret_key, casefold=True)
        digest = self._hmac_hotp(key, time_step)
        offset = digest[-1] & 0x0F
        code_int = (
            (digest[offset] & 0x7F) << 24
            | digest[offset + 1] << 16
            | digest[offset + 2] << 8
            | digest[offset + 3]
        )
        return str(code_int % (10 ** self.digits)).zfill(self.digits)

    def verify_totp(self, code: str, window: int = 1) -> bool:
        current_step = int(time.time()) // self.period
        for offset in range(-window, window + 1):
            if self.generate_totp(current_step + offset) == code:
                return True
        return False

    def generate_backup_codes(self, user_id: str, count: int = 10) -> list[str]:
        codes = [secrets.token_hex(4) for _ in range(count)]
        self._backup_codes[user_id] = [self._hash_code(c) for c in codes]
        return codes

    def verify_backup_code(self, user_id: str, code: str) -> bool:
        hashed = self._hash_code(code)
        codes = self._backup_codes.get(user_id, [])
        if hashed in codes:
            codes.remove(hashed)
            return True
        return False

    def _hash_code(self, code: str) -> str:
        return hashlib.sha256(code.encode()).hexdigest()

    def get_provisioning_uri(self, account_name: str, issuer: str = "SecureEngine") -> str:
        return (
            f"otpauth://totp/{issuer}:{account_name}"
            f"?secret={self.secret_key}&issuer={issuer}"
            f"&digits={self.digits}&period={self.period}"
        )


# ---------------------------------------------------------------------------
# 4. Passwordless Authentication (Magic Links)
# ---------------------------------------------------------------------------

class MagicLinkAuth:
    """Passwordless magic link authentication."""

    def __init__(self, base_url: str = "https://auth.example.com"):
        self.base_url = base_url
        self._links: dict[str, dict[str, Any]] = {}
        self._consumed: set[str] = set()

    def generate_magic_link(self, user_id: str, ttl_seconds: int = 900) -> str:
        token = secrets.token_urlsafe(48)
        self._links[token] = {
            "user_id": user_id,
            "created_at": time.time(),
            "ttl": ttl_seconds,
        }
        return f"{self.base_url}/magic-login?token={token}"

    def validate_magic_link(self, token: str) -> dict[str, Any] | None:
        if token in self._consumed:
            return None
        entry = self._links.get(token)
        if not entry:
            return None
        if time.time() - entry["created_at"] > entry["ttl"]:
            return None
        self._consumed.add(token)
        return {"user_id": entry["user_id"], "authenticated": True}

    def revoke_all_links(self, user_id: str) -> int:
        count = 0
        for token, entry in list(self._links.items()):
            if entry["user_id"] == user_id:
                del self._links[token]
                count += 1
        return count

    def get_pending_links(self, user_id: str) -> list[dict[str, Any]]:
        now = time.time()
        return [
            {"created_at": e["created_at"], "expires_at": e["created_at"] + e["ttl"]}
            for e in self._links.values()
            if e["user_id"] == user_id and now - e["created_at"] <= e["ttl"]
        ]


# ---------------------------------------------------------------------------
# 5. Biometric Authentication Stub
# ---------------------------------------------------------------------------

class BiometricAuth:
    """Biometric authentication stub (fingerprint/face ID)."""

    def __init__(self):
        self._enrolled: dict[str, dict[str, Any]] = {}
        self._auth_history: list[dict[str, Any]] = []

    def enroll(self, user_id: str, biometric_type: str, template_data: str) -> dict[str, Any]:
        template_id = secrets.token_hex(16)
        self._enrolled[template_id] = {
            "user_id": user_id,
            "type": biometric_type,
            "template_hash": hashlib.sha256(template_data.encode()).hexdigest(),
            "enrolled_at": time.time(),
            "active": True,
        }
        return {"template_id": template_id, "status": "enrolled"}

    def authenticate(self, template_id: str, sample_data: str, threshold: float = 0.85) -> dict[str, Any]:
        entry = self._enrolled.get(template_id)
        if not entry or not entry["active"]:
            return {"authenticated": False, "reason": "template_not_found"}
        sample_hash = hashlib.sha256(sample_data.encode()).hexdigest()
        score = 1.0 if hmac.compare_digest(sample_hash, entry["template_hash"]) else 0.0
        authenticated = score >= threshold
        self._auth_history.append({
            "template_id": template_id,
            "user_id": entry["user_id"],
            "score": score,
            "authenticated": authenticated,
            "timestamp": time.time(),
        })
        return {"authenticated": authenticated, "score": score, "threshold": threshold}

    def revoke_template(self, template_id: str) -> bool:
        entry = self._enrolled.get(template_id)
        if entry:
            entry["active"] = False
            return True
        return False

    def get_user_templates(self, user_id: str) -> list[dict[str, Any]]:
        return [
            {"template_id": tid, "type": e["type"], "active": e["active"]}
            for tid, e in self._enrolled.items()
            if e["user_id"] == user_id
        ]


# ---------------------------------------------------------------------------
# 6. Session Management (Concurrent Sessions)
# ---------------------------------------------------------------------------

class SessionManager:
    """Session management with concurrent session support."""

    def __init__(self, max_sessions_per_user: int = 5, session_ttl: int = 3600):
        self.max_sessions = max_sessions_per_user
        self.session_ttl = session_ttl
        self._sessions: dict[str, dict[str, Any]] = {}
        self._user_sessions: dict[str, list[str]] = defaultdict(list)

    def create_session(
        self,
        user_id: str,
        ip_address: str,
        user_agent: str,
    ) -> dict[str, Any]:
        session_id = secrets.token_urlsafe(48)
        now = time.time()
        user_sessions = self._user_sessions[user_id]
        while len(user_sessions) >= self.max_sessions:
            oldest = user_sessions.pop(0)
            self._sessions.pop(oldest, None)
        self._sessions[session_id] = {
            "user_id": user_id,
            "ip_address": ip_address,
            "user_agent": user_agent,
            "created_at": now,
            "last_activity": now,
            "expires_at": now + self.session_ttl,
            "active": True,
        }
        user_sessions.append(session_id)
        return {"session_id": session_id, "expires_at": now + self.session_ttl}

    def validate_session(self, session_id: str) -> dict[str, Any] | None:
        entry = self._sessions.get(session_id)
        if not entry or not entry["active"]:
            return None
        now = time.time()
        if now > entry["expires_at"]:
            self.invalidate_session(session_id)
            return None
        entry["last_activity"] = now
        entry["expires_at"] = now + self.session_ttl
        return {"user_id": entry["user_id"], "ip_address": entry["ip_address"]}

    def invalidate_session(self, session_id: str) -> bool:
        entry = self._sessions.pop(session_id, None)
        if entry:
            user_sessions = self._user_sessions.get(entry["user_id"], [])
            if session_id in user_sessions:
                user_sessions.remove(session_id)
            return True
        return False

    def invalidate_all_user_sessions(self, user_id: str) -> int:
        session_ids = self._user_sessions.pop(user_id, [])
        count = len(session_ids)
        for sid in session_ids:
            self._sessions.pop(sid, None)
        return count

    def get_active_sessions(self, user_id: str) -> list[dict[str, Any]]:
        now = time.time()
        return [
            {
                "session_id": sid,
                "ip_address": self._sessions[sid]["ip_address"],
                "user_agent": self._sessions[sid]["user_agent"],
                "created_at": self._sessions[sid]["created_at"],
                "last_activity": self._sessions[sid]["last_activity"],
            }
            for sid in self._user_sessions.get(user_id, [])
            if sid in self._sessions and now <= self._sessions[sid]["expires_at"]
        ]


# ---------------------------------------------------------------------------
# 7. Device Fingerprinting
# ---------------------------------------------------------------------------

class DeviceFingerprint:
    """Device fingerprinting for fraud detection."""

    def __init__(self):
        self._fingerprints: dict[str, dict[str, Any]] = {}
        self._known_devices: dict[str, set[str]] = defaultdict(set)

    def generate_fingerprint(self, attributes: dict[str, str]) -> str:
        sorted_attrs = "|".join(f"{k}={v}" for k, v in sorted(attributes.items()))
        fp_hash = hashlib.sha256(sorted_attrs.encode()).hexdigest()[:32]
        self._fingerprints[fp_hash] = {
            "attributes": attributes,
            "created_at": time.time(),
            "seen_count": 1,
        }
        return fp_hash

    def register_device(self, user_id: str, fingerprint: str) -> bool:
        is_new = fingerprint not in self._known_devices[user_id]
        self._known_devices[user_id].add(fingerprint)
        return is_new

    def check_device(self, user_id: str, fingerprint: str) -> dict[str, Any]:
        known = fingerprint in self._known_devices.get(user_id, set())
        return {
            "known_device": known,
            "fingerprint": fingerprint,
            "first_seen": self._fingerprints.get(fingerprint, {}).get("created_at"),
        }

    def get_risk_score(self, user_id: str, fingerprint: str, ip_address: str) -> float:
        score = 0.0
        if fingerprint not in self._known_devices.get(user_id, set()):
            score += 0.4
        fp_data = self._fingerprints.get(fingerprint, {})
        if fp_data and time.time() - fp_data.get("created_at", 0) < 3600:
            score += 0.2
        return min(score, 1.0)


# ---------------------------------------------------------------------------
# 8. IP Reputation Checking
# ---------------------------------------------------------------------------

class IPReputationChecker:
    """IP reputation and threat intelligence checking."""

    def __init__(self):
        self._threat_db: dict[str, dict[str, Any]] = {
            "192.168.1.100": {"threat_level": "high", "category": "botnet", "score": 0.9},
            "10.0.0.1": {"threat_level": "low", "category": "internal", "score": 0.1},
        }
        self._whitelist: set[str] = {"127.0.0.1", "::1"}
        self._blacklist: set[str] = set()

    def check_reputation(self, ip_address: str) -> dict[str, Any]:
        if ip_address in self._whitelist:
            return {"ip": ip_address, "threat_level": "none", "score": 0.0, "whitelisted": True}
        if ip_address in self._blacklist:
            return {"ip": ip_address, "threat_level": "critical", "score": 1.0, "blacklisted": True}
        threat = self._threat_db.get(ip_address)
        if threat:
            return {"ip": ip_address, **threat, "whitelisted": False, "blacklisted": False}
        return {"ip": ip_address, "threat_level": "unknown", "score": 0.5, "whitelisted": False, "blacklisted": False}

    def add_to_blacklist(self, ip_address: str, reason: str = "") -> None:
        self._blacklist.add(ip_address)

    def add_to_whitelist(self, ip_address: str) -> None:
        self._whitelist.add(ip_address)

    def get_threat_summary(self) -> dict[str, int]:
        return {
            "blacklisted": len(self._blacklist),
            "whitelisted": len(self._whitelist),
            "known_threats": len(self._threat_db),
        }


# ---------------------------------------------------------------------------
# 9. Geo-Velocity Check (Login Location)
# ---------------------------------------------------------------------------

class GeoVelocityChecker:
    """Detect impossible travel (login from distant locations in short time)."""

    def __init__(self, max_velocity_kmh: float = 900.0):
        self.max_velocity = max_velocity_kmh
        self._login_history: dict[str, list[dict[str, Any]]] = defaultdict(list)

    @staticmethod
    def haversine_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
        R = 6371.0
        lat1_r, lat2_r = math.radians(lat1), math.radians(lat2)
        dlat = math.radians(lat2 - lat1)
        dlon = math.radians(lon2 - lon1)
        a = math.sin(dlat / 2) ** 2 + math.cos(lat1_r) * math.cos(lat2_r) * math.sin(dlon / 2) ** 2
        return R * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))

    def record_login(self, user_id: str, latitude: float, longitude: float) -> dict[str, Any]:
        now = time.time()
        history = self._login_history[user_id]
        is_anomaly = False
        velocity = 0.0
        if history:
            last = history[-1]
            distance_km = self.haversine_distance(
                last["latitude"], last["longitude"], latitude, longitude
            )
            time_diff_hours = (now - last["timestamp"]) / 3600
            if time_diff_hours > 0:
                velocity = distance_km / time_diff_hours
                is_anomaly = velocity > self.max_velocity
            elif distance_km > 0:
                velocity = float('inf')
                is_anomaly = True
        history.append({"latitude": latitude, "longitude": longitude, "timestamp": now})
        if len(history) > 100:
            self._login_history[user_id] = history[-100:]
        return {
            "user_id": user_id,
            "velocity_kmh": round(velocity, 2),
            "is_anomaly": is_anomaly,
            "max_allowed_kmh": self.max_velocity,
        }

    def get_login_history(self, user_id: str) -> list[dict[str, Any]]:
        return list(self._login_history.get(user_id, []))


# ---------------------------------------------------------------------------
# 10. Account Lockout with Progressive Delays
# ---------------------------------------------------------------------------

class AccountLockout:
    """Account lockout with progressive delays after failed attempts."""

    def __init__(
        self,
        max_attempts: int = 5,
        base_delay: float = 60.0,
        max_delay: float = 3600.0,
        lockout_duration: float = 1800.0,
    ):
        self.max_attempts = max_attempts
        self.base_delay = base_delay
        self.max_delay = max_delay
        self.lockout_duration = lockout_duration
        self._attempts: dict[str, list[float]] = defaultdict(list)
        self._lockouts: dict[str, float] = {}

    def _progressive_delay(self, fail_count: int) -> float:
        delay = self.base_delay * (2 ** (fail_count - self.max_attempts))
        return min(delay, self.max_delay)

    def record_attempt(self, user_id: str, success: bool) -> dict[str, Any]:
        now = time.time()
        if user_id in self._lockouts:
            lockout_end = self._lockouts[user_id]
            if now < lockout_end:
                remaining = lockout_end - now
                return {
                    "allowed": False,
                    "reason": "locked_out",
                    "retry_after_seconds": round(remaining, 1),
                    "fail_count": len(self._attempts[user_id]),
                }
            else:
                del self._lockouts[user_id]
                self._attempts[user_id] = []
        if success:
            self._attempts[user_id] = []
            return {"allowed": True, "reason": "success", "fail_count": 0}
        self._attempts[user_id].append(now)
        recent = [t for t in self._attempts[user_id] if now - t < 3600]
        self._attempts[user_id] = recent
        fail_count = len(recent)
        if fail_count >= self.max_attempts:
            delay = self._progressive_delay(fail_count)
            self._lockouts[user_id] = now + delay
            return {
                "allowed": False,
                "reason": "locked_out",
                "retry_after_seconds": round(delay, 1),
                "fail_count": fail_count,
            }
        return {
            "allowed": True,
            "reason": "attempt_recorded",
            "fail_count": fail_count,
            "remaining_attempts": self.max_attempts - fail_count,
        }

    def reset(self, user_id: str) -> None:
        self._attempts.pop(user_id, None)
        self._lockouts.pop(user_id, None)

    def get_status(self, user_id: str) -> dict[str, Any]:
        now = time.time()
        locked = user_id in self._lockouts and now < self._lockouts[user_id]
        return {
            "user_id": user_id,
            "locked": locked,
            "fail_count": len(self._attempts.get(user_id, [])),
            "retry_after": round(self._lockouts[user_id] - now, 1) if locked else 0,
        }
