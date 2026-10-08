#!/usr/bin/env python3
"""
daniela_mesh.py — E-11 · Daniela Mesh: multi-dispositivo offline-first
=====================================================================

Daniela deja de "vivir en el PC y reflejarse en el Pixel". Con la malla vive
**simultaneamente** en todos los nodos: cada uno es autonomo, acepta escrituras
sin red, y converge cuando vuelve a haber conexion. Sin servidor central, sin
cuota, $0/mes.

Nucleo CRDT (tipos replicados libres de conflicto)
--------------------------------------------------
* **LWW-Register**  — ultimo gana, con reloj logico hibrido (HLC) y desempate
  por node_id. Para escalares: contexto actual, ultima ubicacion conocida...
* **OR-Set**        — conjunto observed-remove. Para colecciones: tags NFC
  vistos, peers conocidos, episodios pendientes.
* **PN-Counter**    — contador por nodo (solo crece). Para metricas: pasos,
  caidas, incidentes.

Toda escritura genera una **operacion** con id unico `nodo:secuencia`. Los ops
son idempotentes y conmutativos: aplicarlos en cualquier orden produce el
mismo estado. La sincronizacion es anti-entropia: cada nodo entrega su cola de
ops y recibe la del otro.

Seguridad
---------
* Cero `os.system()` / `shell=True` — todo pasa por `safe_exec` (listas de args).
* El transporte es HTTP propio; no se ejecuta nada que llegue por la red.
* Los ops solo contienen datos (str/int/float/bool/listas/dicts simples);
  cualquier otro tipo se rechaza antes de entrar al estado.

Rutas
-----
    GET  /api/mesh/status                 estado del nodo y de la malla
    GET  /api/mesh/state                  estado CRDT materializado
    POST /api/mesh/set                    escribe un LWW-Register
    GET  /api/mesh/get/<path:key>         lee una clave
    POST /api/mesh/counter/<name>         incrementa un PN-Counter
    GET  /api/mesh/peers                  lista de peers
    POST /api/mesh/peers                  anade / quita un peer
    POST /api/mesh/sync                   anti-entropia (recibe y entrega ops)
    POST /api/mesh/control                start / stop / autosync / save
"""

from __future__ import annotations

import json
import os
import socket
import threading
import time
from pathlib import Path
from typing import Any

# --------------------------------------------------------------------------
# Dependencias opcionales
# --------------------------------------------------------------------------
try:
    from flask import Flask, jsonify, request
except ImportError:  # pragma: no cover
    Flask = None  # type: ignore
    jsonify = None  # type: ignore
    request = None  # type: ignore

try:
    from safe_exec import run_code
except ImportError:  # degrada: el modulo arranca igual
    run_code = None  # type: ignore

try:
    import requests
except ImportError:
    requests = None  # type: ignore


# --------------------------------------------------------------------------
# Constantes
# --------------------------------------------------------------------------
PROJECT_ROOT = Path(__file__).resolve().parent
DATA_DIR = PROJECT_ROOT / "data" / "mesh"
STATE_FILE = DATA_DIR / "state.json"
PEERS_FILE = DATA_DIR / "peers.json"

T_LWW = "lww"
T_ORSET = "orset"
T_PN = "pn"

AUTOSYNC_INTERVAL_S = 30.0
SYNC_TIMEOUT_S = 6.0
MAX_OPS_KEPT = 5000  # la cola de ops se poda para no crecer sin limite
MAX_SEEN_OIDS = 20000

# Tipos permitidos dentro del estado (nada de objetos ejecutables)
_SCALARS = (str, int, float, bool, type(None))


def _es_dato_seguro(v: Any, profundidad: int = 0) -> bool:
    """Solo acepta JSON-plano. Evita colar objetos raros por la red."""
    if profundidad > 6:
        return False
    if isinstance(v, _SCALARS):
        # str con limite razonable para que un peer no infle el estado
        return not (isinstance(v, str) and len(v) > 100_000)
    if isinstance(v, list):
        return len(v) <= 10_000 and all(_es_dato_seguro(x, profundidad + 1) for x in v)
    if isinstance(v, dict):
        return len(v) <= 10_000 and all(
            isinstance(k, str) and _es_dato_seguro(x, profundidad + 1) for k, x in v.items()
        )
    return False


# ==========================================================================
#  Reloj logico hibrido (HLC)
# ==========================================================================
class HLC:
    """Reloj logico hibrido: tiempo fisico + contador + nodo.

    Ordena eventos aunque los relojes de los dispositivos esten desfasados,
    que es exactamente el caso de un PC y un movil que se sincronizan poco.
    """

    def __init__(self, node_id: str) -> None:
        self.node_id = node_id
        self._phys = 0
        self._count = 0
        self._lock = threading.Lock()

    def now(self) -> list[Any]:
        """Devuelve una marca [ms, contador, nodo] y avanza el reloj."""
        with self._lock:
            phys = int(time.time() * 1000)
            if phys > self._phys:
                self._phys, self._count = phys, 0
            else:
                self._count += 1
            return [self._phys, self._count, self.node_id]

    def observe(self, marca: Any) -> None:
        """Ajusta el reloj local al recibir una marca remota."""
        if not isinstance(marca, list) or len(marca) != 3:
            return
        try:
            phys, count = int(marca[0]), int(marca[1])
        except (TypeError, ValueError):
            return
        with self._lock:
            local = self._phys
            if phys > local:
                self._phys, self._count = phys, count
            elif phys == local:
                self._count = max(self._count, count) + 1
            else:
                self._count += 1

    @staticmethod
    def mayor(a: Any, b: Any) -> bool:
        """True si la marca `a` es estrictamente posterior a `b`."""
        if not isinstance(a, list) or len(a) != 3:
            return False
        if not isinstance(b, list) or len(b) != 3:
            return True
        try:
            if int(a[0]) != int(b[0]):
                return int(a[0]) > int(b[0])
            if int(a[1]) != int(b[1]):
                return int(a[1]) > int(b[1])
        except (TypeError, ValueError):
            return False
        return str(a[2]) > str(b[2])  # desempate determinista por nodo


# ==========================================================================
#  Nodo de la malla
# ==========================================================================
class MeshNode:
    """Estado CRDT de un nodo + cola de operaciones + anti-entropia."""

    def __init__(self, node_id: str | None = None) -> None:
        # Si el llamador pasa un node_id explicito manda esa identidad: ni el
        # estado persistido ni el hostname pueden pisarla. Si no, se hereda del
        # disco (reanudar) y, a falta de disco, se autodetecta.
        self._node_id_fijado = node_id is not None
        self.node_id = node_id or self._detectar_node_id()
        self.clock = HLC(self.node_id)
        self._lock = threading.RLock()

        # Estado CRDT
        self.lww: dict[str, dict[str, Any]] = {}  # key -> {v, h}
        self.orset: dict[str, dict[str, Any]] = {}  # key -> {adds:{tag:elem}, rm:[tags]}
        self.pn: dict[str, dict[str, str]] = {}  # key -> {node_id: int}

        # Cola de ops (log) y deduplicacion
        self.ops: list[dict[str, Any]] = []
        self._seen: set = set()
        self._seq = 0

        self.peers: list[str] = []
        self.autosync_on = False
        self._thread: threading.Thread | None = None
        self.stats = {
            "ops_aplicados": 0,
            "ops_generados": 0,
            "syncs_ok": 0,
            "syncs_fallidos": 0,
            "ultimo_sync": None,
            "arrancado": time.time(),
        }

        DATA_DIR.mkdir(parents=True, exist_ok=True)
        self.cargar()

    # ---------------------------------------------------------------- identidad
    @staticmethod
    def _detectar_node_id() -> str:
        try:
            host = socket.gethostname().lower()
        except Exception:
            host = "nodo"
        plat = (
            "android"
            if os.environ.get("PREFIX", "").startswith("/data/data/com.termux")
            else os.name
        )
        return f"{host}-{plat}"

    # ------------------------------------------------------------ ops basicos
    def _nuevo_oid(self) -> str:
        self._seq += 1
        return f"{self.node_id}:{self._seq}"

    def _emitir(self, op: dict[str, Any]) -> dict[str, Any]:
        """Sella una op local, la aplica y la encola para replicar."""
        op["oid"] = self._nuevo_oid()
        op["src"] = self.node_id
        with self._lock:
            self.ops.append(op)
            # OJO: no anadir el oid a _seen aqui. De eso se encarga _aplicar(),
            # que es quien decide si la op es nueva. Si lo marcaramos antes,
            # el nodo rechazaria sus propias escrituras por "duplicadas".
            if len(self.ops) > MAX_OPS_KEPT:
                self.ops = self.ops[-MAX_OPS_KEPT:]
            self.stats["ops_generados"] += 1
            self._aplicar(op)
        return op

    # --------------------------------------------------------------- escritura
    def set_lww(self, key: str, value: Any) -> bool:
        if not isinstance(key, str) or not key or len(key) > 512:
            return False
        if not _es_dato_seguro(value):
            return False
        self._emitir({"t": T_LWW, "k": key, "v": value, "h": self.clock.now()})
        return True

    def orset_add(self, key: str, elem: Any) -> bool:
        if not isinstance(key, str) or not key or len(key) > 512:
            return False
        if not _es_dato_seguro(elem):
            return False
        tag = self._nuevo_oid()
        self._emitir({"t": T_ORSET, "k": key, "op": "add", "v": elem, "tag": tag})
        return True

    def orset_remove(self, key: str, elem: Any) -> bool:
        """OR-Set: solo se pueden borrar los tags efectivamente observados."""
        with self._lock:
            adds = self.orset.get(key, {}).get("adds", {})
            rm = set(self.orset.get(key, {}).get("rm", []))
            tags = [t for t, e in adds.items() if e == elem and t not in rm]
        if not tags:
            return False
        self._emitir({"t": T_ORSET, "k": key, "op": "rm", "tags": tags})
        return True

    def pn_add(self, key: str, delta: int = 1) -> bool:
        if not isinstance(key, str) or not key or len(key) > 512:
            return False
        try:
            delta = int(delta)
        except (TypeError, ValueError):
            return False
        if delta == 0 or abs(delta) > 1_000_000:
            return False
        self._emitir({"t": T_PN, "k": key, "op": "inc", "v": delta})
        return True

    # ------------------------------------------------------------------ aplicar
    def _aplicar(self, op: dict[str, Any]) -> bool:
        """Aplica una op de forma idempotente. True si aporta algo nuevo."""
        oid = op.get("oid")
        if not oid:
            return False
        if oid in self._seen:
            return False
        if not _es_dato_seguro(op.get("v")):
            return False

        t, k = op.get("t"), op.get("k")
        if not isinstance(k, str) or not k:
            return False

        if t == T_LWW:
            h = op.get("h")
            if isinstance(h, list):
                self.clock.observe(h)
            actual = self.lww.get(k)
            if actual is None or HLC.mayor(h, actual.get("h")):
                self.lww[k] = {"v": op.get("v"), "h": h}

        elif t == T_ORSET:
            slot = self.orset.setdefault(k, {"adds": {}, "rm": []})
            if op.get("op") == "add":
                tag = op.get("tag")
                if isinstance(tag, str):
                    slot["adds"][tag] = op.get("v")
            elif op.get("op") == "rm":
                rm = set(slot["rm"])
                for tag in op.get("tags", []) or []:
                    if isinstance(tag, str):
                        rm.add(tag)
                slot["rm"] = sorted(rm)[-MAX_OPS_KEPT:]
            else:
                return False

        elif t == T_PN:
            try:
                delta = int(op.get("v", 0))
            except (TypeError, ValueError):
                return False
            slot = self.pn.setdefault(k, {})
            src = op.get("src") or self.node_id
            slot[src] = int(slot.get(src, 0)) + delta
            self.pn[k] = slot

        else:
            return False

        self._seen.add(oid)
        if len(self._seen) > MAX_SEEN_OIDS:
            self._seen = set(list(self._seen)[-MAX_SEEN_OIDS:])
        self.stats["ops_aplicados"] += 1
        return True

    def fusionar(self, ops: list[dict[str, Any]]) -> int:
        """Anti-entropia: aplica ops remotos. Devuelve cuantos eran nuevos."""
        if not isinstance(ops, list):
            return 0
        nuevos = 0
        with self._lock:
            for op in ops:
                if not isinstance(op, dict):
                    continue
                if self._aplicar(op):
                    self.ops.append(op)
                    nuevos += 1
            if len(self.ops) > MAX_OPS_KEPT:
                self.ops = self.ops[-MAX_OPS_KEPT:]
        return nuevos

    def ops_desde(self, desde: int) -> list[dict[str, Any]]:
        with self._lock:
            if desde < 0 or desde > len(self.ops):
                return list(self.ops)
            return list(self.ops[desde:])

    # ------------------------------------------------------------- materializar
    def estado(self) -> dict[str, Any]:
        with self._lock:
            out: dict[str, Any] = {
                "lww": {k: v.get("v") for k, v in self.lww.items()},
                "orset": {
                    k: list(
                        {
                            json.dumps(e, sort_keys=True): e
                            for t, e in s.get("adds", {}).items()
                            if t not in set(s.get("rm", []))
                        }.values()
                    )
                    for k, s in self.orset.items()
                },
                "pn": {k: sum(int(x) for x in v.values()) for k, v in self.pn.items()},
            }
            return out

    def leer(self, key: str) -> tuple[bool, Any]:
        with self._lock:
            if key in self.lww:
                return True, self.lww[key].get("v")
            if key in self.pn:
                return True, sum(int(x) for x in self.pn[key].values())
            if key in self.orset:
                s = self.orset[key]
                rm = set(s.get("rm", []))
                vals = {
                    json.dumps(e, sort_keys=True): e
                    for t, e in s.get("adds", {}).items()
                    if t not in rm
                }
                return True, list(vals.values())
            return False, None

    # ----------------------------------------------------------------- peers
    def add_peer(self, url: str) -> bool:
        if not isinstance(url, str):
            return False
        url = url.strip().rstrip("/")
        if not url.startswith(("http://", "https://")):
            return False
        if url == f"http://{self.node_id}":
            return False
        with self._lock:
            if url not in self.peers:
                self.peers.append(url)
                self.guardar_peers()
                return True
        return False

    def remove_peer(self, url: str) -> bool:
        with self._lock:
            if url in self.peers:
                self.peers.remove(url)
                self.guardar_peers()
                return True
        return False

    # ------------------------------------------------------------ persistencia
    def guardar(self) -> None:
        DATA_DIR.mkdir(parents=True, exist_ok=True)
        with self._lock:
            payload = {
                "node_id": self.node_id,
                "seq": self._seq,
                "lww": self.lww,
                "orset": self.orset,
                "pn": self.pn,
                "ops": self.ops[-MAX_OPS_KEPT:],
                "seen": list(self._seen)[-MAX_SEEN_OIDS:],
            }
        tmp = STATE_FILE.with_suffix(".tmp")
        tmp.write_text(json.dumps(payload, ensure_ascii=False, indent=1), encoding="utf-8")
        tmp.replace(STATE_FILE)  # escritura atomica

    def cargar(self) -> None:
        if not STATE_FILE.exists():
            return
        try:
            d = json.loads(STATE_FILE.read_text(encoding="utf-8"))
            if not isinstance(d, dict):
                return
            with self._lock:
                persistido = d.get("node_id")
                if self._node_id_fijado:
                    # Identidad impuesta por el llamador. Si lo que hay en disco
                    # es de OTRO nodo, no lo adoptamos: sus oids ("nodo:seq")
                    # colisionarian con los nuestros y el estado seria basura.
                    # Arrancamos limpio en vez de mezclar dos identidades.
                    if persistido and persistido != self.node_id:
                        return
                else:
                    self.node_id = persistido or self.node_id
                    self.clock.node_id = self.node_id
                self._seq = int(d.get("seq") or 0)
                self.lww = d.get("lww") or {}
                self.orset = d.get("orset") or {}
                self.pn = d.get("pn") or {}
                self.ops = d.get("ops") or []
                self._seen = set(d.get("seen") or [])
        except Exception:
            pass  # estado corrupto -> empezar limpio

    def guardar_peers(self) -> None:
        DATA_DIR.mkdir(parents=True, exist_ok=True)
        tmp = PEERS_FILE.with_suffix(".tmp")
        tmp.write_text(json.dumps(self.peers, ensure_ascii=False, indent=1), encoding="utf-8")
        tmp.replace(PEERS_FILE)

    def cargar_peers(self) -> None:
        if not PEERS_FILE.exists():
            return
        try:
            p = json.loads(PEERS_FILE.read_text(encoding="utf-8"))
            if isinstance(p, list):
                self.peers = [x for x in p if isinstance(x, str)]
        except Exception:
            pass

    # ----------------------------------------------------------- sincronizacion
    def sincronizar(self, peer: str | None = None) -> dict[str, Any]:
        """Anti-entropia con uno o todos los peers."""
        if requests is None:
            return {"ok": False, "error": "requests no instalado"}
        objetivos = [peer] if peer else list(self.peers)
        resultado: dict[str, Any] = {"ok": True, "peers": {}}

        for p in objetivos:
            if not p:
                continue
            try:
                enviados = len(self.ops)
                r = requests.post(
                    f"{p}/api/mesh/sync",
                    json={"node_id": self.node_id, "ops": self.ops_desde(0)},
                    timeout=SYNC_TIMEOUT_S,
                )
                if r.status_code != 200:
                    raise RuntimeError(f"HTTP {r.status_code}")
                remotos = (r.json() or {}).get("ops") or []
                nuevos = self.fusionar(remotos)
                with self._lock:
                    self.stats["syncs_ok"] += 1
                    self.stats["ultimo_sync"] = time.time()
                resultado["peers"][p] = {
                    "ok": True,
                    "enviados": enviados,
                    "recibidos": nuevos,
                }
            except Exception as e:
                with self._lock:
                    self.stats["syncs_fallidos"] += 1
                resultado["peers"][p] = {"ok": False, "error": str(e)[:160]}
                resultado["ok"] = False

        self.guardar()
        return resultado

    # ------------------------------------------------------------- autosync
    def _bucle_autosync(self) -> None:
        while self.autosync_on:
            time.sleep(AUTOSYNC_INTERVAL_S)
            if not self.autosync_on:
                break
            try:
                if self.peers:
                    self.sincronizar()
            except Exception:
                continue

    def start(self, autosync: bool = True) -> None:
        self.cargar_peers()
        if autosync and not self.autosync_on:
            self.autosync_on = True
            self._thread = threading.Thread(
                target=self._bucle_autosync, daemon=True, name="mesh-autosync"
            )
            self._thread.start()

    def stop(self) -> None:
        self.autosync_on = False
        self.guardar()

    # ----------------------------------------------------------------- estado
    def resumen(self) -> dict[str, Any]:
        with self._lock:
            return {
                "node_id": self.node_id,
                "peers": list(self.peers),
                "autosync": self.autosync_on,
                "intervalo_s": AUTOSYNC_INTERVAL_S,
                "ops_en_cola": len(self.ops),
                "claves": {
                    "lww": len(self.lww),
                    "orset": len(self.orset),
                    "pn": len(self.pn),
                },
                "requests_disponible": requests is not None,
                "safe_exec_disponible": run_code is not None,
                "stats": dict(self.stats),
                "estado_path": str(STATE_FILE),
            }


# ==========================================================================
#  Singleton
# ==========================================================================
_instancia: MeshNode | None = None
_lock = threading.Lock()


def get_instance() -> MeshNode:
    global _instancia
    if _instancia is None:
        with _lock:
            if _instancia is None:
                _instancia = MeshNode()
    return _instancia


# ==========================================================================
#  Rutas Flask
# ==========================================================================
def register_mesh_routes(app) -> MeshNode | None:
    """Registra las rutas de la malla. Devuelve el nodo o None si falla."""
    if Flask is None or app is None:
        return None
    try:
        node = get_instance()

        @app.route("/api/mesh/status", methods=["GET"])
        def mesh_status():
            return jsonify({"ok": True, "node": node.resumen()})

        @app.route("/api/mesh/state", methods=["GET"])
        def mesh_state():
            return jsonify({"ok": True, "node_id": node.node_id, "state": node.estado()})

        @app.route("/api/mesh/set", methods=["POST"])
        def mesh_set():
            d = request.get_json(silent=True) or {}
            key, val = d.get("key"), d.get("value")
            if not isinstance(key, str) or not key:
                return jsonify({"ok": False, "error": "falta key"}), 400
            if not node.set_lww(key, val):
                return jsonify({"ok": False, "error": "valor no permitido"}), 400
            node.guardar()
            return jsonify({"ok": True, "key": key, "value": val})

        @app.route("/api/mesh/get/<path:key>", methods=["GET"])
        def mesh_get(key):
            encontrado, valor = node.leer(key)
            return jsonify({"ok": encontrado, "key": key, "value": valor})

        @app.route("/api/mesh/counter/<name>", methods=["POST"])
        def mesh_counter(name):
            d = request.get_json(silent=True) or {}
            try:
                delta = int(d.get("delta", 1))
            except (TypeError, ValueError):
                return jsonify({"ok": False, "error": "delta invalido"}), 400
            if not node.pn_add(name, delta):
                return jsonify({"ok": False, "error": "delta fuera de rango"}), 400
            node.guardar()
            return jsonify({"ok": True, "name": name, "total": node.leer(name)[1]})

        @app.route("/api/mesh/peers", methods=["GET", "POST"])
        def mesh_peers():
            if request.method == "GET":
                return jsonify({"ok": True, "peers": node.peers})
            d = request.get_json(silent=True) or {}
            url, accion = d.get("url"), (d.get("action") or "add")
            if not isinstance(url, str):
                return jsonify({"ok": False, "error": "falta url"}), 400
            if accion == "remove":
                ok = node.remove_peer(url)
            elif accion == "sync":
                ok = node.add_peer(url)
                return jsonify({"ok": ok, "sync": node.sincronizar(url)})
            else:
                ok = node.add_peer(url)
            return jsonify({"ok": ok, "peers": node.peers})

        @app.route("/api/mesh/sync", methods=["POST"])
        def mesh_sync():
            """Anti-entropia: recibe ops y devuelve los propios."""
            d = request.get_json(silent=True) or {}
            remotos = d.get("ops") or []
            if not isinstance(remotos, list):
                return jsonify({"ok": False, "error": "ops debe ser lista"}), 400
            nuevos = node.fusionar(remotos)
            if nuevos:
                node.guardar()
            return jsonify(
                {
                    "ok": True,
                    "node_id": node.node_id,
                    "recibidos_nuevos": nuevos,
                    "ops": node.ops_desde(0),
                }
            )

        @app.route("/api/mesh/control", methods=["POST"])
        def mesh_control():
            d = request.get_json(silent=True) or {}
            accion = d.get("action") or "start"
            if accion == "start":
                node.start(autosync=bool(d.get("autosync", True)))
            elif accion == "stop":
                node.stop()
            elif accion == "autosync":
                on = bool(d.get("on", True))
                node.start(autosync=True) if on else node.stop()
            elif accion == "save":
                node.guardar()
            elif accion == "sync":
                return jsonify({"ok": True, "sync": node.sincronizar(d.get("peer"))})
            else:
                return jsonify({"ok": False, "error": f"accion desconocida: {accion}"}), 400
            return jsonify({"ok": True, "node": node.resumen()})

        print(
            "[Mesh] Routes registered: /api/mesh/* "
            "(status, state, set, get, counter, peers, sync, control)"
        )
        return node

    except Exception as e:
        print(f"[Mesh] No se pudo registrar: {e}")
        return None


# ==========================================================================
#  Demo / pruebas
# ==========================================================================
def _demo() -> None:
    print("=" * 68)
    print(" DANIELA MESH (E-11) — prueba de convergencia")
    print("=" * 68)

    a = MeshNode("pc-win")
    b = MeshNode("pixel-android")

    # 1. Escrituras concurrentes SIN red (cada uno por su lado)
    a.set_lww("contexto", "en_casa")
    b.set_lww("contexto", "en_vehiculo")
    a.pn_add("pasos", 120)
    b.pn_add("pasos", 340)
    a.orset_add("tags_nfc", "cocina")
    b.orset_add("tags_nfc", "coche")

    print(f"A ve contexto = {a.leer('contexto')[1]!r}")
    print(f"B ve contexto = {b.leer('contexto')[1]!r}   <- divergen, es correcto")

    # 2. Llega la red -> anti-entropia en ambos sentidos
    b.fusionar(a.ops_desde(0))
    a.fusionar(b.ops_desde(0))

    print("\n-- tras sincronizar --")
    print(
        f"A: contexto={a.leer('contexto')[1]!r}  pasos={a.leer('pasos')[1]}  tags={a.leer('tags_nfc')[1]}"
    )
    print(
        f"B: contexto={b.leer('contexto')[1]!r}  pasos={b.leer('pasos')[1]}  tags={b.leer('tags_nfc')[1]}"
    )

    ok = (
        a.leer("contexto")[1] == b.leer("contexto")[1]
        and a.leer("pasos")[1] == b.leer("pasos")[1] == 460
        and sorted(a.leer("tags_nfc")[1]) == sorted(b.leer("tags_nfc")[1]) == ["coche", "cocina"]
    )
    print(f"\nCONVERGEN: {'SI' if ok else 'NO'}")

    # 3. Idempotencia: reenviar los mismos ops no cambia nada
    antes = a.leer("pasos")[1]
    a.fusionar(b.ops_desde(0))
    a.fusionar(b.ops_desde(0))
    print(f"IDEMPOTENTE: {'SI' if a.leer('pasos')[1] == antes else 'NO'} ({a.leer('pasos')[1]})")

    # 4. Seguridad: rechaza valores no serializables
    print(f"RECHAZA OBJETOS: {'SI' if not a.set_lww('x', object()) else 'NO'}")
    print("=" * 68)


if __name__ == "__main__":
    _demo()
