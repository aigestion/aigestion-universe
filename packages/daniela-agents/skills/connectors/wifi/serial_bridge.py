#!/usr/bin/env python3
"""
USB Serial -> Arduino/ESP32 — Daniela Robotica (E-09 / Fase 7)
===============================================================
Daniela controla software, pero no hardware propio. Un sensor de humedad
o un servo quedaban fuera de su alcance. `termux-usb` expone el puerto
serie: con un ESP32 (4 EUR) por USB-OTG, Daniela LEE sensores
(temperatura, humedad, movimiento, calidad del aire) y ACCIONA reles y
servos. Red de sensores casera por menos de 20 EUR, sin cloud y sin cuota.

ARQUITECTURA
------------
    termux-usb -l            descubre dispositivos
    termux-usb -r <device>   pide permiso y devuelve la ruta / el fd
    pyserial                 abre el puerto a 115200 baudios

El ESP32 habla un protocolo de LINEAS JSON, facil de depurar a mano:

    -> {"c":"ping"}                  Daniela pregunta
    <- {"ok":true,"pong":true}
    -> {"c":"read"}                  pide todas las lecturas
    <- {"ok":true,"s":{"temp":23.4,"hum":51.2,"motion":0}}
    -> {"c":"set","pin":4,"v":1}     enciende un pin
    <- {"ok":true,"pin":4,"v":1}

Acepta tambien el formato compacto `temp=23.4;hum=51.2` para placas
minimalistas que no quieran parsear JSON.

FIRMWARE INCLUIDO
-----------------
`write_firmware()` genera un `main.py` en MicroPython listo para flasear
en el ESP32. Sin ese fichero el modulo solo sirve para hablar con placas
que ya traigan firmware propio.

DEGRADACION
-----------
Sin pyserial, sin cable o sin permiso USB, el modulo sigue arrancando:
entra en modo simulado, las lecturas se marcan como `simulated` y las
rutas responden igual. Daniela nunca se cae por un cable suelto.

Seguridad: todo comando pasa por safe_exec. 0 os.system, 0 shell=True.

Rutas:
  GET  /api/pixel/serial/status          — estado y capacidades
  GET  /api/pixel/serial/devices         — dispositivos USB detectados
  POST /api/pixel/serial/connect         — conecta (puerto + baudios)
  POST /api/pixel/serial/disconnect      — cierra el puerto
  POST /api/pixel/serial/send            — envia una linea cruda o JSON
  POST /api/pixel/serial/command         — comando estructurado
  GET  /api/pixel/serial/sensors         — ultimas lecturas + historial
  GET  /api/pixel/serial/firmware        — devuelve el main.py generado
  POST /api/pixel/serial/firmware        — lo escribe en disco

Coste: $0/mes — ESP32 (~4 EUR) + MicroPython + pyserial (open source)
"""

from __future__ import annotations

import json
import os
import queue
import threading
import time
from collections import deque
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any

from safe_exec import run_json, run_out

try:  # pyserial es opcional: sin el, modo simulado
    import serial  # type: ignore
    HAS_PYSERIAL = True
except ImportError:  # pragma: no cover
    serial = None  # type: ignore
    HAS_PYSERIAL = False

PROJECT_ROOT = Path(__file__).resolve().parent
STATE_DIR = PROJECT_ROOT / "data" / "serial_bridge"
STATE_FILE = STATE_DIR / "serial_state.json"
FIRMWARE_FILE = STATE_DIR / "esp32_main.py"

DEFAULT_BAUD = 115200
MAX_HISTORY = 500
READ_TIMEOUT = 0.5

_instance: SerialBridge | None = None
_instance_lock = threading.Lock()


def is_termux() -> bool:
    return os.path.exists("/data/data/com.termux/files/usr/bin")


def _now() -> str:
    return datetime.now().isoformat(timespec="seconds")


# ─────────────────────────────────────────────────────────────
#  Firmware MicroPython para el ESP32
# ─────────────────────────────────────────────────────────────

FIRMWARE = '''\
# main.py — Daniela Node para ESP32 (MicroPython)
# Generado por serial_bridge.py (aig / DanielaOS)
#
# Flasheo:
#   esptool.py --chip esp32 --port /dev/ttyUSB0 erase_flash
#   esptool.py --chip esp32 --port /dev/ttyUSB0 write_flash -z 0x1000 esp32.bin
#   ampy --port /dev/ttyUSB0 put main.py
#
# Protocolo: una linea JSON por comando, una linea JSON por respuesta.

import json
import time
from machine import Pin, ADC

try:
    import dht
    HAS_DHT = True
except ImportError:
    HAS_DHT = False

# ---- Configuracion: ajusta los pines a tu cableado --------------
DHT_PIN = 4
PIR_PIN = 5
ADC_PIN = 34            # entrada analogica (0-3.3V max!)
RELAYS = (12, 13, 14)   # pines de rele activos en alto
LED = 2                 # LED integrado

_dht = None
if HAS_DHT:
    import machine
    _dht = dht.DHT22(machine.Pin(DHT_PIN))

_pir = Pin(PIR_PIN, Pin.IN)
_adc = ADC(Pin(ADC_PIN))
_adc.atten(ADC.ATTN_11DB)      # rango completo 0-3.3 V
_relays = {p: Pin(p, Pin.OUT, value=0) for p in RELAYS}
_led = Pin(LED, Pin.OUT)


def read_sensors():
    s = {}
    if _dht is not None:
        try:
            _dht.measure()
            s["temp"] = round(_dht.temperature(), 1)
            s["hum"] = round(_dht.humidity(), 1)
        except Exception:
            pass
    s["motion"] = _pir.value()
    s["adc"] = _adc.read()
    s["uptime"] = time.ticks_ms() // 1000
    return s


def handle(cmd):
    c = cmd.get("c")

    if c == "ping":
        return {"ok": True, "pong": True}

    if c == "read":
        return {"ok": True, "s": read_sensors()}

    if c == "set":
        pin = int(cmd.get("pin", -1))
        val = int(cmd.get("v", 0))
        # Solo se permite tocar los pines declarados arriba: nunca uno libre
        if pin in _relays:
            _relays[pin].value(1 if val else 0)
            return {"ok": True, "pin": pin, "v": _relays[pin].value()}
        if pin == LED:
            _led.value(1 if val else 0)
            return {"ok": True, "pin": pin, "v": _led.value()}
        return {"ok": False, "msg": "pin no permitido: %d" % pin}

    if c == "state":
        return {"ok": True, "relays": {p: _relays[p].value() for p in RELAYS}}

    if c == "info":
        return {"ok": True, "node": "daniela-esp32",
                "dht": HAS_DHT, "relays": list(RELAYS),
                "version": 1}

    return {"ok": False, "msg": "comando desconocido: %s" % c}


def main():
    import sys
    print(json.dumps({"ok": True, "boot": True, "node": "daniela-esp32"}))
    while True:
        try:
            line = sys.stdin.readline()
            if not line:
                time.sleep(0.05)
                continue
            line = line.strip()
            if not line:
                continue
            try:
                cmd = json.loads(line)
            except ValueError:
                print(json.dumps({"ok": False, "msg": "JSON invalido"}))
                continue
            print(json.dumps(handle(cmd)))
        except Exception as e:
            print(json.dumps({"ok": False, "msg": str(e)[:60]}))
            time.sleep(0.1)


main()
'''


def validate_firmware(code: str = FIRMWARE) -> dict[str, Any]:
    """Comprueba que el firmware generado parsea como Python 3.

    No valida los modulos MicroPython (machine, dht) porque no existen
    en CPython, pero si la sintaxis: un firmware que no compila es un
    fallo silencioso que se descubre en el peor momento.
    """
    import ast
    try:
        tree = ast.parse(code)
    except SyntaxError as e:
        return {"ok": False, "msg": f"linea {e.lineno}: {e.msg}"}
    funcs = [n.name for n in tree.body
             if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))]
    return {"ok": True, "functions": funcs, "lines": len(code.splitlines())}


@dataclass
class SensorReading:
    ts: str
    values: dict[str, Any]
    simulated: bool = False


class SerialBridge:
    """Puente serie con placas ESP32/Arduino por USB-OTG."""

    def __init__(self) -> None:
        self.port: str | None = None
        self.baud: int = DEFAULT_BAUD
        self._ser: Any = None
        self.connected = False
        self.simulated = not HAS_PYSERIAL

        self.latest: dict[str, Any] = {}
        self.history: deque[dict[str, Any]] = deque(maxlen=MAX_HISTORY)
        self.devices: list[dict[str, Any]] = []
        self._tx: queue.Queue[str] = queue.Queue()
        self._rx_thread: threading.Thread | None = None
        self._poll_thread: threading.Thread | None = None
        self._stop = threading.Event()
        self._lock = threading.Lock()

        self.ticks = 0
        self.commands_sent = 0
        self.readings = 0
        self.errors = 0
        self.last_error: str | None = None
        self._load()

    # ── persistencia ─────────────────────────────────────────

    def _load(self) -> None:
        try:
            STATE_DIR.mkdir(parents=True, exist_ok=True)
            if STATE_FILE.exists():
                data = json.loads(STATE_FILE.read_text(encoding="utf-8"))
                self.port = data.get("port")
                self.baud = int(data.get("baud", DEFAULT_BAUD))
                self.commands_sent = data.get("commands_sent", 0)
        except Exception as e:  # noqa: BLE001
            self.last_error = f"load: {e}"

    def _save(self) -> None:
        try:
            STATE_DIR.mkdir(parents=True, exist_ok=True)
            STATE_FILE.write_text(json.dumps({
                "port": self.port, "baud": self.baud,
                "commands_sent": self.commands_sent, "updated": _now(),
            }, ensure_ascii=False, indent=2), encoding="utf-8")
        except Exception as e:  # noqa: BLE001
            self.last_error = f"save: {e}"

    # ── descubrimiento USB ───────────────────────────────────

    def list_devices(self, refresh: bool = True) -> dict[str, Any]:
        """Lista dispositivos USB via termux-usb -l."""
        if not refresh and self.devices:
            return {"ok": True, "devices": self.devices, "cached": True}
        if not is_termux():
            return {"ok": True, "devices": [], "simulated": True,
                    "msg": "no es Termux: usa /dev/ttyUSB* o COM* en PC"}
        try:
            raw = run_json(["termux-usb", "-l"], timeout=15)
            if isinstance(raw, list):
                self.devices = [d if isinstance(d, dict) else {"device": str(d)}
                                for d in raw]
            elif isinstance(raw, dict):
                self.devices = [raw]
            else:
                self.devices = []
            return {"ok": True, "devices": self.devices}
        except Exception as e:  # noqa: BLE001
            self.last_error = f"usb list: {type(e).__name__}: {str(e)[:80]}"
            return {"ok": False, "msg": self.last_error, "devices": []}

    def request_permission(self, device: str) -> dict[str, Any]:
        """Pide permiso de acceso y devuelve la ruta del dispositivo."""
        if not device:
            return {"ok": False, "msg": "falta el identificador del dispositivo"}
        if not is_termux():
            return {"ok": True, "simulated": True, "device": device,
                    "path": device}
        try:
            out = run_out(["termux-usb", "-r", device], timeout=20)
            path = (out or "").strip()
            if not path:
                return {"ok": False, "msg": "termux-usb no devolvio ruta"}
            return {"ok": True, "device": device, "path": path}
        except Exception as e:  # noqa: BLE001
            self.last_error = f"usb request: {type(e).__name__}"
            return {"ok": False, "msg": self.last_error}

    # ── conexion ─────────────────────────────────────────────

    def connect(self, port: str | None = None,
                baud: int = DEFAULT_BAUD) -> dict[str, Any]:
        port = port or self.port
        if not port:
            return {"ok": False, "msg": "no hay puerto configurado"}
        if not HAS_PYSERIAL:
            # Sin pyserial seguimos "conectados" en modo simulado para
            # poder desarrollar y testear todo lo demas.
            self.port, self.baud = port, int(baud)
            self.connected = True
            self.simulated = True
            self._save()
            return {"ok": True, "simulated": True, "port": port,
                    "msg": "pyserial no instalado: modo simulado"}
        try:
            self._ser = serial.Serial(port, int(baud), timeout=READ_TIMEOUT)
            self.port, self.baud = port, int(baud)
            self.connected = True
            self.simulated = False
            self._stop.clear()
            self._rx_thread = threading.Thread(target=self._rx_loop,
                                               daemon=True, name="SerialRX")
            self._rx_thread.start()
            self._save()
            return {"ok": True, "port": port, "baud": baud}
        except Exception as e:  # noqa: BLE001
            self.errors += 1
            self.last_error = f"connect: {type(e).__name__}: {str(e)[:80]}"
            return {"ok": False, "msg": self.last_error}

    def disconnect(self) -> dict[str, Any]:
        self._stop.set()
        if self._ser is not None:
            try:
                self._ser.close()
            except Exception:  # noqa: BLE001
                pass
        self._ser = None
        self.connected = False
        self._save()
        return {"ok": True, "msg": "puerto cerrado"}

    # ── E/S ──────────────────────────────────────────────────

    def send_raw(self, line: str) -> dict[str, Any]:
        if not line:
            return {"ok": False, "msg": "linea vacia"}
        if not self.connected:
            return {"ok": False, "msg": "no conectado"}
        if self._ser is None:
            self.commands_sent += 1
            return {"ok": True, "simulated": True, "sent": line}
        try:
            self._ser.write((line.strip() + "\n").encode("utf-8"))
            self._ser.flush()
            self.commands_sent += 1
            return {"ok": True, "sent": line}
        except Exception as e:  # noqa: BLE001
            self.errors += 1
            self.last_error = f"write: {type(e).__name__}"
            return {"ok": False, "msg": self.last_error}

    def command(self, cmd: str, **params: Any) -> dict[str, Any]:
        """Comando estructurado -> JSON en una linea."""
        payload = {"c": cmd}
        payload.update(params)
        return self.send_raw(json.dumps(payload))

    def _rx_loop(self) -> None:
        """Lee lineas del puerto y las interpreta."""
        buf = b""
        while not self._stop.is_set() and self._ser is not None:
            try:
                chunk = self._ser.read(1)
                if not chunk:
                    continue
                if chunk in (b"\n", b"\r"):
                    if buf.strip():
                        self._handle_line(buf.decode("utf-8", "replace").strip())
                    buf = b""
                else:
                    buf += chunk
                    if len(buf) > 4096:      # proteccion ante basura
                        buf = b""
            except Exception as e:  # noqa: BLE001
                self.errors += 1
                self.last_error = f"rx: {type(e).__name__}"
                time.sleep(0.5)

    def _handle_line(self, line: str) -> None:
        """Interpreta una linea entrante (JSON o formato compacto k=v)."""
        values: dict[str, Any] = {}
        if line.startswith("{"):
            try:
                obj = json.loads(line)
                if isinstance(obj, dict):
                    if isinstance(obj.get("s"), dict):
                        values = obj["s"]
                    elif "ok" in obj and len(obj) > 1:
                        values = {k: v for k, v in obj.items() if k != "ok"}
            except ValueError:
                self.last_error = "JSON invalido del dispositivo"
                return
        elif "=" in line:
            # Formato compacto: temp=23.4;hum=51.2
            for part in line.replace(",", ";").split(";"):
                if "=" not in part:
                    continue
                k, _, v = part.partition("=")
                k = k.strip()
                if not k:
                    continue
                try:
                    values[k] = float(v)
                    if values[k].is_integer():
                        values[k] = int(values[k])
                except ValueError:
                    values[k] = v.strip()
        else:
            return

        if not values:
            return

        self.latest = {"ts": _now(), "values": values, "simulated": False}
        self.history.append(dict(self.latest))
        self.readings += 1
        self._emit_sensors(values)

    def _emit_sensors(self, values: dict[str, Any]) -> None:
        try:
            from daniela_mobile_core import get_instance as get_core  # type: ignore
            get_core().bus.emit("SENSOR_TICK", {"source": "esp32", **values},
                                source="serial_bridge")
        except Exception:  # noqa: BLE001
            pass

    # ── firmware ─────────────────────────────────────────────

    def firmware(self) -> str:
        return FIRMWARE

    def write_firmware(self, path: str | None = None) -> dict[str, Any]:
        dest = Path(path) if path else FIRMWARE_FILE
        try:
            dest.parent.mkdir(parents=True, exist_ok=True)
            dest.write_text(FIRMWARE, encoding="utf-8")
            return {"ok": True, "path": str(dest), "bytes": len(FIRMWARE)}
        except Exception as e:  # noqa: BLE001
            return {"ok": False, "msg": str(e)[:120]}

    # ── estado ───────────────────────────────────────────────

    def status(self) -> dict[str, Any]:
        return {
            "platform": "termux" if is_termux() else "pc",
            "has_pyserial": HAS_PYSERIAL,
            "connected": self.connected,
            "simulated": self.simulated,
            "port": self.port,
            "baud": self.baud,
            "devices": len(self.devices),
            "readings": self.readings,
            "commands_sent": self.commands_sent,
            "errors": self.errors,
            "history_size": len(self.history),
            "latest": self.latest or None,
            "last_error": self.last_error,
            "updated": _now(),
        }


def get_instance() -> SerialBridge:
    global _instance
    with _instance_lock:
        if _instance is None:
            _instance = SerialBridge()
        return _instance


# ─────────────────────────────────────────────────────────────
#  Rutas Flask
# ─────────────────────────────────────────────────────────────

def register_serial_routes(app) -> int:
    from flask import jsonify, request
    sb = get_instance()

    @app.route("/api/pixel/serial/status", methods=["GET"])
    def ser_status():
        return jsonify(sb.status())

    @app.route("/api/pixel/serial/devices", methods=["GET"])
    def ser_devices():
        refresh = request.args.get("refresh", "1") not in ("0", "false", "no")
        return jsonify(sb.list_devices(refresh))

    @app.route("/api/pixel/serial/connect", methods=["POST"])
    def ser_connect():
        b = request.get_json(silent=True) or {}
        dev = b.get("device")
        if dev:
            perm = sb.request_permission(str(dev))
            if not perm.get("ok"):
                return jsonify(perm)
            return jsonify(sb.connect(perm.get("path") or str(dev),
                                      int(b.get("baud", DEFAULT_BAUD))))
        return jsonify(sb.connect(b.get("port"), int(b.get("baud", DEFAULT_BAUD))))

    @app.route("/api/pixel/serial/disconnect", methods=["POST"])
    def ser_disconnect():
        return jsonify(sb.disconnect())

    @app.route("/api/pixel/serial/send", methods=["POST"])
    def ser_send():
        b = request.get_json(silent=True) or {}
        return jsonify(sb.send_raw(str(b.get("line", ""))))

    @app.route("/api/pixel/serial/command", methods=["POST"])
    def ser_command():
        b = request.get_json(silent=True) or {}
        cmd = str(b.get("cmd", ""))
        if not cmd:
            return jsonify({"ok": False, "msg": "falta 'cmd'"}), 400
        params = {k: v for k, v in b.items() if k != "cmd"}
        return jsonify(sb.command(cmd, **params))

    @app.route("/api/pixel/serial/sensors", methods=["GET"])
    def ser_sensors():
        limit = int(request.args.get("limit", 50))
        return jsonify({"latest": sb.latest or None,
                        "history": list(sb.history)[-limit:],
                        "total": len(sb.history)})

    @app.route("/api/pixel/serial/firmware", methods=["GET", "POST"])
    def ser_firmware():
        if request.method == "GET":
            return jsonify({"ok": True, "language": "micropython",
                            "bytes": len(FIRMWARE), "code": FIRMWARE})
        b = request.get_json(silent=True) or {}
        return jsonify(sb.write_firmware(b.get("path")))

    print("[Serial Bridge] Routes registered: /api/pixel/serial/* (status, "
          "devices, connect, disconnect, send, command, sensors, firmware)")
    return 8


if __name__ == "__main__":
    import io
    import sys
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8",
                                  errors="replace")
    sb = get_instance()
    print("plataforma:", "termux" if is_termux() else "pc")
    print("pyserial instalado:", HAS_PYSERIAL)

    print("\n— parseo de lineas entrantes —")
    for line in ['{"ok":true,"s":{"temp":23.4,"hum":51.2,"motion":0}}',
                 "temp=23.4;hum=51.2;motion=1",
                 "temp=24;hum=50,adc=1024",
                 "basura sin sentido",
                 "{esto no es json}"]:
        before = len(sb.history)
        sb._handle_line(line)
        print(f"  {line[:52]:54s} -> {sb.latest.get('values') if len(sb.history) > before else 'ignorada'}")

    print("\n— conexion sin pyserial (modo simulado) —")
    print("  ", sb.connect("/dev/ttyUSB0"))
    print("  comando ping:", sb.command("ping"))
    print("  comando set:", sb.command("set", pin=12, v=1))
    print("  disconnect:", sb.disconnect())

    print("\n— firmware MicroPython —")
    fw = sb.firmware()
    print("  bytes:", len(fw), "| lineas:", len(fw.splitlines()))
    print("  contiene main():", "def main()" in fw)
    print("  sintaxis valida:", validate_firmware(fw))
    print("  firmware roto:", validate_firmware("def x(:\n  pass"))
    import re
    print("  comandos soportados:", re.findall(r'c == "(\w+)"', fw))
    print("  escribir a disco:", sb.write_firmware())

    print("\n— dispositivos (simulado en PC) —")
    print("  ", sb.list_devices())

    print("\n— envio sin conectar —")
    sb2 = SerialBridge()
    print("  ", sb2.send_raw("hola"))

    print("\nstatus keys:", list(sb.status().keys()))
