"""Motor opcional Nuclei (ProjectDiscovery, MIT): plantillas CVE reales.

Si hay binario en `bin/nuclei/nuclei(.exe)`, ejecuta un perfil SEGURO contra
tus propios servicios (solo plantillas de misconfig/exposición, nada
intrusivo). Si no está, devuelve un hallazgo informativo con cómo instalarlo:

    https://github.com/projectdiscovery/nuclei/releases

Nunca es obligatorio: el resto de auditores funciona sin él.
"""
from __future__ import annotations

import json
import os
import subprocess
import sys

from secops.models import Finding

BIN_DIR = os.path.join("bin", "nuclei")
TEMPLATES_SEGUROS = "http/misconfiguration/http-missing-security-headers.yaml"
TEMPLATES_SEGUROS += ",http/exposures/,http/misconfiguration/"


def localizar() -> str | None:
    nombres = ["nuclei.exe", "nuclei"] if sys.platform == "win32" else ["nuclei"]
    for n in nombres:
        p = os.path.join(BIN_DIR, n)
        if os.path.exists(p):
            return p
    for n in nombres:
        for d in os.environ.get("PATH", "").split(os.pathsep):
            p = os.path.join(d, n)
            if os.path.exists(p):
                return p
    return None


def auditar_nuclei(
    objetivos: list[str] | None = None, timeout: int = 180
) -> list[Finding]:
    exe = localizar()
    if exe is None:
        return [
            Finding(
                id="nuclei-no-instalado",
                titulo="Nuclei no instalado (motor CVE opcional)",
                severidad="info",
                donde=BIN_DIR,
                evidencia="sin binario en bin/nuclei/ ni en PATH",
                remedio="Descargar de github.com/projectdiscovery/nuclei/"
                "releases y descomprimir en bin/nuclei/.",
                auditor="nuclei",
            )
        ]
    objetivos = objetivos or ["http://127.0.0.1:9200", "http://127.0.0.1:9997"]
    hallazgos = []
    for url in objetivos:
        try:
            r = subprocess.run(
                [
                    exe, "-u", url, "-t", TEMPLATES_SEGUROS,
                    "-severity", "medium,high,critical", "-silent", "-jsonl",
                    "-timeout", "10", "-rate-limit", "30",
                ],
                capture_output=True, text=True, timeout=timeout,
            )
        except (subprocess.TimeoutExpired, OSError) as e:
            hallazgos.append(
                Finding(
                    id="nuclei-fallo",
                    titulo=f"Nuclei falló contra {url}",
                    severidad="baja",
                    donde=url,
                    evidencia=str(e)[:120],
                    auditor="nuclei",
                )
            )
            continue
        for linea in r.stdout.splitlines():
            try:
                ev = json.loads(linea)
            except ValueError:
                continue
            info = ev.get("info", {})
            sev = str(info.get("severity", "info")).lower()
            if sev not in ("critica", "alta", "media", "baja", "info"):
                sev = {"critical": "critica", "high": "alta",
                       "medium": "media", "low": "baja"}.get(sev, "info")
            hallazgos.append(
                Finding(
                    id=f"nuclei-{info.get('name', 'x').replace(' ', '-')[:40]}",
                    titulo=f"[Nuclei] {info.get('name', 'hallazgo')}",
                    severidad=sev,
                    donde=ev.get("host", url),
                    evidencia=str(info.get("description", ""))[:200],
                    remedio="Ver plantilla: " + str(info.get("reference", ""))[:120],
                    auditor="nuclei",
                )
            )
    if not hallazgos:
        hallazgos.append(
            Finding(
                id="nuclei-limpio",
                titulo="Nuclei: sin hallazgos en plantillas seguras",
                severidad="info",
                donde=",".join(objetivos),
                auditor="nuclei",
            )
        )
    return hallazgos
