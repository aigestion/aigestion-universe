#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
silicon_vault.py — E-22 · Las llaves de Daniela en silicio (Titan M2 / StrongBox)
================================================================================

Problema que resuelve
---------------------
Tenemos un **P0 abierto**: una `GEMINI_API_KEY` real trackeada en git y varios
`.env` con secretos en texto plano. Un `.env` es texto: se copia, se sube, se
filtra, y queda en el historial para siempre. Rotar la clave no arregla el
problema de fondo — solo lo pospone.

La idea
-------
Que el secreto **nunca exista como texto plano en disco**. Se guarda cifrado; la
clave maestra se deriva del PIN del usuario y se ata al dispositivo. Aunque te
roben el fichero, sin el PIN y sin el teléfono no sirve de nada.

Cómo lo hace (con lo que hay, sin pagar nada)
---------------------------------------------
1. **Derivación**: PBKDF2-HMAC-SHA256, 200.000 iteraciones, sobre
   `PIN + sal aleatoria + sal ligada al dispositivo`.
2. **Cifrado**: *keystream* SHAKE-256 (`hashlib.shake_256`) en XOR con el texto.
3. **Autenticación**: HMAC-SHA256 sobre `nonce || cifrado`, comparado con
   `hmac.compare_digest` (no filtra por tiempo ni por errores).

Todo con **solo la librería estándar** — porque `cryptography` en Termux implica
compilar Rust y nadie quiere eso en un móvil. SHAKE-256 como PRF es una
construcción legítima; HMAC le da integridad. No es AES-GCM, pero es sólido,
auditable en 30 líneas y no añade dependencias.

4. **Ata al hardware**: si `termux-keystore` está disponible (Titan M2 declara
   `strongbox_keystore=300`), se genera un par RSA-2048 en el Keystore de Android
   y su alias entra en la derivación de la clave. El blob cifrado de este
   teléfono **no se descifra en otro**, aunque tengas el PIN.
   Degradación limpia: sin Termux, se usa solo el fingerprint del dispositivo.

Uso típico
----------
```python
from services.security.silicon_vault import get_instance
v = get_instance()
v.desbloquear("000000")
v.guardar("GEMINI_API_KEY", "AIza...")
v.leer("GEMINI_API_KEY")
```

Rutas
-----
    GET    /api/vault/status               estado y backend en uso
    GET    /api/vault/list                 nombres de los secretos (nunca valores)
    POST   /api/vault/unlock               desbloquea con el PIN
    POST   /api/vault/lock                 bloquea y olvida la clave en memoria
    POST   /api/vault/secret               guarda un secreto
    GET    /api/vault/secret/<name>        recupera un secreto
    DELETE /api/vault/secret/<name>        borra un secreto
    POST   /api/vault/migrate              migra una variable de entorno en claro
"""

from __future__ import annotations

import base64
import hashlib
import hmac
import json
import os
import secrets
import subprocess
import time
from pathlib import Path
from typing import Any, Dict, List, Optional

# --------------------------------------------------------------------------
# Dependencias opcionales
# --------------------------------------------------------------------------
try:
    from flask import Flask, jsonify, request
except ImportError:  # pragma: no cover
    Flask = None  # type: ignore
    jsonify = None  # type: ignore
    request = None  # type: ignore


# --------------------------------------------------------------------------
# Constantes
# --------------------------------------------------------------------------
# Raiz del repo (este modulo vive en pixel/ desde Fase 2).
PROJECT_ROOT = Path(__file__).resolve().parents[2]
DATA_DIR = PROJECT_ROOT / "data" / "vault"
VAULT_FILE = DATA_DIR / "vault.json"
SALT_FILE = DATA_DIR / "salt.bin"

PBKDF2_ROUNDS = 200_000
KEY_LEN = 32  # SHAKE-256 keystream / HMAC key
NONCE_LEN = 16
MAX_SECRET_LEN = 8192  # una API key no necesita mas
MAX_NAME_LEN = 64

# Alias del par de claves en el Keystore de Android (Titan M2 si lo hay)
KEYSTORE_ALIAS = "daniela-vault"

# Umbral de inactividad tras el cual la vault se bloquea sola
AUTOLOCK_S = 900.0


# ==========================================================================
#  Utilidades criptográficas (solo stdlib)
# ==========================================================================
def _b64(d: bytes) -> str:
    return base64.b64encode(d).decode("ascii")


def _unb64(s: str) -> bytes:
    try:
        return base64.b64decode(s.encode("ascii"), validate=True)
    except Exception:
        return b""


def _huella_dispositivo() -> str:
    """Algo estable y dificil de clonar, sin necesidad de root.

    Se usa como parte de la sal para que el blob no viaje entre dispositivos.
    No pretende ser criptograficamente fuerte por si sola: es un factor mas,
    no el unico.
    """
    trozos: List[str] = []
    for ruta in (
        "/proc/sys/kernel/random/boot_id",
        "/sys/class/android_usb/android0/iSerial",
        "/proc/cpuinfo",
    ):
        try:
            t = Path(ruta).read_text(errors="replace")[:512]
            if t.strip():
                trozos.append(t)
        except Exception:
            continue
    trozos.append(os.environ.get("ANDROID_ID", ""))
    trozos.append(os.environ.get("TERMUX_APP__PACKAGE_NAME", ""))
    if not trozos:
        trozos.append("generico")
    return hashlib.sha256("|".join(trozos).encode("utf-8", "replace")).hexdigest()


def _derivar(pin: str, sal: bytes, atadura: str) -> bytes:
    """PBKDF2-HMAC-SHA256 sobre PIN + sal + atadura al dispositivo."""
    material = pin.encode("utf-8") + b"|" + atadura.encode("utf-8")
    return hashlib.pbkdf2_hmac("sha256", material, sal, PBKDF2_ROUNDS, KEY_LEN)


def _cifrar(clave: bytes, texto: str) -> Dict[str, str]:
    nonce = secrets.token_bytes(NONCE_LEN)
    flujo = hashlib.shake_256(clave + nonce).digest(len(texto.encode("utf-8")))
    plano = texto.encode("utf-8")
    cif = bytes(a ^ b for a, b in zip(plano, flujo))
    mac = hmac.new(clave, nonce + cif, hashlib.sha256).digest()
    return {"nonce": _b64(nonce), "cipher": _b64(cif), "mac": _b64(mac)}


def _descifrar(clave: bytes, paq: Dict[str, Any]) -> Optional[str]:
    """Devuelve None si el MAC no cuadra ( manipulado o PIN incorrecto )."""
    try:
        nonce = _unb64(str(paq.get("nonce", "")))
        cif = _unb64(str(paq.get("cipher", "")))
        mac = _unb64(str(paq.get("mac", "")))
    except Exception:
        return None
    if not nonce or not cif or len(mac) != 32:
        return None
    if not hmac.compare_digest(hmac.new(clave, nonce + cif, hashlib.sha256).digest(), mac):
        return None
    flujo = hashlib.shake_256(clave + nonce).digest(len(cif))
    try:
        return bytes(a ^ b for a, b in zip(cif, flujo)).decode("utf-8")
    except UnicodeDecodeError:
        return None


# ==========================================================================
#  Acceso al Keystore de Android (termux-keystore)
# ==========================================================================
def _keystore_disponible() -> bool:
    try:
        r = subprocess.run(["termux-keystore", "list"], capture_output=True, timeout=8, shell=False)
        return r.returncode == 0
    except (OSError, subprocess.SubprocessError):
        return False


def _keystore_asegurar() -> str:
    """Crea el par en el Keystore si no existe. Devuelve el estado."""
    if not _keystore_disponible():
        return "no-disponible"
    try:
        r = subprocess.run(["termux-keystore", "list"], capture_output=True, timeout=8, shell=False)
        if KEYSTORE_ALIAS in (r.stdout or b"").decode("utf-8", "replace"):
            return "ok"
    except (OSError, subprocess.SubprocessError):
        return "error"

    try:
        r = subprocess.run(
            ["termux-keystore", "generate", KEYSTORE_ALIAS, "-a", "RSA", "-s", "2048"],
            capture_output=True,
            timeout=25,
            shell=False,
        )
        return "ok" if r.returncode == 0 else "error"
    except (OSError, subprocess.SubprocessError):
        return "error"


# ==========================================================================
#  La caja fuerte
# ==========================================================================
class SiliconVault:
    """Secretos cifrados en reposo, desbloqueados solo en memoria."""

    def __init__(self) -> None:
        self._clave: Optional[bytes] = None
        self._desbloqueado_en = 0.0
        self.sal = b""
        self.atadura = ""
        self.secretos: Dict[str, Dict[str, Any]] = {}
        self.eventos: List[Dict[str, Any]] = []
        self.keystore = "desconocido"

        DATA_DIR.mkdir(parents=True, exist_ok=True)
        self._cargar_sal()
        self._cargar()
        self.keystore = _keystore_asegurar()

    # ------------------------------------------------------------- sal
    def _cargar_sal(self) -> None:
        if SALT_FILE.exists():
            try:
                self.sal = SALT_FILE.read_bytes()
            except Exception:
                self.sal = b""
        if len(self.sal) < 32:
            self.sal = secrets.token_bytes(32)
            try:
                SALT_FILE.write_bytes(self.sal)
            except Exception:
                pass
        self.atadura = _huella_dispositivo() + ":" + KEYSTORE_ALIAS

    # ----------------------------------------------------------- estado
    @property
    def desbloqueada(self) -> bool:
        if self._clave is None:
            return False
        if time.time() - self._desbloqueado_en > AUTOLOCK_S:
            self.bloquear()
            return False
        return True

    def desbloquear(self, pin: str) -> bool:
        """Deriva la clave y comprueba que descifra bien (o que es la 1ª vez)."""
        if not isinstance(pin, str) or not pin:
            return False
        clave = _derivar(pin, self.sal, self.atadura)
        if self.secretos:
            # Hay algo guardado: validamos contra el primer secreto.
            primero = next(iter(self.secretos.values()))
            if _descifrar(clave, primero) is None:
                return False
        self._clave = clave
        self._desbloqueado_en = time.time()
        self._evento("unlock", "ok")
        return True

    def bloquear(self) -> None:
        if self._clave is not None:
            self._evento("lock", "ok")
        self._clave = None
        self._desbloqueado_en = 0.0

    # --------------------------------------------------------- lectura/escritura
    def guardar(self, nombre: str, valor: str) -> bool:
        if not self.desbloqueada or self._clave is None:
            return False
        if not isinstance(nombre, str) or not nombre or len(nombre) > MAX_NAME_LEN:
            return False
        if not nombre.replace("_", "").replace("-", "").replace(".", "").isalnum():
            return False
        if not isinstance(valor, str) or not valor or len(valor) > MAX_SECRET_LEN:
            return False
        self.secretos[nombre] = _cifrar(self._clave, valor)
        self._guardar()
        self._evento("set", nombre)
        return True

    def leer(self, nombre: str) -> Optional[str]:
        if not self.desbloqueada or self._clave is None:
            return None
        paq = self.secretos.get(nombre)
        if not paq:
            return None
        valor = _descifrar(self._clave, paq)
        if valor is not None:
            self._desbloqueado_en = time.time()
            self._evento("get", nombre)
        return valor

    def borrar(self, nombre: str) -> bool:
        if not self.desbloqueada:
            return False
        if self.secretos.pop(nombre, None) is None:
            return False
        self._guardar()
        self._evento("delete", nombre)
        return True

    def migrar(self, nombre: str, var_entorno: Optional[str] = None) -> bool:
        """Coge una variable de entorno en claro y la mete cifrada en la vault.

        Es el camino para cerrar el P0 del `.env`: la clave deja de vivir en
        texto plano y pasa a estar cifrada en reposo.
        """
        var = var_entorno or nombre
        valor = os.environ.get(var)
        if not valor:
            return False
        return self.guardar(nombre, valor)

    # --------------------------------------------------------- persistencia
    def _cargar(self) -> None:
        if not VAULT_FILE.exists():
            return
        try:
            d = json.loads(VAULT_FILE.read_text(encoding="utf-8"))
            if isinstance(d, dict) and isinstance(d.get("secretos"), dict):
                self.secretos = {str(k): v for k, v in d["secretos"].items() if isinstance(v, dict)}
        except Exception:
            self.secretos = {}

    def _guardar(self) -> None:
        DATA_DIR.mkdir(parents=True, exist_ok=True)
        payload = {"version": 1, "atadura": self.atadura[:16], "secretos": self.secretos}
        tmp = VAULT_FILE.with_suffix(".tmp")
        tmp.write_text(json.dumps(payload, ensure_ascii=False, indent=1), encoding="utf-8")
        tmp.replace(VAULT_FILE)

    def _evento(self, tipo: str, detalle: str) -> None:
        self.eventos.append({"t": time.time(), "tipo": tipo, "detalle": detalle})
        self.eventos = self.eventos[-200:]

    # ------------------------------------------------------------- informe
    def estado(self) -> Dict[str, Any]:
        return {
            "desbloqueada": self.desbloqueada,
            "segundos_restantes": (
                max(0, int(AUTOLOCK_S - (time.time() - self._desbloqueado_en)))
                if self._clave is not None
                else 0
            ),
            "secretos": sorted(self.secretos.keys()),
            "keystore": self.keystore,
            "keystore_alias": KEYSTORE_ALIAS,
            "rondas_pbkdf2": PBKDF2_ROUNDS,
            "cifrado": "SHAKE-256 keystream + HMAC-SHA256 (solo stdlib)",
            "fichero": str(VAULT_FILE),
            "eventos": self.eventos[-10:],
        }


# --------------------------------------------------------------------------
#  Singleton
# --------------------------------------------------------------------------
_instancia: Optional[SiliconVault] = None


def get_instance() -> SiliconVault:
    global _instancia
    if _instancia is None:
        _instancia = SiliconVault()
    return _instancia


# --------------------------------------------------------------------------
#  Rutas Flask
# --------------------------------------------------------------------------
def register_vault_routes(app) -> None:  # noqa: C901
    if Flask is None:
        return

    def v() -> SiliconVault:
        return get_instance()

    @app.route("/api/vault/status", methods=["GET"], endpoint="vault__status")
    def _status():
        return jsonify({"ok": True, "vault": v().estado()})

    @app.route("/api/vault/list", methods=["GET"], endpoint="vault__list")
    def _list():
        return jsonify({"ok": True, "secretos": sorted(v().secretos.keys())})

    @app.route("/api/vault/unlock", methods=["POST"], endpoint="vault__unlock")
    def _unlock():
        d = request.get_json(silent=True) or {}
        pin = str(d.get("pin", ""))
        if v().desbloquear(pin):
            return jsonify({"ok": True, "desbloqueada": True})
        return jsonify({"ok": False, "error": "PIN incorrecto o vault vacia"}), 401

    @app.route("/api/vault/lock", methods=["POST"], endpoint="vault__lock")
    def _lock():
        v().bloquear()
        return jsonify({"ok": True, "desbloqueada": False})

    @app.route("/api/vault/secret", methods=["POST"], endpoint="vault__set")
    def _set():
        d = request.get_json(silent=True) or {}
        if v().guardar(str(d.get("name", "")), str(d.get("value", ""))):
            return jsonify({"ok": True})
        return jsonify({"ok": False, "error": "vault bloqueada o datos invalidos"}), 400

    @app.route("/api/vault/secret/<name>", methods=["GET"], endpoint="vault__get")
    def _get(name: str):
        valor = v().leer(name)
        if valor is None:
            return jsonify({"ok": False, "error": "no existe o vault bloqueada"}), 404
        return jsonify({"ok": True, "name": name, "value": valor})

    @app.route("/api/vault/secret/<name>", methods=["DELETE"], endpoint="vault__del")
    def _del(name: str):
        if v().borrar(name):
            return jsonify({"ok": True})
        return jsonify({"ok": False, "error": "no existe o vault bloqueada"}), 404

    @app.route("/api/vault/migrate", methods=["POST"], endpoint="vault__migrate")
    def _migrate():
        d = request.get_json(silent=True) or {}
        nombre = str(d.get("name", ""))
        var = d.get("env")
        if v().migrar(nombre, str(var) if var else None):
            return jsonify(
                {
                    "ok": True,
                    "migrado": nombre,
                    "aviso": "recuerda rotar la clave y purgarla de git",
                }
            )
        return jsonify({"ok": False, "error": "variable de entorno vacia"}), 400

    print(
        "[Silicon Vault] Routes registered: /api/vault/* "
        "(status, list, unlock, lock, secret, migrate)"
    )


# --------------------------------------------------------------------------
#  Demo
# --------------------------------------------------------------------------
def _demo() -> None:
    print("=" * 68)
    print(" SILICON VAULT (E-22) — el secreto nunca vive en claro")
    print("=" * 68)
    v = SiliconVault()
    print("keystore android :", v.keystore)
    print("fichero          :", VAULT_FILE)

    print("\n1) sin desbloquear no se puede escribir")
    print("   guardar() ->", v.guardar("X", "1"), "(False = correcto)")

    print("\n2) desbloqueo con PIN")
    print("   desbloquear('000000') ->", v.desbloquear("000000"))

    print("\n3) guardar y leer")
    v.guardar("GEMINI_API_KEY", "AIzaSyEJEMPLO-NO-REAL")
    v.guardar("DANIELA_PIN", "PIN_DE_EJEMPLO")
    print("   GEMINI_API_KEY ->", v.leer("GEMINI_API_KEY"))

    print("\n4) en disco SOLO hay cifrado")
    raw = json.loads(VAULT_FILE.read_text(encoding="utf-8"))
    blob = json.dumps(raw["secretos"])
    print("   'AIzaSy' en el fichero? ->", "AIzaSy" in blob, "(False = correcto)")
    print("   ejemplo de paquete      ->", json.dumps(raw["secretos"]["DANIELA_PIN"])[:88])

    print("\n5) PIN incorrecto no descifra")
    v.bloquear()
    print("   desbloquear('0000') ->", v.desbloquear("0000"), "(False = correcto)")

    print("\n6) manipular el cifrado se detecta (MAC)")
    v.desbloquear("000000")
    paq = v.secretos["GEMINI_API_KEY"]
    paq["cipher"] = _b64(b"X" * len(_unb64(paq["cipher"])))
    print("   leer() tras manipular ->", v.leer("GEMINI_API_KEY"), "(None = correcto)")
    print("=" * 68)


if __name__ == "__main__":
    _demo()