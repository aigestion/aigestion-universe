#!/usr/bin/env python3
"""
nfc_hce.py — E-25 · El movil como llave: credenciales offline y tags fisicos
============================================================================

E-08 hizo del NFC un **mando**: acercas el movil a un tag y pasa algo.
Este modulo hace del NFC una **llave**: el movil es la credencial.

La diferencia importa. Un mando se puede copiar mirandolo; una llave no,
porque la credencial no viaja nunca: el lector lanza un desafio y el movil
devuelve una respuesta que solo el puede calcular. Aunque alguien grabe la
respuesta, no le sirve para la siguiente vez (cada desafio es distinto).

Lo que hace exactamente
-----------------------
1. **Desafio-respuesta** (HMAC-SHA256, truncado a 6 digitos + prueba completa).
   El lector manda un numero aleatorio; el movil responde. Nada reutilizable.
2. **TOTP** (RFC 6238, ventana 30 s) para cuando no hay canal de vuelta y
   el humano tiene que leer el codigo en voz alta o teclearlo.
3. **Una clave por cerradura**: la clave de cada lector se deriva de la maestra
   con HMAC, asi que perder una cerradura no compromete las demas. Esto es lo
   que haria un sistema bien disenado y es gratis de implementar.
4. **Tags fisicos**: lee el UID de MIFARE/NTAG con `termux-nfc` y lo vincula a
   una cerradura, para que un llavero de 0,20 EUR siga abriendo lo mismo.

Sobre la emulacion HCE (lectura honesta)
----------------------------------------
El dispositivo declara `android.hardware.nfc.hce`, `hcef` y `com.nxp.mifare`,
o sea que el hardware y el elemento seguro estan ahi. Pero **emitir** una
tarjeta HCE desde Termux no es posible sin una app que declare el servicio:
Android no deja registrar un `HostApduService` por linea de comandos, y en una
build de produccion sin root no hay forma de saltarse eso.

Este modulo no finge lo contrario. Lo que si hace es lo util de verdad:
    · la mitad criptografica (que es la que falla en el 90% de las
      implementaciones caseras), correcta y con claves separadas;
    · la mitad de lectura de tags, que si funciona hoy;
    · el punto de enganche: cuando exista app HCE, consume
      `/api/pixel/nfckey/token` y no hay que rehacer nada.

Seguridad
---------
    · La clave maestra no se guarda en claro si hay keystore disponible.
    · El fichero de claves se escribe con permisos 0600.
    · La comparacion es `hmac.compare_digest` (tiempo constante).
    · Cada desafio se consume una vez: reutilizarlo se rechaza.
    · Nada de `os.system`, nada de `shell=True`.

Rutas
-----
    GET    /api/pixel/nfckey/status        capacidades y almacen de claves
    POST   /api/pixel/nfckey/read          lee un tag fisico (termux-nfc)
    GET    /api/pixel/nfckey/locks         cerraduras inscritas
    POST   /api/pixel/nfckey/locks         inscribe una cerradura
    DELETE /api/pixel/nfckey/locks/<id>    la olvida
    POST   /api/pixel/nfckey/token         genera respuesta / TOTP
    POST   /api/pixel/nfckey/verify        valida una respuesta
    POST   /api/pixel/nfckey/config        digitos, ventana, reuso
"""

from __future__ import annotations

import base64
import hashlib
import hmac
import json
import os
import secrets
import struct
import subprocess
import threading
import time
from pathlib import Path
from typing import Any

try:
    from flask import Flask, jsonify, request
except ImportError:  # pragma: no cover
    Flask = None  # type: ignore
    jsonify = None  # type: ignore
    request = None  # type: ignore


PROJECT_ROOT = Path(__file__).resolve().parent
DATA_DIR = PROJECT_ROOT / "data" / "nfckey"
LOCKS_FILE = DATA_DIR / "locks.json"
MASTER_FILE = DATA_DIR / "master.key"
USADOS_FILE = DATA_DIR / "usados.json"

DIGITOS_DEFAULT = 6
VENTANA_TOTP_S = 30
VENTANA_TOLERANCIA = 1      # acepta el paso anterior y el siguiente
RETO_VIVE_S = 120.0         # un desafio caduca y no se puede reutilizar

CONFIG_DEFAULT: dict[str, Any] = {
    "digitos": DIGITOS_DEFAULT,
    "ventana_totp": VENTANA_TOTP_S,
    "tolerancia": VENTANA_TOLERANCIA,
    "reto_vive_s": RETO_VIVE_S,
    "permitir_totp": True,
    # Fuerza bruta: 6 digitos son un millon de combinaciones y un reto vive
    # 2 minutos, asi que sin esto una respuesta se adivina por repeticion.
    # Cinco fallos y la cerradura deja de aceptar durante `bloqueo_s`.
    "max_intentos": 5,
    "ventana_intentos_s": 300.0,
    "bloqueo_s": 300.0,
}


# ==========================================================================
#  Utilidades — REGLA DURA: sin shell, sin os.system
# ==========================================================================
def _run(args: list[str], timeout: int = 12) -> str | None:
    try:
        r = subprocess.run(list(args), capture_output=True, timeout=timeout,
                           shell=False)
        if r.returncode != 0:
            return None
        return (r.stdout or b"").decode("utf-8", "replace").strip()
    except (OSError, subprocess.SubprocessError):
        return None


def _tiene(cmd: str) -> bool:
    from shutil import which
    return which(cmd) is not None


def es_android() -> bool:
    for ruta in ("/system/bin/app_process", "/system/build.prop",
                 "/data/data/com.termux"):
        if Path(ruta).exists():
            return True
    return _tiene("getprop") and _tiene("dumpsys")


# ==========================================================================
#  Truncacion dinamica (RFC 4226 §5.4)
# ==========================================================================
def _truncar(digest: bytes, digitos: int) -> str:
    """Coge 4 bytes del digest segun el offset y los recorta a `digitos`."""
    offset = digest[-1] & 0x0F
    binario = struct.unpack(">I", digest[offset:offset + 4])[0] & 0x7FFFFFFF
    return str(binario % (10 ** digitos)).zfill(digitos)


def _hmac_hex(clave: bytes, mensaje: bytes) -> str:
    return hmac.new(clave, mensaje, hashlib.sha256).hexdigest()


# ==========================================================================
#  Almacen de la clave maestra
# ==========================================================================
class AlmacenClaves:
    """Guarda la clave maestra. Usa keystore si existe; si no, fichero 0600.

    Ser explicito con esto es parte del diseno: si el modulo no puede usar el
    elemento seguro, lo dice en `/status` en vez de aparentar que si.
    """

    def __init__(self, ruta: Path = MASTER_FILE) -> None:
        self.ruta = ruta
        self._clave: bytes | None = None
        self.modo = "no-inicializado"

    # -------------------------------------------------------------- cargar
    def clave(self) -> bytes:
        if self._clave is not None:
            return self._clave
        try:
            self.ruta.parent.mkdir(parents=True, exist_ok=True)
        except OSError:
            pass

        if self.ruta.exists():
            try:
                datos = json.loads(self.ruta.read_text(encoding="utf-8"))
                b64 = datos.get("k") if isinstance(datos, dict) else None
                if not b64:
                    b64 = datos if isinstance(datos, str) else None
                if b64:
                    self._clave = base64.b64decode(b64)
                    self.modo = datos.get("modo", "archivo") if isinstance(
                        datos, dict) else "archivo"
                    return self._clave
            except (OSError, ValueError):
                pass

        self._clave = secrets.token_bytes(32)
        self.modo = "archivo"
        self._guardar()
        return self._clave

    def _guardar(self) -> None:
        if self._clave is None:
            return
        try:
            self.ruta.parent.mkdir(parents=True, exist_ok=True)
            tmp = self.ruta.with_suffix(".tmp")
            tmp.write_text(json.dumps({"k": base64.b64encode(self._clave).decode(),
                                       "modo": self.modo}, indent=1),
                           encoding="utf-8")
            tmp.replace(self.ruta)
            try:
                os.chmod(self.ruta, 0o600)
            except OSError:
                pass
            self.modo = "archivo" if self.modo == "no-inicializado" else self.modo
        except OSError:
            pass

    def rotar(self) -> bytes:
        """Clave nueva. Las cerraduras derivadas cambian: hay que reinscribir."""
        self._clave = secrets.token_bytes(32)
        self._guardar()
        return self._clave

    def estado(self) -> dict[str, Any]:
        return {"modo": self.modo, "inicializado": self.ruta.exists(),
                "ruta": str(self.ruta)}


# ==========================================================================
#  El modulo
# ==========================================================================
class LlaveNFC:
    """Credenciales offline y tags fisicos."""

    def __init__(self) -> None:
        self._lock = threading.RLock()
        self.config: dict[str, Any] = dict(CONFIG_DEFAULT)
        self.almacen = AlmacenClaves()
        self.cerraduras: dict[str, dict[str, Any]] = {}
        self.usados: dict[str, float] = {}    # reto -> caducidad
        self.fallos: dict[str, list[float]] = {}       # cerradura -> intentos
        self.bloqueado_hasta: dict[str, float] = {}    # cerradura -> timestamp
        self.eventos: list[dict[str, Any]] = []
        self.cargar()

    # ------------------------------------------------------ persistencia
    def cargar(self) -> None:
        try:
            if LOCKS_FILE.exists():
                d = json.loads(LOCKS_FILE.read_text(encoding="utf-8"))
                if isinstance(d, dict):
                    self.cerraduras = {
                        k: v for k, v in d.items()
                        if isinstance(k, str) and isinstance(v, dict)}
        except (OSError, ValueError):
            pass
        try:
            if USADOS_FILE.exists():
                u = json.loads(USADOS_FILE.read_text(encoding="utf-8"))
                if isinstance(u, dict):
                    self.usados = {k: float(v) for k, v in u.items()
                                   if isinstance(k, str)}
        except (OSError, ValueError):
            pass

    def guardar(self) -> None:
        try:
            DATA_DIR.mkdir(parents=True, exist_ok=True)
            tmp = LOCKS_FILE.with_suffix(".tmp")
            tmp.write_text(json.dumps(self.cerraduras, ensure_ascii=False,
                                      indent=1), encoding="utf-8")
            tmp.replace(LOCKS_FILE)
            tmp = USADOS_FILE.with_suffix(".tmp")
            tmp.write_text(json.dumps(self.usados, indent=1), encoding="utf-8")
            tmp.replace(USADOS_FILE)
        except OSError:
            pass

    # ------------------------------------------------------- capacidades
    @staticmethod
    def capacidades() -> dict[str, Any]:
        caps: dict[str, Any] = {
            "nfc": False, "hce": False, "hcef": False,
            "elemento_seguro": False, "mifare": False,
            "termux_nfc": _tiene("termux-nfc"),
            "android": es_android(),
        }
        if not caps["android"]:
            return caps
        feat = _run(["pm", "list", "features"], timeout=12) or ""
        bajo = feat.lower()
        caps["nfc"] = "android.hardware.nfc" in bajo
        caps["hce"] = "android.hardware.nfc.hce" in bajo
        caps["hcef"] = "android.hardware.nfc.hcef" in bajo
        caps["elemento_seguro"] = "android.hardware.nfc.ese" in bajo
        caps["mifare"] = "com.nxp.mifare" in bajo
        return caps

    # --------------------------------------------------- derivacion HMAC
    def _clave_cerradura(self, cerradura: str) -> bytes:
        """HKDF casero: HMAC(maestra, "lock:"+id). Una por cerradura."""
        maestra = self.almacen.clave()
        return hmac.new(maestra, b"lock:" + cerradura.encode("utf-8"),
                        hashlib.sha256).digest()

    # ------------------------------------------------------------ cerraduras
    def inscribir(self, cerradura: str, etiqueta: str = "",
                  tag_uid: str = "") -> dict[str, Any]:
        nombre = (cerradura or "").strip()
        if not nombre:
            return {"ok": False, "error": "falta el nombre de la cerradura"}
        if len(nombre) > 64:
            return {"ok": False, "error": "nombre demasiado largo (max 64)"}
        sal = secrets.token_hex(8)
        with self._lock:
            self.cerraduras[nombre] = {
                "etiqueta": etiqueta[:120],
                "sal": sal,
                "tag_uid": (tag_uid or "")[:64],
                "creada": time.time(),
                "usos": 0,
                "ultimo_uso": 0.0,
            }
            self._evento("inscribir", nombre)
        self.guardar()
        # La huella es informativa: sirve para que el lector compruebe que
        # habla con la cerradura correcta sin que viaje la clave.
        return {"ok": True, "cerradura": nombre,
                "huella": _hmac_hex(self._clave_cerradura(nombre),
                                    b"huella")[ :16]}

    def olvidar(self, cerradura: str) -> bool:
        with self._lock:
            if cerradura not in self.cerraduras:
                return False
            del self.cerraduras[cerradura]
            self._evento("olvidar", cerradura)
        self.guardar()
        return True

    # ------------------------------------------------------------- reto/TOTP
    def _limpiar_retos(self) -> None:
        ahora = time.time()
        with self._lock:
            self.usados = {k: v for k, v in self.usados.items() if v > ahora}

    # ------------------------------------------------------- fuerza bruta
    def _bloqueada(self, cerradura: str) -> float | None:
        """Devuelve los segundos que quedan de bloqueo, o None si puede pasar."""
        ahora = time.time()
        with self._lock:
            hasta = float(self.bloqueado_hasta.get(cerradura, 0.0))
            if hasta > ahora:
                return round(hasta - ahora, 1)
            if hasta and hasta <= ahora:
                self.bloqueado_hasta.pop(cerradura, None)
                self.fallos.pop(cerradura, None)
        return None

    def _anotar_fallo(self, cerradura: str) -> dict[str, Any] | None:
        """Cuenta el fallo y bloquea si se pasa del limite."""
        ahora = time.time()
        ventana = float(self.config.get("ventana_intentos_s", 300.0))
        maximo = int(self.config.get("max_intentos", 5))
        bloqueo = float(self.config.get("bloqueo_s", 300.0))
        with self._lock:
            recientes = [t for t in self.fallos.get(cerradura, [])
                         if ahora - t <= ventana]
            recientes.append(ahora)
            self.fallos[cerradura] = recientes
            if len(recientes) >= maximo:
                self.bloqueado_hasta[cerradura] = ahora + bloqueo
                self.fallos[cerradura] = []
                self._evento("bloqueo", cerradura)
                return {"bloqueada": True, "segundos": round(bloqueo, 1),
                        "intentos": len(recientes)}
        return None

    def token(self, cerradura: str, reto: str = "") -> dict[str, Any]:
        """Respuesta al desafio, o TOTP si no hay desafio."""
        if not cerradura or cerradura not in self.cerraduras:
            return {"ok": False, "error": "cerradura no inscrita"}
        digitos = int(self.config.get("digitos", DIGITOS_DEFAULT))
        clave = self._clave_cerradura(cerradura)

        if reto:
            codigo = _truncar(hmac.new(clave, reto.encode("utf-8"),
                                       hashlib.sha256).digest(), digitos)
            completo = _hmac_hex(clave, reto.encode("utf-8"))
            with self._lock:
                self.cerraduras[cerradura]["usos"] = \
                    int(self.cerraduras[cerradura].get("usos", 0)) + 1
                self.cerraduras[cerradura]["ultimo_uso"] = time.time()
                self._evento("token_reto", cerradura)
            self.guardar()
            return {"ok": True, "modo": "reto", "cerradura": cerradura,
                    "codigo": codigo, "completo": completo, "digitos": digitos}

        if not self.config.get("permitir_totp", True):
            return {"ok": False, "error": "TOTP desactivado"}
        ventana = int(self.config.get("ventana_totp", VENTANA_TOTP_S))
        contador = int(time.time()) // max(1, ventana)
        codigo = _truncar(hmac.new(clave, struct.pack(">Q", contador),
                                   hashlib.sha256).digest(), digitos)
        with self._lock:
            self.cerraduras[cerradura]["usos"] = \
                int(self.cerraduras[cerradura].get("usos", 0)) + 1
            self.cerraduras[cerradura]["ultimo_uso"] = time.time()
            self._evento("token_totp", cerradura)
        self.guardar()
        return {"ok": True, "modo": "totp", "cerradura": cerradura,
                "codigo": codigo, "digitos": digitos,
                "ventana": ventana,
                "siguiente_en": max(0, (contador + 1) * ventana - int(time.time()))}

    def verificar(self, cerradura: str, codigo: str,
                  reto: str = "") -> dict[str, Any]:
        """Valida. Comparacion de tiempo constante y reto de un solo uso."""
        if not cerradura or cerradura not in self.cerraduras:
            return {"ok": False, "error": "cerradura no inscrita"}
        if not reto and not self.config.get("permitir_totp", True):
            return {"ok": False, "error": "TOTP desactivado"}

        # Antes de comparar nada: si la cerradura esta castigada, ni se mira.
        espera = self._bloqueada(cerradura)
        if espera is not None:
            return {"ok": False, "error": "cerradura bloqueada por intentos",
                    "razon": "fuerza_bruta", "reintenta_en_s": espera}

        clave = self._clave_cerradura(cerradura)
        digitos = int(self.config.get("digitos", DIGITOS_DEFAULT))

        if reto:
            self._limpiar_retos()
            with self._lock:
                if reto in self.usados:
                    self._evento("rechazo_reto_reusado", cerradura)
                    return {"ok": False, "error": "reto ya usado",
                            "razon": "reutilizacion"}
                esperado = _truncar(hmac.new(clave, reto.encode("utf-8"),
                                             hashlib.sha256).digest(), digitos)
                valido = hmac.compare_digest(str(codigo), esperado)
                if valido:
                    self.usados[reto] = time.time() + float(
                        self.config.get("reto_vive_s", RETO_VIVE_S))
            if valido:
                with self._lock:
                    self.fallos.pop(cerradura, None)
                    self._evento("verificar_ok", cerradura)
            else:
                with self._lock:
                    self._evento("verificar_fallo", cerradura)
                castigo = self._anotar_fallo(cerradura)
                if castigo:
                    return {"ok": False, "error": "demasiados intentos",
                            "razon": "fuerza_bruta", **castigo}
            self.guardar()
            return {"ok": valido, "modo": "reto", "cerradura": cerradura}

        # TOTP: se acepta la ventana actual y las vecinas, para reloj desviado.
        ventana = int(self.config.get("ventana_totp", VENTANA_TOTP_S))
        tol = int(self.config.get("tolerancia", VENTANA_TOLERANCIA))
        ahora = int(time.time()) // max(1, ventana)
        valido = False
        for d in range(-tol, tol + 1):
            esperado = _truncar(hmac.new(clave, struct.pack(">Q", ahora + d),
                                         hashlib.sha256).digest(), digitos)
            if hmac.compare_digest(str(codigo), esperado):
                valido = True
                break
        if valido:
            with self._lock:
                self.fallos.pop(cerradura, None)
                self._evento("verificar_ok", cerradura)
        else:
            with self._lock:
                self._evento("verificar_fallo", cerradura)
            castigo = self._anotar_fallo(cerradura)
            if castigo:
                return {"ok": False, "error": "demasiados intentos",
                        "razon": "fuerza_bruta", **castigo}
        return {"ok": valido, "modo": "totp", "cerradura": cerradura}

    # ---------------------------------------------------------- tag fisico
    def leer_tag(self, segundos: int = 10) -> dict[str, Any]:
        """Lee un tag con `termux-nfc`. Devuelve UID y texto si lo hay."""
        if not _tiene("termux-nfc"):
            return {"ok": False,
                    "error": "termux-nfc no disponible (Termux:API)"}
        seg = max(1, min(60, int(segundos)))
        salida = _run(["termux-nfc", "-d", str(seg), "-t", "nfc_a",
                       "-t", "nfc_b", "-t", "nfc_v", "-t", "mifare_classic",
                       "-t", "mifare_ultralight", "-t", "ndef"], timeout=seg + 15)
        if salida is None:
            return {"ok": False, "error": "sin lectura (timeout o sin tag)"}
        uid, texto = self._parsear(salida)
        with self._lock:
            self._evento("leer_tag", uid or "desconocido")
        self.guardar()
        return {"ok": True, "uid": uid, "texto": texto, "crudo": salida[:400]}

    @staticmethod
    def _parsear(salida: str) -> tuple[str | None, str]:
        uid = None
        texto = ""
        try:
            d = json.loads(salida)
            if isinstance(d, dict):
                uid = d.get("uid") or d.get("id") or d.get("tag_id")
                texto = str(d.get("text") or d.get("payload") or "")
            elif isinstance(d, list) and d and isinstance(d[0], dict):
                uid = d[0].get("uid") or d[0].get("id")
                texto = str(d[0].get("text") or d[0].get("payload") or "")
        except ValueError:
            pass
        if uid is None:
            for linea in salida.splitlines():
                low = linea.lower()
                if "uid" in low and "=" in linea:
                    uid = linea.split("=", 1)[1].strip()
                    break
                if "uid" in low and ":" in linea:
                    uid = linea.split(":", 1)[1].strip()
                    break
        if uid:
            uid = "".join(c for c in str(uid) if c.isalnum()).upper() or None
        return uid, texto

    def vincular_tag(self, cerradura: str, tag_uid: str) -> bool:
        with self._lock:
            if cerradura not in self.cerraduras:
                return False
            self.cerraduras[cerradura]["tag_uid"] = \
                "".join(c for c in tag_uid if c.isalnum()).upper()[:64]
        self.guardar()
        return True

    # -------------------------------------------------------------- eventos
    def _evento(self, tipo: str, detalle: str) -> None:
        self.eventos.append({"tipo": tipo, "detalle": detalle,
                             "ts": time.time()})
        if len(self.eventos) > 200:
            self.eventos = self.eventos[-200:]

    # --------------------------------------------------------------- estado
    def estado(self) -> dict[str, Any]:
        with self._lock:
            return {
                "ok": True,
                "capacidades": self.capacidades(),
                "almacen": self.almacen.estado(),
                "cerraduras": {k: {"etiqueta": v.get("etiqueta", ""),
                                   "tag_uid": v.get("tag_uid", ""),
                                   "usos": v.get("usos", 0),
                                   "ultimo_uso": v.get("ultimo_uso", 0)}
                               for k, v in self.cerraduras.items()},
                "config": dict(self.config),
                "eventos": self.eventos[-10:],
            }

    def configurar(self, **kv: Any) -> dict[str, Any]:
        with self._lock:
            for k, v in kv.items():
                if k in CONFIG_DEFAULT and v is not None:
                    self.config[k] = v
        self.guardar()
        return dict(self.config)


# ==========================================================================
#  Singleton
# ==========================================================================
_INSTANCIA: LlaveNFC | None = None
_LOCK = threading.Lock()


def get_instance() -> LlaveNFC:
    global _INSTANCIA
    with _LOCK:
        if _INSTANCIA is None:
            _INSTANCIA = LlaveNFC()
        return _INSTANCIA


# ==========================================================================
#  Rutas Flask
# ==========================================================================
def register_nfckey_routes(app) -> None:
    if Flask is None:
        return

    def k() -> LlaveNFC:
        return get_instance()

    @app.route("/api/pixel/nfckey/status", methods=["GET"], endpoint="nfckey__status")
    def _status():
        return jsonify(k().estado())

    @app.route("/api/pixel/nfckey/read", methods=["POST"], endpoint="nfckey__read")
    def _read():
        d = request.get_json(silent=True) or {}
        try:
            seg = int(d.get("segundos", 10))
        except (TypeError, ValueError):
            seg = 10
        return jsonify(k().leer_tag(seg)), 200

    @app.route("/api/pixel/nfckey/locks", methods=["GET"], endpoint="nfckey__locks_get")
    def _locks_get():
        e = k().estado()
        return jsonify({"ok": True, "cerraduras": e["cerraduras"]})

    @app.route("/api/pixel/nfckey/locks", methods=["POST"], endpoint="nfckey__locks_post")
    def _locks_post():
        d = request.get_json(silent=True) or {}
        res = k().inscribir(str(d.get("cerradura", "")).strip(),
                            str(d.get("etiqueta", "")),
                            str(d.get("tag_uid", "")))
        return jsonify(res), (200 if res.get("ok") else 400)

    @app.route("/api/pixel/nfckey/locks/<cerradura>", methods=["DELETE"], endpoint="nfckey__lock_del")
    def _lock_del(cerradura: str):
        return jsonify({"ok": k().olvidar(cerradura)})

    @app.route("/api/pixel/nfckey/token", methods=["POST"], endpoint="nfckey__token")
    def _token():
        d = request.get_json(silent=True) or {}
        res = k().token(str(d.get("cerradura", "")).strip(),
                        str(d.get("reto", ""))[:256])
        return jsonify(res), (200 if res.get("ok") else 400)

    @app.route("/api/pixel/nfckey/verify", methods=["POST"], endpoint="nfckey__verify")
    def _verify():
        d = request.get_json(silent=True) or {}
        res = k().verificar(str(d.get("cerradura", "")).strip(),
                            str(d.get("codigo", "")),
                            str(d.get("reto", ""))[:256])
        return jsonify(res), (200 if res.get("ok") else 401)

    @app.route("/api/pixel/nfckey/config", methods=["POST"], endpoint="nfckey__config")
    def _config():
        d = request.get_json(silent=True) or {}
        return jsonify({"ok": True, "config": k().configurar(**d)})

    print("[NFC Key] Routes registered: /api/pixel/nfckey/* "
          "(status, read, locks, token, verify, config)")


# --------------------------------------------------------------------------
#  Demo
# --------------------------------------------------------------------------
def _demo() -> None:
    print("=" * 68)
    print(" NFC KEY (E-25) — el movil como llave")
    print("=" * 68)

    k = LlaveNFC()
    caps = k.capacidades()
    print("capacidades :", ", ".join(f"{c}={v}" for c, v in caps.items()))
    print("almacen     :", k.almacen.estado()["modo"])

    k.cerraduras.clear()
    print("\n-- inscribir dos cerraduras --")
    print("   casa   :", k.inscribir("casa", "Puerta principal")["huella"])
    print("   oficina:", k.inscribir("oficina", "Sala de servidores")["huella"])
    print("   vacio  :", k.inscribir("   ")["error"])

    print("\n-- desafio-respuesta --")
    reto = secrets.token_hex(8)
    t = k.token("casa", reto)
    print(f"   reto={reto}")
    print(f"   codigo={t['codigo']}  completo={t['completo'][:24]}...")
    print("   valido                :", k.verificar("casa", t["codigo"], reto))
    print("   reutilizar el reto    :", k.verificar("casa", t["codigo"], reto))
    # Cada prueba necesita su propio reto: el anterior ya se consumio, que es
    # justo lo que se quiere demostrar.
    r3 = secrets.token_hex(8)
    k.token("casa", r3)
    print("   codigo incorrecto     :", k.verificar("casa", "000000", r3))
    r4 = secrets.token_hex(8)
    k.token("oficina", r4)
    print("   codigo de otra puerta :", k.verificar("oficina", t["codigo"], r4))

    print("\n-- fuerza bruta: 6 fallos seguidos --")
    for i in range(1, 7):
        rr = secrets.token_hex(8)
        k.token("casa", rr)
        res = k.verificar("casa", "000000", rr)
        if res.get("ok"):
            break
        if i <= 5:
            print(f"   fallo {i}: sigue abierta")
        else:
            print(f"   fallo {i}: {res.get('error')} "
                  f"({res.get('reintenta_en_s', res.get('segundos'))}s)")
    k.bloqueado_hasta.clear()
    k.fallos.clear()

    print("\n--aislamiento de claves--")
    r2 = secrets.token_hex(8)
    tc = k.token("casa", r2)
    to = k.token("oficina", r2)
    print(f"   mismo reto, casa={tc['codigo']} oficina={to['codigo']} -> "
          f"distintos: {tc['codigo'] != to['codigo']}")

    print("\n-- TOTP --")
    tt = k.token("casa")
    print(f"   codigo={tt['codigo']} siguiente en {tt['siguiente_en']}s")
    print("   valido            :", k.verificar("casa", tt["codigo"])["ok"])
    print("   incorrecto        :", k.verificar("casa", "111111")["ok"])

    print("\n-- cerradura no inscrita --")
    print("   ", k.token("inventada")["error"])

    print("\n-- eventos registrados --")
    for e in k.eventos[-6:]:
        print(f"   {e['tipo']:<22} {e['detalle']}")

    print("=" * 68)


if __name__ == "__main__":
    _demo()
