#!/usr/bin/env python3
"""
core.business_store — Clientes como usuarios de negocio
=================================================================
Modelo de negocio de aig: **un cliente es un usuario de negocio**, no una
fila en una tabla de contactos. Cada cliente:

  - tiene identidad y marca propia   -> se enlaza a un tenant white-label
  - tiene plan contratado            -> se enlaza a un tier de `billing_system`
  - tiene direccion geocodificada    -> aparece como nodo en el globo 3D
  - tiene estado operativo           -> color del nodo (verde/amarillo/rojo)
  - tiene telemetria y eventos       -> pulsos e incidencias en el visor

Esto es lo que convierte aig de "una herramienta" en "una plataforma":
el negocio se ve, literalmente, en el globo.

Se apoya en lo que ya existe, sin duplicarlo:
  - `core/billing_system.py`  -> TIERS (free / pro / enterprise)
  - `scripts/deploy/tenant_bootstrap.py` -> tenants/<slug>/ (marca + auth + DBs)

Base de datos: aig/data/business/business.db (SQLite, stdlib)
Geocodificacion: Nominatim (sin clave) con cache en disco y limite de 1 req/s.

Uso:
  python core/business_store.py alta --nombre "Gestoria Lopez" \\
      --direccion "Calle Mayor 1, Madrid" --tier pro --tenant gestoria-lopez
  python core/business_store.py listar
  python core/business_store.py estado <id> activo
  python core/business_store.py resumen
"""

from __future__ import annotations

import json
import os
import sqlite3
import threading
import time
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any

import requests

# ── Config ───────────────────────────────────────────────────

# La raiz se busca por marcador: este fichero se aplano de `core/` a la raiz
# (2026-09-29), asi que un `join(BASE_DIR, "..", ...)` salia del proyecto.
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
DATA_DIR = os.path.join(BASE_DIR, "data", "business")
DB_PATH = os.path.join(DATA_DIR, "business.db")
GEO_CACHE = os.path.join(DATA_DIR, "geocode_cache.json")

TIMEOUT = 12
USER_AGENT = "aig-DanielaOS/1.0 (contacto@aigestion.net)"
NOMINATIM = "https://nominatim.openstreetmap.org/search"
PAUSA_GEO = 1.1          # Nominatim pide maximo 1 req/s

# Estados operativos -> color del nodo en el globo (requisito 2 del visor)
ESTADOS: dict[str, dict[str, str]] = {
    "activo":     {"color": "#22c55e", "etiqueta": "Activo / Operativo"},
    "alerta":     {"color": "#eab308", "etiqueta": "Telemetria / Alertas"},
    "incidencia": {"color": "#ef4444", "etiqueta": "Incidencia / Error"},
    "inactivo":   {"color": "#6b7280", "etiqueta": "Inactivo"},
}

# Planes: espejo de core/billing_system.TIERS (no se importa para no acoplar)
TIERS_VALIDOS = ("free", "pro", "enterprise")

# Precio mensual en euros, espejo de core/billing_system.TIERS[*].price_monthly.
# Si cambias uno, cambia el otro: `comprobar_tiers()` detecta la divergencia.
PRECIO_TIER = {
    "free": 0,
    "pro": 29,
    "enterprise": 99,
}


def precio_de_tier(tier: str) -> float:
    """Precio mensual del plan. 0 si el plan no se reconoce."""
    return float(PRECIO_TIER.get((tier or "").strip().lower(), 0))


def comprobar_tiers() -> dict[str, Any]:
    """Compara el espejo local con la fuente real de facturacion.

    Se llama a proposito (CLI/tests), nunca en el camino caliente: importar
    `core.billing_system` crea su base de datos como efecto de importacion.
    """
    try:
        from core.billing_system import TIERS  # type: ignore
    except Exception as e:  # noqa: BLE001
        return {"ok": False, "motivo": f"no se pudo importar billing_system: {e}"}

    divergencias = {}
    for tier, precio in PRECIO_TIER.items():
        real = (TIERS.get(tier) or {}).get("price_monthly")
        if real is not None and float(real) != float(precio):
            divergencias[tier] = {"local": precio, "real": real}
    return {"ok": not divergencias, "divergencias": divergencias,
            "precios": dict(PRECIO_TIER)}


# ── Modelo ───────────────────────────────────────────────────


@dataclass
class Cliente:
    """Un usuario de negocio de aig."""

    id: str
    nombre: str
    sector: str = ""
    direccion: str = ""
    ciudad: str = ""
    pais: str = ""
    lat: float | None = None
    lon: float | None = None
    estado: str = "activo"
    tier: str = "free"
    tenant_slug: str = ""
    email: str = ""
    telefono: str = ""
    web: str = ""
    notas: str = ""
    mrr: float = 0.0                 # ingreso mensual recurrente
    creado: float = field(default_factory=time.time)
    actualizado: float = field(default_factory=time.time)

    def to_dict(self) -> dict[str, Any]:
        d = asdict(self)
        d["color"] = ESTADOS.get(self.estado, ESTADOS["inactivo"])["color"]
        d["estado_etiqueta"] = ESTADOS.get(self.estado, ESTADOS["inactivo"])["etiqueta"]
        d["ubicado"] = self.lat is not None and self.lon is not None
        return d


# ── Base de datos ────────────────────────────────────────────

DDL = """
CREATE TABLE IF NOT EXISTS clientes (
    id          TEXT PRIMARY KEY,
    nombre      TEXT NOT NULL,
    sector      TEXT DEFAULT '',
    direccion   TEXT DEFAULT '',
    ciudad      TEXT DEFAULT '',
    pais        TEXT DEFAULT '',
    lat         REAL,
    lon         REAL,
    estado      TEXT NOT NULL DEFAULT 'activo',
    tier        TEXT NOT NULL DEFAULT 'free',
    tenant_slug TEXT DEFAULT '',
    email       TEXT DEFAULT '',
    telefono    TEXT DEFAULT '',
    web         TEXT DEFAULT '',
    notas       TEXT DEFAULT '',
    mrr         REAL DEFAULT 0,
    creado      REAL NOT NULL,
    actualizado REAL NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_cli_estado ON clientes(estado);
CREATE INDEX IF NOT EXISTS idx_cli_tier   ON clientes(tier);

CREATE TABLE IF NOT EXISTS eventos (
    id         INTEGER PRIMARY KEY AUTOINCREMENT,
    cliente_id TEXT NOT NULL,
    tipo       TEXT NOT NULL,
    mensaje    TEXT DEFAULT '',
    severidad  TEXT DEFAULT 'info',
    ts         REAL NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_ev_cliente ON eventos(cliente_id, ts DESC);
"""

_CAMPOS = ("id", "nombre", "sector", "direccion", "ciudad", "pais", "lat", "lon",
           "estado", "tier", "tenant_slug", "email", "telefono", "web", "notas",
           "mrr", "creado", "actualizado")

# Bases de datos cuyo esquema ya se ha creado en este proceso (ver _asegurar_esquema).
_ESQUEMA_LISTO: set = set()
_ESQUEMA_CANDADO = threading.Lock()
_DIR_LISTO = False


def _asegurar_directorio() -> None:
    """Crea DATA_DIR una sola vez por proceso.

    Medido en este equipo, `os.makedirs(..., exist_ok=True)` cuesta ~7 ms por
    llamada (Windows + antivirus revisando cada componente de la ruta), mas que
    el propio `sqlite3.connect`. Llamarlo en cada `_conectar()` era, de largo,
    el mayor sobrecoste por consulta.
    """
    global _DIR_LISTO
    if _DIR_LISTO:
        return
    os.makedirs(DATA_DIR, exist_ok=True)
    _DIR_LISTO = True


def _asegurar_esquema(con: sqlite3.Connection, forzar: bool = False) -> None:
    """Crea las tablas **una sola vez por proceso y por base de datos**.

    Antes se ejecutaba `executescript(DDL)` en CADA conexion. Medido en este
    equipo: `_conectar()` costaba ~22.5 ms frente a ~7.8 ms de un
    `sqlite3.connect` pelado -> ~15 ms de sobrecoste por consulta, y cada
    endpoint abre y cierra su propia conexion.

    `forzar=True` se usa cuando el fichero no existia antes de conectar (primer
    arranque o borrado en caliente): en ese caso el esquema hay que recrearlo
    aunque este proceso ya lo hubiera hecho sobre otro fichero.
    """
    clave = os.path.normcase(os.path.abspath(DB_PATH))
    if not forzar and clave in _ESQUEMA_LISTO:
        return
    with _ESQUEMA_CANDADO:
        if not forzar and clave in _ESQUEMA_LISTO:
            return
        con.executescript(DDL)
        _ESQUEMA_LISTO.add(clave)


def _olvidar_esquema() -> None:
    """Olvida que el esquema ya esta creado (para pruebas y borrados en caliente)."""
    _ESQUEMA_LISTO.clear()


def _conectar() -> sqlite3.Connection:
    _asegurar_directorio()
    existia = os.path.exists(DB_PATH)
    con = sqlite3.connect(DB_PATH, timeout=15)
    con.row_factory = sqlite3.Row
    _asegurar_esquema(con, forzar=not existia)
    return con


def _fila_a_cliente(r: sqlite3.Row) -> Cliente:
    return Cliente(**{k: r[k] for k in _CAMPOS if k in r.keys()})


# ── Geocodificacion (sin clave, con cache) ───────────────────


def _cargar_cache() -> dict[str, Any]:
    if not os.path.exists(GEO_CACHE):
        return {}
    try:
        with open(GEO_CACHE, encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}


def _guardar_cache(c: dict[str, Any]) -> None:
    os.makedirs(DATA_DIR, exist_ok=True)
    with open(GEO_CACHE, "w", encoding="utf-8") as f:
        json.dump(c, f, ensure_ascii=False, indent=1)


def geocodificar(direccion: str) -> dict[str, Any] | None:
    """Direccion -> {lat, lon, ciudad, pais}. Cache en disco, 1 req/s.

    Devuelve None si no se encuentra. Nunca lanza: la app debe seguir
    funcionando aunque el geocodificador este caido.
    """
    direccion = (direccion or "").strip()
    if not direccion:
        return None

    cache = _cargar_cache()
    clave = direccion.lower()
    if clave in cache:
        return cache[clave] or None

    resultado: dict[str, Any] | None = None
    try:
        r = requests.get(
            NOMINATIM,
            params={"q": direccion, "format": "json", "limit": 1,
                    "addressdetails": 1},
            headers={"User-Agent": USER_AGENT},
            timeout=TIMEOUT,
        )
        if r.status_code == 200:
            datos = r.json()
            if datos:
                d0 = datos[0]
                addr = d0.get("address", {}) or {}
                resultado = {
                    "lat": float(d0["lat"]),
                    "lon": float(d0["lon"]),
                    "ciudad": (addr.get("city") or addr.get("town")
                               or addr.get("village") or addr.get("municipality") or ""),
                    "pais": addr.get("country", ""),
                    "mostrado": d0.get("display_name", ""),
                }
    except Exception:
        resultado = None

    cache[clave] = resultado
    _guardar_cache(cache)
    time.sleep(PAUSA_GEO)   # respeta el limite de Nominatim
    return resultado


# ── Operaciones ──────────────────────────────────────────────


def _slug(texto: str) -> str:
    import re
    s = re.sub(r"[^a-z0-9]+", "-", (texto or "").lower()).strip("-")
    return s[:48] or f"cliente-{int(time.time())}"


def alta(nombre: str, direccion: str = "", tier: str = "free",
         tenant_slug: str = "", sector: str = "", email: str = "",
         telefono: str = "", web: str = "", notas: str = "",
         mrr: float | None = None, id_: str | None = None,
         geocodificar_direccion: bool = True) -> Cliente:
    """Da de alta un cliente (usuario de negocio). Geocodifica su direccion.

    Si no se indica `mrr`, se deriva del precio del plan (`PRECIO_TIER`). Un
    `mrr=0` explicito se respeta (descuentos, pruebas).
    """
    if tier not in TIERS_VALIDOS:
        raise ValueError(f"tier invalido: {tier!r}. Validos: {TIERS_VALIDOS}")

    cid = id_ or _slug(nombre)
    geo = geocodificar(direccion) if (direccion and geocodificar_direccion) else None
    mrr_final = precio_de_tier(tier) if mrr is None else float(mrr)

    c = Cliente(
        id=cid, nombre=nombre, sector=sector, direccion=direccion,
        ciudad=(geo or {}).get("ciudad", ""), pais=(geo or {}).get("pais", ""),
        lat=(geo or {}).get("lat"), lon=(geo or {}).get("lon"),
        tier=tier, tenant_slug=tenant_slug or cid, email=email,
        telefono=telefono, web=web, notas=notas, mrr=mrr_final,
    )

    con = _conectar()
    try:
        con.execute(
            f"INSERT INTO clientes ({','.join(_CAMPOS)}) "
            f"VALUES ({','.join('?' * len(_CAMPOS))})",
            tuple(getattr(c, k) for k in _CAMPOS),
        )
        con.commit()
    except sqlite3.IntegrityError:
        raise ValueError(f"ya existe un cliente con id {cid!r}") from None
    finally:
        con.close()

    registrar_evento(cid, "alta", f"Cliente dado de alta (tier {tier})", "info")
    return c


def listar(estado: str | None = None, tier: str | None = None,
           solo_ubicados: bool = False) -> list[Cliente]:
    sql = "SELECT * FROM clientes WHERE 1=1"
    params: list[Any] = []
    if estado:
        sql += " AND estado = ?"
        params.append(estado)
    if tier:
        sql += " AND tier = ?"
        params.append(tier)
    if solo_ubicados:
        sql += " AND lat IS NOT NULL AND lon IS NOT NULL"
    sql += " ORDER BY creado DESC"
    con = _conectar()
    try:
        return [_fila_a_cliente(r) for r in con.execute(sql, params)]
    finally:
        con.close()


def obtener(cid: str) -> Cliente | None:
    con = _conectar()
    try:
        r = con.execute("SELECT * FROM clientes WHERE id = ?", (cid,)).fetchone()
        return _fila_a_cliente(r) if r else None
    finally:
        con.close()


def cambiar_estado(cid: str, estado: str, mensaje: str = "") -> Cliente | None:
    """Cambia el estado operativo -> cambia el color del nodo en el globo."""
    if estado not in ESTADOS:
        raise ValueError(f"estado invalido: {estado!r}. Validos: {tuple(ESTADOS)}")
    con = _conectar()
    try:
        cur = con.execute(
            "UPDATE clientes SET estado = ?, actualizado = ? WHERE id = ?",
            (estado, time.time(), cid),
        )
        con.commit()
        if cur.rowcount == 0:
            return None
    finally:
        con.close()
    sev = {"activo": "info", "alerta": "aviso",
           "incidencia": "error", "inactivo": "info"}.get(estado, "info")
    registrar_evento(cid, "estado", mensaje or f"Estado -> {estado}", sev)
    return obtener(cid)


def ubicar(cid: str, direccion: str) -> Cliente | None:
    """(Re)geocodifica la direccion de un cliente y actualiza su nodo."""
    geo = geocodificar(direccion)
    con = _conectar()
    try:
        con.execute(
            "UPDATE clientes SET direccion = ?, ciudad = ?, pais = ?, "
            "lat = ?, lon = ?, actualizado = ? WHERE id = ?",
            (direccion, (geo or {}).get("ciudad", ""), (geo or {}).get("pais", ""),
             (geo or {}).get("lat"), (geo or {}).get("lon"), time.time(), cid),
        )
        con.commit()
    finally:
        con.close()
    return obtener(cid)


def registrar_evento(cid: str, tipo: str, mensaje: str = "",
                     severidad: str = "info") -> None:
    """Telemetria del cliente: alimenta pulsos y alertas del visor."""
    con = _conectar()
    try:
        con.execute(
            "INSERT INTO eventos (cliente_id, tipo, mensaje, severidad, ts) "
            "VALUES (?,?,?,?,?)",
            (cid, tipo, mensaje, severidad, time.time()),
        )
        con.commit()
    finally:
        con.close()


def eventos(cid: str | None = None, limite: int = 50) -> list[dict[str, Any]]:
    con = _conectar()
    try:
        if cid:
            filas = con.execute(
                "SELECT * FROM eventos WHERE cliente_id = ? ORDER BY ts DESC LIMIT ?",
                (cid, limite)).fetchall()
        else:
            filas = con.execute(
                "SELECT * FROM eventos ORDER BY ts DESC LIMIT ?", (limite,)).fetchall()
        return [dict(r) for r in filas]
    finally:
        con.close()


def resumen() -> dict[str, Any]:
    """Agregados para el panel: por estado, por tier y MRR total."""
    con = _conectar()
    try:
        por_estado = {r["estado"]: r["n"] for r in con.execute(
            "SELECT estado, COUNT(*) n FROM clientes GROUP BY estado")}
        por_tier = {r["tier"]: r["n"] for r in con.execute(
            "SELECT tier, COUNT(*) n FROM clientes GROUP BY tier")}
        tot = con.execute(
            "SELECT COUNT(*) n, COALESCE(SUM(mrr),0) mrr, "
            "SUM(CASE WHEN lat IS NOT NULL THEN 1 ELSE 0 END) ubic "
            "FROM clientes").fetchone()
        return {
            "total": tot["n"],
            "ubicados": tot["ubic"],
            "mrr_total": round(tot["mrr"], 2),
            "por_estado": {k: {"n": v, "color": ESTADOS[k]["color"]}
                           for k, v in por_estado.items() if k in ESTADOS},
            "por_tier": por_tier,
        }
    finally:
        con.close()


# ── CLI ──────────────────────────────────────────────────────


def _main(argv: list[str] | None = None) -> int:
    import argparse

    p = argparse.ArgumentParser(description="Clientes de aig (usuarios de negocio)")
    sub = p.add_subparsers(dest="cmd", required=True)

    a = sub.add_parser("alta", help="dar de alta un cliente")
    a.add_argument("--nombre", required=True)
    a.add_argument("--direccion", default="")
    a.add_argument("--tier", default="free", choices=TIERS_VALIDOS)
    a.add_argument("--tenant", default="")
    a.add_argument("--sector", default="")
    a.add_argument("--email", default="")
    a.add_argument("--mrr", type=float, default=0.0)

    sub.add_parser("listar", help="listar clientes")

    e = sub.add_parser("estado", help="cambiar estado operativo")
    e.add_argument("id")
    e.add_argument("estado", choices=tuple(ESTADOS))
    e.add_argument("--mensaje", default="")

    u = sub.add_parser("ubicar", help="(re)geocodificar direccion")
    u.add_argument("id")
    u.add_argument("direccion")

    sub.add_parser("resumen", help="agregados del panel")

    args = p.parse_args(argv)

    if args.cmd == "alta":
        c = alta(args.nombre, args.direccion, args.tier, args.tenant,
                 args.sector, args.email, mrr=args.mrr)
        est = f"{c.lat:.4f},{c.lon:.4f} ({c.ciudad}, {c.pais})" if c.lat else "SIN UBICAR"
        print(f"cliente '{c.id}' creado — {c.nombre} [{c.tier}]")
        print(f"  ubicacion: {est}")
        return 0

    if args.cmd == "listar":
        cs = listar()
        if not cs:
            print("(sin clientes)")
        for c in cs:
            ubi = f"{c.lat:.3f},{c.lon:.3f}" if c.lat else "sin ubicar"
            print(f"{c.id:<22} {c.nombre[:26]:<26} {c.tier:<11} "
                  f"{c.estado:<11} {ubi}")
        return 0

    if args.cmd == "estado":
        c = cambiar_estado(args.id, args.estado, args.mensaje)
        if c is None:
            print(f"no existe el cliente {args.id!r}")
            return 1
        print(f"{c.nombre} -> {c.estado} ({c.to_dict()['color']})")
        return 0

    if args.cmd == "ubicar":
        c = ubicar(args.id, args.direccion)
        if c is None:
            print(f"no existe el cliente {args.id!r}")
            return 1
        print(f"{c.nombre}: {c.lat},{c.lon} ({c.ciudad}, {c.pais})"
              if c.lat else "no se pudo geocodificar")
        return 0

    if args.cmd == "resumen":
        r = resumen()
        print(f"clientes: {r['total']}  ubicados: {r['ubicados']}  "
              f"MRR: {r['mrr_total']} EUR")
        for k, v in r["por_estado"].items():
            print(f"  {k:<11} {v['n']:<4} {v['color']}")
        for k, v in r["por_tier"].items():
            print(f"  tier {k:<11} {v}")
        return 0

    return 2


if __name__ == "__main__":
    import sys
    sys.exit(_main())
