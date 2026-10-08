#!/usr/bin/env python3
"""
NFC Physical Automation — el mundo como interfaz (E-08 / Fase 7)
================================================================
Automatizar hoy requiere sacar el movil y hablarle. A veces eso no toca:
conduciendo, en una reunion, con las manos ocupadas. Un tag NFC de 0,20 EUR
resuelve eso: acercas el movil y ocurre algo.

    tag en la mesita  -> 'modo noche'   (luces fuera, alarma puesta, silencio)
    tag en el coche   -> 'modo conduccion' (GPS, musica, respuesta por voz)
    tag en la entrada -> 'llegue a casa'

Daniela tambien puede ESCRIBIR tags para compartir escenas: grabas un tag,
lo pegas donde quieras, y cualquiera que lo toque ejecuta esa escena.

FORMATO DEL PAYLOAD
-------------------
    daniela:scene:<nombre>     ejecuta una escena registrada
    daniela:event:<TIPO>       emite un evento en el bus del Mobile Core
    daniela:url:<url>          abre una URL
    <cualquier otra cosa>      se trata como texto libre y solo se notifica

SEGURIDAD — REGLA DURA
----------------------
Un tag NUNCA ejecuta comandos de shell. Solo puede contener pasos
estructurados de una allowlist: scene, event, ir_macro, notify, toast,
speak, url, set_home, blackbox. Quien tenga acceso fisico al tag no
consigue ejecucion de codigo. Ademas hay anti-rebote: el mismo tag no
vuelve a disparar dentro de DEBOUNCE_S segundos.

LECTOR: `termux-nfc -r` bloquea hasta que acercan un tag y escupe JSON.
Un hilo en segundo plano lo relanza en bucle, asi que Daniela esta siempre
a la escucha sin consumir bateria (es el hardware NFC el que espera).

Seguridad: todo comando pasa por safe_exec. 0 os.system, 0 shell=True.

Rutas:
  GET  /api/pixel/nfc/status             — estado del lector
  POST /api/pixel/nfc/start              — arranca el lector en background
  POST /api/pixel/nfc/stop               — lo detiene
  POST /api/pixel/nfc/read               — lectura bloqueante de un tag
  POST /api/pixel/nfc/write              — escribe un tag
  GET  /api/pixel/nfc/tags               — registro de tags
  POST /api/pixel/nfc/tags               — asocia un tag a una accion
  GET  /api/pixel/nfc/scenes             — escenas disponibles
  POST /api/pixel/nfc/scenes             — crea o ejecuta una escena
  POST /api/pixel/nfc/dispatch           — simula un tag (tests / web / QR)

Coste: $0/mes — tags NTAG213 (~0,20 EUR) + Termux:API
"""

from __future__ import annotations

import json
import os
import re
import threading
import time
from dataclasses import asdict, dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any

from safe_exec import run_code, run_json

PROJECT_ROOT = Path(__file__).resolve().parent
STATE_DIR = PROJECT_ROOT / "data" / "nfc"
TAGS_FILE = STATE_DIR / "tags.json"
SCENES_FILE = STATE_DIR / "scenes.json"

DEBOUNCE_S = 3.0          # el mismo tag no redispara antes de esto
READ_TIMEOUT = 60         # termux-nfc -r espera hasta 60 s por tag
MAX_LOG = 200

PAYLOAD_RE = re.compile(r"^daniela:(scene|event|url):(.+)$", re.IGNORECASE)

# Allowlist de tipos de paso. Nada de shell.
STEP_TYPES = ("scene", "event", "ir_macro", "notify", "toast", "speak",
              "url", "set_home", "blackbox", "wait")

_instance: NFCAutomation | None = None
_instance_lock = threading.Lock()


def is_termux() -> bool:
    return os.path.exists("/data/data/com.termux/files/usr/bin")


def _now() -> str:
    return datetime.now().isoformat(timespec="seconds")


@dataclass
class TagBinding:
    tag_id: str
    action: str                       # scene:<n> | event:<T> | url:<u>
    label: str = ""
    room: str = ""
    created: str = field(default_factory=_now)
    hits: int = 0
    last_seen: str | None = None
    enabled: bool = True


@dataclass
class Scene:
    name: str
    steps: list[dict[str, Any]] = field(default_factory=list)
    note: str = ""
    created: str = field(default_factory=_now)
    runs: int = 0


class NFCAutomation:
    """Lector NFC + escenas, con dispatch seguro por allowlist."""

    def __init__(self) -> None:
        self.tags: dict[str, TagBinding] = {}
        self.scenes: dict[str, Scene] = {}
        self.running = False
        self._thread: threading.Thread | None = None
        self._stop = threading.Event()
        self._last_hit: dict[str, float] = {}
        self.log: list[dict[str, Any]] = []
        self.reads = 0
        self.writes = 0
        self.dispatches = 0
        self.last_error: str | None = None
        self._lock = threading.Lock()
        self._load()
        self._seed_scenes()

    # ── persistencia ─────────────────────────────────────────

    def _load(self) -> None:
        try:
            STATE_DIR.mkdir(parents=True, exist_ok=True)
        except Exception as e:  # noqa: BLE001
            self.last_error = f"mkdir: {e}"
        try:
            if TAGS_FILE.exists():
                data = json.loads(TAGS_FILE.read_text(encoding="utf-8"))
                for tid, t in data.get("tags", {}).items():
                    self.tags[tid] = TagBinding(**t)
        except Exception as e:  # noqa: BLE001
            self.last_error = f"load tags: {e}"
        try:
            if SCENES_FILE.exists():
                data = json.loads(SCENES_FILE.read_text(encoding="utf-8"))
                for name, s in data.get("scenes", {}).items():
                    self.scenes[name] = Scene(**s)
        except Exception as e:  # noqa: BLE001
            self.last_error = f"load scenes: {e}"

    def _save(self) -> None:
        try:
            STATE_DIR.mkdir(parents=True, exist_ok=True)
            TAGS_FILE.write_text(json.dumps({
                "tags": {k: asdict(v) for k, v in self.tags.items()},
                "updated": _now(),
            }, ensure_ascii=False, indent=2), encoding="utf-8")
            SCENES_FILE.write_text(json.dumps({
                "scenes": {k: asdict(v) for k, v in self.scenes.items()},
                "updated": _now(),
            }, ensure_ascii=False, indent=2), encoding="utf-8")
        except Exception as e:  # noqa: BLE001
            self.last_error = f"save: {e}"

    def _seed_scenes(self) -> None:
        """Escenas de ejemplo que muestran el patron."""
        if self.scenes:
            return
        self.scenes["modo_noche"] = Scene(
            name="modo_noche",
            steps=[
                {"type": "speak", "text": "Buenas noches, Comandante."},
                {"type": "ir_macro", "macro": "tv_off"},
                {"type": "notify", "title": "Daniela",
                 "content": "Modo noche activado"},
                {"type": "event", "event": "NIGHT_MODE"},
            ],
            note="Mesita de noche: apaga la tele, avisa y silencia",
        )
        self.scenes["modo_conduccion"] = Scene(
            name="modo_conduccion",
            steps=[
                {"type": "speak", "text": "Modo conduccion. Manos libres activos."},
                {"type": "notify", "title": "Daniela",
                 "content": "Modo conduccion activo", "ongoing": True},
                {"type": "event", "event": "DRIVING_MODE"},
            ],
            note="Soporte del coche: voz y avisos sin tocar la pantalla",
        )
        self.scenes["llegue_a_casa"] = Scene(
            name="llegue_a_casa",
            steps=[
                {"type": "set_home"},
                {"type": "speak", "text": "Bienvenido a casa."},
                {"type": "event", "event": "ZONE_CHANGE", "data": {"zone": "home"}},
            ],
            note="Tag de la entrada: fija la zona hogar y saluda",
        )
        self._save()

    # ── lectura / escritura ──────────────────────────────────

    def read_once(self, timeout: int = READ_TIMEOUT) -> dict[str, Any]:
        """Lectura bloqueante de un tag. Devuelve lo que haya en el tag."""
        if not is_termux():
            return {"ok": True, "simulated": True,
                    "msg": "no es Termux: lectura simulada"}
        try:
            raw = run_json(["termux-nfc", "-r"], timeout=timeout)
        except Exception as e:  # noqa: BLE001
            self.last_error = f"read: {type(e).__name__}: {str(e)[:80]}"
            return {"ok": False, "msg": self.last_error}

        if not isinstance(raw, dict):
            return {"ok": False, "msg": "salida inesperada de termux-nfc",
                    "raw": raw}

        tag_id = str(raw.get("id") or raw.get("tag") or "").lower()
        payload = self._extract_payload(raw)
        self.reads += 1
        entry = {"ts": _now(), "tag_id": tag_id, "payload": payload,
                 "tech": raw.get("tech") or raw.get("techList") or []}
        self._append_log(entry)
        return {"ok": True, **entry}

    @staticmethod
    def _extract_payload(raw: dict[str, Any]) -> str:
        """El payload puede venir en varios sitios segun la version."""
        for key in ("payload", "text", "message", "content"):
            v = raw.get(key)
            if isinstance(v, str) and v.strip():
                return v.strip()
        msgs = raw.get("messages")
        if isinstance(msgs, list) and msgs:
            first = msgs[0]
            if isinstance(first, str):
                return first.strip()
            if isinstance(first, dict):
                for key in ("payload", "text", "content"):
                    v = first.get(key)
                    if isinstance(v, str) and v.strip():
                        return v.strip()
        return ""

    def write(self, payload: str, mime: str = "text/plain") -> dict[str, Any]:
        """Escribe un tag. El movil debe estar encima del tag."""
        if not payload.strip():
            return {"ok": False, "msg": "payload vacio"}
        if not is_termux():
            self.writes += 1
            return {"ok": True, "simulated": True, "payload": payload}
        try:
            rc = run_code(["termux-nfc", "-w", "-t", mime, payload],
                          timeout=READ_TIMEOUT)
            if rc == 0:
                self.writes += 1
                self._save()
                return {"ok": True, "payload": payload, "mime": mime}
            return {"ok": False, "msg": f"termux-nfc rc={rc}"}
        except Exception as e:  # noqa: BLE001
            self.last_error = f"write: {type(e).__name__}: {str(e)[:80]}"
            return {"ok": False, "msg": self.last_error}

    # ── dispatch ─────────────────────────────────────────────

    def dispatch(self, payload: str, tag_id: str = "") -> dict[str, Any]:
        """Interpreta el payload de un tag y ejecuta la accion."""
        payload = (payload or "").strip()
        if not payload:
            return {"ok": False, "msg": "payload vacio"}

        # Anti-rebote: el mismo tag no debe relanzar la escena 10 veces
        key = tag_id or payload
        now = time.time()
        if now - self._last_hit.get(key, 0) < DEBOUNCE_S:
            return {"ok": False, "msg": "ignorado por anti-rebote",
                    "debounce_s": DEBOUNCE_S}
        self._last_hit[key] = now

        # 1. Si el tag esta registrado, manda su binding
        binding = self.tags.get(tag_id.lower())
        if binding and binding.enabled:
            binding.hits += 1
            binding.last_seen = _now()
            self._save()
            self.dispatches += 1
            res = self._run_action(binding.action)
            self._append_log({"ts": _now(), "tag_id": tag_id,
                              "payload": payload, "binding": binding.action,
                              "result": res})
            return res

        # 2. Si no, interpreta el payload directamente
        m = PAYLOAD_RE.match(payload)
        if not m:
            # Texto libre: no se ejecuta nada, solo se avisa
            res = {"ok": True, "action": "texto_libre", "notified": True,
                   "text": payload,
                   "msg": "tag no reconocido: se notifica pero no se ejecuta"}
            try:
                run_code(["termux-toast", f"NFC: {payload[:60]}"], timeout=8)
            except Exception:  # noqa: BLE001
                pass
            self._append_log({"ts": _now(), "tag_id": tag_id,
                              "payload": payload, "result": res})
            return res

        kind = m.group(1).lower()
        self.dispatches += 1
        # Se pasa el payload COMPLETO (con el prefijo daniela:) porque
        # _run_action valida contra el mismo patron.
        res = self._run_action(payload)
        self._append_log({"ts": _now(), "tag_id": tag_id, "payload": payload,
                          "action": f"{kind}:{m.group(2).strip()}",
                          "result": res})
        return res

    def _run_action(self, action: str) -> dict[str, Any]:
        m = PAYLOAD_RE.match(action)
        if not m:
            return {"ok": False, "msg": f"accion no valida: {action}"}
        kind, value = m.group(1).lower(), m.group(2).strip()
        if kind == "scene":
            return self.run_scene(value)
        if kind == "event":
            return self._emit(value, {})
        if kind == "url":
            return self._open_url(value)
        return {"ok": False, "msg": "tipo desconocido"}

    # ── escenas ──────────────────────────────────────────────

    def run_scene(self, name: str) -> dict[str, Any]:
        s = self.scenes.get(name)
        if not s:
            return {"ok": False, "msg": f"escena '{name}' no existe",
                    "available": sorted(self.scenes)}
        results: list[dict[str, Any]] = []
        for i, step in enumerate(s.steps, start=1):
            res = self._run_step(step)
            results.append({"step": i, "type": step.get("type"), **res})
            if not res.get("ok") and not res.get("nonfatal"):
                s.runs += 1
                self._save()
                return {"ok": False, "scene": name,
                        "msg": f"fallo el paso {i}", "results": results}
            wait = float(step.get("wait", 0) or 0)
            if wait > 0:
                time.sleep(wait)
        s.runs += 1
        self._save()
        return {"ok": True, "scene": name, "steps": len(results),
                "results": results}

    def _run_step(self, step: dict[str, Any]) -> dict[str, Any]:
        """Ejecuta un paso. SOLO los tipos de STEP_TYPES; nunca shell."""
        stype = str(step.get("type", "")).lower()
        if stype not in STEP_TYPES:
            return {"ok": False, "msg": f"tipo de paso no permitido: {stype}",
                    "allowed": list(STEP_TYPES)}

        try:
            if stype == "wait":
                time.sleep(float(step.get("seconds", 1)))
                return {"ok": True}
            if stype == "scene":
                return self.run_scene(str(step.get("name", "")))
            if stype == "event":
                return self._emit(str(step.get("event", "")),
                                  step.get("data") or {})
            if stype == "ir_macro":
                from ir_bridge import get_instance as get_ir  # type: ignore
                r = get_ir().run_macro(str(step.get("macro", "")))
                # Un IR que no exista no debe tumbar la escena entera
                r["nonfatal"] = True
                return r
            if stype == "notify":
                return self._notify(str(step.get("title", "Daniela")),
                                    str(step.get("content", "")),
                                    bool(step.get("ongoing", False)))
            if stype == "toast":
                run_code(["termux-toast", str(step.get("text", ""))], timeout=8)
                return {"ok": True}
            if stype == "speak":
                run_code(["termux-tts-speak", "-l", "es",
                          str(step.get("text", ""))], timeout=20)
                return {"ok": True}
            if stype == "url":
                return self._open_url(str(step.get("url", "")))
            if stype == "set_home":
                from context_engine import get_instance as get_ctx  # type: ignore
                r = get_ctx().set_home_here()
                r["nonfatal"] = True
                return r
            if stype == "blackbox":
                from blackbox_forense import get_instance as get_bb  # type: ignore
                return get_bb().trigger(reason=str(step.get("reason", "nfc")))
        except Exception as e:  # noqa: BLE001
            return {"ok": False, "nonfatal": True,
                    "msg": f"{type(e).__name__}: {str(e)[:80]}"}
        return {"ok": False, "msg": "tipo no implementado"}

    # ── integraciones ────────────────────────────────────────

    def _emit(self, event: str, data: dict[str, Any]) -> dict[str, Any]:
        if not event:
            return {"ok": False, "msg": "evento vacio"}
        try:
            from daniela_mobile_core import get_instance as get_core  # type: ignore
            get_core().bus.emit(event.upper(), data, source="nfc")
            return {"ok": True, "event": event.upper()}
        except Exception:  # noqa: BLE001
            return {"ok": True, "event": event.upper(),
                    "msg": "Mobile Core no disponible: evento no propagado"}

    def _notify(self, title: str, content: str, ongoing: bool) -> dict[str, Any]:
        try:
            from native_ui import get_instance as get_ui  # type: ignore
            return get_ui().notify(title, content, "nfc", None, ongoing)
        except Exception:  # noqa: BLE001
            return {"ok": True, "msg": "UI no disponible"}

    @staticmethod
    def _open_url(url: str) -> dict[str, Any]:
        if not url:
            return {"ok": False, "msg": "url vacia"}
        if not (url.startswith(("http://", "https://"))):
            return {"ok": False, "msg": "la url debe empezar por http(s)://"}
        try:
            from native_ui import get_instance as get_ui  # type: ignore
            return get_ui().open_url(url)
        except Exception:  # noqa: BLE001
            return {"ok": False, "msg": "UI no disponible"}

    # ── registro de tags ─────────────────────────────────────

    def bind(self, tag_id: str, action: str, label: str = "",
             room: str = "") -> dict[str, Any]:
        if not PAYLOAD_RE.match(action):
            return {"ok": False,
                    "msg": "la accion debe tener la forma daniela:scene:<n>, "
                           "daniela:event:<T> o daniela:url:<url>"}
        self.tags[tag_id.lower()] = TagBinding(
            tag_id=tag_id.lower(), action=action, label=label, room=room)
        self._save()
        return {"ok": True, "tag": asdict(self.tags[tag_id.lower()])}

    def unbind(self, tag_id: str) -> dict[str, Any]:
        if tag_id.lower() not in self.tags:
            return {"ok": False, "msg": "tag no registrado"}
        del self.tags[tag_id.lower()]
        self._save()
        return {"ok": True, "deleted": tag_id, "remaining": len(self.tags)}

    def add_scene(self, name: str, steps: list[dict[str, Any]],
                  note: str = "") -> dict[str, Any]:
        if not steps:
            return {"ok": False, "msg": "la escena necesita al menos un paso"}
        bad = [s.get("type") for s in steps if s.get("type") not in STEP_TYPES]
        if bad:
            return {"ok": False, "msg": "tipos de paso no permitidos",
                    "invalid": bad, "allowed": list(STEP_TYPES)}
        self.scenes[name] = Scene(name=name, steps=steps, note=note)
        self._save()
        return {"ok": True, "scene": asdict(self.scenes[name])}

    # ── bucle lector ─────────────────────────────────────────

    def _loop(self) -> None:
        while not self._stop.is_set():
            if not is_termux():
                self._stop.wait(5.0)
                continue
            res = self.read_once()
            if res.get("ok"):
                payload = res.get("payload") or ""
                if payload:
                    self.dispatch(payload, res.get("tag_id", ""))
            else:
                # Sin NFC o timeout: no martillear
                self._stop.wait(2.0)

    def start(self) -> dict[str, Any]:
        if self.running:
            return {"ok": False, "msg": "el lector ya esta activo"}
        self._stop.clear()
        self._thread = threading.Thread(target=self._loop, daemon=True,
                                        name="NFCReader")
        self._thread.start()
        self.running = True
        return {"ok": True, "msg": "lector NFC activo"}

    def stop(self) -> dict[str, Any]:
        if not self.running:
            return {"ok": False, "msg": "el lector no estaba activo"}
        self._stop.set()
        self.running = False
        self._save()
        return {"ok": True, "msg": "lector NFC detenido"}

    def _append_log(self, entry: dict[str, Any]) -> None:
        self.log.append(entry)
        if len(self.log) > MAX_LOG:
            self.log = self.log[-MAX_LOG:]

    def status(self) -> dict[str, Any]:
        return {
            "platform": "termux" if is_termux() else "pc",
            "running": self.running,
            "tags": len(self.tags),
            "scenes": len(self.scenes),
            "reads": self.reads,
            "writes": self.writes,
            "dispatches": self.dispatches,
            "debounce_s": DEBOUNCE_S,
            "step_types": list(STEP_TYPES),
            "log_size": len(self.log),
            "last_error": self.last_error,
            "updated": _now(),
        }


def get_instance() -> NFCAutomation:
    global _instance
    with _instance_lock:
        if _instance is None:
            _instance = NFCAutomation()
        return _instance


# ─────────────────────────────────────────────────────────────
#  Rutas Flask
# ─────────────────────────────────────────────────────────────

def register_nfc_routes(app) -> int:
    from flask import jsonify, request
    nfc = get_instance()

    @app.route("/api/pixel/nfc/status", methods=["GET"])
    def nfc_status():
        return jsonify(nfc.status())

    @app.route("/api/pixel/nfc/start", methods=["POST"])
    def nfc_start():
        return jsonify(nfc.start())

    @app.route("/api/pixel/nfc/stop", methods=["POST"])
    def nfc_stop():
        return jsonify(nfc.stop())

    @app.route("/api/pixel/nfc/read", methods=["POST"])
    def nfc_read():
        body = request.get_json(silent=True) or {}
        return jsonify(nfc.read_once(int(body.get("timeout", READ_TIMEOUT))))

    @app.route("/api/pixel/nfc/write", methods=["POST"])
    def nfc_write():
        body = request.get_json(silent=True) or {}
        return jsonify(nfc.write(str(body.get("payload", "")),
                                 str(body.get("mime", "text/plain"))))

    @app.route("/api/pixel/nfc/tags", methods=["GET", "POST"])
    def nfc_tags():
        if request.method == "GET":
            return jsonify({"tags": {k: asdict(v)
                                     for k, v in nfc.tags.items()}})
        body = request.get_json(silent=True) or {}
        if body.get("delete"):
            return jsonify(nfc.unbind(str(body["delete"])))
        if not body.get("tag_id") or not body.get("action"):
            return jsonify({"ok": False, "msg": "faltan tag_id o action"}), 400
        return jsonify(nfc.bind(str(body["tag_id"]), str(body["action"]),
                                str(body.get("label", "")),
                                str(body.get("room", ""))))

    @app.route("/api/pixel/nfc/scenes", methods=["GET", "POST"])
    def nfc_scenes():
        if request.method == "GET":
            return jsonify({"scenes": {k: asdict(v)
                                       for k, v in nfc.scenes.items()}})
        body = request.get_json(silent=True) or {}
        if body.get("run"):
            return jsonify(nfc.run_scene(str(body["run"])))
        if not body.get("name"):
            return jsonify({"ok": False, "msg": "falta 'name'"}), 400
        return jsonify(nfc.add_scene(str(body["name"]),
                                     body.get("steps", []),
                                     str(body.get("note", ""))))

    @app.route("/api/pixel/nfc/dispatch", methods=["POST"])
    def nfc_dispatch():
        body = request.get_json(silent=True) or {}
        return jsonify(nfc.dispatch(str(body.get("payload", "")),
                                    str(body.get("tag_id", ""))))

    print("[NFC] Routes registered: /api/pixel/nfc/* (status, start, stop, read, "
          "write, tags, scenes, dispatch)")
    return 8


if __name__ == "__main__":
    import io
    import sys
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8',
                                  errors="replace")
    nfc = get_instance()
    print("plataforma:", "termux" if is_termux() else "pc")

    print("\n— parseo de payloads —")
    for p in ["daniela:scene:modo_noche", "daniela:event:PANIC",
              "daniela:url:https://example.com", "hola mundo",
              "daniela:shell:rm -rf /"]:
        m = PAYLOAD_RE.match(p)
        print(f"  {p:35s} -> {'RECONOCIDO ' + m.group(1) if m else 'texto libre (no ejecuta)'}")

    print("\n— allowlist de pasos (seguridad) —")
    print("  permitidos:", nfc_run := STEP_TYPES)
    r = nfc._run_step({"type": "exec", "cmd": "rm -rf /"})
    print("  paso tipo 'exec':", r["ok"], "|", r["msg"])

    print("\n— anti-rebote —")
    print("  1er disparo:", {k: v for k, v in
                             nfc.dispatch("daniela:scene:modo_conduccion").items()
                             if k != "results"})
    print("  2o inmediato:", nfc.dispatch("daniela:scene:modo_conduccion"))
    time.sleep(DEBOUNCE_S + 0.1)
    print("  tras la espera:", {k: v for k, v in
                                nfc.dispatch("daniela:scene:modo_conduccion").items()
                                if k != "results"})

    print("\n— tag registrado manda sobre el payload —")
    nfc.bind("a1b2c3", "daniela:scene:llegue_a_casa", label="Entrada")
    print("  ", {k: v for k, v in
                 nfc.dispatch("daniela:scene:modo_noche", "a1b2c3").items()
                 if k != "results"})

    print("\n— escritura de tag (simulada) —")
    print("  ", nfc.write("daniela:scene:modo_noche"))

    print("\n— escenas disponibles —")
    for name, s in nfc.scenes.items():
        print(f"   {name:16s} {len(s.steps)} pasos — {s.note}")

    print("\n— url maliciosa rechazada —")
    print("  ", nfc._open_url("javascript:alert(1)"))

    print("\nstatus keys:", list(nfc.status().keys()))
