#!/usr/bin/env python3
"""
Caja Negra Forense — buffer circular de 5 minutos (E-06 / Fase 6)
==================================================================
Un movil que graba cuando tu le das al boton llega TARDE: lo importante
ya paso. Esta caja negra funciona como la de un avion — graba siempre en
un buffer circular y solo CONGELA a disco cuando algo ocurre. Asi el
incidente contiene los 5 minutos ANTERIORES al disparo, no solo los de
despues.

Tres capas que se capturan en paralelo:

  1. TELEMETRIA  — acelerometro, giroscopio, luz, proximidad, pasos,
                   bateria, GPS y contexto inferido (~1 Hz, en memoria).
  2. AUDIO       — segmentos rotativos de 30 s (10 segmentos = 5 min de
                   pre-roll). Al disparar, los segmentos completos se
                   copian al incidente y arranca un post-roll de 60 s.
  3. IMAGEN      — rafaga de fotos al disparar (camara trasera/delantera).

INTEGRIDAD FORENSE: cada fichero se hash-ea con SHA-256 y se encadena
(hash-chain): entry[i] = SHA256(entry[i-1] + file_hash + timestamp).
Si alguien altera un fichero, la cadena se rompe y el manifiesto lo
delata. Es la diferencia entre "tengo un mp3" y "tengo una prueba".

Disparadores:
  - Manual .......... POST /api/blackbox/trigger
  - PANIC ........... boton de panico / palabra clave (bus del Mobile Core)
  - FALL_DETECTED ... caida confirmada (Context Engine)
  - Bateria critica, perdida de senal, o cualquier evento del bus

Retencion: los incidentes ocupan disco. Se guardan MAX_INCIDENTS y los
segmentos rotativos nunca crecen (siempre 10 ficheros).

Seguridad: todo comando pasa por safe_exec. 0 os.system, 0 shell=True.

Rutas:
  GET  /api/blackbox/status                  — estado del buffer
  POST /api/blackbox/start                   — arranca la grabacion continua
  POST /api/blackbox/stop                    — la detiene
  POST /api/blackbox/trigger                 — congela un incidente
  GET  /api/blackbox/incidents               — lista de incidentes
  GET  /api/blackbox/incident/<id>           — detalle + manifiesto
  GET  /api/blackbox/incident/<id>/verify    — verifica la cadena de hashes
  POST /api/blackbox/incident/<id>/delete    — borra un incidente
  GET  /api/blackbox/config                  — configuracion
  POST /api/blackbox/config                  — ajusta la configuracion

Coste: $0/mes — Termux:API (gratis), almacenamiento local.
"""

from __future__ import annotations

import hashlib
import json
import shutil
import threading
import time
from collections import deque
from datetime import datetime
from pathlib import Path
from typing import Any, Deque, Dict, List, Optional

from bridges.comms.safe_exec import run_code, run_json

# Raiz del repo (este modulo vive en pixel/ desde Fase 2).
PROJECT_ROOT = Path(__file__).resolve().parents[2]
BB_DIR = PROJECT_ROOT / "data" / "blackbox"
SEG_DIR = BB_DIR / "segments"
INC_DIR = BB_DIR / "incidents"
STATE_FILE = BB_DIR / "blackbox_state.json"

# ── Configuracion por defecto ─────────────────────────────────
DEFAULT_CONFIG: Dict[str, Any] = {
    "pre_roll_s": 300,  # 5 minutos de pre-roll
    "post_roll_s": 60,  # 60 s de grabacion tras el disparo
    "segment_s": 30,  # duracion de cada segmento de audio
    "tick_s": 1.0,  # muestreo de telemetria
    "max_incidents": 20,  # retencion
    "audio_enabled": True,
    "photo_burst": 3,  # fotos al disparar
    "photo_enabled": True,
    "gps_every_s": 15,  # GPS es caro en bateria: no cada segundo
    "auto_triggers": ["PANIC", "FALL_DETECTED"],
}

INCIDENT_RETENTION_DAYS = 90

_instance: Optional["BlackBox"] = None
_instance_lock = threading.Lock()


def is_termux() -> bool:
    return __import__("os").path.exists("/data/data/com.termux/files/usr/bin")


def _now() -> str:
    return datetime.now().isoformat(timespec="seconds")


def sha256_file(path: Path, chunk: int = 1 << 20) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(chunk), b""):
            h.update(block)
    return h.hexdigest()


# ─────────────────────────────────────────────────────────────


class BlackBox:
    """Grabador continuo con buffer circular y congelacion a disco."""

    def __init__(self) -> None:
        self.config: Dict[str, Any] = dict(DEFAULT_CONFIG)
        self.running = False
        self._thread: Optional[threading.Thread] = None
        self._audio_thread: Optional[threading.Thread] = None
        self._stop = threading.Event()

        # Buffer circular de telemetria
        self.buffer: Deque[Dict[str, Any]] = deque(maxlen=2000)
        # Segmentos de audio: lista de (path, start_ts, end_ts, completo)
        self.segments: Deque[Dict[str, Any]] = deque(maxlen=40)

        self.incidents: List[Dict[str, Any]] = []
        self.ticks = 0
        self.last_error: Optional[str] = None
        self._recording_proc: Optional[Any] = None
        self._post_roll_until: Optional[float] = None
        self._last_gps_ts = 0.0
        self._last_gps: Optional[Dict[str, Any]] = None

        self._load()

    # ── persistencia ─────────────────────────────────────────

    def _load(self) -> None:
        try:
            BB_DIR.mkdir(parents=True, exist_ok=True)
            SEG_DIR.mkdir(parents=True, exist_ok=True)
            INC_DIR.mkdir(parents=True, exist_ok=True)
        except Exception as e:  # noqa: BLE001
            self.last_error = f"mkdir: {e}"
        try:
            if STATE_FILE.exists():
                data = json.loads(STATE_FILE.read_text(encoding="utf-8"))
                self.config.update(data.get("config", {}))
                self.incidents = data.get("incidents", [])
        except Exception as e:  # noqa: BLE001
            self.last_error = f"load: {e}"

    def _save(self) -> None:
        try:
            BB_DIR.mkdir(parents=True, exist_ok=True)
            STATE_FILE.write_text(
                json.dumps(
                    {
                        "config": self.config,
                        "incidents": self.incidents,
                        "updated": _now(),
                    },
                    ensure_ascii=False,
                    indent=2,
                ),
                encoding="utf-8",
            )
        except Exception as e:  # noqa: BLE001
            self.last_error = f"save: {e}"

    # ── sensores ─────────────────────────────────────────────

    def _read_gps(self) -> Optional[Dict[str, Any]]:
        now = time.time()
        if now - self._last_gps_ts < float(self.config["gps_every_s"]):
            return self._last_gps
        try:
            loc = run_json(["termux-location", "-p", "network", "-r", "once"], timeout=6)
            if isinstance(loc, dict) and loc.get("latitude"):
                self._last_gps = {
                    "lat": loc.get("latitude"),
                    "lon": loc.get("longitude"),
                    "alt": loc.get("altitude"),
                    "speed": loc.get("speed"),
                    "acc": loc.get("accuracy"),
                }
        except Exception:  # noqa: BLE001
            pass
        self._last_gps_ts = now
        return self._last_gps

    def _sample(self) -> Dict[str, Any]:
        sample: Dict[str, Any] = {"ts": _now(), "t": time.time()}
        try:
            from services.sensors.sensor_stream_live import get_instance as get_stream  # type: ignore

            snap = get_stream().get_snapshot() or {}
            for k in ("accelerometer", "gyroscope", "magnetometer", "light", "proximity", "step"):
                if snap.get(k) is not None:
                    sample[k] = snap[k]
            if snap.get("battery"):
                sample["battery"] = snap["battery"]
        except Exception:  # noqa: BLE001
            pass
        try:
            from core.context.context_engine import get_instance as get_ctx  # type: ignore

            cur = get_ctx().current
            sample["context"] = cur.get("context")
            sample["context_conf"] = cur.get("confidence")
        except Exception:  # noqa: BLE001
            pass
        gps = self._read_gps()
        if gps:
            sample["gps"] = gps
        return sample

    # ── audio rotativo ───────────────────────────────────────

    def _audio_loop(self) -> None:
        """Graba segmentos consecutivos y mantiene solo la ventana de pre-roll."""
        seg_s = int(self.config["segment_s"])
        idx = 0
        while not self._stop.is_set():
            if not self.config.get("audio_enabled") or not is_termux():
                self._stop.wait(2.0)
                continue
            idx += 1
            path = SEG_DIR / f"seg_{idx % 12:02d}.mp3"
            start = time.time()
            rec: Dict[str, Any] = {
                "path": str(path),
                "start": start,
                "start_iso": _now(),
                "end": None,
                "complete": False,
            }
            self.segments.append(rec)
            try:
                run_code(
                    ["termux-microphone-record", "-l", str(seg_s), "-f", str(path)],
                    timeout=seg_s + 8,
                )
            except Exception as e:  # noqa: BLE001
                self.last_error = f"audio: {type(e).__name__}: {str(e)[:60]}"
            rec["end"] = time.time()
            rec["complete"] = path.exists()
            self._purge_segments()

    def _purge_segments(self) -> None:
        """Descarta los segmentos mas viejos que la ventana de pre-roll."""
        window = float(self.config["pre_roll_s"])
        cutoff = time.time() - window
        while len(self.segments) > 1:
            oldest = self.segments[0]
            if (oldest.get("end") or 0) < cutoff:
                self.segments.popleft()
            else:
                break

    # ── bucle principal ──────────────────────────────────────

    def _loop(self) -> None:
        while not self._stop.is_set():
            try:
                self.ticks += 1
                self.buffer.append(self._sample())
                self._trim_buffer()
            except Exception as e:  # noqa: BLE001
                self.last_error = f"tick: {e}"
            self._stop.wait(float(self.config["tick_s"]))

    def _trim_buffer(self) -> None:
        cutoff = time.time() - float(self.config["pre_roll_s"])
        while self.buffer and self.buffer[0].get("t", 0) < cutoff:
            self.buffer.popleft()

    def start(self) -> Dict[str, Any]:
        if self.running:
            return {"ok": False, "msg": "ya esta grabando"}
        self._stop.clear()
        self.running = True
        self._thread = threading.Thread(target=self._loop, daemon=True, name="BlackBox")
        self._thread.start()
        if self.config.get("audio_enabled"):
            self._audio_thread = threading.Thread(
                target=self._audio_loop, daemon=True, name="BlackBoxAudio"
            )
            self._audio_thread.start()
        self._subscribe_bus()
        return {"ok": True, "msg": "Caja negra grabando (buffer circular)"}

    def stop(self) -> Dict[str, Any]:
        if not self.running:
            return {"ok": False, "msg": "no estaba grabando"}
        self._stop.set()
        self.running = False
        try:
            run_code(["termux-microphone-record", "-q"], timeout=5)
        except Exception:  # noqa: BLE001
            pass
        self._save()
        return {"ok": True, "msg": "Caja negra detenida"}

    def _subscribe_bus(self) -> None:
        """Se engancha al bus del Mobile Core para autodispararse."""
        try:
            from core.autonomy.daniela_mobile_core import get_instance as get_core  # type: ignore

            core = get_core()
            triggers = set(self.config.get("auto_triggers", []))

            def handler(event: Dict[str, Any]) -> None:
                if event.get("type") in triggers:
                    self.trigger(reason=event.get("type"), data=event.get("data") or {})

            core.bus.subscribe(None, handler)
        except Exception:  # noqa: BLE001
            pass

    # ── congelacion del incidente ────────────────────────────

    def trigger(
        self, reason: str = "manual", data: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Congela el buffer circular en disco como incidente."""
        ts = datetime.now()
        # Resolucion de milisegundos: dos incidentes en el mismo segundo
        # (panic + caida casi simultaneos) no deben pisarse.
        inc_id = f"inc_{ts.strftime('%Y%m%d_%H%M%S')}_{int(time.time() * 1000) % 1000:03d}"
        inc_dir = INC_DIR / inc_id
        try:
            inc_dir.mkdir(parents=True, exist_ok=True)
        except Exception as e:  # noqa: BLE001
            return {"ok": False, "msg": f"no se pudo crear el directorio: {e}"}

        # 1. Telemetria del pre-roll
        telemetry = list(self.buffer)
        gps_track = [{"ts": s.get("ts"), "gps": s["gps"]} for s in telemetry if s.get("gps")]

        # 2. Audio: copiar segmentos completos dentro de la ventana
        audio_files: List[str] = []
        cutoff = time.time() - float(self.config["pre_roll_s"])
        for seg in list(self.segments):
            if not seg.get("complete"):
                continue
            if (seg.get("end") or 0) < cutoff:
                continue
            src = Path(seg["path"])
            if not src.exists():
                continue
            dst = inc_dir / src.name
            try:
                shutil.copy2(src, dst)
                audio_files.append(dst.name)
            except Exception as e:  # noqa: BLE001
                self.last_error = f"copy audio: {e}"

        # 3. Post-roll: audio fresco desde el momento del disparo
        post_file: Optional[str] = None
        if self.config.get("audio_enabled") and is_termux():
            dst = inc_dir / "post_roll.mp3"
            try:
                run_code(
                    [
                        "termux-microphone-record",
                        "-l",
                        str(int(self.config["post_roll_s"])),
                        "-f",
                        str(dst),
                    ],
                    timeout=int(self.config["post_roll_s"]) + 10,
                )
                if dst.exists():
                    post_file = dst.name
            except Exception as e:  # noqa: BLE001
                self.last_error = f"post-roll: {type(e).__name__}: {str(e)[:60]}"

        # 4. Rafaga de fotos
        photos: List[str] = []
        if self.config.get("photo_enabled") and is_termux():
            for i in range(int(self.config["photo_burst"])):
                dst = inc_dir / f"photo_{i}.jpg"
                try:
                    run_code(["termux-camera-photo", "-c", "0", str(dst)], timeout=12)
                    if dst.exists():
                        photos.append(dst.name)
                except Exception:  # noqa: BLE001
                    pass

        # 5. Ubicacion final
        final_loc = self._read_gps() or (gps_track[-1]["gps"] if gps_track else None)

        # 6. Telemetria a disco ANTES de hashearla (entra en la cadena)
        telemetry_file = "telemetry.json"
        try:
            (inc_dir / telemetry_file).write_text(
                json.dumps(telemetry, ensure_ascii=False), encoding="utf-8"
            )
        except Exception as e:  # noqa: BLE001
            self.last_error = f"telemetry: {e}"
            telemetry_file = ""

        # 7. Manifiesto con cadena de hashes
        files = (
            ([telemetry_file] if telemetry_file else [])
            + audio_files
            + ([post_file] if post_file else [])
            + photos
        )
        chain = self._build_chain(inc_dir, files)
        manifest = {
            "id": inc_id,
            "created": _now(),
            "reason": reason,
            "trigger_data": data or {},
            "device": "pixel-termux" if is_termux() else "pc",
            "pre_roll_s": self.config["pre_roll_s"],
            "post_roll_s": self.config["post_roll_s"],
            "telemetry_samples": len(telemetry),
            "telemetry_span_s": (
                round(telemetry[-1]["t"] - telemetry[0]["t"], 1) if len(telemetry) >= 2 else 0
            ),
            "gps_points": len(gps_track),
            "final_location": final_loc,
            "audio_segments": audio_files,
            "post_roll": post_file,
            "photos": photos,
            "files": chain,
            "chain_root": chain[0]["entry_hash"] if chain else None,
            "chain_head": chain[-1]["entry_hash"] if chain else None,
        }

        # Sello del propio manifiesto: SHA-256 de su contenido canónico.
        # Si alguien edita el manifiesto a mano, el sello no cuadra.
        manifest["seal"] = self._seal(manifest)

        try:
            (inc_dir / "manifest.json").write_text(
                json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8"
            )
        except Exception as e:  # noqa: BLE001
            self.last_error = f"manifest: {e}"

        record = {
            "id": inc_id,
            "created": manifest["created"],
            "reason": reason,
            "path": str(inc_dir),
            "files": len(files),
            "samples": len(telemetry),
            "location": final_loc,
            "chain_head": (manifest["chain_head"] or "")[:12],
        }
        self.incidents.append(record)
        self._prune_incidents()
        self._save()

        # Feedback: saver que quedo registrado
        try:
            run_code(["termux-vibrate", "-d", "200"], timeout=3)
            run_code(
                ["termux-tts-speak", "-l", "es", "Caja negra activada. Datos resguardados."],
                timeout=6,
            )
        except Exception:  # noqa: BLE001
            pass

        return {"ok": True, "incident": record, "manifest": manifest}

    @staticmethod
    def _seal(manifest: Dict[str, Any]) -> str:
        """SHA-256 del manifiesto en forma canonica (sin el propio sello)."""
        canon = {k: v for k, v in manifest.items() if k != "seal"}
        blob = json.dumps(canon, sort_keys=True, ensure_ascii=False, separators=(",", ":"))
        return hashlib.sha256(blob.encode("utf-8")).hexdigest()

    def _build_chain(self, inc_dir: Path, files: List[str]) -> List[Dict[str, Any]]:
        """Cadena de hashes: entry = SHA256(prev_entry + file_hash + ts)."""
        chain: List[Dict[str, str]] = []
        prev = "0" * 64
        for name in files:
            p = inc_dir / name
            if not p.exists():
                continue
            try:
                fhash = sha256_file(p)
            except Exception:  # noqa: BLE001
                continue
            ts = _now()
            entry = hashlib.sha256(f"{prev}{fhash}{ts}".encode()).hexdigest()
            chain.append(
                {
                    "file": name,
                    "size": p.stat().st_size,
                    "sha256": fhash,
                    "ts": ts,
                    "prev": prev,
                    "entry_hash": entry,
                }
            )
            prev = entry
        return chain  # type: ignore[return-value]

    def verify(self, inc_id: str) -> Dict[str, Any]:
        """Recalcula hashes y la cadena. Dice si el incidente fue alterado."""
        inc_dir = INC_DIR / inc_id
        mpath = inc_dir / "manifest.json"
        if not mpath.exists():
            return {"ok": False, "msg": "incidente no encontrado"}
        try:
            manifest = json.loads(mpath.read_text(encoding="utf-8"))
        except Exception as e:  # noqa: BLE001
            return {"ok": False, "msg": f"manifiesto ilegible: {e}"}

        altered: List[str] = []
        missing: List[str] = []

        # 0. Sello del manifiesto
        seal_ok = True
        stored_seal = manifest.get("seal")
        if not stored_seal:
            seal_ok = False
            altered.append("manifest.json (sin sello)")
        else:
            recomputed = self._seal(manifest)
            if recomputed != stored_seal:
                seal_ok = False
                altered.append("manifest.json (sello invalido)")

        chain = manifest.get("files", [])
        prev = "0" * 64
        for e in chain:
            p = inc_dir / e["file"]
            if not p.exists():
                missing.append(e["file"])
                prev = e.get("entry_hash", prev)
                continue
            actual = sha256_file(p)
            if actual != e.get("sha256"):
                altered.append(e["file"])
            if e.get("prev") != prev:
                altered.append(f"{e['file']} (cadena rota)")
            prev = e.get("entry_hash", prev)

        return {
            "ok": True,
            "incident": inc_id,
            "seal_valid": seal_ok,
            "files_checked": len(chain),
            "missing": missing,
            "altered": altered,
            "integrity": "VALIDA" if not altered and not missing else "COMPROMETIDA",
        }

    def _prune_incidents(self) -> None:
        max_inc = int(self.config["max_incidents"])
        while len(self.incidents) > max_inc:
            old = self.incidents.pop(0)
            try:
                shutil.rmtree(INC_DIR / old["id"], ignore_errors=True)
            except Exception:  # noqa: BLE001
                pass

    def delete_incident(self, inc_id: str) -> Dict[str, Any]:
        before = len(self.incidents)
        self.incidents = [i for i in self.incidents if i["id"] != inc_id]
        try:
            shutil.rmtree(INC_DIR / inc_id, ignore_errors=True)
        except Exception:  # noqa: BLE001
            pass
        self._save()
        return {"ok": len(self.incidents) < before, "remaining": len(self.incidents)}

    # ── estado ───────────────────────────────────────────────

    def status(self) -> Dict[str, Any]:
        span = 0.0
        if len(self.buffer) >= 2:
            span = round(self.buffer[-1]["t"] - self.buffer[0]["t"], 1)
        last = self.buffer[-1] if self.buffer else None
        return {
            "running": self.running,
            "platform": "termux" if is_termux() else "pc",
            "ticks": self.ticks,
            "buffer_samples": len(self.buffer),
            "buffer_span_s": span,
            "buffer_capacity_s": self.config["pre_roll_s"],
            "audio_segments": len([s for s in self.segments if s.get("complete")]),
            "incidents": len(self.incidents),
            "last_sample": last,
            "config": self.config,
            "last_error": self.last_error,
            "updated": _now(),
        }


def get_instance() -> BlackBox:
    global _instance
    with _instance_lock:
        if _instance is None:
            _instance = BlackBox()
        return _instance


# ─────────────────────────────────────────────────────────────
#  Rutas Flask
# ─────────────────────────────────────────────────────────────


def register_blackbox_routes(app) -> int:
    from flask import jsonify, request

    bb = get_instance()

    @app.route("/api/blackbox/status", methods=["GET"])
    def bb_status():
        return jsonify(bb.status())

    @app.route("/api/blackbox/start", methods=["POST"])
    def bb_start():
        return jsonify(bb.start())

    @app.route("/api/blackbox/stop", methods=["POST"])
    def bb_stop():
        return jsonify(bb.stop())

    @app.route("/api/blackbox/trigger", methods=["POST"])
    def bb_trigger():
        body = request.get_json(silent=True) or {}
        return jsonify(bb.trigger(reason=str(body.get("reason", "manual")), data=body.get("data")))

    @app.route("/api/blackbox/incidents", methods=["GET"])
    def bb_incidents():
        return jsonify({"incidents": bb.incidents, "total": len(bb.incidents)})

    @app.route("/api/blackbox/incident/<inc_id>", methods=["GET"])
    def bb_incident(inc_id: str):
        mpath = INC_DIR / inc_id / "manifest.json"
        if not mpath.exists():
            return jsonify({"ok": False, "msg": "no encontrado"}), 404
        try:
            return jsonify(json.loads(mpath.read_text(encoding="utf-8")))
        except Exception as e:  # noqa: BLE001
            return jsonify({"ok": False, "msg": str(e)}), 500

    @app.route("/api/blackbox/incident/<inc_id>/verify", methods=["GET"])
    def bb_verify(inc_id: str):
        return jsonify(bb.verify(inc_id))

    @app.route("/api/blackbox/incident/<inc_id>/delete", methods=["POST"])
    def bb_delete(inc_id: str):
        return jsonify(bb.delete_incident(inc_id))

    @app.route("/api/blackbox/config", methods=["GET", "POST"])
    def bb_config():
        if request.method == "GET":
            return jsonify({"config": bb.config, "defaults": DEFAULT_CONFIG})
        body = request.get_json(silent=True) or {}
        changed: Dict[str, Any] = {}
        for k, v in body.items():
            if k in DEFAULT_CONFIG:
                bb.config[k] = v
                changed[k] = v
        bb._save()
        return jsonify({"ok": True, "changed": changed, "config": bb.config})

    print(
        "[Black Box] Routes registered: /api/blackbox/* (status, start, stop, "
        "trigger, incidents, incident/<id>, verify, delete, config)"
    )
    return 9


if __name__ == "__main__":
    import io
    import sys

    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
    bb = get_instance()
    print("plataforma:", "termux" if is_termux() else "pc")

    # Rellenar el buffer con 30 muestras sinteticas
    print("\n— llenando buffer circular —")
    t0 = time.time()
    for i in range(30):
        bb.buffer.append(
            {
                "ts": _now(),
                "t": t0 - 30 + i,
                "accelerometer": [0.1, 0.2, 9.8],
                "light": 120 + i,
                "gps": {"lat": 40.4168 + i * 0.0001, "lon": -3.7038, "speed": 0},
                "context": "caminando",
            }
        )
    bb._trim_buffer()
    print("  muestras:", len(bb.buffer))

    print("\n— disparo manual —")
    res = bb.trigger(reason="test", data={"origen": "smoke test"})
    inc = res.get("incident", {})
    print(
        "  ok:",
        res.get("ok"),
        "| id:",
        inc.get("id"),
        "| muestras:",
        inc.get("samples"),
        "| gps:",
        inc.get("location"),
    )

    print("\n— verificacion de integridad —")
    v = bb.verify(inc["id"])
    print(
        "  ",
        v.get("integrity"),
        "| ficheros:",
        v.get("files_checked"),
        "| alterados:",
        v.get("altered"),
        "| ausentes:",
        v.get("missing"),
    )

    print("\n— manipulacion 1: alterar telemetry.json —")
    tpath = INC_DIR / inc["id"] / "telemetry.json"
    tpath.write_text(tpath.read_text(encoding="utf-8") + "\n[]", encoding="utf-8")
    v2 = bb.verify(inc["id"])
    print("  ", v2.get("integrity"), "| alterados:", v2.get("altered"))

    print("\n— manipulacion 2: reescribir el manifiesto a mano —")
    mpath = INC_DIR / inc["id"] / "manifest.json"
    mpath.write_text("{}", encoding="utf-8")
    v3 = bb.verify(inc["id"])
    print("  ", v3.get("integrity"), "| alterados:", v3.get("altered"))

    print("\n— manipulacion 3: borrar un fichero de la cadena —")
    bb2 = get_instance()
    t0 = time.time()
    for i in range(5):
        bb2.buffer.append(
            {"ts": _now(), "t": t0 + i, "light": i, "gps": {"lat": 40.4, "lon": -3.7}}
        )
    r2 = bb2.trigger(reason="test-borrado")
    inc2 = r2["incident"]
    (INC_DIR / inc2["id"] / "telemetry.json").unlink()
    v4 = bb2.verify(inc2["id"])
    print("  ", v4.get("integrity"), "| ausentes:", v4.get("missing"))
    bb2.delete_incident(inc2["id"])

    print("\n— limpieza —")
    print("  ", bb.delete_incident(inc["id"]))

    print("\nstatus keys:", list(bb.status().keys()))

# Alias para compatibilidad
BlackboxForense = BlackBox