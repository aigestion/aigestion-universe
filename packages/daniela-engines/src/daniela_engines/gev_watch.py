#!/usr/bin/env python3
"""
GEV Watch — feeds de God's Eye View como disparadores
=====================================================
Convierte los feeds en vivo de God's Eye View en **eventos** cuando algo entra
en una geocerca. Es el paso de "app que miras" a "radar que te avisa".

Idea 2.1 del documento de integracion. Deliberadamente desacoplado:
  - No importa `auto-engine` ni ningun otro modulo de Daniela.
  - Emite eventos por callback; quien los consuma decide que hacer
    (Telegram, auto_engine, el panel de Daniela, lo que sea).

Capas vigilables:
  vuelos     - /api/opensky        (sin clave)
  militares  - /api/adsblol/mil    (sin clave)
  sismos     - USGS all_day        (sin clave)
  incendios  - /api/firms          (requiere clave NASA FIRMS en GEV)
  barcos     - /api/ais-live       (requiere clave AISStream en GEV)

Estado en disco (core/data/gev_watch/):
  zonas.json   - geocercas configuradas
  estado.json  - entidades ya vistas, para no repetir avisos

Coste: $0. Ninguna capa de las que funcionan sin clave cuesta dinero.

Uso:
  python core/gev_watch.py zonas
  python core/gev_watch.py add casa 41.39 2.15 --radio 25 --capas vuelos,sismos
  python core/gev_watch.py once
  python core/gev_watch.py run --intervalo 300
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import threading
import time
from collections.abc import Callable, Sequence
from dataclasses import asdict, dataclass, field
from typing import Any

from gev_bridge import GevClient, distancia_km, gev_link

# ── Config ───────────────────────────────────────────────────

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
STATE_DIR = os.path.join(BASE_DIR, "data", "gev_watch")
ZONAS_FILE = os.path.join(STATE_DIR, "zonas.json")
ESTADO_FILE = os.path.join(STATE_DIR, "estado.json")

INTERVALO_DEFECTO = 300          # 5 min
RETENCION_VISTOS_S = 6 * 3600    # 6 h: tras esto, una entidad puede volver a avisar
CAPAS_VALIDAS = ("vuelos", "militares", "sismos", "incendios", "barcos")


# ── Modelos ──────────────────────────────────────────────────


@dataclass
class Zona:
    """Geocerca circular con las capas que se vigilan en ella."""

    key: str
    nombre: str
    lat: float
    lon: float
    radio_km: float = 25.0
    capas: list[str] = field(default_factory=lambda: ["vuelos", "sismos"])
    min_mag: float = 4.0          # umbral solo para sismos
    alt_camara: float = 1200.0    # altitud del globo al mostrar la zona

    @classmethod
    def desde_dict(cls, d: dict[str, Any]) -> Zona:
        capas = [c for c in d.get("capas", ["vuelos", "sismos"]) if c in CAPAS_VALIDAS]
        return cls(
            key=d["key"],
            nombre=d.get("nombre", d["key"]),
            lat=float(d["lat"]),
            lon=float(d["lon"]),
            radio_km=float(d.get("radio_km", 25.0)),
            capas=capas or ["vuelos", "sismos"],
            min_mag=float(d.get("min_mag", 4.0)),
            alt_camara=float(d.get("alt_camara", 1200.0)),
        )


@dataclass
class Evento:
    """Algo entro en una geocerca."""

    zona: str
    zona_nombre: str
    capa: str
    entidad_id: str
    titulo: str
    detalle: str
    lat: float
    lon: float
    dist_km: float
    ts: float = field(default_factory=time.time)
    link: str = ""

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    def linea(self) -> str:
        return f"[{self.zona_nombre}/{self.capa}] {self.titulo} — {self.detalle}"


# ── Persistencia ─────────────────────────────────────────────


def _asegurar_dir() -> None:
    os.makedirs(STATE_DIR, exist_ok=True)


def cargar_zonas() -> list[Zona]:
    if not os.path.exists(ZONAS_FILE):
        return []
    with open(ZONAS_FILE, encoding="utf-8") as f:
        return [Zona.desde_dict(d) for d in json.load(f)]


def guardar_zonas(zonas: list[Zona]) -> None:
    _asegurar_dir()
    with open(ZONAS_FILE, "w", encoding="utf-8") as f:
        json.dump([asdict(z) for z in zonas], f, ensure_ascii=False, indent=2)


def _cargar_estado() -> dict[str, float]:
    if not os.path.exists(ESTADO_FILE):
        return {}
    try:
        with open(ESTADO_FILE, encoding="utf-8") as f:
            return {k: float(v) for k, v in json.load(f).items()}
    except Exception:
        return {}


def _guardar_estado(vistos: dict[str, float]) -> None:
    _asegurar_dir()
    with open(ESTADO_FILE, "w", encoding="utf-8") as f:
        json.dump(vistos, f, indent=2)


# ── Vigilante ────────────────────────────────────────────────


class GevWatcher:
    """Revisa los feeds de GEV contra las geocercas y emite eventos."""

    def __init__(self, zonas: list[Zona] | None = None,
                 client: GevClient | None = None):
        self.zonas = zonas if zonas is not None else cargar_zonas()
        self.client = client or GevClient()
        self.vistos = _cargar_estado()
        self._callbacks: list[Callable[[Evento], None]] = []
        self._lock = threading.Lock()

    # -- suscripcion --

    def register_callback(self, cb: Callable[[Evento], None]) -> None:
        """Registra un consumidor de eventos (Telegram, auto_engine, ...)."""
        self._callbacks.append(cb)

    def _emitir(self, ev: Evento) -> None:
        for cb in self._callbacks:
            try:
                cb(ev)
            except Exception as e:  # un consumidor roto no debe parar el radar
                print(f"[gev_watch] callback fallo: {e}", file=sys.stderr)

    # -- deduplicacion --

    def _clave(self, zona: Zona, capa: str, entidad: str) -> str:
        return f"{zona.key}|{capa}|{entidad}"

    def _ya_visto(self, zona: Zona, capa: str, entidad: str) -> bool:
        k = self._clave(zona, capa, entidad)
        t = self.vistos.get(k)
        if t is None:
            return False
        if time.time() - t > RETENCION_VISTOS_S:
            self.vistos.pop(k, None)
            return False
        return True

    def _marcar_visto(self, zona: Zona, capa: str, entidad: str) -> None:
        self.vistos[self._clave(zona, capa, entidad)] = time.time()

    # -- revision --

    def revisar(self) -> list[Evento]:
        """Una pasada por todas las zonas y capas. Devuelve los eventos nuevos."""
        eventos: list[Evento] = []
        for zona in self.zonas:
            for capa in zona.capas:
                try:
                    eventos.extend(self._revisar_capa(zona, capa))
                except Exception as e:
                    # una capa sin clave o caida no debe tumbar el resto
                    print(f"[gev_watch] capa {capa} en {zona.key} fallo: "
                          f"{type(e).__name__}: {e}", file=sys.stderr)
        if eventos:
            _guardar_estado(self.vistos)
            for ev in eventos:
                self._emitir(ev)
        return eventos

    def _revisar_capa(self, zona: Zona, capa: str) -> list[Evento]:
        if capa == "vuelos":
            return self._revisar_puntos(
                zona, capa, self.client.vuelos(),
                id_de=lambda x: x.get("callsign") or x.get("icao24") or "?",
                titulo_de=lambda x: x.get("callsign") or x.get("icao24") or "aeronave",
                detalle_de=lambda x: f"{x.get('pais','?')}, "
                                     f"{x.get('alt_m') or '?'} m, rumbo {x.get('rumbo') or '?'}",
            )
        if capa == "sismos":
            return self._revisar_puntos(
                zona, capa,
                GevClient.sismos(min_mag=zona.min_mag, limite=500),
                id_de=lambda x: f"{x['mag']}-{x['lat']:.2f}-{x['lon']:.2f}",
                titulo_de=lambda x: f"Sismo M{x['mag']}",
                detalle_de=lambda x: str(x.get("lugar") or ""),
            )
        if capa == "incendios":
            datos = self.client.incendios()
            focos = datos.get("fires") if isinstance(datos, dict) else datos
            return self._revisar_puntos(
                zona, capa, focos or [],
                id_de=lambda x: f"{x.get('latitude')},{x.get('longitude')}",
                titulo_de=lambda x: "Foco de incendio",
                detalle_de=lambda x: f"confianza {x.get('confidence','?')}, "
                                     f"FRP {x.get('frp','?')}",
                lat_de=lambda x: x.get("latitude"),
                lon_de=lambda x: x.get("longitude"),
            )
        if capa in ("militares", "barcos"):
            return self._revisar_generico(zona, capa)
        return []

    def _revisar_puntos(
        self,
        zona: Zona,
        capa: str,
        items: Sequence[dict[str, Any]],
        *,
        id_de: Callable[[dict[str, Any]], str],
        titulo_de: Callable[[dict[str, Any]], str],
        detalle_de: Callable[[dict[str, Any]], str],
        lat_de: Callable[[dict[str, Any]], Any] = lambda x: x.get("lat"),
        lon_de: Callable[[dict[str, Any]], Any] = lambda x: x.get("lon"),
    ) -> list[Evento]:
        out: list[Evento] = []
        for it in items:
            lat, lon = lat_de(it), lon_de(it)
            if lat is None or lon is None:
                continue
            d = distancia_km(zona.lat, zona.lon, float(lat), float(lon))
            if d > zona.radio_km:
                continue
            entidad = str(id_de(it))
            if self._ya_visto(zona, capa, entidad):
                continue
            self._marcar_visto(zona, capa, entidad)
            estilo = "flir" if capa in ("sismos", "incendios") else "normal"
            out.append(Evento(
                zona=zona.key,
                zona_nombre=zona.nombre,
                capa=capa,
                entidad_id=entidad,
                titulo=titulo_de(it),
                detalle=detalle_de(it),
                lat=float(lat),
                lon=float(lon),
                dist_km=round(d, 2),
                link=gev_link(float(lat), float(lon), alt=zona.alt_camara, style=estilo),
            ))
        out.sort(key=lambda e: e.dist_km)
        return out

    def _revisar_generico(self, zona: Zona, capa: str) -> list[Evento]:
        """Capas cuyo formato no esta verificado (militares, barcos).

        Busca recursivamente cualquier dict con lat/lon. Tolerante a proposito:
        si el formato cambia, sigue encontrando puntos en vez de romperse.
        """
        datos = self.client.militares() if capa == "militares" else self.client.barcos()
        puntos = list(_extraer_puntos(datos))
        return self._revisar_puntos(
            zona, capa, puntos,
            id_de=lambda x: str(x.get("_id") or f"{x['lat']},{x['lon']}"),
            titulo_de=lambda x: str(x.get("_id") or f"{capa[:-1] or capa} sin identificar"),
            detalle_de=lambda x: f"a {x.get('_alt', '?')}",
        )

    # -- bucle --

    def correr(self, intervalo: int = INTERVALO_DEFECTO,
               parar: threading.Event | None = None) -> None:
        """Bucle de vigilancia. `parar` permite terminarlo desde fuera."""
        print(f"[gev_watch] vigilando {len(self.zonas)} zona(s) cada {intervalo}s")
        while not (parar and parar.is_set()):
            try:
                for ev in self.revisar():
                    print("[evento] " + ev.linea())
            except Exception as e:
                print(f"[gev_watch] pasada fallo: {e}", file=sys.stderr)
            if parar:
                parar.wait(intervalo)
            else:
                time.sleep(intervalo)


# ── Extraccion tolerante de puntos ───────────────────────────


def _extraer_puntos(obj: Any, _prof: int = 0) -> Any:
    """Genera dicts con lat/lon encontrados en cualquier estructura anidada."""
    if _prof > 6:
        return
    if isinstance(obj, dict):
        lat = obj.get("lat", obj.get("latitude"))
        lon = obj.get("lon", obj.get("longitude"))
        if isinstance(lat, (int, float)) and isinstance(lon, (int, float)):
            yield {
                "lat": float(lat),
                "lon": float(lon),
                "_id": obj.get("callsign") or obj.get("name") or obj.get("mmsi")
                       or obj.get("icao24") or obj.get("hex"),
                "_alt": obj.get("alt") or obj.get("altitude") or obj.get("alt_m"),
            }
            return
        for v in obj.values():
            yield from _extraer_puntos(v, _prof + 1)
    elif isinstance(obj, (list, tuple)):
        for v in obj:
            yield from _extraer_puntos(v, _prof + 1)


# ── CLI ──────────────────────────────────────────────────────


def _main(argv: Sequence[str] | None = None) -> int:
    p = argparse.ArgumentParser(description="Geocercas sobre los feeds de GEV")
    sub = p.add_subparsers(dest="cmd", required=True)

    sub.add_parser("zonas", help="listar geocercas")

    a = sub.add_parser("add", help="anadir/actualizar una geocerca")
    a.add_argument("key")
    a.add_argument("lat", type=float)
    a.add_argument("lon", type=float)
    a.add_argument("--nombre", default=None)
    a.add_argument("--radio", type=float, default=25.0)
    a.add_argument("--capas", default="vuelos,sismos")

    r = sub.add_parser("rm", help="borrar una geocerca")
    r.add_argument("key")

    sub.add_parser("once", help="una pasada de vigilancia")

    c = sub.add_parser("run", help="vigilancia continua")
    c.add_argument("--intervalo", type=int, default=INTERVALO_DEFECTO)

    args = p.parse_args(argv)

    if args.cmd == "zonas":
        zs = cargar_zonas()
        if not zs:
            print("(sin geocercas)")
        for z in zs:
            print(f"{z.key:<12} {z.nombre:<18} {z.lat:.4f},{z.lon:.4f} "
                  f"r={z.radio_km}km capas={','.join(z.capas)}")
        return 0

    if args.cmd == "add":
        capas = [c.strip() for c in args.capas.split(",") if c.strip() in CAPAS_VALIDAS]
        zs = [z for z in cargar_zonas() if z.key != args.key]
        zs.append(Zona(key=args.key, nombre=args.nombre or args.key, lat=args.lat,
                       lon=args.lon, radio_km=args.radio, capas=capas or ["vuelos", "sismos"]))
        guardar_zonas(zs)
        print(f"zona '{args.key}' guardada ({len(zs)} en total)")
        return 0

    if args.cmd == "rm":
        zs = [z for z in cargar_zonas() if z.key != args.key]
        guardar_zonas(zs)
        print(f"zona '{args.key}' borrada ({len(zs)} restantes)")
        return 0

    if args.cmd == "once":
        w = GevWatcher()
        if not w.zonas:
            print("no hay geocercas: usa 'add' primero")
            return 1
        evs = w.revisar()
        print(f"{len(evs)} evento(s) nuevo(s)")
        for ev in evs:
            print("  " + ev.linea())
        return 0

    if args.cmd == "run":
        GevWatcher().correr(args.intervalo)
        return 0

    return 2


if __name__ == "__main__":
    sys.exit(_main())
