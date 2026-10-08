#!/usr/bin/env python3
"""
core.location — Sede dinamica de aigestion.net
========================================================
Detecta desde donde se conecta el usuario y situa el nodo principal de
"Sede aigestion.net" en el globo 3D. Expone la propiedad `core.location`
para cambiarla en tiempo real.

Requisito 1 del visor. Restriccion de diseno: **no romper el historial RAG**.
Por eso los cambios NO sobrescriben: el estado actual vive en `actual.json` y
cada cambio se ANEXA a `historial.jsonl`. Asi se puede reconstruir donde estaba
la sede en cualquier fecha, y el RAG no pierde trazabilidad.

Estrategia de deteccion (en cascada, tolerante a fallos):
  1. Variable de entorno aig_HQ (lat,lon[,etiqueta]) — override manual
  2. Fichero de configuracion fijado a mano (fijar())
  3. Geolocalizacion por IP (varios proveedores sin clave, con fallback)
  4. Ultimo valor conocido del historial
  5. Fallback neutro (0,0) marcado como `desconocida`

Ninguna peticion de red es obligatoria: si todo falla, sigue funcionando.

Coste: $0. Los proveedores usados no requieren clave.
"""

from __future__ import annotations

import json
import os
import time
from dataclasses import asdict, dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any

import requests

# ── Config ───────────────────────────────────────────────────

# Raiz por marcador: este fichero se aplano de `core/` a la raiz (2026-09-29),
# asi que un `join(BASE_DIR, "..", ...)` salia del proyecto y los datos de la
# Sede caian en `files/home/apps/data/` en vez de `<repo>/data/location/`.
_BASE = Path(__file__).resolve()
BASE_DIR = str(
    next(
        (
            c
            for c in (_BASE.parent, *_BASE.parents)
            if (c / ".git").exists() or (c / "tests" / "conftest.py").exists()
        ),
        _BASE.parent,
    )
)
DATA_DIR = os.path.join(BASE_DIR, "data", "location")
ACTUAL_FILE = os.path.abspath(os.path.join(DATA_DIR, "actual.json"))
HISTORIAL_FILE = os.path.abspath(os.path.join(DATA_DIR, "historial.jsonl"))

TIMEOUT = 8
USER_AGENT = "aig-DanielaOS/1.0"

ETIQUETA_DEFECTO = "Sede aigestion.net"

# Proveedores de geolocalizacion por IP, sin clave. Se prueban en orden.
PROVEEDORES = (
    (
        "ip-api.com",
        "http://ip-api.com/json/?fields=status,city,regionName,country,lat,lon,timezone,query",
        lambda d: {
            "lat": d.get("lat"), "lon": d.get("lon"),
            "ciudad": d.get("city"), "region": d.get("regionName"),
            "pais": d.get("country"), "tz": d.get("timezone"), "ip": d.get("query"),
        },
    ),
    (
        "ipapi.co",
        "https://ipapi.co/json/",
        lambda d: {
            "lat": d.get("latitude"), "lon": d.get("longitude"),
            "ciudad": d.get("city"), "region": d.get("region"),
            "pais": d.get("country_name"), "tz": d.get("timezone"), "ip": d.get("ip"),
        },
    ),
)


# ── Modelo ───────────────────────────────────────────────────


@dataclass
class Ubicacion:
    """Donde esta la sede principal."""

    lat: float
    lon: float
    etiqueta: str = ETIQUETA_DEFECTO
    ciudad: str | None = None
    region: str | None = None
    pais: str | None = None
    tz: str | None = None
    ip: str | None = None
    fuente: str = "desconocida"     # env | manual | ip:<proveedor> | historial | fallback
    ts: float = field(default_factory=time.time)
    alt_camara: float = 2500.0      # altitud sugerida al enfocar en el globo

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def desde_dict(cls, d: dict[str, Any]) -> Ubicacion:
        campos = set(cls.__dataclass_fields__)  # type: ignore[attr-defined]
        return cls(**{k: v for k, v in d.items() if k in campos})

    def descripcion(self) -> str:
        partes = [p for p in (self.ciudad, self.region, self.pais) if p]
        return ", ".join(partes) if partes else f"{self.lat:.4f}, {self.lon:.4f}"

    @property
    def valida(self) -> bool:
        return not (self.lat == 0.0 and self.lon == 0.0)


# ── Persistencia ─────────────────────────────────────────────


def _asegurar_dir() -> None:
    os.makedirs(os.path.dirname(ACTUAL_FILE), exist_ok=True)


def _leer_actual() -> Ubicacion | None:
    if not os.path.exists(ACTUAL_FILE):
        return None
    try:
        with open(ACTUAL_FILE, encoding="utf-8") as f:
            return Ubicacion.desde_dict(json.load(f))
    except Exception:
        return None


def _escribir_actual(u: Ubicacion) -> None:
    _asegurar_dir()
    with open(ACTUAL_FILE, "w", encoding="utf-8") as f:
        json.dump(u.to_dict(), f, ensure_ascii=False, indent=2)


def _anexar_historial(u: Ubicacion, motivo: str) -> None:
    """Anexa al historial. NUNCA sobrescribe: el RAG necesita trazabilidad."""
    _asegurar_dir()
    fila = u.to_dict()
    fila["motivo"] = motivo
    fila["registrado"] = datetime.now().isoformat(timespec="seconds")
    with open(HISTORIAL_FILE, "a", encoding="utf-8") as f:
        f.write(json.dumps(fila, ensure_ascii=False) + "\n")


def historial(limite: int = 50) -> list[dict[str, Any]]:
    """Cambios de sede registrados, del mas reciente al mas antiguo."""
    if not os.path.exists(HISTORIAL_FILE):
        return []
    filas: list[dict[str, Any]] = []
    with open(HISTORIAL_FILE, encoding="utf-8") as f:
        for linea in f:
            linea = linea.strip()
            if linea:
                try:
                    filas.append(json.loads(linea))
                except json.JSONDecodeError:
                    continue
    return list(reversed(filas))[:limite]


# ── Deteccion ────────────────────────────────────────────────


def _desde_env() -> Ubicacion | None:
    """aig_HQ="lat,lon[,etiqueta]" — override explicito por entorno."""
    raw = os.getenv("aig_HQ", "").strip()
    if not raw:
        return None
    partes = [p.strip() for p in raw.split(",")]
    if len(partes) < 2:
        return None
    try:
        lat, lon = float(partes[0]), float(partes[1])
    except ValueError:
        return None
    return Ubicacion(lat=lat, lon=lon,
                     etiqueta=partes[2] if len(partes) > 2 else ETIQUETA_DEFECTO,
                     fuente="env")


def _desde_ip() -> Ubicacion | None:
    """Geolocalizacion por IP. Prueba proveedores en orden, sin clave."""
    for nombre, url, mapear in PROVEEDORES:
        try:
            r = requests.get(url, timeout=TIMEOUT, headers={"User-Agent": USER_AGENT})
            if r.status_code != 200:
                continue
            d = mapear(r.json())
            lat, lon = d.get("lat"), d.get("lon")
            if lat is None or lon is None:
                continue
            return Ubicacion(
                lat=float(lat), lon=float(lon), etiqueta=ETIQUETA_DEFECTO,
                ciudad=d.get("ciudad"), region=d.get("region"), pais=d.get("pais"),
                tz=d.get("tz"), ip=d.get("ip"), fuente=f"ip:{nombre}",
            )
        except Exception:
            continue  # proveedor caido: siguiente
    return None


def detectar(forzar: bool = False) -> Ubicacion:
    """Resuelve la ubicacion de la sede, en cascada.

    `forzar=True` ignora el valor guardado y vuelve a detectar por IP.
    Registra el cambio en el historial solo si la ubicacion varia.
    """
    previa = _leer_actual()

    if not forzar and previa is not None and previa.fuente != "fallback":
        return previa

    candidatas = [_desde_env()]
    if not forzar and previa is not None:
        candidatas.append(previa)
    candidatas.append(_desde_ip())
    candidatas.append(previa)

    elegida = next((c for c in candidatas if c is not None), None)
    if elegida is None:
        elegida = Ubicacion(lat=0.0, lon=0.0, fuente="fallback",
                            etiqueta=f"{ETIQUETA_DEFECTO} (sin detectar)")

    # Solo se registra si cambio de verdad: evita ruido en el historial.
    cambio = (
        previa is None
        or abs(previa.lat - elegida.lat) > 1e-4
        or abs(previa.lon - elegida.lon) > 1e-4
        or previa.fuente != elegida.fuente
    )
    _escribir_actual(elegida)
    if cambio:
        _anexar_historial(elegida, "forzado" if forzar else "deteccion")
    return elegida


def actual() -> Ubicacion:
    """Ubicacion vigente. Detecta si aun no hay ninguna guardada."""
    u = _leer_actual()
    return u if u is not None else detectar()


def fijar(lat: float, lon: float, etiqueta: str = ETIQUETA_DEFECTO,
          ciudad: str | None = None) -> Ubicacion:
    """Fija la sede a mano. Queda registrado en el historial."""
    u = Ubicacion(lat=float(lat), lon=float(lon), etiqueta=etiqueta,
                  ciudad=ciudad, fuente="manual")
    _escribir_actual(u)
    _anexar_historial(u, "manual")
    return u


# ── CLI ──────────────────────────────────────────────────────


def _main(argv: list[str] | None = None) -> int:
    import argparse

    p = argparse.ArgumentParser(description="Sede dinamica de aigestion.net")
    sub = p.add_subparsers(dest="cmd", required=True)
    sub.add_parser("ver", help="ubicacion vigente")
    d = sub.add_parser("detectar", help="volver a detectar por IP")
    d.add_argument("--forzar", action="store_true")
    f = sub.add_parser("fijar", help="fijar a mano")
    f.add_argument("lat", type=float)
    f.add_argument("lon", type=float)
    f.add_argument("--etiqueta", default=ETIQUETA_DEFECTO)
    h = sub.add_parser("historial", help="cambios registrados")
    h.add_argument("--limite", type=int, default=20)

    args = p.parse_args(argv)

    if args.cmd == "ver":
        u = actual()
        print(f"{u.etiqueta}: {u.descripcion()}")
        print(f"  {u.lat:.5f}, {u.lon:.5f}  [{u.fuente}]")
        if u.tz:
            print(f"  zona horaria: {u.tz}")
        return 0

    if args.cmd == "detectar":
        u = detectar(forzar=args.forzar)
        print(f"{u.etiqueta}: {u.descripcion()}  [{u.fuente}]")
        print(f"  {u.lat:.5f}, {u.lon:.5f}")
        return 0

    if args.cmd == "fijar":
        u = fijar(args.lat, args.lon, args.etiqueta)
        print(f"sede fijada: {u.lat:.5f}, {u.lon:.5f} ({u.etiqueta})")
        return 0

    if args.cmd == "historial":
        filas = historial(args.limite)
        if not filas:
            print("(sin cambios registrados)")
        for f_ in filas:
            print(f"{f_.get('registrado','?')}  {f_['lat']:.4f},{f_['lon']:.4f}  "
                  f"[{f_.get('fuente','?')}] {f_.get('motivo','')}")
        return 0

    return 2


if __name__ == "__main__":
    import sys
    sys.exit(_main())
