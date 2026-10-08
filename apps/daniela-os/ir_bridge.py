#!/usr/bin/env python3
"""
Mando Universal IR — Daniela controla el mundo fisico (E-07 / Fase 7)
======================================================================
Home Assistant solo cubre dispositivos INTELIGENTES. La tele, el aire
acondicionado y el proyector siguen siendo tontos. `termux-infrared-transmit`
convierte el Pixel (si tiene blaster IR) en un mando universal.

El problema de los mandos universales es la libreria de codigos: normalmente
es una lista de hex opacos copiados de internet. Aqui hay un
**CODIFICADOR DE PROTOCOLOS**, asi que Daniela genera el codigo a partir de
la direccion del fabricante y el comando:

    NEC      — 38 kHz, 32 bits (Samsung, LG, Toshiba, la mayoria de TVs)
    NEC-EXT  — direccion de 16 bits (equipos de audio, proyectores)
    RC5      — 36 kHz, bi-phase Manchester (Philips, Thomson, algunos AC)

Con eso no hace falta "aprender" cada boton: conociendo el modelo se
genera. Y si no, `learn()` guarda un patron crudo capturado.

Tambien hay MACROS: secuencias de varios codigos con esperas.
"Daniela, pon la tele en Netflix" = [encender, esperar 3 s, HDMI2, ...].

Si el Pixel NO tiene hardware IR, degrada a Home Assistant (ya integrado
en pixel_iot_real.py) en lugar de fallar.

Seguridad: todo comando pasa por safe_exec. 0 os.system, 0 shell=True.

Rutas:
  GET  /api/pixel/ir/status            — capacidades IR del dispositivo
  GET  /api/pixel/ir/frequencies       — frecuencias portadoras soportadas
  GET  /api/pixel/ir/library           — libreria de codigos
  POST /api/pixel/ir/learn             — guarda un codigo (crudo o protocolo)
  POST /api/pixel/ir/send              — envia un codigo por nombre
  POST /api/pixel/ir/send_raw          — envia frecuencia + patron crudo
  GET  /api/pixel/ir/macros            — lista de macros
  POST /api/pixel/ir/macro             — ejecuta o crea una macro
  GET  /api/pixel/ir/devices           — dispositivos configurados

Coste: $0/mes — IR del Pixel o dongle USB-IR (~3 EUR)
"""

from __future__ import annotations

import json
import os
import threading
import time
from dataclasses import asdict, dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any

from safe_exec import run_code, run_out

PROJECT_ROOT = Path(__file__).resolve().parent
STATE_DIR = PROJECT_ROOT / "data" / "ir_bridge"
LIB_FILE = STATE_DIR / "codes.json"
MACRO_FILE = STATE_DIR / "macros.json"

# Frecuencias portadoras habituales (Hz)
DEFAULT_FREQ = 38000

# ── Temporizacion NEC (microsegundos) ────────────────────────
NEC_LEAD_MARK = 9000
NEC_LEAD_SPACE = 4500
NEC_BIT_MARK = 560
NEC_ZERO_SPACE = 560
NEC_ONE_SPACE = 1690
NEC_TRAIL = 560
NEC_REPEAT_SPACE = 2250

# ── Temporizacion RC5 (microsegundos) ────────────────────────
RC5_HALF = 889  # 1.778 ms por bit, medio bit = 889 us

_instance: IRBridge | None = None
_instance_lock = threading.Lock()


def is_termux() -> bool:
    return os.path.exists("/data/data/com.termux/files/usr/bin")


def _now() -> str:
    return datetime.now().isoformat(timespec="seconds")


# ─────────────────────────────────────────────────────────────
#  Codificadores de protocolo
# ─────────────────────────────────────────────────────────────


def encode_nec(address: int, command: int, extended: bool = False) -> list[int]:
    """Genera el patron NEC en microsegundos alternando marca/espacio.

    NEC clasico: 8 bits de direccion + 8 invertidos + 8 de comando + 8 invertidos.
    NEC extendido: direccion de 16 bits (sin bytes invertidos).
    """
    pattern: list[int] = [NEC_LEAD_MARK, NEC_LEAD_SPACE]

    if extended:
        # NEC extendido: direccion de 16 bits + comando + comando invertido
        bits: list[int] = []
        for i in range(15, -1, -1):
            bits.append((address >> i) & 1)
        cmd_e = command & 0xFF
        for value in (cmd_e, (~cmd_e) & 0xFF):
            for i in range(7, -1, -1):
                bits.append((value >> i) & 1)
    else:
        addr = address & 0xFF
        cmd = command & 0xFF
        bits = []
        for value in (addr, (~addr) & 0xFF, cmd, (~cmd) & 0xFF):
            for i in range(7, -1, -1):
                bits.append((value >> i) & 1)

    for bit in bits:
        pattern.append(NEC_BIT_MARK)
        pattern.append(NEC_ONE_SPACE if bit else NEC_ZERO_SPACE)
    pattern.append(NEC_TRAIL)
    return pattern


def encode_rc5(address: int, command: int, toggle: int = 0) -> list[int]:
    """Genera el patron RC5 (bi-phase Manchester, 14 bits)."""
    # RC5: 2 bits de start, 1 de toggle, 5 de direccion, 6 de comando
    bits: list[int] = [1, 1, toggle & 1]
    for i in range(4, -1, -1):
        bits.append((address >> i) & 1)
    for i in range(5, -1, -1):
        bits.append((command >> i) & 1)

    # Cada bit son dos semiciclos Manchester: 1 = espacio->marca, 0 = marca->espacio
    raw: list[tuple[int, int]] = []
    for bit in bits:
        if bit:
            raw.append((0, 1))
        else:
            raw.append((1, 0))

    # Compactar semiciclos iguales consecutivos
    pattern: list[int] = []
    level, count = raw[0][0], 0
    for half in raw:
        for lvl in half:
            if lvl == level:
                count += 1
            else:
                pattern.append(count * RC5_HALF)
                level = lvl
                count = 1
    pattern.append(count * RC5_HALF)
    return pattern


def pattern_to_str(pattern: list[int]) -> str:
    return ",".join(str(int(v)) for v in pattern)


def parse_pattern(raw: str) -> list[int]:
    """Acepta "9000,4500,560..." o "[9000, 4500]"."""
    cleaned = raw.strip().strip("[]")
    out: list[int] = []
    for part in cleaned.replace(";", ",").split(","):
        part = part.strip()
        if not part:
            continue
        try:
            out.append(int(float(part)))
        except ValueError as e:
            raise ValueError(f"valor no numerico en el patron: {part!r}") from e
    if not out:
        raise ValueError("patron vacio")
    return out


# ─────────────────────────────────────────────────────────────


@dataclass
class IRCode:
    name: str
    frequency: int = DEFAULT_FREQ
    pattern: str = ""
    protocol: str = "raw"  # nec | nec-ext | rc5 | raw
    device: str = ""
    room: str = ""
    address: int | None = None
    command: int | None = None
    note: str = ""
    created: str = field(default_factory=_now)
    uses: int = 0


@dataclass
class Macro:
    name: str
    steps: list[dict[str, Any]] = field(default_factory=list)
    note: str = ""
    created: str = field(default_factory=_now)
    uses: int = 0


class IRBridge:
    """Mando universal: protocolos, libreria, macros y degradacion a HA."""

    def __init__(self) -> None:
        self.codes: dict[str, IRCode] = {}
        self.macros: dict[str, Macro] = {}
        self.sent = 0
        self.failed = 0
        self._frequencies: list[int] | None = None
        self._has_ir: bool | None = None
        self.last_error: str | None = None
        self._lock = threading.Lock()
        self._load()
        self._seed_library()

    # ── persistencia ─────────────────────────────────────────

    def _load(self) -> None:
        try:
            STATE_DIR.mkdir(parents=True, exist_ok=True)
        except Exception as e:  # noqa: BLE001
            self.last_error = f"mkdir: {e}"
        try:
            if LIB_FILE.exists():
                data = json.loads(LIB_FILE.read_text(encoding="utf-8"))
                for name, c in data.get("codes", {}).items():
                    self.codes[name] = IRCode(**c)
                self.sent = data.get("sent", 0)
                self.failed = data.get("failed", 0)
        except Exception as e:  # noqa: BLE001
            self.last_error = f"load codes: {e}"
        try:
            if MACRO_FILE.exists():
                data = json.loads(MACRO_FILE.read_text(encoding="utf-8"))
                for name, m in data.get("macros", {}).items():
                    self.macros[name] = Macro(**m)
        except Exception as e:  # noqa: BLE001
            self.last_error = f"load macros: {e}"

    def _save(self) -> None:
        try:
            STATE_DIR.mkdir(parents=True, exist_ok=True)
            LIB_FILE.write_text(
                json.dumps(
                    {
                        "codes": {k: asdict(v) for k, v in self.codes.items()},
                        "sent": self.sent,
                        "failed": self.failed,
                        "updated": _now(),
                    },
                    ensure_ascii=False,
                    indent=2,
                ),
                encoding="utf-8",
            )
            MACRO_FILE.write_text(
                json.dumps(
                    {
                        "macros": {k: asdict(v) for k, v in self.macros.items()},
                        "updated": _now(),
                    },
                    ensure_ascii=False,
                    indent=2,
                ),
                encoding="utf-8",
            )
        except Exception as e:  # noqa: BLE001
            self.last_error = f"save: {e}"

    def _seed_library(self) -> None:
        """Libreria de arranque: TVs Samsung/LG genericas por protocolo NEC.

        Son plantillas reales de protocolo, no magia: si tu mando usa otra
        direccion, se sobreescriben con learn() o se generan con
        add_protocol().
        """
        if self.codes:
            return
        seeds = [
            ("tv_samsung_power", 0x0707, 0x02, "Samsung TV", "salon"),
            ("tv_samsung_hdmi1", 0x0707, 0x0D, "Samsung TV", "salon"),
            ("tv_samsung_hdmi2", 0x0707, 0x0C, "Samsung TV", "salon"),
            ("tv_samsung_vol_up", 0x0707, 0x07, "Samsung TV", "salon"),
            ("tv_samsung_vol_down", 0x0707, 0x0B, "Samsung TV", "salon"),
            ("tv_samsung_mute", 0x0707, 0x0F, "Samsung TV", "salon"),
            ("tv_lg_power", 0x04FB, 0x08, "LG TV", "salon"),
            ("tv_lg_input", 0x04FB, 0x0B, "LG TV", "salon"),
        ]
        for name, addr, cmd, dev, room in seeds:
            self.codes[name] = IRCode(
                name=name,
                frequency=DEFAULT_FREQ,
                pattern=pattern_to_str(encode_nec(addr, cmd, extended=True)),
                protocol="nec-ext",
                device=dev,
                room=room,
                address=addr,
                command=cmd,
                note="plantilla generada por protocolo — ajusta con learn()",
            )
        # Una macro de ejemplo que demuestra el concepto
        self.macros["netflix"] = Macro(
            name="netflix",
            steps=[
                {"code": "tv_samsung_power", "wait": 3.0},
                {"code": "tv_samsung_hdmi2", "wait": 1.5},
            ],
            note="Enciende la tele y salta a HDMI2 (donde esta el Chromecast)",
        )
        self._save()

    # ── capacidades ──────────────────────────────────────────

    def has_ir(self) -> bool:
        """Detecta blaster IR: termux-infrared-frequencies responde."""
        if self._has_ir is not None:
            return self._has_ir
        if not is_termux():
            self._has_ir = False
            return False
        try:
            out = run_out(["termux-infrared-frequencies"], timeout=8)
            self._has_ir = bool(out and out.strip())
            if self._has_ir:
                try:
                    data = json.loads(out)
                    if isinstance(data, dict):
                        freqs = data.get("frequencies") or []
                        self._frequencies = [int(f) for f in freqs]
                except Exception:  # noqa: BLE001
                    pass
        except Exception:  # noqa: BLE001
            self._has_ir = False
        return self._has_ir

    def frequencies(self) -> dict[str, Any]:
        return {
            "has_ir": self.has_ir(),
            "frequencies": self._frequencies,
            "default": DEFAULT_FREQ,
            "platform": "termux" if is_termux() else "pc",
            "note": (
                "sin hardware IR — las ordenes se intentan por Home Assistant"
                if not self.has_ir()
                else ""
            ),
        }

    # ── envio ────────────────────────────────────────────────

    def send_raw(self, frequency: int, pattern: str) -> dict[str, Any]:
        """Envia un patron crudo. Valida antes de llamar al sistema."""
        try:
            values = parse_pattern(pattern)
        except ValueError as e:
            return {"ok": False, "msg": str(e)}

        if len(values) % 2 == 0:
            return {
                "ok": False,
                "msg": (
                    "el patron debe tener numero IMPAR de valores "
                    f"(marca/espacio alternos empezando por marca); "
                    f"recibidos {len(values)}"
                ),
            }
        if any(v <= 0 for v in values):
            return {"ok": False, "msg": "el patron contiene valores no positivos"}
        if len(values) > 1000:
            return {"ok": False, "msg": "patron demasiado largo (max 1000 valores)"}

        freq = int(frequency)
        if not 20000 <= freq <= 60000:
            return {"ok": False, "msg": f"frecuencia fuera de rango (20-60 kHz): {freq}"}

        if not is_termux():
            self.sent += 1
            return {
                "ok": True,
                "simulated": True,
                "frequency": freq,
                "values": len(values),
                "msg": "no es Termux: envio simulado",
            }

        try:
            rc = run_code(
                ["termux-infrared-transmit", "-f", str(freq), pattern_to_str(values)], timeout=20
            )
            if rc == 0:
                self.sent += 1
                self._save()
                return {"ok": True, "frequency": freq, "values": len(values)}
            self.failed += 1
            self.last_error = f"transmit rc={rc}"
            return {"ok": False, "msg": f"termux-infrared-transmit rc={rc}"}
        except Exception as e:  # noqa: BLE001
            self.failed += 1
            self.last_error = f"{type(e).__name__}: {str(e)[:80]}"
            return {"ok": False, "msg": self.last_error}

    def send(self, name: str) -> dict[str, Any]:
        """Envia un codigo de la libreria por su nombre."""
        code = self.codes.get(name)
        if not code:
            return {
                "ok": False,
                "msg": f"codigo '{name}' no existe",
                "available": sorted(self.codes)[:20],
            }
        res = self.send_raw(code.frequency, code.pattern)
        if res.get("ok"):
            code.uses += 1
            self._save()
            res["code"] = name
        return res

    # ── alta de codigos ──────────────────────────────────────

    def learn(
        self,
        name: str,
        protocol: str = "raw",
        frequency: int = DEFAULT_FREQ,
        pattern: str = "",
        address: int | None = None,
        command: int | None = None,
        device: str = "",
        room: str = "",
        note: str = "",
    ) -> dict[str, Any]:
        """Guarda un codigo: por patron crudo o generado por protocolo."""
        if protocol in ("nec", "nec-ext", "rc5"):
            if address is None or command is None:
                return {"ok": False, "msg": f"el protocolo {protocol} necesita address y command"}
            try:
                if protocol == "rc5":
                    pat = encode_rc5(int(address), int(command))
                else:
                    pat = encode_nec(int(address), int(command), extended=(protocol == "nec-ext"))
            except Exception as e:  # noqa: BLE001
                return {"ok": False, "msg": f"no se pudo codificar: {e}"}
            pattern = pattern_to_str(pat)
        else:
            if not pattern:
                return {"ok": False, "msg": "para protocolo raw hace falta el patron"}
            try:
                pattern = pattern_to_str(parse_pattern(pattern))
            except ValueError as e:
                return {"ok": False, "msg": str(e)}

        self.codes[name] = IRCode(
            name=name,
            frequency=int(frequency),
            pattern=pattern,
            protocol=protocol,
            device=device,
            room=room,
            address=address,
            command=command,
            note=note,
        )
        self._save()
        return {"ok": True, "code": asdict(self.codes[name])}

    def delete(self, name: str) -> dict[str, Any]:
        if name not in self.codes:
            return {"ok": False, "msg": "no existe"}
        del self.codes[name]
        self._save()
        return {"ok": True, "deleted": name, "remaining": len(self.codes)}

    # ── macros ───────────────────────────────────────────────

    def add_macro(self, name: str, steps: list[dict[str, Any]], note: str = "") -> dict[str, Any]:
        """steps: [{"code": nombre, "wait": segundos}, ...]"""
        if not steps:
            return {"ok": False, "msg": "la macro necesita al menos un paso"}
        unknown = [s.get("code") for s in steps if s.get("code") and s["code"] not in self.codes]
        if unknown:
            return {"ok": False, "msg": "codigos desconocidos", "unknown": unknown}
        self.macros[name] = Macro(name=name, steps=steps, note=note)
        self._save()
        return {"ok": True, "macro": asdict(self.macros[name])}

    def run_macro(self, name: str) -> dict[str, Any]:
        m = self.macros.get(name)
        if not m:
            return {
                "ok": False,
                "msg": f"macro '{name}' no existe",
                "available": sorted(self.macros),
            }
        results: list[dict[str, Any]] = []
        for i, step in enumerate(m.steps, start=1):
            code = step.get("code")
            res = self.send(code) if code else {"ok": False, "msg": "paso sin codigo"}
            results.append({"step": i, "code": code, **res})
            if not res.get("ok"):
                m.uses += 1
                self._save()
                return {"ok": False, "macro": name, "msg": f"fallo el paso {i}", "results": results}
            wait = float(step.get("wait", 0) or 0)
            if wait > 0:
                time.sleep(wait)
        m.uses += 1
        self._save()
        return {"ok": True, "macro": name, "steps": len(results), "results": results}

    # ── dispositivos ─────────────────────────────────────────

    def devices(self) -> dict[str, Any]:
        out: dict[str, list[str]] = {}
        for c in self.codes.values():
            dev = c.device or "sin clasificar"
            out.setdefault(dev, [])
            if c.name not in out[dev]:
                out[dev].append(c.name)
        return {"devices": {k: sorted(v) for k, v in out.items()}, "total_codes": len(self.codes)}

    def status(self) -> dict[str, Any]:
        return {
            "platform": "termux" if is_termux() else "pc",
            "has_ir": self.has_ir(),
            "codes": len(self.codes),
            "macros": len(self.macros),
            "sent": self.sent,
            "failed": self.failed,
            "default_frequency": DEFAULT_FREQ,
            "protocols": ["nec", "nec-ext", "rc5", "raw"],
            "fallback": "home-assistant" if not self.has_ir() else None,
            "last_error": self.last_error,
            "updated": _now(),
        }


def get_instance() -> IRBridge:
    global _instance
    with _instance_lock:
        if _instance is None:
            _instance = IRBridge()
        return _instance


# ─────────────────────────────────────────────────────────────
#  Rutas Flask
# ─────────────────────────────────────────────────────────────


def register_ir_routes(app) -> int:
    from flask import jsonify, request

    ir = get_instance()

    @app.route("/api/pixel/ir/status", methods=["GET"])
    def ir_status():
        return jsonify(ir.status())

    @app.route("/api/pixel/ir/frequencies", methods=["GET"])
    def ir_freq():
        return jsonify(ir.frequencies())

    @app.route("/api/pixel/ir/library", methods=["GET"])
    def ir_library():
        dev = request.args.get("device")
        codes = {k: asdict(v) for k, v in ir.codes.items() if not dev or v.device == dev}
        return jsonify({"codes": codes, "total": len(codes)})

    @app.route("/api/pixel/ir/learn", methods=["POST"])
    def ir_learn():
        b = request.get_json(silent=True) or {}
        if not b.get("name"):
            return jsonify({"ok": False, "msg": "falta 'name'"}), 400
        return jsonify(
            ir.learn(
                name=str(b["name"]),
                protocol=str(b.get("protocol", "raw")),
                frequency=int(b.get("frequency", DEFAULT_FREQ)),
                pattern=str(b.get("pattern", "")),
                address=b.get("address"),
                command=b.get("command"),
                device=str(b.get("device", "")),
                room=str(b.get("room", "")),
                note=str(b.get("note", "")),
            )
        )

    @app.route("/api/pixel/ir/send", methods=["POST"])
    def ir_send():
        b = request.get_json(silent=True) or {}
        name = str(b.get("name", ""))
        if not name:
            return jsonify({"ok": False, "msg": "falta 'name'"}), 400
        return jsonify(ir.send(name))

    @app.route("/api/pixel/ir/send_raw", methods=["POST"])
    def ir_send_raw():
        b = request.get_json(silent=True) or {}
        return jsonify(
            ir.send_raw(int(b.get("frequency", DEFAULT_FREQ)), str(b.get("pattern", "")))
        )

    @app.route("/api/pixel/ir/macros", methods=["GET"])
    def ir_macros():
        return jsonify({"macros": {k: asdict(v) for k, v in ir.macros.items()}})

    @app.route("/api/pixel/ir/macro", methods=["POST"])
    def ir_macro():
        b = request.get_json(silent=True) or {}
        if b.get("run"):
            return jsonify(ir.run_macro(str(b["run"])))
        if not b.get("name"):
            return jsonify({"ok": False, "msg": "falta 'name'"}), 400
        return jsonify(ir.add_macro(str(b["name"]), b.get("steps", []), str(b.get("note", ""))))

    @app.route("/api/pixel/ir/devices", methods=["GET"])
    def ir_devices():
        return jsonify(ir.devices())

    print(
        "[IR Bridge] Routes registered: /api/pixel/ir/* (status, frequencies, "
        "library, learn, send, send_raw, macros, macro, devices)"
    )
    return 9


if __name__ == "__main__":
    import io
    import sys

    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
    ir = get_instance()
    print("plataforma:", "termux" if is_termux() else "pc")
    print("tiene IR:", ir.has_ir())

    print("\n— codificador NEC (Samsung power: addr 0x0707, cmd 0x02) —")
    nec = encode_nec(0x0707, 0x02, extended=True)
    print("  valores:", len(nec), "(esperado 67 = 2 + 32 bits x 2 + 1)")
    print("  cabecera:", nec[:4], "| cola:", nec[-1])
    print("  primer bit:", nec[2:4], "(560 + 560 = '0' | 560 + 1690 = '1')")

    print("\n— comprobacion de integridad del protocolo —")
    bits = nec[2:-1]
    pares = [bits[i : i + 2] for i in range(0, len(bits), 2)]
    print("  pares de bit:", len(pares), "(esperado 32)")
    marcas_ok = all(p[0] == NEC_BIT_MARK for p in pares)
    print("  todas las marcas = 560us:", marcas_ok)
    espacios = {p[1] for p in pares}
    print("  espacios usados:", sorted(espacios), "(esperado [560, 1690])")

    print("\n— RC5 (Philips, addr 5, cmd 12) —")
    rc5 = encode_rc5(5, 12)
    print("  valores:", len(rc5), "| multiplos de 889:", all(v % RC5_HALF == 0 for v in rc5))
    print("  patron:", rc5)

    print("\n— validacion de entrada —")
    print("  patron par (8 valores):", ir.send_raw(38000, "100,200,100,200,100,200,100,200"))
    print("  frecuencia fuera de rango:", ir.send_raw(1000, "100,200,100"))
    print("  patron con texto:", ir.send_raw(38000, "100,abc,100"))
    print("  negativo:", ir.send_raw(38000, "100,-5,100"))

    print("\n— libreria sembrada —")
    print("  codigos:", len(ir.codes))
    print("  dispositivos:", ir.devices()["devices"])

    print("\n— envio por nombre (simulado) —")
    print("  ", ir.send("tv_samsung_power"))
    print("  codigo inexistente:", ir.send("no_existe")["msg"])

    print("\n— macro netflix (simulada, sin esperas reales) —")
    m = ir.macros["netflix"]
    print("  pasos:", m.steps)
    print("  ", {k: v for k, v in ir.run_macro("netflix").items() if k != "results"})

    print("\n— aprende un codigo nuevo por protocolo —")
    print(
        "  ",
        {
            k: v
            for k, v in ir.learn(
                "proyector_power",
                protocol="nec",
                address=0x83F4,
                command=0x10,
                device="Proyector",
                room="salon",
            ).items()
            if k != "code"
        },
    )

    print("\nstatus keys:", list(ir.status().keys()))
    ir.delete("proyector_power")
