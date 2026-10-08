#!/usr/bin/env python3
"""
live_wallpaper.py — E-24 · El telefono se ve como Daniela
=========================================================

Es la idea de mayor **impacto percibido por menos codigo** de toda la Fase 10.
Hoy Daniela es invisible hasta que abres una app. Con esto, el fondo del
telefono cambia segun el contexto que ya calcula el context engine (E-05):

    durmiendo    -> azul profundo, casi negro
    en_casa      -> verde azulado, calmado
    en_vehiculo  -> ambar, en movimiento
    caminando    -> verde, activo
    en_mano      -> los colores de Daniela (cian / magenta sobre casi negro)
    caida        -> rojo de alerta (que se vea que paso algo)

Ademas el fondo lleva el **reloj** y una **franja de bateria**, asi que de un
vistazo sabes la hora y cuanta bateria queda sin desbloquear.

Cómo genera la imagen sin dependencias
--------------------------------------
Escribe PNG a mano con `zlib` y `struct`: cabecera IHDR, un bloque IDAT
comprimido y el IEND. Unas 40 lineas y no hace falta ni PIL. Si PIL esta
disponible lo usa para dibujar texto nitido; si no, dibuja los digitos con una
**tipografia de 3x5 pixeles** incluida en el modulo (escalable).

Se aplica con `termux-wallpaper` (Termux:API 0.51+). Si no esta, el PNG se
genera igual y se queda en `data/wallpaper/` para que lo pongas a mano.

Rutas
-----
    GET  /api/pixel/wallpaper/status       estado, tema actual y temas
    GET  /api/pixel/wallpaper/current      el PNG recien generado
    POST /api/pixel/wallpaper/generate     genera sin aplicar
    POST /api/pixel/wallpaper/apply        genera y aplica (contexto o forzado)
    POST /api/pixel/wallpaper/config       resolucion, destino, reloj, bateria
    GET  /api/pixel/wallpaper/themes       paleta de cada contexto
"""

from __future__ import annotations

import json
import math
import struct
import subprocess
import time
import zlib
from pathlib import Path
from typing import Any

# --------------------------------------------------------------------------
# Dependencias opcionales
# --------------------------------------------------------------------------
try:
    from flask import Flask, jsonify, request, send_file
except ImportError:  # pragma: no cover
    Flask = None  # type: ignore
    jsonify = None  # type: ignore
    request = None  # type: ignore
    send_file = None  # type: ignore

try:
    from PIL import Image, ImageDraw  # opcional: solo mejora el texto
except ImportError:
    Image = None  # type: ignore
    ImageDraw = None  # type: ignore


# --------------------------------------------------------------------------
# Constantes
# --------------------------------------------------------------------------
PROJECT_ROOT = Path(__file__).resolve().parent
DATA_DIR = PROJECT_ROOT / "data" / "wallpaper"
OUT_FILE = DATA_DIR / "daniela_wallpaper.png"
CONFIG_FILE = DATA_DIR / "config.json"

# Pixel 8a
ANCHO_DEFAULT = 1080
ALTO_DEFAULT = 2400

# Paleta por contexto: (color_arriba, color_abajo, color_acento)
TEMAS: dict[str, tuple[tuple[int, int, int], ...]] = {
    "durmiendo": ((8, 10, 26), (16, 20, 48), (90, 100, 180)),
    "en_casa": ((6, 32, 34), (10, 58, 56), (93, 202, 165)),
    "caminando": ((14, 38, 16), (24, 74, 28), (151, 196, 89)),
    "en_vehiculo": ((48, 30, 6), (84, 54, 10), (239, 159, 39)),
    "en_mano": ((11, 15, 25), (8, 10, 18), (0, 255, 255)),
    "en_bolsillo": ((10, 10, 14), (6, 6, 9), (70, 70, 90)),
    "quieto": ((12, 14, 22), (18, 22, 34), (120, 130, 160)),
    "caida": ((60, 8, 12), (120, 16, 20), (226, 75, 74)),
    "desconocido": ((10, 12, 20), (16, 20, 32), (110, 120, 150)),
}

# Tipografia minima 3x5 para dibujar la hora sin PIL
GLIFOS: dict[str, list[str]] = {
    "0": ["111", "101", "101", "101", "111"],
    "1": ["010", "110", "010", "010", "111"],
    "2": ["111", "001", "111", "100", "111"],
    "3": ["111", "001", "111", "001", "111"],
    "4": ["101", "101", "111", "001", "001"],
    "5": ["111", "100", "111", "001", "111"],
    "6": ["111", "100", "111", "101", "111"],
    "7": ["111", "001", "010", "010", "010"],
    "8": ["111", "101", "111", "101", "111"],
    "9": ["111", "101", "111", "001", "111"],
    ":": ["000", "010", "000", "010", "000"],
    " ": ["000", "000", "000", "000", "000"],
}


# ==========================================================================
#  Escritor PNG (solo stdlib)
# ==========================================================================
def _chunk(tipo: bytes, datos: bytes) -> bytes:
    return (
        struct.pack(">I", len(datos))
        + tipo
        + datos
        + struct.pack(">I", zlib.crc32(tipo + datos) & 0xFFFFFFFF)
    )


def escribir_png(ruta: Path, ancho: int, alto: int, rgb: bytearray) -> bool:
    """`rgb` son ancho*alto*3 bytes, fila a fila, sin bytes de filtro."""
    if len(rgb) != ancho * alto * 3:
        return False
    crudo = bytearray()
    paso = ancho * 3
    for y in range(alto):
        crudo.append(0)  # filtro None
        crudo += rgb[y * paso : (y + 1) * paso]
    png = (
        b"\x89PNG\r\n\x1a\n"
        + _chunk(b"IHDR", struct.pack(">IIBBBBB", ancho, alto, 8, 2, 0, 0, 0))
        + _chunk(b"IDAT", zlib.compress(bytes(crudo), 6))
        + _chunk(b"IEND", b"")
    )
    ruta.parent.mkdir(parents=True, exist_ok=True)
    ruta.write_bytes(png)
    return True


# ==========================================================================
#  Lienzo
# ==========================================================================
class Lienzo:
    """Un buffer RGB con las pocas operaciones que necesitamos."""

    def __init__(self, ancho: int, alto: int) -> None:
        self.w = ancho
        self.h = alto
        self.buf = bytearray(ancho * alto * 3)

    def punto(self, x: int, y: int, c: tuple[int, int, int]) -> None:
        if 0 <= x < self.w and 0 <= y < self.h:
            i = (y * self.w + x) * 3
            self.buf[i], self.buf[i + 1], self.buf[i + 2] = c

    def rect(self, x0: int, y0: int, x1: int, y1: int, c: tuple[int, int, int]) -> None:
        for y in range(max(0, y0), min(self.h, y1)):
            i = (y * self.w + max(0, x0)) * 3
            for _x in range(max(0, x0), min(self.w, x1)):
                self.buf[i], self.buf[i + 1], self.buf[i + 2] = c
                i += 3

    def degradado(self, arriba: tuple[int, int, int], abajo: tuple[int, int, int]) -> None:
        for y in range(self.h):
            t = y / max(1, self.h - 1)
            t = t * t * (3 - 2 * t)  # suavizado
            c = (
                int(arriba[0] + (abajo[0] - arriba[0]) * t),
                int(arriba[1] + (abajo[1] - arriba[1]) * t),
                int(arriba[2] + (abajo[2] - arriba[2]) * t),
            )
            self.rect(0, y, self.w, y + 1, c)

    def texto(self, s: str, x: int, y: int, escala: int, c: tuple[int, int, int]) -> int:
        """Dibuja con la tipografia 3x5. Devuelve el ancho ocupado."""
        cursor = x
        for ch in s:
            g = GLIFOS.get(ch, GLIFOS[" "])
            for fila, lineas in enumerate(g):
                for col, bit in enumerate(lineas):
                    if bit == "1":
                        self.rect(
                            cursor + col * escala,
                            y + fila * escala,
                            cursor + (col + 1) * escala,
                            y + (fila + 1) * escala,
                            c,
                        )
            cursor += (3 + 1) * escala
        return cursor - x


# ==========================================================================
#  Generador
# ==========================================================================
def generar(
    contexto: str = "en_mano",
    ancho: int = ANCHO_DEFAULT,
    alto: int = ALTO_DEFAULT,
    bateria: int | None = None,
    hora: str | None = None,
    con_reloj: bool = True,
) -> Path:
    """Compone el wallpaper del contexto dado y lo deja en OUT_FILE."""
    arriba, abajo, acento = TEMAS.get(contexto, TEMAS["desconocido"])
    lien = Lienzo(ancho, alto)
    lien.degradado(arriba, abajo)

    # Una rejilla tenue para que no sea un plano muerto
    paso = max(60, ancho // 12)
    tenue = tuple(int(v * 0.35 + acento[i] * 0.10) for i, v in enumerate(arriba))
    for x in range(0, ancho, paso):
        lien.rect(x, 0, x + 1, alto, tenue)
    for y in range(0, alto, paso):
        lien.rect(0, y, ancho, y + 1, tenue)

    # Halo del color de acento, centrado arriba
    cx, cy = ancho // 2, int(alto * 0.30)
    radio = int(ancho * 0.55)
    for dy in range(-radio, radio, 3):
        for dx in range(-radio, radio, 3):
            d = math.hypot(dx, dy)
            if d < radio:
                a = (1 - d / radio) ** 2 * 0.20
                x, y = cx + dx, cy + dy
                if 0 <= x < ancho and 0 <= y < alto:
                    i = (y * ancho + x) * 3
                    for k in range(3):
                        lien.buf[i + k] = min(255, int(lien.buf[i + k] * (1 - a) + acento[k] * a))

    if con_reloj and hora:
        escala = max(8, ancho // 34)
        ancho_txt = len(hora) * 4 * escala
        lien.texto(hora, (ancho - ancho_txt) // 2, cy - escala * 3, escala, acento)

        # Nombre del contexto, mas pequeno y discreto
        escala2 = max(3, escala // 4)
        w2 = len(contexto) * 4 * escala2
        lien.texto(
            contexto.upper().replace("_", " "), (ancho - w2) // 2, cy + escala * 5, escala2, tenue
        )

    if bateria is not None:
        bateria = max(0, min(100, int(bateria)))
        margen = int(ancho * 0.12)
        alto_barra = max(6, ancho // 90)
        y = alto - int(alto * 0.08)
        ancho_total = ancho - 2 * margen
        lien.rect(margen, y, margen + ancho_total, y + alto_barra, tenue)
        relleno = int(ancho_total * bateria / 100)
        color = acento if bateria > 25 else (226, 75, 74)
        lien.rect(margen, y, margen + relleno, y + alto_barra, color)

    OUT_FILE.parent.mkdir(parents=True, exist_ok=True)
    escribir_png(OUT_FILE, ancho, alto, lien.buf)
    return OUT_FILE


def aplicar(ruta: Path, bloqueo: bool = False) -> dict[str, Any]:
    """Aplica el PNG con termux-wallpaper. Degrada si la API no esta."""
    args = ["termux-wallpaper"]
    args.append("-l" if bloqueo else "-f")
    args += ["-f", str(ruta)]
    try:
        r = subprocess.run(args, capture_output=True, timeout=20, shell=False)
        if r.returncode == 0:
            return {"aplicado": True, "destino": "bloqueo" if bloqueo else "inicio"}
        return {
            "aplicado": False,
            "error": (r.stderr or b"").decode("utf-8", "replace")[:180]
            or "termux-wallpaper devolvio error",
        }
    except (OSError, subprocess.SubprocessError) as e:
        return {"aplicado": False, "error": f"termux-wallpaper no disponible: {e}"}


# ==========================================================================
#  Estado del modulo
# ==========================================================================
class WallpaperVivo:
    def __init__(self) -> None:
        self.config = {
            "ancho": ANCHO_DEFAULT,
            "alto": ALTO_DEFAULT,
            "con_reloj": True,
            "bloqueo_tambien": False,
            "auto": False,
        }
        self.contexto = "en_mano"
        self.ultima_generacion: float | None = None
        self.historial: list[dict[str, Any]] = []
        DATA_DIR.mkdir(parents=True, exist_ok=True)
        self._cargar()

    def _cargar(self) -> None:
        if CONFIG_FILE.exists():
            try:
                d = json.loads(CONFIG_FILE.read_text(encoding="utf-8"))
                if isinstance(d, dict):
                    self.config.update({k: v for k, v in d.items() if k in self.config})
            except Exception:
                pass

    def _guardar(self) -> None:
        tmp = CONFIG_FILE.with_suffix(".tmp")
        tmp.write_text(json.dumps(self.config, ensure_ascii=False, indent=1), encoding="utf-8")
        tmp.replace(CONFIG_FILE)

    def configurar(self, **kv: Any) -> dict[str, Any]:
        for k, v in kv.items():
            if k in self.config and isinstance(v, type(self.config[k])):
                self.config[k] = v
        self._guardar()
        return dict(self.config)

    def actualizar(
        self, contexto: str, bateria: int | None = None, aplicar_tambien: bool = False
    ) -> dict[str, Any]:
        self.contexto = contexto if contexto in TEMAS else "desconocido"
        ruta = generar(
            self.contexto,
            int(self.config["ancho"]),
            int(self.config["alto"]),
            bateria,
            time.strftime("%H:%M"),
            bool(self.config["con_reloj"]),
        )
        self.ultima_generacion = time.time()
        info: dict[str, Any] = {
            "contexto": self.contexto,
            "ruta": str(ruta),
            "bytes": ruta.stat().st_size if ruta.exists() else 0,
            "aplicado": None,
        }
        if aplicar_tambien:
            res = aplicar(ruta, bool(self.config["bloqueo_tambien"]))
            info.update(res)
            if res.get("aplicado") and self.config["bloqueo_tambien"]:
                aplicar(ruta, True)
        self.historial.append({"t": time.time(), **info})
        self.historial = self.historial[-50:]
        return info


_instancia: WallpaperVivo | None = None


def get_instance() -> WallpaperVivo:
    global _instancia
    if _instancia is None:
        _instancia = WallpaperVivo()
    return _instancia


# --------------------------------------------------------------------------
#  Rutas Flask
# --------------------------------------------------------------------------
def register_wallpaper_routes(app) -> None:
    if Flask is None:
        return

    def w() -> WallpaperVivo:
        return get_instance()

    @app.route("/api/pixel/wallpaper/status", methods=["GET"], endpoint="wallpaper__status")
    def _status():
        return jsonify(
            {
                "ok": True,
                "contexto": w().contexto,
                "config": w().config,
                "ultima_generacion": w().ultima_generacion,
                "existe": OUT_FILE.exists(),
            }
        )

    @app.route("/api/pixel/wallpaper/current", methods=["GET"], endpoint="wallpaper__current")
    def _current():
        if not OUT_FILE.exists():
            return jsonify({"ok": False, "error": "aun no se ha generado"}), 404
        return send_file(str(OUT_FILE), mimetype="image/png")

    @app.route("/api/pixel/wallpaper/generate", methods=["POST"], endpoint="wallpaper__generate")
    def _generate():
        d = request.get_json(silent=True) or {}
        info = w().actualizar(
            str(d.get("contexto", w().contexto)), d.get("bateria"), aplicar_tambien=False
        )
        return jsonify({"ok": True, **info})

    @app.route("/api/pixel/wallpaper/apply", methods=["POST"], endpoint="wallpaper__apply")
    def _apply():
        d = request.get_json(silent=True) or {}
        info = w().actualizar(
            str(d.get("contexto", w().contexto)), d.get("bateria"), aplicar_tambien=True
        )
        return jsonify({"ok": True, **info})

    @app.route("/api/pixel/wallpaper/config", methods=["POST"], endpoint="wallpaper__config")
    def _config():
        d = request.get_json(silent=True) or {}
        return jsonify({"ok": True, "config": w().configurar(**d)})

    @app.route("/api/pixel/wallpaper/themes", methods=["GET"], endpoint="wallpaper__themes")
    def _themes():
        return jsonify(
            {
                "ok": True,
                "temas": {
                    k: {"arriba": v[0], "abajo": v[1], "acento": v[2]} for k, v in TEMAS.items()
                },
            }
        )

    print(
        "[Live Wallpaper] Routes registered: /api/pixel/wallpaper/* "
        "(status, current, generate, apply, config, themes)"
    )


# --------------------------------------------------------------------------
#  Demo
# --------------------------------------------------------------------------
def _demo() -> None:
    print("=" * 68)
    print(" LIVE WALLPAPER (E-24) — el telefono se ve como Daniela")
    print("=" * 68)
    pequeno = (360, 780)  # mas rapido para la demo
    for contexto in ("durmiendo", "en_casa", "caminando", "en_vehiculo", "en_mano", "caida"):
        ruta = generar(contexto, pequeno[0], pequeno[1], bateria=72, hora="22:15", con_reloj=True)
        kb = ruta.stat().st_size // 1024
        arriba, _, acento = TEMAS[contexto]
        print(f"   {contexto:12s} -> {ruta.name}  {kb:>4} KB   arriba={arriba} acento={acento}")

    print("\n-- el PNG es valido --")
    datos = OUT_FILE.read_bytes()
    print("   firma PNG :", datos[:8] == b"\x89PNG\r\n\x1a\n")
    ancho, alto = struct.unpack(">II", datos[16:24])
    print(f"   dimensiones: {ancho} x {alto}")
    print("   termux-wallpaper:", aplicar(OUT_FILE).get("error", "disponible")[:60])
    print("=" * 68)


if __name__ == "__main__":
    _demo()
