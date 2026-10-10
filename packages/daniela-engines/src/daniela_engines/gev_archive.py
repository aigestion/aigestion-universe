#!/usr/bin/env python3
"""
GEV Archive — rebobinar tu mundo
================================
Guarda periodicamente lo que God's Eye View ve dentro de tus geocercas, para
poder **volver atras en el tiempo** y preguntar que habia alli antes.

Idea 3.1 del documento de integracion. El README de GEV dice que su "long game"
es el viaje en el tiempo y que no lo hacen porque "data gets expensive and
compute brutal" — cierto **para el planeta entero**. Para un area de interes
personal son kilobytes, no petabytes. Eso es exactamente lo que hace esto.

  GEV global  ->  caro e inviable
  Tu AOI      ->  trivial

Por que SQLite y no `data_engine/storage.py`: `TimeSeriesStore` es **en memoria**
(`self.data = {}`), asi que se pierde al reiniciar. Para historico hace falta
persistencia real. SQLite viene en la stdlib: cero dependencias.

Base de datos: core/data/gev_archive/aoi.db

Uso:
  python core/gev_archive.py capturar            # una foto del AOI
  python core/gev_archive.py stats               # que hay guardado
  python core/gev_archive.py timeline 41.39 2.15 --radio 60 --horas 24
  python core/gev_archive.py rebobinar 41.39 2.15 --hace 3 --radio 60
"""

from __future__ import annotations

import argparse
import json
import os
import sqlite3
import sys
import time
from collections.abc import Sequence
from dataclasses import dataclass
from datetime import datetime
from typing import Any

from gev_bridge import GevClient, distancia_km, gev_link
from gev_watch import Zona, cargar_zonas

# ── Config ───────────────────────────────────────────────────

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
STATE_DIR = os.path.join(BASE_DIR, "data", "gev_archive")
DB_PATH = os.path.join(STATE_DIR, "aoi.db")

BUCKET_S = 60          # resolución: 1 minuto
RETENCION_DIAS = 30    # por defecto, 30 dias de historico


# ── Esquema ──────────────────────────────────────────────────

DDL = """
CREATE TABLE IF NOT EXISTS observaciones (
    id        INTEGER PRIMARY KEY AUTOINCREMENT,
    ts        REAL    NOT NULL,
    bucket    INTEGER NOT NULL,
    capa      TEXT    NOT NULL,
    entidad   TEXT    NOT NULL,
    lat       REAL    NOT NULL,
    lon       REAL    NOT NULL,
    alt       REAL,
    meta      TEXT,
    zona      TEXT,
    UNIQUE(bucket, capa, entidad)
);
CREATE INDEX IF NOT EXISTS idx_obs_ts  ON observaciones(ts);
CREATE INDEX IF NOT EXISTS idx_obs_bk  ON observaciones(bucket);
CREATE INDEX IF NOT EXISTS idx_obs_ll  ON observaciones(lat, lon);
CREATE INDEX IF NOT EXISTS idx_obs_cap ON observaciones(capa);
"""


def _conectar() -> sqlite3.Connection:
    os.makedirs(STATE_DIR, exist_ok=True)
    con = sqlite3.connect(DB_PATH, timeout=15)
    con.row_factory = sqlite3.Row
    con.executescript(DDL)
    return con


# ── Captura ──────────────────────────────────────────────────


@dataclass
class ResumenCaptura:
    ts: float
    filas: int
    por_capa: dict[str, int]
    errores: list[str]


def capturar(zonas: list[Zona] | None = None,
             client: GevClient | None = None) -> ResumenCaptura:
    """Toma una foto de los feeds de GEV dentro de cada geocerca."""
    zonas = zonas if zonas is not None else cargar_zonas()
    client = client or GevClient()
    ahora = time.time()
    bucket = int(ahora // BUCKET_S)
    filas: list[tuple] = []
    por_capa: dict[str, int] = {}
    errores: list[str] = []

    # Se piden los feeds UNA vez y se filtran contra todas las zonas.
    capas_necesarias = {c for z in zonas for c in z.capas}

    def _add(zona: Zona, capa: str, entidad: str, lat: float, lon: float,
             alt: Any, meta: dict[str, Any]) -> None:
        filas.append((ahora, bucket, capa, entidad, lat, lon,
                      float(alt) if isinstance(alt, (int, float)) else None,
                      json.dumps(meta, ensure_ascii=False)[:800], zona.key))
        por_capa[capa] = por_capa.get(capa, 0) + 1

    for capa in sorted(capas_necesarias):
        try:
            items = _leer_capa(client, capa, zonas)
        except Exception as e:
            errores.append(f"{capa}: {type(e).__name__}: {e}")
            continue
        for zona in zonas:
            if capa not in zona.capas:
                continue
            for it in items:
                lat, lon = it.get("lat"), it.get("lon")
                if lat is None or lon is None:
                    continue
                if distancia_km(zona.lat, zona.lon, float(lat), float(lon)) > zona.radio_km:
                    continue
                entidad = str(it.get("_id") or f"{lat:.4f},{lon:.4f}")
                meta = {k: v for k, v in it.items() if k not in ("lat", "lon")}
                _add(zona, capa, entidad, float(lat), float(lon), it.get("_alt"), meta)

    con = _conectar()
    try:
        con.executemany(
            "INSERT OR IGNORE INTO observaciones "
            "(ts, bucket, capa, entidad, lat, lon, alt, meta, zona) "
            "VALUES (?,?,?,?,?,?,?,?,?)",
            filas,
        )
        con.commit()
        insertadas = con.total_changes
    finally:
        con.close()

    return ResumenCaptura(ahora, insertadas, por_capa, errores)


def _leer_capa(client: GevClient, capa: str, zonas: list[Zona]) -> list[dict[str, Any]]:
    """Lee una capa y la normaliza a dicts con lat/lon/_id/_alt."""
    if capa == "vuelos":
        return client.vuelos()
    if capa == "sismos":
        mag_min = min((z.min_mag for z in zonas if "sismos" in z.capas), default=4.0)
        return [
            {"lat": s["lat"], "lon": s["lon"], "_id": f"M{s['mag']}-{s['lugar']}",
             "_alt": None, "mag": s["mag"], "lugar": s["lugar"]}
            for s in GevClient.sismos(min_mag=mag_min, limite=500)
        ]
    if capa == "incendios":
        datos = client.incendios()
        focos = datos.get("fires") if isinstance(datos, dict) else datos
        return [
            {"lat": f.get("latitude"), "lon": f.get("longitude"),
             "_id": f"{f.get('latitude')},{f.get('longitude')}", "_alt": None,
             "confidence": f.get("confidence"), "frp": f.get("frp")}
            for f in (focos or [])
        ]
    if capa == "militares":
        from gev_watch import _extraer_puntos
        return list(_extraer_puntos(client.militares()))
    if capa == "barcos":
        from gev_watch import _extraer_puntos
        return list(_extraer_puntos(client.barcos()))
    return []


# ── Consultas ────────────────────────────────────────────────


def rebobinar(ts: float, lat: float, lon: float, radio_km: float = 50,
              capa: str | None = None, tolerancia_s: int = 900) -> list[dict[str, Any]]:
    """Que habia en ese punto, lo mas cerca posible de ese instante.

    Busca la foto (bucket) mas cercana dentro de `tolerancia_s` y devuelve
    las observaciones de ese momento dentro del radio.
    """
    con = _conectar()
    try:
        fila = con.execute(
            "SELECT bucket FROM observaciones "
            "ORDER BY ABS(ts - ?) LIMIT 1", (ts,)
        ).fetchone()
        if not fila:
            return []
        bucket = fila["bucket"]
        if abs(bucket * BUCKET_S - ts) > tolerancia_s:
            return []
        sql = ("SELECT ts, capa, entidad, lat, lon, alt, meta, zona "
               "FROM observaciones WHERE bucket = ?")
        params: list[Any] = [bucket]
        if capa:
            sql += " AND capa = ?"
            params.append(capa)
        out: list[dict[str, Any]] = []
        for r in con.execute(sql, params):
            d = distancia_km(lat, lon, r["lat"], r["lon"])
            if d > radio_km:
                continue
            out.append({
                "ts": r["ts"],
                "hora": datetime.fromtimestamp(r["ts"]).strftime("%Y-%m-%d %H:%M:%S"),
                "capa": r["capa"], "entidad": r["entidad"],
                "lat": r["lat"], "lon": r["lon"], "alt": r["alt"],
                "dist_km": round(d, 2), "zona": r["zona"],
                "meta": json.loads(r["meta"]) if r["meta"] else {},
                "link": gev_link(r["lat"], r["lon"], alt=1200,
                                 style="flir" if r["capa"] in ("sismos", "incendios") else "normal"),
            })
        out.sort(key=lambda x: x["dist_km"])
        return out
    finally:
        con.close()


def timeline(lat: float, lon: float, radio_km: float = 50, horas: int = 24,
             bucket_min: int = 60, capa: str | None = None) -> list[dict[str, Any]]:
    """Cuenta de observaciones por franja temporal. Para ver la evolucion."""
    desde = time.time() - horas * 3600
    con = _conectar()
    try:
        sql = ("SELECT ts, capa, lat, lon FROM observaciones WHERE ts >= ?")
        params: list[Any] = [desde]
        if capa:
            sql += " AND capa = ?"
            params.append(capa)
        cubos: dict[int, dict[str, int]] = {}
        ancho = bucket_min * 60
        for r in con.execute(sql, params):
            if distancia_km(lat, lon, r["lat"], r["lon"]) > radio_km:
                continue
            b = int(r["ts"] // ancho) * ancho
            d = cubos.setdefault(b, {})
            d[r["capa"]] = d.get(r["capa"], 0) + 1
        return [
            {
                "desde": datetime.fromtimestamp(b).strftime("%m-%d %H:%M"),
                "total": sum(v.values()),
                **v,
            }
            for b, v in sorted(cubos.items())
        ]
    finally:
        con.close()


def stats() -> dict[str, Any]:
    """Que hay guardado: total, rango temporal y desglose por capa."""
    con = _conectar()
    try:
        tot = con.execute("SELECT COUNT(*) c FROM observaciones").fetchone()["c"]
        if not tot:
            return {"total": 0, "por_capa": {}, "desde": None, "hasta": None,
                    "db_mb": round(_tamano_mb(), 2)}
        r = con.execute("SELECT MIN(ts) a, MAX(ts) b FROM observaciones").fetchone()
        capas = {
            row["capa"]: row["c"]
            for row in con.execute(
                "SELECT capa, COUNT(*) c FROM observaciones GROUP BY capa ORDER BY c DESC")
        }
        return {
            "total": tot,
            "por_capa": capas,
            "desde": datetime.fromtimestamp(r["a"]).strftime("%Y-%m-%d %H:%M:%S"),
            "hasta": datetime.fromtimestamp(r["b"]).strftime("%Y-%m-%d %H:%M:%S"),
            "db_mb": round(_tamano_mb(), 2),
        }
    finally:
        con.close()


def _tamano_mb() -> float:
    try:
        return os.path.getsize(DB_PATH) / (1024 * 1024)
    except OSError:
        return 0.0


def purgar(dias: int = RETENCION_DIAS) -> int:
    """Borra observaciones mas antiguas que `dias`. Devuelve cuantas."""
    limite = time.time() - dias * 86400
    con = _conectar()
    try:
        cur = con.execute("DELETE FROM observaciones WHERE ts < ?", (limite,))
        con.commit()
        return cur.rowcount
    finally:
        con.close()


# ── CLI ──────────────────────────────────────────────────────


def _main(argv: Sequence[str] | None = None) -> int:
    p = argparse.ArgumentParser(description="Archivo del AOI sobre los feeds de GEV")
    sub = p.add_subparsers(dest="cmd", required=True)

    sub.add_parser("capturar", help="una foto del AOI")
    sub.add_parser("stats", help="que hay guardado")

    t = sub.add_parser("timeline", help="evolucion temporal")
    t.add_argument("lat", type=float)
    t.add_argument("lon", type=float)
    t.add_argument("--radio", type=float, default=50)
    t.add_argument("--horas", type=int, default=24)
    t.add_argument("--bucket-min", type=int, default=60)

    r = sub.add_parser("rebobinar", help="que habia alli en un momento dado")
    r.add_argument("lat", type=float)
    r.add_argument("lon", type=float)
    r.add_argument("--hace", type=float, default=1.0,
                   help="horas hacia atras (0 = ahora)")
    r.add_argument("--radio", type=float, default=50)
    r.add_argument("--capa", default=None)

    g = sub.add_parser("purgar", help="borrar historico antiguo")
    g.add_argument("--dias", type=int, default=RETENCION_DIAS)

    args = p.parse_args(argv)

    if args.cmd == "capturar":
        res = capturar()
        print(f"capturadas {res.filas} fila(s) nuevas")
        for capa, n in sorted(res.por_capa.items()):
            print(f"  {capa:<10} {n}")
        for e in res.errores:
            print(f"  [aviso] {e}", file=sys.stderr)
        return 0

    if args.cmd == "stats":
        s = stats()
        print(f"total: {s['total']} observaciones  (db: {s['db_mb']} MB)")
        if s["desde"]:
            print(f"rango: {s['desde']}  ->  {s['hasta']}")
        for capa, n in s["por_capa"].items():
            print(f"  {capa:<10} {n}")
        return 0

    if args.cmd == "timeline":
        filas = timeline(args.lat, args.lon, args.radio, args.horas, args.bucket_min)
        if not filas:
            print("(sin datos: ejecuta 'capturar' varias veces primero)")
            return 0
        for f in filas:
            resto = " ".join(f"{k}={v}" for k, v in f.items()
                             if k not in ("desde", "total"))
            print(f"{f['desde']}  total={f['total']:<5} {resto}")
        return 0

    if args.cmd == "rebobinar":
        ts = time.time() - args.hace * 3600
        filas = rebobinar(ts, args.lat, args.lon, args.radio, args.capa)
        if not filas:
            print("(sin foto cercana a ese instante)")
            return 0
        print(f"foto de {filas[0]['hora']} — {len(filas)} objeto(s):")
        for f in filas[:25]:
            print(f"  {f['capa']:<10} {f['entidad']:<22} {f['dist_km']:>7} km")
        return 0

    if args.cmd == "purgar":
        n = purgar(args.dias)
        print(f"borradas {n} observacion(es) de mas de {args.dias} dias")
        return 0

    return 2


if __name__ == "__main__":
    sys.exit(_main())
