"""Auditor de autenticación: qué responde sin credenciales.

Prueba endpoints que DEBERÍAN exigir auth y reporta los que contestan 200
sin token. Incluye sondas de inyección básicas (SQLi/XSS/path traversal)
contra endpoints de lectura propios: si el servidor refleja el payload sin
neutralizar, es hallazgo.
"""
from __future__ import annotations

from secops.models import Finding
from secops.net import HttpResp, http_get

# (nombre, path, método de prueba)
PROTEGIDOS = [
    ("daniela-chat", "http://127.0.0.1:9200/api/ai/chat"),
    ("daniela-iot", "http://127.0.0.1:9200/api/iot/devices"),
    ("hermes-estado", "http://127.0.0.1:9300/api/status"),
    ("dashboard-servicios", "http://127.0.0.1:9997/api/services"),
    ("pixel-tts", "http://192.168.1.130:8095/api/voice/tts"),
    ("pixel-chat", "http://192.168.1.130:8095/api/ai/chat"),
]

SONDAS_INYECCION = [
    "' OR '1'='1",
    "<script>alert(1)</script>",
    "../../etc/passwd",
    "{{7*7}}",
    "${7*7}",
]


def _refleja_sin_neutralizar(texto: str, payload: str) -> bool:
    return payload in texto


def auditar_auth(get=http_get) -> list[Finding]:
    hallazgos = []
    for nombre, url in PROTEGIDOS:
        try:
            r: HttpResp = get(url, timeout=4.0)
        except Exception:
            continue  # caído o filtrado: no es hallazgo de auth
        if r.status == 200:
            hallazgos.append(
                Finding(
                    id=f"auth-publico-{nombre}",
                    titulo=f"{nombre} responde 200 sin credenciales",
                    severidad="alta"
                    if any(k in nombre for k in ("chat", "iot", "tts"))
                    else "media",
                    donde=url,
                    evidencia=f"GET sin Authorization -> HTTP 200 ({len(r.body)} bytes)",
                    remedio="Exigir JWT/token también en loopback o mover el "
                    "endpoint tras el middleware de auth.",
                    auditor="auth",
                )
            )
        elif r.status == 401:
            hallazgos.append(
                Finding(
                    id=f"auth-ok-{nombre}",
                    titulo=f"{nombre} exige credenciales (401)",
                    severidad="info",
                    donde=url,
                    evidencia="GET sin Authorization -> HTTP 401",
                    auditor="auth",
                )
            )
    return hallazgos


def auditar_inyeccion(get=http_get) -> list[Finding]:
    """Reflejo de payloads en endpoints de búsqueda/eco propios."""
    hallazgos = []
    objetivos = [
        "http://127.0.0.1:9200/api/memory/search",
        "http://127.0.0.1:9997/api/services",
    ]
    for url in objetivos:
        for payload in SONDAS_INYECCION:
            try:
                r: HttpResp = get(f"{url}?q={payload}", timeout=4.0)
            except Exception:
                break  # servicio caído: pasar al siguiente
            cuerpo = r.body.decode("utf-8", errors="ignore")
            if r.status == 200 and _refleja_sin_neutralizar(cuerpo, payload):
                hallazgos.append(
                    Finding(
                        id=f"inyeccion-reflejo-{abs(hash(url + payload)) % 10000}",
                        titulo="Respuesta refleja el payload sin neutralizar",
                        severidad="alta",
                        donde=url,
                        evidencia=f"payload reflejado: {payload[:40]}",
                        remedio="Escapar HTML, parametrizar consultas y validar "
                        "entrada en el borde.",
                        auditor="inyeccion",
                    )
                )
                break
    return hallazgos
