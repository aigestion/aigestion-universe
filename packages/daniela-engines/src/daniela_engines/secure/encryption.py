"""Encryption Services - Ideas 31-40."""

from __future__ import annotations

import base64
import hashlib
import hmac
import os
import secrets
import time
from typing import Any

# ---------------------------------------------------------------------------
# 31. AES-256 Encryption/Decryption
# ---------------------------------------------------------------------------

class AES256Cipher:
    """AES-256-GCM encryption and decryption."""

    KEY_SIZE = 32
    NONCE_SIZE = 12
    TAG_SIZE = 16

    def __init__(self, key: bytes | None = None):
        self.key = key or os.urandom(self.KEY_SIZE)

    def _derive_key(self, password: str, salt: bytes) -> bytes:
        return hashlib.pbkdf2_hmac("sha256", password.encode(), salt, 100000, dklen=self.KEY_SIZE)

    def encrypt(self, plaintext: str, associated_data: str = "") -> dict[str, str]:
        nonce = os.urandom(self.NONCE_SIZE)
        plaintext_bytes = plaintext.encode("utf-8")
        aad = associated_data.encode("utf-8") if associated_data else b""
        from cryptography.hazmat.primitives.ciphers.aead import AESGCM
        aes = AESGCM(self.key)
        ciphertext = aes.encrypt(nonce, plaintext_bytes, aad)
        return {
            "ciphertext": base64.b64encode(ciphertext).decode(),
            "nonce": base64.b64encode(nonce).decode(),
            "associated_data": associated_data,
        }

    def decrypt(self, ciphertext_b64: str, nonce_b64: str, associated_data: str = "") -> str:
        ciphertext = base64.b64decode(ciphertext_b64)
        nonce = base64.b64decode(nonce_b64)
        aad = associated_data.encode("utf-8") if associated_data else b""
        from cryptography.hazmat.primitives.ciphers.aead import AESGCM
        aes = AESGCM(self.key)
        plaintext = aes.decrypt(nonce, ciphertext, aad)
        return plaintext.decode("utf-8")

    def encrypt_from_password(self, plaintext: str, password: str) -> dict[str, str]:
        salt = os.urandom(16)
        key = self._derive_key(password, salt)
        nonce = os.urandom(self.NONCE_SIZE)
        from cryptography.hazmat.primitives.ciphers.aead import AESGCM
        aes = AESGCM(key)
        ciphertext = aes.encrypt(nonce, plaintext.encode("utf-8"), b"")
        return {
            "ciphertext": base64.b64encode(ciphertext).decode(),
            "nonce": base64.b64encode(nonce).decode(),
            "salt": base64.b64encode(salt).decode(),
        }


# ---------------------------------------------------------------------------
# 32. RSA Key Pair Generation
# ---------------------------------------------------------------------------

class RSAKeyManager:
    """RSA key pair generation and management."""

    def __init__(self):
        self._keys: dict[str, Any] = {}

    def generate_keypair(self, key_size: int = 4096, label: str = "") -> dict[str, str]:
        from cryptography.hazmat.primitives import serialization
        from cryptography.hazmat.primitives.asymmetric import rsa
        private_key = rsa.generate_private_key(public_exponent=65537, key_size=key_size)
        public_key = private_key.public_key()
        private_pem = private_key.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.PKCS8,
            encryption_algorithm=serialization.NoEncryption(),
        )
        public_pem = public_key.public_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PublicFormat.SubjectPublicKeyInfo,
        )
        key_id = hashlib.sha256(public_pem).hexdigest()[:16]
        self._keys[key_id] = {"label": label, "created_at": time.time(), "key_size": key_size}
        return {
            "key_id": key_id,
            "private_key": private_pem.decode(),
            "public_key": public_pem.decode(),
            "key_size": key_size,
        }

    def list_keys(self) -> list[dict[str, Any]]:
        return [{"key_id": kid, **info} for kid, info in self._keys.items()]

    def delete_key(self, key_id: str) -> bool:
        return self._keys.pop(key_id, None) is not None


# ---------------------------------------------------------------------------
# 33. Certificate Manager
# ---------------------------------------------------------------------------

class CertificateManager:
    """X.509 certificate management."""

    def __init__(self):
        self._certificates: dict[str, dict[str, Any]] = {}

    def generate_self_signed(
        self, common_name: str, organization: str = "", days_valid: int = 365
    ) -> dict[str, str]:
        import datetime

        from cryptography import x509
        from cryptography.hazmat.primitives import hashes, serialization
        from cryptography.hazmat.primitives.asymmetric import rsa
        from cryptography.x509.oid import NameOID
        key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
        name_attrs = [x509.NameAttribute(NameOID.COMMON_NAME, common_name)]
        if organization:
            name_attrs.append(x509.NameAttribute(NameOID.ORGANIZATION_NAME, organization))
        subject = issuer = x509.Name(name_attrs)
        cert = (
            x509.CertificateBuilder()
            .subject_name(subject)
            .issuer_name(issuer)
            .public_key(key.public_key())
            .serial_number(x509.random_serial_number())
            .not_valid_before(datetime.datetime.utcnow())
            .not_valid_after(datetime.datetime.utcnow() + datetime.timedelta(days=days_valid))
            .sign(key, hashes.SHA256())
        )
        cert_pem = cert.public_bytes(serialization.Encoding.PEM)
        key_pem = key.private_bytes(
            serialization.Encoding.PEM,
            serialization.PrivateFormat.PKCS8,
            serialization.NoEncryption(),
        )
        cert_id = hashlib.sha256(cert_pem).hexdigest()[:16]
        self._certificates[cert_id] = {
            "common_name": common_name,
            "organization": organization,
            "created_at": time.time(),
            "expires_at": time.time() + (days_valid * 86400),
        }
        return {"cert_id": cert_id, "certificate": cert_pem.decode(), "private_key": key_pem.decode()}

    def check_expiry(self, cert_id: str) -> dict[str, Any]:
        cert = self._certificates.get(cert_id)
        if not cert:
            return {"error": "certificate_not_found"}
        remaining = cert["expires_at"] - time.time()
        return {
            "cert_id": cert_id,
            "expired": remaining < 0,
            "remaining_days": round(remaining / 86400, 1),
        }

    def list_certificates(self) -> list[dict[str, Any]]:
        return [{"cert_id": cid, **info} for cid, info in self._certificates.items()]


# ---------------------------------------------------------------------------
# 34. Secret Rotation Scheduler
# ---------------------------------------------------------------------------

class SecretRotationScheduler:
    """Automated secret rotation scheduling."""

    def __init__(self):
        self._schedules: dict[str, dict[str, Any]] = {}
        self._history: dict[str, list[dict[str, Any]]] = {}

    def create_schedule(
        self, secret_name: str, rotation_interval_days: int, notify_before_days: int = 7
    ) -> str:
        schedule_id = hashlib.sha256(f"{secret_name}{time.time()}".encode()).hexdigest()[:16]
        self._schedules[schedule_id] = {
            "secret_name": secret_name,
            "rotation_interval_days": rotation_interval_days,
            "notify_before_days": notify_before_days,
            "last_rotated": time.time(),
            "created_at": time.time(),
            "active": True,
        }
        self._history[schedule_id] = []
        return schedule_id

    def check_rotation_needed(self, schedule_id: str) -> dict[str, Any]:
        schedule = self._schedules.get(schedule_id)
        if not schedule:
            return {"error": "schedule_not_found"}
        now = time.time()
        elapsed_days = (now - schedule["last_rotated"]) / 86400
        needs_rotation = elapsed_days >= schedule["rotation_interval_days"]
        notify_at = schedule["rotation_interval_days"] - schedule["notify_before_days"]
        should_notify = elapsed_days >= notify_at and not needs_rotation
        return {
            "schedule_id": schedule_id,
            "secret_name": schedule["secret_name"],
            "needs_rotation": needs_rotation,
            "should_notify": should_notify,
            "elapsed_days": round(elapsed_days, 1),
            "interval_days": schedule["rotation_interval_days"],
        }

    def rotate(self, schedule_id: str, new_value: str = "") -> dict[str, Any]:
        schedule = self._schedules.get(schedule_id)
        if not schedule:
            return {"error": "schedule_not_found"}
        old_last = schedule["last_rotated"]
        schedule["last_rotated"] = time.time()
        self._history[schedule_id].append({
            "rotated_at": time.time(),
            "previous_rotation": old_last,
        })
        return {"schedule_id": schedule_id, "rotated": True, "new_rotation_time": time.time()}

    def get_all_schedules(self) -> list[dict[str, Any]]:
        return [
            {"schedule_id": sid, "secret_name": s["secret_name"], "active": s["active"]}
            for sid, s in self._schedules.items()
        ]


# ---------------------------------------------------------------------------
# 35. Key Vault (HSM Simulation)
# ---------------------------------------------------------------------------

class KeyVault:
    """Hardware Security Module simulation for key management."""

    def __init__(self):
        self._keys: dict[str, dict[str, Any]] = {}
        self._access_log: list[dict[str, Any]] = []

    def store_key(self, key_id: str, key_data: bytes, key_type: str = "symmetric", metadata: dict | None = None) -> dict[str, Any]:
        key_hash = hashlib.sha256(key_data).hexdigest()
        self._keys[key_id] = {
            "key_hash": key_hash,
            "key_type": key_type,
            "metadata": metadata or {},
            "created_at": time.time(),
            "version": 1,
            "active": True,
        }
        self._log_access(key_id, "store")
        return {"key_id": key_id, "stored": True, "key_hash": key_hash[:16]}

    def retrieve_key(self, key_id: str, requester: str = "system") -> dict[str, Any]:
        key = self._keys.get(key_id)
        if not key or not key["active"]:
            return {"error": "key_not_found"}
        self._log_access(key_id, "retrieve", requester)
        return {"key_id": key_id, "key_type": key["key_type"], "version": key["version"]}

    def rotate_key(self, key_id: str, new_key_data: bytes) -> dict[str, Any]:
        key = self._keys.get(key_id)
        if not key:
            return {"error": "key_not_found"}
        key["version"] += 1
        key["key_hash"] = hashlib.sha256(new_key_data).hexdigest()
        key["last_rotated"] = time.time()
        self._log_access(key_id, "rotate")
        return {"key_id": key_id, "new_version": key["version"]}

    def deactivate_key(self, key_id: str) -> bool:
        key = self._keys.get(key_id)
        if key:
            key["active"] = False
            self._log_access(key_id, "deactivate")
            return True
        return False

    def list_keys(self) -> list[dict[str, Any]]:
        return [
            {"key_id": kid, "type": k["key_type"], "version": k["version"], "active": k["active"]}
            for kid, k in self._keys.items()
        ]

    def _log_access(self, key_id: str, operation: str, requester: str = "system") -> None:
        self._access_log.append({
            "key_id": key_id,
            "operation": operation,
            "requester": requester,
            "timestamp": time.time(),
        })


# ---------------------------------------------------------------------------
# 36. Data Masking (PII Redaction)
# ---------------------------------------------------------------------------

class PIIMasker:
    """Personally Identifiable Information masking and redaction."""

    PATTERNS = {
        "email": (r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}", "email"),
        "phone": (r"\b\d{3}[-.]?\d{3}[-.]?\d{4}\b", "phone"),
        "ssn": (r"\b\d{3}-\d{2}-\d{4}\b", "ssn"),
        "credit_card": (r"\b\d{4}[-\s]?\d{4}[-\s]?\d{4}[-\s]?\d{4}\b", "credit_card"),
        "ip_address": (r"\b\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}\b", "ip_address"),
        "date_of_birth": (r"\b\d{2}/\d{2}/\d{4}\b", "date_of_birth"),
    }

    def __init__(self):
        self._masks: dict[str, str] = {
            "email": "***@***.***",
            "phone": "***-***-****",
            "ssn": "***-**-****",
            "credit_card": "****-****-****-****",
            "ip_address": "*.*.*.*",
            "date_of_birth": "**/**/****",
        }

    def mask(self, text: str, pii_types: list[str] | None = None) -> str:
        import re
        result = text
        for _name, (pattern, pii_type) in self.PATTERNS.items():
            if pii_types and pii_type not in pii_types:
                continue
            mask = self._masks.get(pii_type, "***")
            result = re.sub(pattern, mask, result)
        return result

    def detect(self, text: str) -> list[dict[str, Any]]:
        import re
        findings: list[dict[str, Any]] = []
        for _name, (pattern, pii_type) in self.PATTERNS.items():
            matches = re.finditer(pattern, text)
            for match in matches:
                findings.append({
                    "type": pii_type,
                    "position": match.start(),
                    "length": match.end() - match.start(),
                    "masked_value": self._masks.get(pii_type, "***"),
                })
        return findings

    def mask_dict(self, data: dict[str, Any], fields: list[str] | None = None) -> dict[str, Any]:
        import re
        result = {}
        for key, value in data.items():
            if isinstance(value, str):
                if fields and key not in fields:
                    result[key] = value
                else:
                    masked = value
                    for _name, (pattern, pii_type) in self.PATTERNS.items():
                        masked = re.sub(pattern, self._masks.get(pii_type, "***"), masked)
                    result[key] = masked
            else:
                result[key] = value
        return result


# ---------------------------------------------------------------------------
# 37. Tokenization Service
# ---------------------------------------------------------------------------

class TokenizationService:
    """Tokenization for sensitive data replacement."""

    def __init__(self):
        self._tokens: dict[str, dict[str, Any]] = {}
        self._reverse: dict[str, str] = {}

    def tokenize(self, value: str, token_type: str = "general") -> str:
        token = f"tok_{secrets.token_hex(16)}"
        self._tokens[token] = {
            "value": value,
            "type": token_type,
            "created_at": time.time(),
        }
        self._reverse[hashlib.sha256(value.encode()).hexdigest()] = token
        return token

    def detokenize(self, token: str) -> str | None:
        entry = self._tokens.get(token)
        return entry["value"] if entry else None

    def tokenize_batch(self, values: list[dict[str, str]]) -> list[dict[str, str]]:
        return [
            {"original_key": v.get("key", ""), "token": self.tokenize(v["value"], v.get("type", "general"))}
            for v in values
        ]

    def get_token_info(self, token: str) -> dict[str, Any] | None:
        entry = self._tokens.get(token)
        if not entry:
            return None
        return {"type": entry["type"], "created_at": entry["created_at"], "has_value": True}

    def revoke_token(self, token: str) -> bool:
        entry = self._tokens.pop(token, None)
        if entry:
            h = hashlib.sha256(entry["value"].encode()).hexdigest()
            self._reverse.pop(h, None)
            return True
        return False


# ---------------------------------------------------------------------------
# 38. Hash Verification (bcrypt/scrypt)
# ---------------------------------------------------------------------------

class HashVerifier:
    """Password hashing and verification using bcrypt/scrypt."""

    def __init__(self):
        self._hashes: dict[str, str] = {}

    def hash_password(self, password: str, algorithm: str = "scrypt") -> str:
        salt = os.urandom(16)
        if algorithm == "scrypt":
            key = hashlib.scrypt(password.encode(), salt=salt, n=16384, r=8, p=1, dklen=32)
        else:
            key = hashlib.pbkdf2_hmac("sha256", password.encode(), salt, 100000)
        hash_str = f"${algorithm}${base64.b64encode(salt).decode()}${base64.b64encode(key).decode()}"
        return hash_str

    def verify_password(self, password: str, hash_str: str) -> bool:
        parts = hash_str.split("$")
        if len(parts) != 4:
            return False
        algorithm = parts[1]
        salt = base64.b64decode(parts[2])
        expected_key = base64.b64decode(parts[3])
        if algorithm == "scrypt":
            key = hashlib.scrypt(password.encode(), salt=salt, n=16384, r=8, p=1, dklen=32)
        else:
            key = hashlib.pbkdf2_hmac("sha256", password.encode(), salt, 100000)
        return hmac.compare_digest(key, expected_key)

    def hash_data(self, data: str, algorithm: str = "sha256") -> str:
        h = hashlib.new(algorithm)
        h.update(data.encode())
        return h.hexdigest()

    def verify_integrity(self, data: str, expected_hash: str, algorithm: str = "sha256") -> bool:
        return hmac.compare_digest(self.hash_data(data, algorithm), expected_hash)

    def constant_time_compare(self, a: str, b: str) -> bool:
        return hmac.compare_digest(a.encode(), b.encode())


# ---------------------------------------------------------------------------
# 39. Digital Signature Service
# ---------------------------------------------------------------------------

class DigitalSignatureService:
    """Digital signature creation and verification."""

    def __init__(self):
        self._signatures: dict[str, dict[str, Any]] = {}

    def generate_keypair(self) -> tuple[bytes, bytes]:
        from cryptography.hazmat.primitives import serialization
        from cryptography.hazmat.primitives.asymmetric import ec
        private_key = ec.generate_private_key(ec.SECP256R1())
        public_key = private_key.public_key()
        priv_pem = private_key.private_bytes(
            serialization.Encoding.PEM,
            serialization.PrivateFormat.PKCS8,
            serialization.NoEncryption(),
        )
        pub_pem = public_key.public_bytes(
            serialization.Encoding.PEM,
            serialization.PublicFormat.SubjectPublicKeyInfo,
        )
        return priv_pem, pub_pem

    def sign(self, data: bytes, private_key_pem: bytes) -> bytes:
        from cryptography.hazmat.primitives import hashes, serialization
        from cryptography.hazmat.primitives.asymmetric import ec
        private_key = serialization.load_pem_private_key(private_key_pem, password=None)
        signature = private_key.sign(data, ec.ECDSA(hashes.SHA256()))
        sig_id = hashlib.sha256(signature).hexdigest()[:16]
        self._signatures[sig_id] = {
            "data_hash": hashlib.sha256(data).hexdigest(),
            "created_at": time.time(),
        }
        return signature

    def verify(self, data: bytes, signature: bytes, public_key_pem: bytes) -> bool:
        from cryptography.hazmat.primitives import hashes, serialization
        from cryptography.hazmat.primitives.asymmetric import ec
        try:
            public_key = serialization.load_pem_public_key(public_key_pem)
            public_key.verify(signature, data, ec.ECDSA(hashes.SHA256()))
            return True
        except Exception:
            return False

    def get_signature_info(self, signature: bytes) -> dict[str, Any]:
        sig_hash = hashlib.sha256(signature).hexdigest()[:16]
        info = self._signatures.get(sig_hash, {})
        return {"signature_hash": sig_hash, "info": info}


# ---------------------------------------------------------------------------
# 40. Encryption at Rest for Databases
# ---------------------------------------------------------------------------

class DatabaseEncryption:
    """Encryption at rest for database fields and records."""

    def __init__(self, master_key: bytes | None = None):
        self.master_key = master_key or os.urandom(32)
        self._encrypted_fields: dict[str, dict[str, Any]] = {}

    def encrypt_field(self, record_id: str, field_name: str, value: str) -> dict[str, str]:
        from cryptography.hazmat.primitives.ciphers.aead import AESGCM
        key = hashlib.pbkdf2_hmac("sha256", self.master_key, record_id.encode(), 10000, dklen=32)
        nonce = os.urandom(12)
        aes = AESGCM(key)
        ciphertext = aes.encrypt(nonce, value.encode(), field_name.encode())
        enc_id = f"{record_id}:{field_name}"
        self._encrypted_fields[enc_id] = {"nonce": nonce, "created_at": time.time()}
        return {
            "ciphertext": base64.b64encode(ciphertext).decode(),
            "nonce": base64.b64encode(nonce).decode(),
        }

    def decrypt_field(self, record_id: str, field_name: str, ciphertext_b64: str, nonce_b64: str) -> str:
        from cryptography.hazmat.primitives.ciphers.aead import AESGCM
        key = hashlib.pbkdf2_hmac("sha256", self.master_key, record_id.encode(), 10000, dklen=32)
        nonce = base64.b64decode(nonce_b64)
        ciphertext = base64.b64decode(ciphertext_b64)
        aes = AESGCM(key)
        plaintext = aes.decrypt(nonce, ciphertext, field_name.encode())
        return plaintext.decode()

    def encrypt_record(self, record_id: str, fields: dict[str, str]) -> dict[str, dict[str, str]]:
        return {field: self.encrypt_field(record_id, field, value) for field, value in fields.items()}

    def decrypt_record(self, record_id: str, encrypted_fields: dict[str, dict[str, str]]) -> dict[str, str]:
        return {
            field: self.decrypt_field(record_id, field, enc["ciphertext"], enc["nonce"])
            for field, enc in encrypted_fields.items()
        }

    def get_encrypted_fields_count(self) -> int:
        return len(self._encrypted_fields)
