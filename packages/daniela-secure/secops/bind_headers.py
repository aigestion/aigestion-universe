"""Auditor de superficie: qué escucha, dónde y cómo.

Detecta servicios atados a 0.0.0.0 (toda la WiFi los ve), HTTP sin TLS y
cabeceras de seguridad ausentes.
"""
from __future__ import annotations

from secops.models import Finding
from secops.net import HttpResp, banner_http, es_wildcard

# Servicios propios conocidos: (nombre, host, puerto, requiere_auth).
SERVICIOS = [
    ("daniela", "127.0.0.1", 9200, True),
    ("hermes", "127.0.0.1", 9300, True),
    ("dashboard", "127.0.0.1", 9997, True),
    ("pwa-pixel", "192.168.1.130", 8095, True),
    ("gateway-pixel", "192.168.1.130", 8082, True),
    ("unified-pc", "127.0.0.1", 8082, False),
    ("epic-pc", "127.0.0.1", 5020, False),
]

CABECERAS = (
    "content-security-policy",
    "strict-transport-security",
    "x-frame-options",
    "x-content-type-options",
    "referrer-policy",
    "permissions-policy",
)


def auditar_binds(escuchas: list[dict]) -> list[Finding]:
    """Cada socket en 0.0.0.0 es visible desde toda la WiFi/LAN."""
    hallazgos = []
    for e in escuchas:
        if not es_wildcard(e["ip"]):
            continue
        hallazgos.append(
            Finding(
                id=f"bind-wildcard-{e['puerto']}",
                titulo=f"Puerto {e['puerto']} expuesto a toda la red ({e['ip']})",
                severidad="alta" if e["puerto"] in (9200, 9300, 8095, 8082) else "media",
                donde=f"{e['ip']}:{e['puerto']}",
                evidencia=f"socket TCP en LISTEN sobre {e['ip']}",
                remedio="Atar a 127.0.0.1 y exponer solo vía Caddy con token; "
                "si debe ser LAN, documentarlo en el ADR.",
                auditor="bind",
            )
        )
    return hallazgos


def auditar_cabeceras(get=banner_http) -> list[Finding]:
    hallazgos = []
    for nombre, host, puerto, _auth in SERVICIOS:
        try:
            r: HttpResp | None = get(host, puerto)
        except Exception:
            continue
        if r is None:
            continue
        donde = f"{host}:{puerto}"
        if r.url.startswith("http://"):
            hallazgos.append(
                Finding(
                    id=f"http-plano-{nombre}",
                    titulo=f"{nombre} habla HTTP sin cifrar",
                    severidad="media",
                    donde=donde,
                    evidencia=f"GET {r.url} -> {r.status} sin TLS",
                    remedio="TLS en el borde (Caddy con CA local) o túnel; "
                    "nunca credenciales por HTTP en WiFi.",
                    auditor="headers",
                )
            )
        heads = {k.lower(): v for k, v in r.headers.items()}
        faltan = [c for c in CABECERAS if c not in heads]
        if faltan and r.status < 400:
            hallazgos.append(
                Finding(
                    id=f"headers-{nombre}",
                    titulo=f"{nombre} sin cabeceras de seguridad ({len(faltan)})",
                    severidad="baja",
                    donde=donde,
                    evidencia="faltan: " + ", ".join(faltan),
                    remedio="Añadir CSP, X-Frame-Options, X-Content-Type-Options "
                    "y Referrer-Policy en el servidor o en Caddy.",
                    auditor="headers",
                )
            )
        server = heads.get("server", "")
        if server and "werkzeug" in server.lower():
            hallazgos.append(
                Finding(
                    id=f"banner-{nombre}",
                    titulo=f"{nombre} anuncia Werkzeug (huella de debug)",
                    severidad="baja",
                    donde=donde,
                    evidencia=f"Server: {server}",
                    remedio="Ocultar el banner (SERVER_NAME / proxy) y jamás "
                    "allow_unsafe_werkzeug en LAN.",
                    auditor="headers",
                )
            )
    return hallazgos
