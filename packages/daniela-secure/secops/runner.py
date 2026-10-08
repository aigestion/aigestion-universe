"""Orquestador: ejecuta auditores, guarda informe y resume para Daniela."""
from __future__ import annotations

import datetime
import hashlib
import json
import os

from secops import counts, ordenar
from secops.auth_audit import auditar_auth, auditar_inyeccion
from secops.bind_headers import SERVICIOS, auditar_binds, auditar_cabeceras
from secops.deps_audit import auditar_deps
from secops.lan_audit import auditar_lan
from secops.models import Finding
from secops.net import netstat_listen
from secops.nuclei import auditar_nuclei
from secops.secrets_audit import auditar_secretos

REPORT_DIR = os.path.join("data", "secops", "reports")


def ejecutar(perfil: str = "rapido", raiz: str = ".") -> dict:
    """perfil 'rapido' (~15s, sin LAN) o 'completo' (con LAN + Nuclei)."""
    hallazgos: list[Finding] = []
    hallazgos += auditar_binds(netstat_listen())
    hallazgos += auditar_cabeceras()
    hallazgos += auditar_auth()
    hallazgos += auditar_inyeccion()
    hallazgos += auditar_secretos()
    hallazgos += auditar_deps(raiz)
    if perfil == "completo":
        hallazgos += auditar_lan()
        hallazgos += auditar_nuclei()
    hallazgos = ordenar(hallazgos)
    informe = {
        "fecha": datetime.datetime.now().isoformat(timespec="seconds"),
        "perfil": perfil,
        "totales": counts(hallazgos),
        "hallazgos": [
            {
                "id": h.id, "titulo": h.titulo, "severidad": h.severidad,
                "donde": h.donde, "evidencia": h.evidencia,
                "remedio": h.remedio, "auditor": h.auditor,
            }
            for h in hallazgos
        ],
    }
    return informe


def guardar(informe: dict, carpeta: str = REPORT_DIR) -> str:
    os.makedirs(carpeta, exist_ok=True)
    crudo = json.dumps(informe, ensure_ascii=False, sort_keys=True)
    digest = hashlib.sha256(crudo.encode()).hexdigest()[:8]
    nombre = f"audit-{informe['fecha'][:10]}-{informe['perfil']}-{digest}.json"
    ruta = os.path.join(carpeta, nombre)
    with open(ruta, "w", encoding="utf-8") as fh:
        fh.write(crudo)
    ultimo = os.path.join(carpeta, "latest.json")
    with open(ultimo, "w", encoding="utf-8") as fh:
        fh.write(crudo)
    return ruta


def resumen_para_daniela(informe: dict, max_items: int = 8) -> str:
    t = informe["totales"]
    lineas = [
        f"Auditoría {informe['perfil']} del {informe['fecha']}: "
        f"{t['critica']} críticas, {t['alta']} altas, {t['media']} medias, "
        f"{t['baja']} bajas."
    ]
    n = 0
    for h in informe["hallazgos"]:
        if h["severidad"] in ("info",):
            continue
        if n >= max_items:
            break
        lineas.append(f"- [{h['severidad']}] {h['titulo']} ({h['donde']}). {h['remedio']}")
        n += 1
    if not n:
        lineas.append("Sin hallazgos accionables. Todo limpio.")
    return "\n".join(lineas)


def servicios() -> list[tuple]:
    return SERVICIOS
