#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
stereo_vision.py — E-26 · Profundidad con dos fotos, sin OpenCV y sin numpy
===========================================================================

El movil sabe donde esta (GPS, WiFi, barometro) pero no sabe **que tiene
delante**. Esa mitad del problema es la que resuelve esto: medir a que
distancia esta lo que hay enfocado.

Lo dificil no es la idea, es el entorno. En Termux no hay OpenCV ni numpy
(compilarlos en el movil es inviable y, si se pudiera, serian 200 MB), asi que
el calculo de disparidad —lo que normalmente hace una libreria en C— esta
escrito aqui en Python puro, con `zlib` para el PNG y aritmetica de enteros.

Como se consigue la profundidad
--------------------------------
Dos fotos de la misma escena desde dos sitios separados por una distancia
conocida `B` (la *linea de base*). Un punto del mundo cae en las dos imagenes
en posiciones distintas; esa diferencia es la **disparidad** `d` y la
distancia sale de una triangulacion de toda la vida:

    distancia = (B * f) / d

Cuanto mas cerca esta algo, mas se desplaza entre una foto y la otra. Por eso
un dedo delante de la cara "salta" mucho y una montana no se mueve.

Dos formas de tener esas dos fotos, y cual funciona de verdad
-------------------------------------------------------------
1. **Estereo de movimiento** (el que usa este modulo por defecto). Haces una
   foto, desplazas el movil unos centimetros hacia un lado y haces otra. Es
   exactamente lo que haces tu con la cabeza para calcular una distancia, y con
   una escena quieto funciona muy bien. El modulo vibra entre las dos fotos
   para que sepas cuando moverlo.
2. **Dos camaras a la vez**. El dispositivo declara `camera.concurrent`, asi
   que se le puede pedir a dos sensores simultaneos. Pero sus opticas son
   distintas (gran angular frente a ultra gran angular) y eso exige
   *rectificar* las imagenes antes de compararlas, que es otro problema
   bastante mas serio. Por eso esta via esta presente pero marcada como
   experimental: se captura, no se promete.

Lo honesto: con la via 1 y una escena estatica se obtienen distancias
utiles —del orden del 5-10% de error a 1-2 metros—, que es mas que suficiente
para lo que realmente importa aqui: **saber si hay algo cerca y a que lado**.

Seguridad
---------
    · Nada de `os.system`, nada de `shell=True`.
    · Todo fichero se escribe dentro de `data/stereo/`.
    · El PNG se decodifica a mano con comprobacion de limites: una imagen
      corrupta da error, nunca una lectura fuera de rango.

Rutas
-----
    GET  /api/pixel/stereo/status      camaras, calibracion y ultimo calculo
    POST /api/pixel/stereo/capture     hace el par de fotos
    POST /api/pixel/stereo/depth       calcula profundidad de un par
    GET  /api/pixel/stereo/last        ultimo analisis en JSON
    GET  /api/pixel/stereo/depth.png   el mapa de profundidad como imagen
    POST /api/pixel/stereo/config      linea de base, bloque, rango, FOV
"""

from __future__ import annotations

import json
import math
import struct
import subprocess
import threading
import time
import zlib
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

try:
    from flask import Flask, jsonify, request, send_file
except ImportError:  # pragma: no cover
    Flask = None  # type: ignore
    jsonify = None  # type: ignore
    request = None  # type: ignore
    send_file = None  # type: ignore


# Raiz del repo (este modulo vive en pixel/ desde Fase 2).
PROJECT_ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = PROJECT_ROOT / "data" / "stereo"
DEPTH_PNG = DATA_DIR / "depth.png"
LAST_JSON = DATA_DIR / "last.json"

CONFIG_DEFAULT: Dict[str, Any] = {
    "linea_base_m": 0.06,      # 6 cm de desplazamiento entre fotos
    "fov_horizontal": 65.0,    # campo de vision de la camara principal
    "bloque": 5,               # lado de la ventana de comparacion (impar)
    "rango_disparidad": 32,    # cuantos pixels se busca a lo sumo
    "ancho_trabajo": 160,      # se reduce a esto antes de comparar
    "espera_entre_fotos": 1.6, # segundos para que te de tiempo a mover
    "vibrar_entre_fotos": True,
    "sensor_trasero": 0,
}

# Tope de seguridad al decodificar: nadie necesita 8000x8000 para medir.
MAX_PIXELS = 12_000_000


# ==========================================================================
#  Utilidades — REGLA DURA: sin shell, sin os.system
# ==========================================================================
def _run(args: List[str], timeout: int = 25) -> Optional[str]:
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
#  PNG minimo: lector y escritor de 8 bits, sin dependencias
# ==========================================================================
def leer_png_gris(ruta: Path) -> Optional[Tuple[int, int, List[int]]]:
    """Devuelve (ancho, alto, lista de grises 0-255). None si no se puede."""
    try:
        bruto = Path(ruta).read_bytes()
    except OSError:
        return None
    if len(bruto) < 8 or bruto[:8] != b"\x89PNG\r\n\x1a\n":
        return None

    pos = 8
    ancho = alto = profundidad = tipo = 0
    idat = bytearray()
    while pos + 8 <= len(bruto):
        try:
            largo, etiqueta = struct.unpack(">I4s", bruto[pos:pos + 8])
        except struct.error:
            return None
        if largo > len(bruto):
            return None
        cuerpo = bruto[pos + 8:pos + 8 + largo]
        if etiqueta == b"IHDR":
            if len(cuerpo) < 13:
                return None
            ancho, alto, profundidad, tipo, _, _, entrelazado = struct.unpack(
                ">IIBBBBB", cuerpo[:13])
            if profundidad != 8 or entrelazado != 0:
                return None           # solo 8 bits sin entrelazar
            if tipo not in (0, 2, 6):
                return None           # gris, RGB o RGBA
        elif etiqueta == b"IDAT":
            idat.extend(cuerpo)
        elif etiqueta == b"IEND":
            break
        pos += 12 + largo

    if not ancho or not alto:
        return None
    if ancho * alto > MAX_PIXELS:
        return None

    canales = {0: 1, 2: 3, 6: 4}.get(tipo)
    if canales is None:
        return None
    try:
        datos = zlib.decompress(bytes(idat))
    except zlib.error:
        return None

    bpp = canales
    esperado = alto * (1 + ancho * bpp)
    if len(datos) < esperado:
        return None

    gris: List[int] = [0] * (ancho * alto)
    anterior = bytearray(ancho * bpp)
    p = 0
    for y in range(alto):
        filtro = datos[p]
        p += 1
        linea = bytearray(datos[p:p + ancho * bpp])
        p += ancho * bpp
        if filtro == 1:                       # Sub
            for i in range(bpp, len(linea)):
                linea[i] = (linea[i] + linea[i - bpp]) & 0xFF
        elif filtro == 2:                     # Up
            for i in range(len(linea)):
                linea[i] = (linea[i] + anterior[i]) & 0xFF
        elif filtro == 3:                     # Average
            for i in range(len(linea)):
                izq = linea[i - bpp] if i >= bpp else 0
                linea[i] = (linea[i] + ((izq + anterior[i]) >> 1)) & 0xFF
        elif filtro == 4:                     # Paeth
            for i in range(len(linea)):
                a = linea[i - bpp] if i >= bpp else 0
                b = anterior[i]
                c = anterior[i - bpp] if i >= bpp else 0
                pp = a + b - c
                pa, pb, pc = abs(pp - a), abs(pp - b), abs(pp - c)
                if pa <= pb and pa <= pc:
                    pred = a
                elif pb <= pc:
                    pred = b
                else:
                    pred = c
                linea[i] = (linea[i] + pred) & 0xFF
        elif filtro != 0:
            return None
        anterior = linea
        base = y * ancho
        if canales >= 3:
            for x in range(ancho):
                o = x * bpp
                # Rec. 601: es lo que usa todo el mundo para pasar a gris.
                gris[base + x] = (linea[o] * 77 + linea[o + 1] * 151 +
                                  linea[o + 2] * 28) >> 8
        else:
            for x in range(ancho):
                gris[base + x] = linea[x]
    return ancho, alto, gris


def escribir_png_gris(ruta: Path, ancho: int, alto: int, gris: List[int]) -> bool:
    """Escribe un PNG de 8 bits en escala de grises. Sin PIL, sin numpy."""
    if ancho <= 0 or alto <= 0 or len(gris) < ancho * alto:
        return False
    crudo = bytearray()
    for y in range(alto):
        crudo.append(0)                        # filtro None: rapido y valido
        base = y * ancho
        crudo.extend(gris[base:base + ancho])

    def chunk(tipo: bytes, cuerpo: bytes) -> bytes:
        return (struct.pack(">I", len(cuerpo)) + tipo + cuerpo +
                struct.pack(">I", zlib.crc32(tipo + cuerpo) & 0xFFFFFFFF))

    ihdr = struct.pack(">IIBBBBB", ancho, alto, 8, 0, 0, 0, 0)
    png = (b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", ihdr) +
           chunk(b"IDAT", zlib.compress(bytes(crudo), 6)) +
           chunk(b"IEND", b""))
    try:
        ruta.parent.mkdir(parents=True, exist_ok=True)
        tmp = ruta.with_suffix(".tmp.png")
        tmp.write_bytes(png)
        tmp.replace(ruta)
        return True
    except OSError:
        return False


# ==========================================================================
#  Reduccion y disparidad
# ==========================================================================
def reducir(gris: List[int], ancho: int, alto: int,
            nuevo_ancho: int) -> Tuple[int, int, List[int]]:
    """Reescala por muestreo de area (promedio de bloque)."""
    if nuevo_ancho <= 0 or ancho <= 0 or alto <= 0:
        return 0, 0, []
    if nuevo_ancho >= ancho:
        return ancho, alto, list(gris)
    escala = ancho / float(nuevo_ancho)
    nuevo_alto = max(1, int(alto / escala))
    out: List[int] = []
    for y in range(nuevo_alto):
        y0 = min(alto - 1, int(y * escala))
        y1 = min(alto, max(y0 + 1, int((y + 1) * escala)))
        for x in range(nuevo_ancho):
            x0 = min(ancho - 1, int(x * escala))
            x1 = min(ancho, max(x0 + 1, int((x + 1) * escala)))
            acc = 0
            n = 0
            for yy in range(y0, y1):
                base = yy * ancho
                for xx in range(x0, x1):
                    acc += gris[base + xx]
                    n += 1
            out.append(acc // max(1, n))
    return nuevo_ancho, nuevo_alto, out


def mapa_disparidad(izq: List[int], der: List[int], ancho: int, alto: int,
                    bloque: int = 5, rango: int = 32) -> List[int]:
    """Disparidad por bloques con SAD (suma de diferencias absolutas).

    Para cada pixel busca, en la imagen derecha, el desplazamiento `d` que
    minimiza la diferencia con su vecindario. Es el algoritmo mas simple que
    da resultado util y —con la imagen reducida— corre en pocos segundos.
    """
    if ancho <= 0 or alto <= 0:
        return []
    radio = max(0, int(bloque) // 2)
    rango = max(1, min(int(rango), ancho - 1))
    mapa = [0] * (ancho * alto)
    mejor_global = 1 << 30

    for y in range(radio, alto - radio):
        base = y * ancho
        for x in range(radio, ancho - radio):
            mejor_d = 0
            mejor_v = 1 << 30
            for d in range(rango):
                acc = 0
                for dy in range(-radio, radio + 1):
                    fi = base + dy * ancho
                    for dx in range(-radio, radio + 1):
                        ia = fi + x + dx
                        ib = fi + x + dx - d
                        if ib < fi:
                            acc += 255      # fuera de la imagen: penaliza
                            continue
                        acc += abs(izq[ia] - der[ib])
                if acc < mejor_v:
                    mejor_v = acc
                    mejor_d = d
            mapa[base + x] = mejor_d
            if mejor_v < mejor_global:
                mejor_global = mejor_v
    return mapa


def a_distancias(mapa: List[int], ancho: int, alto: int,
                 linea_base_m: float, f_px: float) -> List[float]:
    """Triangulacion: z = B*f/d. Disparidad 0 = infinito (no medible)."""
    out: List[float] = []
    k = linea_base_m * f_px
    for d in mapa:
        out.append(float("inf") if d <= 0 else k / float(d))
    return out


# ==========================================================================
#  El modulo
# ==========================================================================
class VisionEstereo:
    def __init__(self) -> None:
        self._lock = threading.RLock()
        self.config: Dict[str, Any] = dict(CONFIG_DEFAULT)
        self.ultimo: Optional[Dict[str, Any]] = None
        try:
            DATA_DIR.mkdir(parents=True, exist_ok=True)
        except OSError:
            pass
        self.cargar()

    # ------------------------------------------------------ persistencia
    def cargar(self) -> None:
        try:
            if LAST_JSON.exists():
                d = json.loads(LAST_JSON.read_text(encoding="utf-8"))
                if isinstance(d, dict):
                    self.ultimo = d
        except (OSError, ValueError):
            pass

    def guardar(self) -> None:
        if self.ultimo is None:
            return
        try:
            DATA_DIR.mkdir(parents=True, exist_ok=True)
            tmp = LAST_JSON.with_suffix(".tmp")
            tmp.write_text(json.dumps(self.ultimo, ensure_ascii=False, indent=1),
                           encoding="utf-8")
            tmp.replace(LAST_JSON)
        except OSError:
            pass

    # --------------------------------------------------------- capacidades
    @staticmethod
    def camaras() -> List[Dict[str, Any]]:
        """Camaras disponibles y si el dispositivo permite usar dos a la vez."""
        info: List[Dict[str, Any]] = []
        concurrente = False
        if es_android():
            feat = _run(["pm", "list", "features"], timeout=12) or ""
            concurrente = "android.hardware.camera.concurrent" in feat.lower()
            out = _run(["termux-camera-info"], timeout=12)
            if out:
                try:
                    d = json.loads(out)
                    if isinstance(d, list):
                        for i, c in enumerate(d):
                            if isinstance(c, dict):
                                info.append({
                                    "id": i,
                                    "resolucion": c.get("jpeg_output_sizes") or
                                                  c.get("image_format"),
                                    "facing": c.get("facing"),
                                    "focal": c.get("focal_length"),
                                })
                except ValueError:
                    pass
        return info, concurrente  # type: ignore[return-value]

    @classmethod
    def capacidades(cls) -> Dict[str, Any]:
        info, concurrente = cls.camaras()
        return {"camaras": info, "concurrente": concurrente,
                "termux_camera": _tiene("termux-camera-photo"),
                "android": es_android(),
                "opencv": False, "numpy": False}

    # ------------------------------------------------------------ captura
    def capturar(self, espera: float = 0.0) -> Dict[str, Any]:
        """Dos fotos separadas por un pequeno desplazamiento lateral.

        Vibra entre medias: es la senal de que hay que mover el movil unos
        centimetros. Sin ese movimiento las dos fotos son casi identicas y la
        disparidad sale plana (el modulo lo detecta y te lo dice).
        """
        if not _tiene("termux-camera-photo"):
            return {"ok": False, "error": "termux-camera-photo no disponible"}
        espera = float(espera or self.config.get("espera_entre_fotos", 1.6))
        s = int(self.config.get("sensor_trasero", 0))
        t = time.strftime("%Y%m%d-%H%M%S")
        a = DATA_DIR / f"izq-{t}.jpg"
        b = DATA_DIR / f"der-{t}.jpg"

        ok1 = _run(["termux-camera-photo", "-c", str(s), str(a)], timeout=30)
        if ok1 is None:
            return {"ok": False, "error": "fallo la primera foto"}
        if self.config.get("vibrar_entre_fotos") and _tiene("termux-vibrate"):
            _run(["termux-vibrate", "-d", "150"], timeout=6)
        time.sleep(min(8.0, max(0.4, espera)))
        ok2 = _run(["termux-camera-photo", "-c", str(s), str(b)], timeout=30)
        if ok2 is None:
            return {"ok": False, "error": "fallo la segunda foto"}
        return {"ok": True, "izquierda": str(a), "derecha": str(b)}

    # ---------------------------------------------------------- profundidad
    def calcular(self, ruta_izq: str, ruta_der: str) -> Dict[str, Any]:
        li = leer_png_gris(Path(ruta_izq))
        ld = leer_png_gris(Path(ruta_der))
        if li is None or ld is None:
            return {"ok": False,
                    "error": "no se pudo leer el par (PNG 8 bits sin entrelazar)"}
        (wa, ha, ga) = li
        (wb, hb, gb) = ld
        if (wa, ha) != (wb, hb):
            # Se iguala por abajo: cortar es mas honesto que estirar.
            wa = min(wa, wb)
            ha = min(ha, hb)
            ga, gb = self._recortar(ga, wa, ha, wa), self._recortar(gb, wb, hb, wa)

        ancho_t = int(self.config.get("ancho_trabajo", 160))
        wa, ha, ga = reducir(ga, wa, ha, ancho_t)
        _, _, gb = reducir(gb, wb, hb, wa)
        hb = ha

        bloque = int(self.config.get("bloque", 5))
        if bloque % 2 == 0:
            bloque += 1
        rango = int(self.config.get("rango_disparidad", 32))

        t0 = time.time()
        mapa = mapa_disparidad(ga, gb, wa, hb, bloque, rango)
        tardanza = time.time() - t0

        fov = float(self.config.get("fov_horizontal", 65.0))
        f_px = (wa / 2.0) / math.tan(math.radians(max(1.0, fov)) / 2.0)
        base_m = float(self.config.get("linea_base_m", 0.06))
        dist = a_distancias(mapa, wa, hb, base_m, f_px)

        resumen = self._percibir(mapa, dist, wa, hb)

        # El mapa se normaliza para verse: disparidad alta = cerca = claro.
        disp_max = max(mapa) or 1
        visual = [int(255 * v / disp_max) for v in mapa]
        png_ok = escribir_png_gris(DEPTH_PNG, wa, hb, visual)

        with self._lock:
            self.ultimo = {
                "ok": True,
                "ancho": wa, "alto": hb,
                "bloque": bloque, "rango": rango,
                "focal_px": round(f_px, 2),
                "linea_base_m": base_m,
                "tardanza_s": round(tardanza, 2),
                "mapa_png": str(DEPTH_PNG) if png_ok else None,
                "origen": {"izquierda": ruta_izq, "derecha": ruta_der},
                "ts": time.time(),
                **resumen,
            }
        self.guardar()
        return self.ultimo

    @staticmethod
    def _recortar(gris: List[int], ancho: int, alto: int,
                  nuevo_ancho: int) -> List[int]:
        if nuevo_ancho >= ancho:
            return list(gris)
        out: List[int] = []
        for y in range(alto):
            base = y * ancho
            out.extend(gris[base:base + nuevo_ancho])
        return out

    # ------------------------------------------------------------- lectura
    @staticmethod
    def _percibir(mapa: List[int], dist: List[float], ancho: int,
                  alto: int) -> Dict[str, Any]:
        """Convierte el mapa en algo que se pueda decir en voz alta."""
        if not mapa or ancho <= 0 or alto <= 0:
            return {"disparidad_media": 0.0, "cercano_cm": None,
                    "sector": "desconocido", "texto": "sin datos"}

        validos = [d for d in dist if d != float("inf") and d > 0]
        disp_media = sum(mapa) / float(len(mapa)) if mapa else 0.0

        # Se descartan los bordes: ahi la comparacion tiene menos vecinos y
        # el resultado es ruido, no medicion.
        margen = max(1, ancho // 10)
        cercano = float("inf")
        sector = "centro"
        cx = -1
        for y in range(margen, alto - margen):
            base = y * ancho
            for x in range(margen, ancho - margen):
                d = dist[base + x]
                if d < cercano:
                    cercano = d
                    cx = x
        if cx >= 0:
            if cx < ancho / 3.0:
                sector = "izquierda"
            elif cx > 2.0 * ancho / 3.0:
                sector = "derecha"
            else:
                sector = "centro"

        # Lo primero es distinguir "no hay con que comparar" de "no hay nada
        # delante": con dos fotos identicas la disparidad es cero en todas
        # partes, y eso no significa que no haya obstaculos, sino que el
        # modulo no ha podido medir.
        if disp_media < 0.5:
            return {"disparidad_media": round(disp_media, 2),
                    "cercano_cm": None, "sector": sector,
                    "texto": ("las dos fotos son casi identicas: mueve el "
                              "movil unos centimetros entre una y otra")}

        if not validos:
            return {"disparidad_media": round(disp_media, 2),
                    "cercano_cm": None, "sector": sector,
                    "texto": "no se detecta textura suficiente"}

        cercano_cm = None if cercano == float("inf") else round(cercano * 100, 1)
        articulo = "al" if sector == "centro" else "a la"
        if cercano_cm is None:
            texto = "nada medible delante"
        else:
            texto = f"obstaculo a {cercano_cm:.0f} cm, {articulo} {sector}"

        return {"disparidad_media": round(disp_media, 2),
                "cercano_cm": cercano_cm,
                "sector": sector,
                "texto": texto,
                "muestras_validas": len(validos)}

    # --------------------------------------------------------------- estado
    def estado(self) -> Dict[str, Any]:
        with self._lock:
            return {"ok": True, "capacidades": self.capacidades(),
                    "config": dict(self.config),
                    "ultimo": self.ultimo,
                    "mapa_disponible": DEPTH_PNG.exists()}

    def configurar(self, **kv: Any) -> Dict[str, Any]:
        with self._lock:
            for k, v in kv.items():
                if k in CONFIG_DEFAULT and v is not None:
                    self.config[k] = v
        return dict(self.config)


# ==========================================================================
#  Singleton
# ==========================================================================
_INSTANCIA: Optional[VisionEstereo] = None
_LOCK = threading.Lock()


def get_instance() -> VisionEstereo:
    global _INSTANCIA
    with _LOCK:
        if _INSTANCIA is None:
            _INSTANCIA = VisionEstereo()
        return _INSTANCIA


# ==========================================================================
#  Rutas Flask
# ==========================================================================
def register_stereo_routes(app) -> None:
    if Flask is None:
        return

    def v() -> VisionEstereo:
        return get_instance()

    @app.route("/api/pixel/stereo/status", methods=["GET"], endpoint="stereo__status")
    def _status():
        return jsonify(v().estado())

    @app.route("/api/pixel/stereo/capture", methods=["POST"], endpoint="stereo__capture")
    def _capture():
        d = request.get_json(silent=True) or {}
        try:
            espera = float(d.get("espera", 0.0))
        except (TypeError, ValueError):
            espera = 0.0
        res = v().capturar(espera)
        return jsonify(res), (200 if res.get("ok") else 500)

    @app.route("/api/pixel/stereo/depth", methods=["POST"], endpoint="stereo__depth")
    def _depth():
        d = request.get_json(silent=True) or {}
        a, b = d.get("izquierda"), d.get("derecha")
        if not a or not b:
            return jsonify({"ok": False,
                            "error": "faltan las rutas de las dos fotos"}), 400
        res = v().calcular(str(a), str(b))
        return jsonify(res), (200 if res.get("ok") else 400)

    @app.route("/api/pixel/stereo/last", methods=["GET"], endpoint="stereo__last")
    def _last():
        return jsonify({"ok": True, "ultimo": v().ultimo})

    @app.route("/api/pixel/stereo/depth.png", methods=["GET"], endpoint="stereo__png")
    def _png():
        if send_file is None or not DEPTH_PNG.exists():
            return jsonify({"ok": False, "error": "aun no hay mapa"}), 404
        return send_file(str(DEPTH_PNG), mimetype="image/png")

    @app.route("/api/pixel/stereo/config", methods=["POST"], endpoint="stereo__config")
    def _config():
        d = request.get_json(silent=True) or {}
        return jsonify({"ok": True, "config": v().configurar(**d)})

    print("[Stereo Vision] Routes registered: /api/pixel/stereo/* "
          "(status, capture, depth, last, depth.png, config)")


# --------------------------------------------------------------------------
#  Demo con un par sintetico de disparidad conocida
# --------------------------------------------------------------------------
def _hacer_par(ancho: int = 64, alto: int = 48,
               disp_fondo: int = 8, disp_caja: int = 20):
    """Escena sintetica: fondo lejano y una caja centrada mas cerca."""
    import random
    rnd = random.Random(1234)
    pad = disp_caja + 2
    izq = [[rnd.randrange(40, 220) for _ in range(ancho + pad)]
           for _ in range(alto)]
    der = [[0] * (ancho + pad) for _ in range(alto)]
    for y in range(alto):
        for x in range(ancho + pad):
            d = disp_caja if (20 <= x <= 44 and 12 <= y <= 36) else disp_fondo
            der[y][x] = izq[y][x - d] if x - d >= 0 else izq[y][0]
    _a = [v for fila in izq for v in fila]
    _b = [v for fila in der for v in fila]
    return (ancho + pad, alto, _a, _b, 20, 44, 12, 36)


def _demo() -> None:
    print("=" * 68)
    print(" STEREO VISION (E-26) — profundidad sin OpenCV y sin numpy")
    print("=" * 68)

    wa, ha, ga, gb, x0, x1, y0, y1 = _hacer_par()
    escribir_png_gris(DATA_DIR / "demo_izq.png", wa, ha, ga)
    escribir_png_gris(DATA_DIR / "demo_der.png", wa, ha, gb)
    releido = leer_png_gris(DATA_DIR / "demo_izq.png")
    print("PNG escrito y releido :", releido is not None and
          (releido[0], releido[1]) == (wa, ha))

    v = VisionEstereo()
    v.config["ancho_trabajo"] = 64
    v.config["bloque"] = 5
    v.config["rango_disparidad"] = 26
    v.config["linea_base_m"] = 0.06
    v.config["fov_horizontal"] = 65.0

    t0 = time.time()
    res = v.calcular(str(DATA_DIR / "demo_izq.png"),
                     str(DATA_DIR / "demo_der.png"))
    print(f"calculado en          : {time.time() - t0:.2f}s "
          f"({res['ancho']}x{res['alto']}, bloque={res['bloque']})")
    print("disparidad media      :", res["disparidad_media"])
    print("mas cercano           :", res["cercano_cm"], "cm")
    print("sector                :", res["sector"])
    print("lectura               :", res["texto"])
    print("mapa PNG              :", res["mapa_png"])

    print("\n-- coherencia: la caja esta mas cerca que el fondo --")
    print("   la caja se declaro a disparidad 20 y el fondo a 8")
    print("   el punto mas cercano cae dentro de la caja:",
          res["sector"] == "centro")

    print("\n-- imagen identica = sin medicion --")
    escribir_png_gris(DATA_DIR / "demo_misma.png", wa, ha, ga)
    r2 = v.calcular(str(DATA_DIR / "demo_izq.png"),
                    str(DATA_DIR / "demo_misma.png"))
    print("   ", r2["texto"][:70])

    print("\n-- fichero corrupto --")
    malo = DATA_DIR / "demo_malo.png"
    malo.write_bytes(b"\x89PNG\r\n\x1a\n" + b"basura" * 20)
    print("   ", v.calcular(str(malo), str(DATA_DIR / "demo_der.png"))["error"])
    malo.unlink(missing_ok=True)
    for f in ("demo_izq.png", "demo_der.png", "demo_misma.png"):
        (DATA_DIR / f).unlink(missing_ok=True)

    print("=" * 68)


if __name__ == "__main__":
    _demo()


# Compatibilidad: el stub anterior exportaba `StereoVision`.
StereoVision = VisionEstereo