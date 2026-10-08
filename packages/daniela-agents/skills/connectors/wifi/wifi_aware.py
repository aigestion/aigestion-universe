#!/usr/bin/env python3
"""
wifi_aware.py — E-20 · Malla sin infraestructura: Daniela se sincroniza donde sea
===============================================================================

E-11 resolvio el *problema dificil*: que dos nodos que se escriben por separado
acaben en el mismo estado (CRDTs, reloj hibrido, anti-entropia idempotente).
Pero resuelve solo la mitad del problema de verdad, porque asume que los nodos
**pueden hablarse**: una URL conocida, un router, una nube detras.

Ese supuesto cae justo cuando mas importa:
  · en la calle, donde no hay router ni quieres gastar datos,
  · en un apagon, que es exactamente cuando necesitas que tu agenda y tus
    notas sigan convergentes,
  · entre dos moviles en un coche, en el campo, en una obra.

Este modulo es la otra mitad: **el transporte**. Descubre companeros sin
infraestructura y le entrega a E-11 la URL de cada uno para que la
anti-entropia haga su trabajo. Si E-11 es el idioma, esto es el camino.

Los cuatro caminos, en orden de preferencia
-------------------------------------------
1. `aware`   Wi-Fi Aware / NAN (802.11mc). Descubrimiento entre dispositivos
             **sin router, sin internet y sin emparejamiento**. Es lo ideal y
             el dispositivo declara `android.hardware.wifi.aware`, pero en una
             build de produccion sin root el sistema no lo expone por linea de
             comandos, asi que se *intenta* y se cae al siguiente.
2. `p2p`     Wi-Fi Direct (`cmd wifip2p`). Mismo problema de permisos, misma
             politica: se intenta, no se exige.
3. `hotspot` Uno enciende su punto de acceso y los demas se enganchan. Es el
             modo que de verdad funciona hoy sin root, y por eso el modulo es
             capaz de decidir *quien* lo enciende (el que va cargando y con
             bateria, no el primero que llega).
4. `lan`     Difusion UDP en la red comun. Siempre disponible, incluso en el
             PC de desarrollo: es el suelo del que nunca se cae.

La regla que ordena todo: **el modulo nunca falla por falta de hardware**.
Degrada por capas y siempre acaba en `lan`, que funciona en cualquier sitio
donde ya haya una red. En un portatil sin WiFi Aware, la demo de abajo sigue
pasando entera.

Rutas
-----
    GET  /api/pixel/aware/status      capacidades, transporte activo, peers
    GET  /api/pixel/aware/peers       companeros vistos y su antiguedad
    POST /api/pixel/aware/publish     empieza a anunciarse (beacon)
    POST /api/pixel/aware/discover    escanea companeros durante N segundos
    POST /api/pixel/aware/sync        sincroniza CRDTs con uno o todos
    POST /api/pixel/aware/config      transporte preferido, puerto, tiempos
"""

from __future__ import annotations

import json
import socket
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
DATA_DIR = PROJECT_ROOT / "data" / "aware"
CONFIG_FILE = DATA_DIR / "config.json"
PEERS_FILE = DATA_DIR / "peers.json"

# Puerto del beacon. 41337 no esta registrado por nadie y esta fuera del
# rango efimero habitual de Android, asi que rara vez choca con otra app.
BEACON_PORT = 41337

CONFIG_DEFAULT: dict[str, Any] = {
    "servicio": "daniela",           # nombre del servicio anunciado
    "puerto_http": 8082,             # donde escucha el hub de cada nodo
    "transporte_preferido": "auto",  # auto|aware|p2p|hotspot|lan
    "intervalo_beacon": 3.0,         # segundos entre anuncios
    "peer_vivo_s": 45.0,             # un peer sin senal mas de esto se olvida
    "auto_sync": True,               # sincronizar CRDTs al descubrir
    "auto_sync_s": 60.0,             # cada cuanto reintentar
    "min_bateria_hotspot": 40,       # por debajo de esto no hagas de router
}


# ==========================================================================
#  Utilidades de ejecucion — REGLA DURA: sin shell, sin os.system
# ==========================================================================
def _run(args: list[str], timeout: int = 10) -> str | None:
    """Ejecuta una lista de argumentos. `shell=False` siempre, por diseno."""
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
    """`cmd` existe en Android (service tool) y en Windows (cmd.exe).

    En Windows `cmd connectivity start-tethering` devuelve 0 y una banner:
    un falso positivo que haria creer al modulo que encendio un hotspot.
    Por eso cualquier uso de las herramientas de sistema de Android se
    condiciona a esto, no a que el binario exista.
    """
    for ruta in ("/system/bin/app_process", "/system/build.prop",
                 "/data/data/com.termux"):
        if Path(ruta).exists():
            return True
    return _tiene("getprop") and _tiene("dumpsys")


# ==========================================================================
#  Deteccion de capacidades
# ==========================================================================
def capacidades() -> dict[str, bool]:
    """Que caminos existen en esta maquina. Nunca lanza excepciones."""
    caps = {"aware": False, "p2p": False, "hotspot": False, "lan": True}
    if not es_android():
        # En PC solo existe el camino universal. Decir otra cosa seria una
        # mentira que luego se paga en el movil.
        caps["lan"] = bool(direccion_local())
        return caps

    # 1) caracteristicas declaradas por el sistema (Android)
    feat = _run(["pm", "list", "features"], timeout=12)
    if feat:
        bajo = feat.lower()
        if "android.hardware.wifi.aware" in bajo:
            caps["aware"] = True
        if "android.hardware.wifi.direct" in bajo:
            caps["p2p"] = True
        if "android.hardware.wifi" in bajo or "android.hardware.telephony" in bajo:
            caps["hotspot"] = True

    # 2) utilidades de linea de comandos que expondrian esos caminos
    if _run(["/system/bin/cmd", "wifiaware", "help"], timeout=6):
        caps["aware"] = True
    if _run(["/system/bin/cmd", "wifip2p", "help"], timeout=6):
        caps["p2p"] = True
    if _tiene("termux-wifi-enable"):
        caps["hotspot"] = True

    # 3) una interfaz con IP es condicion suficiente para `lan`
    caps["lan"] = bool(direccion_local())
    return caps


def direccion_local() -> str | None:
    """IP propia sin abrir sockets UDP sucios: se mira la tabla de rutas."""
    s = None
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        # No se envia nada: conectar solo hace que el SO elija interfaz.
        s.connect(("8.8.8.8", 80))
        return s.getsockname()[0]
    except OSError:
        return None
    finally:
        if s is not None:
            try:
                s.close()
            except OSError:
                pass


def broadcast_local() -> str:
    """Direccion de difusion de la subred propia (mejor esfuerzo)."""
    ip = direccion_local()
    if not ip:
        return "255.255.255.255"
    out = _run(["ip", "addr"], timeout=6)
    if out:
        bloque = ""
        for linea in out.splitlines():
            if linea.startswith((" ", "\t")):
                if ip in linea and "/" in linea:
                    bloque = linea
                    break
            else:
                bloque = ""
        if bloque and "/" in bloque:
            try:
                cidr = int(bloque.split("/")[1].split()[0])
                if 0 < cidr <= 32:
                    mascara = (0xFFFFFFFF << (32 - cidr)) & 0xFFFFFFFF
                    partes = [int(x) for x in ip.split(".")]
                    entero = (partes[0] << 24) | (partes[1] << 16) | \
                             (partes[2] << 8) | partes[3]
                    bc = (entero & mascara) | (~mascara & 0xFFFFFFFF)
                    return ".".join(str((bc >> s) & 255) for s in (24, 16, 8, 0))
            except (ValueError, IndexError):
                pass
    return "255.255.255.255"


# ==========================================================================
#  Nodo de malla sin infraestructura
# ==========================================================================
class MallaSinInfra:
    """Descubre companeros por difusion y los entrega a E-11 para sincronizar.

    El beacon es un datagrama UDP firmado por nadie: por eso el payload es
    *solo informativo* (quien soy, donde escucho, cuanta bateria me queda) y
    el intercambio de verdad (las operaciones CRDT) va por HTTP, donde si hay
    autenticacion en el hub. Un atacante en la red local puede ver que existes;
    no puede inyectar estado, porque E-11 rechaza objetos mal formados y
    valida cada operacion antes de fusionarla.
    """

    def __init__(self, node_id: str | None = None) -> None:
        self._lock = threading.RLock()
        self.config: dict[str, Any] = dict(CONFIG_DEFAULT)
        self.nodo = node_id or self._detectar_id()
        self.peers: dict[str, dict[str, Any]] = {}   # url -> info
        self.transporte = "lan"
        self.publicando = False
        self._thread_beacon: threading.Thread | None = None
        self._thread_sync: threading.Thread | None = None
        self.stats: dict[str, Any] = {
            "beacons": 0, "descubrimientos": 0,
            "syncs_ok": 0, "syncs_fallo": 0,
            "ultimo_sync": 0.0,
        }
        self.cargar()

    # ------------------------------------------------------------ identidad
    @staticmethod
    def _detectar_id() -> str:
        import platform
        base = platform.node() or "nodo"
        return "".join(c if c.isalnum() else "-" for c in base).strip("-") or "nodo"

    # ------------------------------------------------------ persistencia
    def cargar(self) -> None:
        try:
            if CONFIG_FILE.exists():
                d = json.loads(CONFIG_FILE.read_text(encoding="utf-8"))
                if isinstance(d, dict):
                    for k, v in d.items():
                        if k in CONFIG_DEFAULT:
                            self.config[k] = v
        except (OSError, ValueError):
            pass
        try:
            if PEERS_FILE.exists():
                p = json.loads(PEERS_FILE.read_text(encoding="utf-8"))
                if isinstance(p, dict):
                    self.peers = {k: v for k, v in p.items()
                                  if isinstance(k, str) and isinstance(v, dict)}
        except (OSError, ValueError):
            pass

    def guardar(self) -> None:
        try:
            DATA_DIR.mkdir(parents=True, exist_ok=True)
            tmp = CONFIG_FILE.with_suffix(".tmp")
            tmp.write_text(json.dumps(self.config, ensure_ascii=False, indent=1),
                           encoding="utf-8")
            tmp.replace(CONFIG_FILE)
            tmp = PEERS_FILE.with_suffix(".tmp")
            tmp.write_text(json.dumps(self.peers, ensure_ascii=False, indent=1),
                           encoding="utf-8")
            tmp.replace(PEERS_FILE)
        except OSError:
            pass

    # ------------------------------------------------------------- energia
    @staticmethod
    def bateria() -> int | None:
        out = _run(["termux-battery-status"], timeout=8)
        if out:
            try:
                d = json.loads(out)
                v = d.get("percentage")
                if isinstance(v, (int, float)):
                    return int(v)
            except ValueError:
                pass
        out = _run(["dumpsys", "battery"], timeout=8)
        if out:
            for linea in out.splitlines():
                if "level" in linea:
                    partes = linea.split(":")
                    if len(partes) == 2:
                        try:
                            return int(partes[1].strip())
                        except ValueError:
                            return None
        return None

    # ----------------------------------------------------------- transporte
    def elegir_transporte(self) -> str:
        """El mejor camino disponible. `auto` nunca se queda sin opcion."""
        pref = str(self.config.get("transporte_preferido", "auto"))
        caps = capacidades()
        if pref in ("aware", "p2p", "hotspot", "lan"):
            return pref if caps.get(pref, pref == "lan") else "lan"
        for t in ("aware", "p2p", "hotspot", "lan"):
            if caps.get(t):
                return t
        return "lan"

    def abrir_hotspot(self) -> dict[str, Any]:
        """Enciende el punto de acceso propio. Solo si hay bateria suficiente.

        Se delega en `cmd` porque es la unica via sin root y sin Termux:API.
        En una build de produccion esto devolvera `no-permitido` y el modulo
        seguira en `lan`. La llamada nunca se hace en modo degradado: primero
        se comprueba la bateria, para no dejar al movil sin red movil.
        """
        if not es_android():
            return {"ok": False, "error": "no es Android",
                    "transporte": "hotspot"}
        b = self.bateria()
        minimo = int(self.config.get("min_bateria_hotspot", 40))
        if b is not None and b < minimo:
            return {"ok": False, "error": f"bateria {b}% < {minimo}%",
                    "transporte": "hotspot"}
        out = _run(["/system/bin/cmd", "connectivity", "start-tethering",
                    "1", "true"], timeout=12)
        return {"ok": out is not None,
                "detalle": (out or "sin salida")[:120],
                "transporte": "hotspot"}

    # --------------------------------------------------------------- beacon
    def _payload(self) -> bytes:
        return json.dumps({
            "servicio": self.config.get("servicio", "daniela"),
            "nodo": self.nodo,
            "transporte": self.transporte,
            "puerto": int(self.config.get("puerto_http", 8082)),
            "bateria": self.bateria(),
            "ts": time.time(),
        }, ensure_ascii=False).encode("utf-8")

    def _bucle_beacon(self) -> None:
        intervalo = float(self.config.get("intervalo_beacon", 3.0))
        while self.publicando:
            try:
                s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
                s.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
                s.bind(("", 0))
                try:
                    s.sendto(self._payload(), (broadcast_local(), BEACON_PORT))
                    with self._lock:
                        self.stats["beacons"] += 1
                finally:
                    s.close()
            except OSError:
                pass
            for _ in range(max(1, int(intervalo * 4))):
                if not self.publicando:
                    return
                time.sleep(0.25)

    def publicar(self) -> dict[str, Any]:
        """Empieza a anunciarse. Idempotente."""
        with self._lock:
            self.transporte = self.elegir_transporte()
            if self.publicando:
                return {"ok": True, "ya_publicando": True,
                        "transporte": self.transporte, "nodo": self.nodo}
            self.publicando = True
            self._thread_beacon = threading.Thread(
                target=self._bucle_beacon, daemon=True, name="aware-beacon")
            self._thread_beacon.start()
            if self.config.get("auto_sync") and not self._thread_sync:
                self._thread_sync = threading.Thread(
                    target=self._bucle_sync, daemon=True, name="aware-sync")
                self._thread_sync.start()
        return {"ok": True, "transporte": self.transporte, "nodo": self.nodo,
                "puerto": self.config.get("puerto_http", 8082)}

    def detener(self) -> dict[str, Any]:
        with self._lock:
            self.publicando = False
        self.guardar()
        return {"ok": True, "publicando": False}

    # ------------------------------------------------------------ descubrir
    def escuchar(self, segundos: float = 5.0) -> int:
        """Abre el oido un rato y devuelve cuantos companeros ha oido."""
        vistos = 0
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            try:
                s.bind(("", BEACON_PORT))
            except OSError:
                return 0
            s.settimeout(0.4)
            fin = time.time() + max(0.5, float(segundos))
            while time.time() < fin:
                try:
                    datos, origen = s.recvfrom(4096)
                except TimeoutError:
                    continue
                except OSError:
                    break
                if self._registrar(datos, (origen or [""])[0]):
                    vistos += 1
            s.close()
        except OSError:
            return vistos
        return vistos

    def _registrar(self, datos: bytes, ip: str) -> bool:
        try:
            d = json.loads(datos.decode("utf-8", "replace"))
        except (ValueError, UnicodeDecodeError):
            return False
        if not isinstance(d, dict):
            return False
        if str(d.get("servicio", "")) != str(self.config.get("servicio", "daniela")):
            return False
        nodo = str(d.get("nodo", "")).strip()
        if not nodo or nodo == self.nodo:
            return False   # no nos descubrimos a nosotros mismos
        puerto = d.get("puerto")
        try:
            puerto = int(puerto)
        except (TypeError, ValueError):
            puerto = 8082
        url = f"http://{ip}:{puerto}"
        with self._lock:
            self.peers[url] = {
                "nodo": nodo,
                "ip": ip,
                "puerto": puerto,
                "transporte": str(d.get("transporte", "lan")),
                "bateria": d.get("bateria"),
                "visto": time.time(),
            }
            self.stats["descubrimientos"] += 1
        return True

    def descubrir(self, segundos: float = 5.0) -> dict[str, Any]:
        """Anuncia y escucha a la vez, que es como se descubre de verdad."""
        fue = self.publicando
        if not fue:
            self.publicar()
        vistos = self.escuchar(segundos)
        if not fue:
            self.detener()
        return {"ok": True, "vistos": vistos, "peers": self.peers_vivos()}

    def peers_vivos(self) -> dict[str, dict[str, Any]]:
        vivos_s = float(self.config.get("peer_vivo_s", 45.0))
        ahora = time.time()
        with self._lock:
            vivos = {u: dict(i) for u, i in self.peers.items()
                     if ahora - float(i.get("visto", 0)) <= vivos_s}
            for _u, i in vivos.items():
                i["hace_s"] = round(ahora - float(i.get("visto", ahora)), 1)
        return vivos

    # ------------------------------------------------------------ sincronía
    def _bucle_sync(self) -> None:
        cada = float(self.config.get("auto_sync_s", 60.0))
        while self.publicando and self.config.get("auto_sync"):
            try:
                if self.peers_vivos():
                    self.sincronizar()
            except Exception:
                pass
            for _ in range(max(1, int(cada * 4))):
                if not self.publicando or not self.config.get("auto_sync"):
                    return
                time.sleep(0.25)

    def sincronizar(self, url: str | None = None) -> dict[str, Any]:
        """Entrega los peers descubiertos a E-11 y deja que converjan.

        Si E-11 no esta instalado no es un error: este modulo sigue siendo
        util como radar de companeros, y lo dice claro en la respuesta.
        """
        try:
            from daniela_mesh import get_instance as get_mesh
        except ImportError:
            return {"ok": False, "error": "E-11 (daniela_mesh) no disponible",
                    "peers": list(self.peers_vivos().keys())}

        mesh = get_mesh()
        objetivos = [url] if url else list(self.peers_vivos().keys())
        if not objetivos:
            return {"ok": False, "error": "sin peers vivos", "peers": []}

        salida: dict[str, Any] = {"ok": True, "nodo": self.nodo, "peers": {}}
        for u in objetivos:
            try:
                mesh.add_peer(u)
                r = mesh.sincronizar(u)
                with self._lock:
                    if r and r.get("ok"):
                        self.stats["syncs_ok"] += 1
                        self.stats["ultimo_sync"] = time.time()
                    else:
                        self.stats["syncs_fallo"] += 1
                salida["peers"][u] = r
                if not (r or {}).get("ok"):
                    salida["ok"] = False
            except Exception as e:
                with self._lock:
                    self.stats["syncs_fallo"] += 1
                salida["peers"][u] = {"ok": False, "error": str(e)[:160]}
                salida["ok"] = False
        self.guardar()
        return salida

    # ------------------------------------------------------------- estado
    def estado(self) -> dict[str, Any]:
        with self._lock:
            return {
                "ok": True,
                "nodo": self.nodo,
                "transporte": self.transporte,
                "publicando": self.publicando,
                "ip_local": direccion_local(),
                "broadcast": broadcast_local(),
                "puerto_beacon": BEACON_PORT,
                "capacidades": capacidades(),
                "bateria": self.bateria(),
                "peers": self.peers_vivos(),
                "config": dict(self.config),
                "stats": dict(self.stats),
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
_INSTANCIA: MallaSinInfra | None = None
_LOCK = threading.Lock()


def get_instance(node_id: str | None = None) -> MallaSinInfra:
    global _INSTANCIA
    with _LOCK:
        if _INSTANCIA is None:
            _INSTANCIA = MallaSinInfra(node_id)
        return _INSTANCIA


# ==========================================================================
#  Rutas Flask
# ==========================================================================
def register_aware_routes(app) -> None:
    if Flask is None:
        return

    def m() -> MallaSinInfra:
        return get_instance()

    @app.route("/api/pixel/aware/status", methods=["GET"], endpoint="aware__status")
    def _status():
        return jsonify(m().estado())

    @app.route("/api/pixel/aware/peers", methods=["GET"], endpoint="aware__peers")
    def _peers():
        return jsonify({"ok": True, "peers": m().peers_vivos()})

    @app.route("/api/pixel/aware/publish", methods=["POST"], endpoint="aware__publish")
    def _publish():
        d = request.get_json(silent=True) or {}
        if d.get("stop"):
            return jsonify(m().detener())
        if d.get("node_id"):
            m().nodo = str(d["node_id"])[:64]
        return jsonify(m().publicar())

    @app.route("/api/pixel/aware/discover", methods=["POST"], endpoint="aware__discover")
    def _discover():
        d = request.get_json(silent=True) or {}
        try:
            seg = float(d.get("segundos", 5.0))
        except (TypeError, ValueError):
            seg = 5.0
        seg = min(30.0, max(0.5, seg))
        return jsonify(m().descubrir(seg))

    @app.route("/api/pixel/aware/sync", methods=["POST"], endpoint="aware__sync")
    def _sync():
        d = request.get_json(silent=True) or {}
        url = d.get("url")
        res = m().sincronizar(str(url) if url else None)
        return jsonify(res), (200 if res.get("ok") else 502)

    @app.route("/api/pixel/aware/config", methods=["POST"], endpoint="aware__config")
    def _config():
        d = request.get_json(silent=True) or {}
        return jsonify({"ok": True, "config": m().configurar(**d)})

    print("[WiFi Aware] Routes registered: /api/pixel/aware/* "
          "(status, peers, publish, discover, sync, config)")


# --------------------------------------------------------------------------
#  Demo
# --------------------------------------------------------------------------
def _demo() -> None:
    print("=" * 68)
    print(" WIFI AWARE (E-20) — malla sin infraestructura")
    print("=" * 68)

    caps = capacidades()
    print("capacidades :", ", ".join(f"{k}={v}" for k, v in caps.items()))
    print("ip local    :", direccion_local())
    print("broadcast   :", broadcast_local())

    m = MallaSinInfra("demo-pc")
    m.transporte = m.elegir_transporte()
    print("transporte  :", m.transporte)

    print("\n-- beacon: dos nodos anunciandose en la misma subred --")
    # Un segundo nodo real en otro proceso seria ideal, pero para la demo
    # simulamos el datagrama entrante: es exactamente el mismo camino de
    # codigo (``_registrar``) que recorre un beacon de verdad.
    otro = MallaSinInfra("pixel-android")
    otro.config["servicio"] = "daniela"

    m.config["peer_vivo_s"] = 45.0
    m._registrar(otro._payload(), "192.168.1.133")   # noqa: SLF001
    m._registrar(b"no es json", "192.168.1.50")      # noqa: SLF001
    m._registrar(m._payload(), "192.168.1.133")      # noqa: SLF001 - el mismo

    vivos = m.peers_vivos()
    print(f"   peers vivos: {len(vivos)}")
    for u, i in vivos.items():
        print(f"   - {i['nodo']:<15} {u:<28} bateria={i['bateria']}")

    print("\n-- basura y auto-descubrimiento --")
    print("   payload no JSON descartado :", len(vivos) == 1)
    print("   no se descubre a si mismo  :", all(
        i["nodo"] != "demo-pc" for i in vivos.values()))

    print("\n-- expiracion de peers --")
    m.config["peer_vivo_s"] = 0.0
    print("   con peer_vivo_s=0 expiran  :", len(m.peers_vivos()) == 0)
    m.config["peer_vivo_s"] = 45.0

    print("\n-- sincronizacion CRDT (E-11) --")
    sync = m.sincronizar()
    print("   ok      :", sync.get("ok"))
    print("   detalle :", str(sync.get("error", sync.get("peers")))[:90])

    print("\n-- hotspot con bateria baja --")
    m.config["min_bateria_hotspot"] = 999
    print("   ", m.abrir_hotspot())
    m.config["min_bateria_hotspot"] = 40

    print("=" * 68)


if __name__ == "__main__":
    _demo()
