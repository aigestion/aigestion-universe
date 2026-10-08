#!/usr/bin/env python3
"""
gev.i18n — Idioma de Daniela
============================================
**Espanol por defecto, ingles opcional.** Un solo catalogo es la fuente de
verdad: el backend lo sirve y el visor lo aplica con atributos `data-i18n`.

Resolucion del idioma (de mayor a menor prioridad):
  1. `?lang=xx` en la URL
  2. cookie `daniela_lang`
  3. cabecera `Accept-Language` del navegador
  4. IDIOMA_POR_DEFECTO  ->  "es"

Rutas:
  GET /api/i18n          -> catalogo del idioma resuelto
  GET /api/i18n/<lang>   -> catalogo de un idioma concreto
  GET /api/idiomas       -> idiomas soportados
"""

from __future__ import annotations

import os
import time
from typing import Any

IDIOMA_POR_DEFECTO = os.getenv("DANIELA_LANG", "es").strip().lower() or "es"

IDIOMAS_SOPORTADOS: list[str] = ["es", "en"]

NOMBRES = {"es": "Espanol", "en": "English"}

# ── Catalogo ─────────────────────────────────────────────────
# Clave -> {idioma: texto}. Si falta una traduccion se cae al defecto.

CATALOGO: dict[str, dict[str, str]] = {
    # Cabecera
    "app.titulo": {"es": "God's Eye Dashboard", "en": "God's Eye Dashboard"},
    "app.subtitulo": {"es": "Daniela OS", "en": "Daniela OS"},
    "hud.sede": {"es": "Ir a la Sede", "en": "Go to HQ"},
    "hud.globo": {"es": "Ver todo", "en": "View all"},
    "hud.refrescar": {"es": "Refrescar", "en": "Refresh"},
    "hud.pro": {"es": "Visor completo", "en": "Full viewer"},
    "hud.idioma": {"es": "Idioma", "en": "Language"},
    "hud.admin": {"es": "Administrador — acceso total", "en": "Administrator — full access"},
    "hud.cliente": {"es": "Cliente — acceso restringido", "en": "Client — restricted access"},
    "hud.empresas": {"es": "empresas", "en": "companies"},
    "hud.en_globo": {"es": "en el globo", "en": "on the globe"},
    "hud.mrr": {"es": "MRR", "en": "MRR"},
    "hud.restringido": {"es": "restringido", "en": "restricted"},
    "hud.agregados": {"es": "agregados", "en": "aggregates"},
    # Panel lateral
    "panel.titulo": {"es": "Nodos", "en": "Nodes"},
    "panel.vacio": {"es": "Sin nodos visibles.", "en": "No visible nodes."},
    "panel.sede": {"es": "Sede (solo admin)", "en": "HQ (admin only)"},
    "panel.sede_marca": {"es": "Sede", "en": "HQ"},
    "panel.sin_ubicacion": {"es": "Sin ubicacion registrada", "en": "No location on record"},
    "panel.sin_telemetria": {"es": "Sin telemetria reciente.", "en": "No recent telemetry."},
    "panel.sede_no_disp": {
        "es": "La Sede no esta disponible para tu rol.",
        "en": "HQ is not available for your role.",
    },
    "panel.sin_acceso": {"es": "Sin acceso a esa empresa.", "en": "No access to that company."},
    # Command Center
    "cc.titulo": {"es": "Daniela Command Center", "en": "Daniela Command Center"},
    "cc.listo": {"es": "Listo. Elige una herramienta.", "en": "Ready. Pick a tool."},
    "cc.astra": {"es": "Astra Document Sniper", "en": "Astra Document Sniper"},
    "cc.astra.sub": {"es": "Ingesta RAG", "en": "RAG ingestion"},
    "cc.voice": {"es": "Voice Briefing Agent", "en": "Voice Briefing Agent"},
    "cc.voice.sub": {"es": "Sintesis TTS / resumen", "en": "TTS synthesis / briefing"},
    "cc.inbox": {"es": "Inbox Zero Drafter", "en": "Inbox Zero Drafter"},
    "cc.inbox.sub": {"es": "Triaje correo y WhatsApp", "en": "Email & WhatsApp triage"},
    "cc.telemetria": {"es": "Life Telemetry HUD", "en": "Life Telemetry HUD"},
    "cc.telemetria.sub": {"es": "Hardware, sensores, ESP32", "en": "Hardware, sensors, ESP32"},
    "cc.consola": {"es": "Command & Control", "en": "Command & Control"},
    "cc.consola.sub": {"es": "Terminal de agentes y logs", "en": "Agent terminal & logs"},
    "cc.memoria": {"es": "Memoria de Daniela", "en": "Daniela's Memory"},
    "cc.memoria.sub": {"es": "Recuerdos: buscar y guardar", "en": "Memories: search & save"},
    "cc.memoria.ph": {"es": "¿Qué recuerdas de…?", "en": "What do you remember about…?"},
    "cc.memoria.buscar": {"es": "Buscar", "en": "Search"},
    "cc.memoria.guardar": {"es": "Guardar", "en": "Save"},
    "cc.memoria.vacia": {
        "es": "Memoria vacía: guarda el primer recuerdo.",
        "en": "Empty memory: save the first one.",
    },
    "cc.memoria.restringida": {
        "es": "La memoria es global (sin filtro por tenant): solo el "
        "administrador puede leerla o escribirla.",
        "en": "The memory is global (no per-tenant filter): administrators only.",
    },
    "cc.cargando": {"es": "Consultando a Daniela...", "en": "Asking Daniela..."},
    "cc.no_conectado": {"es": "Sin conectar", "en": "Not connected"},
    # Empresa
    "emp.titulo": {"es": "Empresa", "en": "Company"},
    "emp.plan": {"es": "Plan", "en": "Plan"},
    "emp.estado": {"es": "Estado", "en": "Status"},
    "emp.mrr": {"es": "MRR", "en": "MRR"},
    "emp.eventos": {"es": "Eventos 24h", "en": "Events 24h"},
    "emp.estructura": {"es": "Estructura 3D", "en": "3D structure"},
    "emp.telemetria": {"es": "Telemetria reciente", "en": "Recent telemetry"},
    # Capas OSINT
    "osint.titulo": {"es": "Capas OSINT", "en": "OSINT layers"},
    "osint.sismos": {"es": "Sismos", "en": "Earthquakes"},
    "osint.vuelos": {"es": "Vuelos", "en": "Flights"},
    "osint.militares": {"es": "Militares", "en": "Military"},
    "osint.incendios": {"es": "Incendios", "en": "Fires"},
    "osint.barcos": {"es": "Barcos", "en": "Vessels"},
    "osint.camaras": {"es": "Camaras", "en": "Cameras"},
    "osint.sin_gev": {"es": "GEV no responde", "en": "GEV not responding"},
    "osint.cargando": {"es": "Cargando capa...", "en": "Loading layer..."},
    "osint.vacia": {"es": "Sin puntos en esta zona.", "en": "No points in this area."},
    # Alta de cliente
    "cli.titulo": {"es": "Nueva empresa", "en": "New company"},
    "cli.nombre": {"es": "Nombre", "en": "Name"},
    "cli.direccion": {"es": "Direccion", "en": "Address"},
    "cli.sector": {"es": "Sector", "en": "Sector"},
    "cli.tier": {"es": "Plan", "en": "Tier"},
    "cli.crear": {"es": "Crear empresa", "en": "Create company"},
    "cli.creada": {"es": "Empresa creada.", "en": "Company created."},
    "cli.falta_nombre": {"es": "Falta el nombre.", "en": "Name is required."},
    # Avisos
    "aviso.ok": {"es": "Hecho.", "en": "Done."},
    "aviso.error": {"es": "Error", "en": "Error"},
    "aviso.denegado": {"es": "Acceso denegado.", "en": "Access denied."},
}


def normalizar(lang: Any) -> str:
    """Devuelve un idioma soportado o el defecto."""
    if not lang:
        return IDIOMA_POR_DEFECTO
    corto = str(lang).strip().lower().replace("_", "-").split("-")[0]
    return corto if corto in IDIOMAS_SOPORTADOS else IDIOMA_POR_DEFECTO


def traducir(clave: str, lang: str = "") -> str:
    """Traduce una clave. Si no existe, devuelve la clave (no inventa texto)."""
    idioma = normalizar(lang)
    entrada = CATALOGO.get(clave)
    if not entrada:
        return clave
    return entrada.get(idioma) or entrada.get(IDIOMA_POR_DEFECTO) or clave


def catalogo(lang: str = "") -> dict[str, str]:
    """Todo el catalogo ya resuelto a un idioma."""
    idioma = normalizar(lang)
    return {k: traducir(k, idioma) for k in CATALOGO}


def _resolver_peticion(request) -> str:
    """Aplica la cascada de resolucion de idioma."""
    # 1. query string
    q = request.args.get("lang")
    if q:
        return normalizar(q)
    # 2. cookie
    c = request.cookies.get("daniela_lang")
    if c:
        return normalizar(c)
    # 3. Accept-Language (el primero que soportemos)
    for trozo in (request.headers.get("Accept-Language") or "").split(","):
        corto = trozo.split(";")[0].strip()
        if corto:
            n = normalizar(corto)
            if n in IDIOMAS_SOPORTADOS and n == corto.lower()[:2]:
                return n
    # 4. defecto
    return IDIOMA_POR_DEFECTO


def registrar_i18n(app) -> None:
    """Registra las rutas de idioma en `app`."""
    from flask import jsonify, request

    @app.route("/api/i18n")
    def api_i18n():
        lang = _resolver_peticion(request)
        return jsonify(
            {
                "ok": True,
                "idioma": lang,
                "defecto": IDIOMA_POR_DEFECTO,
                "soportados": IDIOMAS_SOPORTADOS,
                "cadenas": catalogo(lang),
                "ts": time.time(),
            }
        )

    @app.route("/api/i18n/<lang>")
    def api_i18n_lang(lang: str):
        idioma = normalizar(lang)
        return jsonify(
            {
                "ok": True,
                "idioma": idioma,
                "defecto": IDIOMA_POR_DEFECTO,
                "soportados": IDIOMAS_SOPORTADOS,
                "cadenas": catalogo(idioma),
                "ts": time.time(),
            }
        )

    @app.route("/api/idiomas")
    def api_idiomas():
        return jsonify(
            {
                "ok": True,
                "defecto": IDIOMA_POR_DEFECTO,
                "soportados": [{"codigo": c, "nombre": NOMBRES[c]} for c in IDIOMAS_SOPORTADOS],
            }
        )

    print(
        f"[i18n] idioma por defecto: {IDIOMA_POR_DEFECTO} "
        f"(soportados: {', '.join(IDIOMAS_SOPORTADOS)})"
    )
