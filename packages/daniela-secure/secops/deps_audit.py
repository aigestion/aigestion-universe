"""Auditor de dependencias: inventario + OSV.dev (sin claves, stdlib).

Lee requirements*.txt y package.json/package-lock.json, y consulta la base
pública OSV.dev por vulnerabilidades conocidas. Sin red → hallazgo info.
"""
from __future__ import annotations

import json
import os
import re
import urllib.request

from secops.models import Finding

OSV_URL = "https://api.osv.dev/v1/querybatch"


def _reqs(raiz: str) -> dict[str, str]:
    deps: dict[str, str] = {}
    for base, _dirs, fich in os.walk(raiz):
        if ".git" in base or "node_modules" in base or "venv" in base:
            continue
        for f in fich:
            if f == "requirements.txt" or (f.startswith("requirements") and f.endswith(".txt")):
                try:
                    with open(os.path.join(base, f), encoding="utf-8", errors="ignore") as fh:
                        for linea in fh:
                            linea = linea.strip()
                            if not linea or linea.startswith(("#", "-")):
                                continue
                            m = re.match(r"([A-Za-z0-9_.-]+)\s*([=<>!~]+)\s*([\w.*+-]+)?", linea)
                            if m:
                                deps.setdefault(m.group(1).lower(), m.group(3) or "?")
                except OSError:
                    continue
    return deps


def _npm(raiz: str) -> dict[str, str]:
    deps: dict[str, str] = {}
    for base, _dirs, fich in os.walk(raiz):
        if ".git" in base or "node_modules" in base:
            continue
        if "package.json" in fich:
            try:
                with open(os.path.join(base, "package.json"), encoding="utf-8") as fh:
                    pj = json.load(fh)
                for sec in ("dependencies", "devDependencies"):
                    for k, v in (pj.get(sec) or {}).items():
                        deps.setdefault(k.lower(), str(v).lstrip("^~>=< "))
            except (OSError, ValueError):
                continue
    return deps


def _osv_consulta(paquetes: list[tuple[str, str, str]]) -> dict:
    """paquetes: [(nombre, version, ecosistema)]. Devuelve {nombre: [ids]}."""
    if not paquetes:
        return {}
    cuerpo = {"queries": []}
    for nombre, version, eco in paquetes:
        q: dict = {"package": {"name": nombre, "ecosystem": eco}}
        if version and version != "?":
            q["version"] = version
        cuerpo["queries"].append(q)
    req = urllib.request.Request(
        OSV_URL, data=json.dumps(cuerpo).encode(), headers={"Content-Type": "application/json"}
    )
    with urllib.request.urlopen(req, timeout=20) as r:
        data = json.load(r)
    out: dict[str, list[str]] = {}
    for (nombre, _v, _e), res in zip(paquetes, data.get("results", [])):
        vulns = [v.get("id", "?") for v in res.get("vulns", [])]
        if vulns:
            out[nombre] = vulns
    return out


def _version_instalada(nombre: str) -> str:
    """Versión real en este entorno (importlib.metadata), "" si no está."""
    try:
        from importlib import metadata
    except ImportError:
        return ""
    for candidato in (nombre, nombre.replace("-", "_"), nombre.replace("_", "-")):
        try:
            return metadata.version(candidato)
        except Exception:
            continue
    return ""


def auditar_deps(raiz: str, consultar=_osv_consulta) -> list[Finding]:
    hallazgos = []
    py = _reqs(raiz)
    js = _npm(raiz)
    hallazgos.append(
        Finding(
            id="deps-inventario",
            titulo=f"Inventario: {len(py)} paquetes pip + {len(js)} npm",
            severidad="info",
            donde=raiz,
            evidencia=f"pip={len(py)} npm={len(js)}",
            auditor="deps",
        )
    )
    if not py and not js:
        return hallazgos
    # Sin versión no hay veredicto: se resuelve la instalada en este entorno.
    # Lo no instalado y sin fijar se reporta como info (no como CVE).
    paquetes = []
    for n, v in list(py.items()):
        if v and v != "?":
            paquetes.append((n, v, "PyPI"))
            continue
        real = _version_instalada(n)
        if real:
            paquetes.append((n, real, "PyPI"))
        else:
            hallazgos.append(
                Finding(
                    id=f"deps-sin-fijar-{n}",
                    titulo=f"{n} sin versión fijada ni instalada: no evaluable",
                    severidad="info",
                    donde=n,
                    remedio="Fijar versión en requirements y auditar.",
                    auditor="deps",
                )
            )
    for n, v in js.items():
        vv = v.lstrip("^~>=< ").split()[0] if v else "?"
        if vv and vv != "?" and vv[0].isdigit():
            paquetes.append((n, vv, "npm"))
        else:
            hallazgos.append(
                Finding(
                    id=f"deps-sin-fijar-{n}",
                    titulo=f"{n} sin versión fijada: no evaluable",
                    severidad="info",
                    donde=n,
                    remedio="Fijar versión en package.json.",
                    auditor="deps",
                )
            )
    try:
        vulns = consultar(paquetes)
    except Exception as e:
        hallazgos.append(
            Finding(
                id="deps-osv-sin-red",
                titulo="OSV.dev no alcanzable: sin veredicto de CVEs",
                severidad="info",
                donde=OSV_URL,
                evidencia=str(e)[:120],
                remedio="Reejecutar con red o instalar pip-audit.",
                auditor="deps",
            )
        )
        return hallazgos
    for nombre, ids in vulns.items():
        hallazgos.append(
            Finding(
                id=f"deps-cve-{nombre}",
                titulo=f"{nombre} con {len(ids)} CVE(s) conocidos",
                severidad="alta",
                donde=nombre,
                evidencia=", ".join(ids[:5]),
                remedio="Actualizar a versión parcheada y fijar en lockfile.",
                auditor="deps",
            )
        )
    return hallazgos
