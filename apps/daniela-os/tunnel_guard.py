#!/usr/bin/env python3
"""
tunnel_guard.py — E-30 · Cerrar la puerta que dejamos abierta
=============================================================

El problema, con nombres y apellidos
------------------------------------
Dos auditorias seguidas (`AUDITORIA_TELEFONO.md` y su version profunda)
encontraron lo mismo:

    28646  cloudflared  cloudflared tunnel --protocol http2
                        --url http://localhost:8082

Ese tunel coge el puerto 8082 del movil —donde escucha el Termux API Gateway,
el modulo que puede leer tus SMS, sacar fotos, grabar el micro, mandar
notificaciones y ejecutar comandos de Termux— y lo publica en una URL publica
de internet. Con `trycloudflare.com` no hace falta ni cuenta: cualquiera que
adivine la URL entra.

Y la puerta tiene la cerradura puesta del lado de dentro, porque el token que
la protege no es un secreto: es la cadena literal `daniela-pixel-2026`,
escrita a mano en **22 ficheros** del repositorio. Esta en GitHub. No es una
clave: es una etiqueta.

Que hace este modulo
--------------------
1. **Escanea** si hay tuneles abiertos (local: cloudflared, ngrok, frpc, bore,
   chisel...; movil: por ADB) y a que puerto apuntan.
2. **Prueba el gateway** con y sin token. Si responde sin token, eso ya no es
   un riesgo: es una brecha confirmada.
3. **Audita** el repositorio buscando el token por defecto incrustado.
4. **Rota** el token: genera uno criptograficamente fuerte y lo escribe en el
   `.env` con los DOS nombres que usa el proyecto (`PIXEL_TOKEN` en el PC,
   `PIXEL_GATEWAY_TOKEN` en el movil), porque si solo cambias uno, se corta
   el puente y Daniela deja de ver al movil.
5. **Endurece** el codigo: sustituye el token incrustado por `os.getenv(...)`.
   Y aqui hay una trampa en la que casi caemos: si el default pasa a ser `""`
   y la comparacion es `if token != AUTH_TOKEN`, entonces una peticion SIN
   cabecera (`token == ""`) coincidiria con el default vacio y **entraria**.
   Por eso el parche anade ademas `if not AUTH_TOKEN or ...`: sin token
   configurado, el gateway rechaza todo (fail-closed).
6. **Comparacion en tiempo constante** (`hmac.compare_digest`) en vez de `!=`,
   para que no se pueda adivinar el token midiendo microsegundos.
7. **Plan de migracion a Tailscale**: la red privada que sustituye al tunel
   publico. Gratis hasta 100 dispositivos. Si Tailscale esta instalado, lee
   `tailscale status --json` y te dice la IP del Pixel.

La regla de seguridad de siempre
--------------------------------
Cero `os.system()`, cero `shell=True`. Todo va con `subprocess.run(lista)`.
La unica excepcion aparente es PowerShell para leer la linea de comandos de un
proceso, y va como lista de argumentos, sin shell, con `-NoProfile` y con el
nombre del proceso validado contra `[A-Za-z0-9_.-]+` antes de interpolarlo.

Las rutas que CAMBIAN algo (rotar, endurecer, matar tuneles) solo se sirven a
`127.0.0.1`. Y matar exige `{"confirmar": true}` y re-verificar en el momento
de matar que el binario sigue en la lista cerrada de tuneles conocidos.

Uso
---
    GET  /api/guard/status          diagnostico y nivel de riesgo
    GET  /api/guard/scan            escaneo de tuneles + prueba del gateway
    GET  /api/guard/audit           auditoria de secretos incrustados
    POST /api/guard/token/rotate    genera (y opcionalmente escribe) el token
    POST /api/guard/harden          parchea el codigo (dry-run si aplicar=false)
    GET  /api/guard/tailscale       estado de Tailscale + plan de migracion
    POST /api/guard/tunnel/stop     mata tuneles locales (pide confirmar)
    GET  /api/guard/report          informe markdown
"""

from __future__ import annotations

import csv
import io
import json
import os
import re
import secrets
import shutil
import subprocess
import threading
from datetime import datetime
from pathlib import Path
from typing import Any

from flask import Blueprint, jsonify, request

# --------------------------------------------------------------------------
#  Rutas y constantes
# --------------------------------------------------------------------------
ROOT = Path(__file__).resolve().parent
DATA_DIR = ROOT / "data" / "tunnel_guard"
STATE_FILE = DATA_DIR / "estado.json"
REPORT_FILE = DATA_DIR / "informe.md"
BACKUP_DIR = DATA_DIR / "backups"

TOKEN_DEBIL = "daniela-pixel-2026"
CLAVE_PC = "PIXEL_TOKEN"
CLAVE_MOVIL = "PIXEL_GATEWAY_TOKEN"
PUERTO_GATEWAY = 8082

# Lista CERRADA. Nunca se acepta un binario a matar que no este aqui.
BINARIOS_TUNEL = (
    "cloudflared",
    "ngrok",
    "frpc",
    "bore",
    "localtunnel",
    "serveo",
    "chisel",
    "inlets",
    "teleconsole",
)
# Subcadenas que delatan un tunel en la linea de comandos.
PISTAS_TUNEL = (
    "trycloudflare.com",
    "cloudflare.com",
    "ngrok",
    "--url http",
    "tunnel",
)

# Que preguntamos al puerto 8082 para saber que hay detras.
RUTAS_SONDA = ("/api/pixel/health", "/", "/api/skills/dispatch")

EXCLUIDOS = {
    ".venv",
    "venv",
    "node_modules",
    ".git",
    "__pycache__",
    "archive",
    ".mypy_cache",
    ".pytest_cache",
    ".ruff_cache",
}

NOMBRE_SEGURO = re.compile(r"^[A-Za-z0-9_.-]+$")


def _ahora() -> str:
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def _sello() -> str:
    return datetime.now().strftime("%Y%m%d_%H%M%S")


# --------------------------------------------------------------------------
#  Helpers de ejecucion segura
# --------------------------------------------------------------------------
def _run(args: list[str], timeout: int = 20) -> dict[str, Any]:
    """Ejecuta un comando SIN shell. Devuelve codigo, salida y error."""
    try:
        p = subprocess.run(
            args,
            capture_output=True,
            text=True,
            timeout=timeout,
            shell=False,
            errors="replace",
        )
        return {
            "codigo": p.returncode,
            "salida": p.stdout or "",
            "error": (p.stderr or "").strip()[:400],
        }
    except FileNotFoundError:
        return {"codigo": 127, "salida": "", "error": "no encontrado"}
    except subprocess.TimeoutExpired:
        return {"codigo": -9, "salida": "", "error": "timeout"}
    except Exception as e:  # noqa: BLE001
        return {"codigo": -1, "salida": "", "error": f"{type(e).__name__}"}


def _tiene(nombre: str) -> bool:
    return shutil.which(nombre) is not None


# --------------------------------------------------------------------------
#  1. Escaneo de tuneles
# --------------------------------------------------------------------------
def _procesos() -> list[dict[str, Any]]:
    """Lista de procesos del sistema. Sin shell, con degradacion elegante."""
    try:
        import psutil  # type: ignore

        out = []
        for p in psutil.process_iter(["pid", "name", "cmdline"]):
            try:
                info = p.info
                cmd = info.get("cmdline") or []
                out.append(
                    {
                        "pid": int(info["pid"]),
                        "nombre": str(info.get("name") or ""),
                        "cmd": " ".join(str(c) for c in cmd),
                    }
                )
            except Exception:  # noqa: BLE001
                continue
        return out
    except Exception:  # noqa: BLE001
        pass

    if os.name == "nt":
        return _procesos_windows()
    return _procesos_posix()


def _procesos_windows() -> list[dict[str, Any]]:
    r = _run(["tasklist", "/FO", "CSV", "/NH"], timeout=30)
    if r["codigo"] != 0:
        return []
    out: list[dict[str, Any]] = []
    for fila in csv.reader(io.StringIO(r["salida"])):
        if len(fila) < 2:
            continue
        nombre = fila[0].strip().strip('"')
        try:
            pid = int(fila[1].strip().strip('"'))
        except ValueError:
            continue
        out.append({"pid": pid, "nombre": nombre, "cmd": ""})
    return _rellenar_cmd_windows(out)


def _rellenar_cmd_windows(procs: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Lee la linea de comandos de los tuneles. Una sola llamada por nombre."""
    nombres = sorted({p["nombre"] for p in procs if _es_tunel(p["nombre"])})
    if not nombres:
        return procs
    ps = shutil.which("powershell") or shutil.which("pwsh") or "powershell.exe"
    mapa: dict[int, str] = {}
    for nombre in nombres:
        if not NOMBRE_SEGURO.match(nombre):
            continue
        # Ojo con las llaves: en f-string {{ y }} se escapan a { y }
        script = (
            "Get-CimInstance Win32_Process -Filter "
            f"\"Name='{nombre}'\" | ForEach-Object {{ "
            "$_.ProcessId.ToString() + '|' + $_.CommandLine }}"
        )
        r = _run([ps, "-NoProfile", "-NonInteractive", "-Command", script], timeout=25)
        if r["codigo"] != 0:
            continue
        for linea in r["salida"].splitlines():
            if "|" not in linea:
                continue
            pid_txt, _, cmd = linea.partition("|")
            try:
                mapa[int(pid_txt.strip())] = cmd.strip()
            except ValueError:
                continue
    for p in procs:
        p["cmd"] = mapa.get(int(p["pid"]), "")
    return procs


def _procesos_posix() -> list[dict[str, Any]]:
    r = _run(["ps", "-eo", "pid=,args="], timeout=30)
    if r["codigo"] != 0:
        return []
    out: list[dict[str, Any]] = []
    for linea in r["salida"].splitlines():
        partes = linea.strip().split(None, 1)
        if len(partes) != 2:
            continue
        try:
            pid = int(partes[0])
        except ValueError:
            continue
        cmd = partes[1]
        nombre = os.path.basename(cmd.split()[0]) if cmd.split() else ""
        out.append({"pid": pid, "nombre": nombre, "cmd": cmd})
    return out


def _es_tunel(nombre: str) -> bool:
    n = (nombre or "").lower()
    if n.endswith(".exe"):
        n = n[:-4]
    return any(n == b or n.startswith(b) for b in BINARIOS_TUNEL)


def _puerto_del_cmd(cmd: str) -> int | None:
    m = re.search(r"(?:localhost|127\.0\.0\.1|0\.0\.0\.0)[:/](\d{2,5})", cmd or "")
    if m:
        try:
            return int(m.group(1))
        except ValueError:
            return None
    return None


def _escanear_tuneles_locales() -> list[dict[str, Any]]:
    hallados: list[dict[str, Any]] = []
    for p in _procesos():
        nombre = p.get("nombre") or ""
        cmd = p.get("cmd") or ""
        if not _es_tunel(nombre):
            continue
        puerto = _puerto_del_cmd(cmd)
        hallados.append(
            {
                "pid": p.get("pid"),
                "binario": nombre,
                "puerto_local": puerto,
                "expone_gateway": puerto == PUERTO_GATEWAY,
                "cmd": (cmd[:220] + "...") if len(cmd) > 220 else cmd,
                "donde": "este_pc",
            }
        )
    return hallados


def _escanear_tuneles_adb() -> dict[str, Any]:
    """Mira los procesos del movil por ADB. Degrada si no hay ADB."""
    if not _tiene("adb"):
        return {"ok": False, "motivo": "adb no esta en el PATH", "tuneles": []}
    r = _run(["adb", "shell", "ps", "-A", "-o", "PID,ARGS"], timeout=25)
    if r["codigo"] != 0:
        return {"ok": False, "motivo": r["error"] or "sin dispositivo o adb fallo", "tuneles": []}
    tuneles = []
    for linea in r["salida"].splitlines():
        partes = linea.strip().split(None, 1)
        if len(partes) != 2:
            continue
        pid, args = partes
        nombre = os.path.basename(args.split()[0])
        if not _es_tunel(nombre):
            continue
        if not pid.isdigit():
            continue
        puerto = _puerto_del_cmd(args)
        tuneles.append(
            {
                "pid": int(pid),
                "binario": nombre,
                "puerto_local": puerto,
                "expone_gateway": puerto == PUERTO_GATEWAY,
                "cmd": args[:220],
                "donde": "movil",
            }
        )
    return {"ok": True, "motivo": "", "tuneles": tuneles}


# --------------------------------------------------------------------------
#  2. Prueba del gateway: responde sin token?
# --------------------------------------------------------------------------
def _ips_pixel() -> list[str]:
    """IPs candidatas del Pixel. Env PIXEL_IPS gana, si no, las conocidas."""
    raw = os.getenv("PIXEL_IPS", "")
    if raw.strip():
        return [s.strip() for s in raw.split(",") if s.strip()]
    try:
        from pixel_bridge_hub import KNOWN_IPS  # type: ignore

        return list(KNOWN_IPS)
    except Exception:  # noqa: BLE001
        return ["192.168.1.133", "192.168.1.170", "192.168.1.100"]


def _probar_gateway() -> dict[str, Any]:
    """Para cada IP: responde? que es? responde SIN token? (brecha confirmada)

    Importa distinguir QUE hay detras del puerto, porque las auditorias
    descubrieron que en el 8082 no escucha el Termux API Gateway sino un HUD
    de mentira (`python3 server.py`) que solo sirve `/` y
    `/api/skills/dispatch`. Exponer uno u otro son dos problemas distintos:
    el HUD falso no filtra datos, pero si acepta dispatch sin token, es una
    puerta de mando abierta.
    """
    try:
        import requests  # type: ignore
    except Exception:  # noqa: BLE001
        return {"ok": False, "motivo": "requests no disponible", "ips": []}

    token = os.getenv(CLAVE_PC, "")
    sin_proxy = {"http": None, "https": None}
    resultados = []

    for ip in _ips_pixel():
        base = f"http://{ip}:{PUERTO_GATEWAY}"
        item: dict[str, Any] = {
            "ip": ip,
            "vivo": False,
            "tipo": "nada",
            "responde_sin_token": False,
            "detalle": {},
        }

        vivo = False
        for ruta in RUTAS_SONDA:
            try:
                r = requests.get(
                    f"{base}{ruta}", headers={"X-Pixel-Token": token}, timeout=4, proxies=sin_proxy
                )
                item["detalle"][f"con_token {ruta}"] = r.status_code
                vivo = True
            except Exception:  # noqa: BLE001
                item["detalle"][f"con_token {ruta}"] = "sin respuesta"
        if not vivo:
            resultados.append(item)
            continue
        item["vivo"] = True

        for ruta in RUTAS_SONDA:
            codigo = None
            try:
                r2 = requests.get(f"{base}{ruta}", timeout=4, proxies=sin_proxy)
                codigo = r2.status_code
            except Exception:  # noqa: BLE001
                codigo = None
            item["detalle"][f"sin_token {ruta}"] = codigo or "sin respuesta"
            # 200 = abierto; 405 = la ruta existe (es POST) pero no esta
            # protegida frente a GET anonimo, asi que tambien cuenta.
            if codigo in (200, 405):
                item["responde_sin_token"] = True

        health = item["detalle"].get("sin_token /api/pixel/health")
        if isinstance(health, int) and health in (200, 401, 403):
            item["tipo"] = "gateway_real"
        elif item["responde_sin_token"]:
            item["tipo"] = "servidor_sin_auth"
        else:
            item["tipo"] = "desconocido"
        resultados.append(item)
    return {"ok": True, "motivo": "", "ips": resultados}


# --------------------------------------------------------------------------
#  3. Auditoria de secretos incrustados
# --------------------------------------------------------------------------
def _ficheros_python() -> list[Path]:
    out = []
    for p in ROOT.rglob("*.py"):
        if any(parte in EXCLUIDOS for parte in p.parts):
            continue
        out.append(p)
    return sorted(out)


def _auditar() -> list[dict[str, Any]]:
    hallados = []
    for p in _ficheros_python():
        try:
            lineas = p.read_text(encoding="utf-8", errors="replace").splitlines()
        except Exception:  # noqa: BLE001
            continue
        for i, ln in enumerate(lineas, 1):
            if TOKEN_DEBIL in ln:
                tipo = "token_por_defecto"
                if "AUTH_TOKEN" in ln:
                    tipo = "auth_token_fijo"
                elif "os.getenv" in ln or "os.environ" in ln:
                    tipo = "default_en_getenv"
                hallados.append(
                    {
                        "fichero": str(p.relative_to(ROOT)).replace("\\", "/"),
                        "linea": i,
                        "tipo": tipo,
                        "texto": ln.strip()[:160],
                    }
                )
    return hallados


# --------------------------------------------------------------------------
#  4. Parches de endurecimiento
# --------------------------------------------------------------------------
# Cada regla: (id, descripcion, patron, reemplazo)
# Se aplican EN ORDEN; la ultima es la red de seguridad.
PARCHES: list[tuple[str, str, re.Pattern[str], str]] = [
    (
        "auth_token_fijo",
        "AUTH_TOKEN deja de ser un literal y pasa a leer PIXEL_TOKEN del .env",
        re.compile(r'^AUTH_TOKEN\s*=\s*os.getenv("PIXEL_TOKEN", "")', re.M),
        'AUTH_TOKEN = os.getenv("PIXEL_TOKEN", "")',
    ),
    (
        "default_gateway",
        "El gateway lee PIXEL_GATEWAY_TOKEN; sin el, queda vacio y cierra",
        re.compile(r'os\.environ\.get\("PIXEL_GATEWAY_TOKEN",\s*os.getenv("PIXEL_TOKEN", "")\)'),
        'os.environ.get("PIXEL_GATEWAY_TOKEN", "")',
    ),
    (
        "default_getenv",
        "Quita el default del os.getenv del PC",
        re.compile(r'os\.getenv\("PIXEL_TOKEN",\s*os.getenv("PIXEL_TOKEN", "")\)'),
        'os.getenv("PIXEL_TOKEN", "")',
    ),
    (
        "comparacion_constante",
        "Compara con hmac.compare_digest y falla cerrado si no hay token (si no, "
        "una peticion sin cabecera coincide con el default vacio y ENTRA)",
        re.compile(r"^(\s*)if token != AUTH_TOKEN:", re.M),
        r"\1if not AUTH_TOKEN or not hmac.compare_digest(token, AUTH_TOKEN):",
    ),
    (
        "resto",
        "Red de seguridad: cualquier literal suelto que quede",
        re.compile(r'os.getenv("PIXEL_TOKEN", "")'),
        'os.getenv("PIXEL_TOKEN", "")',
    ),
]


def _necesita(texto: str, modulo: str) -> bool:
    """True si el texto usa `modulo.` pero no lo importa."""
    if re.search(rf"^\s*import\s+{modulo}\b", texto, re.M):
        return False
    if re.search(rf"^\s*from\s+{modulo}\b", texto, re.M):
        return False
    if re.search(rf"^\s*import\s+.*\b{modulo}\b", texto, re.M):
        return False
    return re.search(rf"\b{modulo}\.", texto) is not None


def _anadir_import(texto: str, modulo: str) -> str:
    """Inserta `import modulo` tras el ultimo import de la cabecera."""
    lineas = texto.splitlines()
    ultimo = 0
    for i, ln in enumerate(lineas):
        if re.match(r"^\s*(import|from)\s+\S", ln):
            ultimo = i
    lineas.insert(ultimo + 1, f"import {modulo}")
    return "\n".join(lineas) + ("\n" if texto.endswith("\n") else "")


def _planificar_parches() -> dict[str, Any]:
    """Dry-run: que ficheros cambiarian y cuantas lineas."""
    plan: list[dict[str, Any]] = []
    for p in _ficheros_python():
        try:
            original = p.read_text(encoding="utf-8", errors="replace")
        except Exception:  # noqa: BLE001
            continue
        texto = original
        aplicadas = []
        for pid, _desc, patron, reempl in PARCHES:
            texto2, n = patron.subn(reempl, texto)
            if n:
                aplicadas.append({"regla": pid, "cambios": n})
                texto = texto2
        if not aplicadas:
            continue
        extras = []
        for mod in ("os", "hmac"):
            if _necesita(texto, mod):
                extras.append(mod)
        plan.append(
            {
                "fichero": str(p.relative_to(ROOT)).replace("\\", "/"),
                "lineas_originales": original.count("\n") + 1,
                "reglas": aplicadas,
                "imports_a_anadir": extras,
            }
        )
    return {"total_ficheros": len(plan), "ficheros": plan}


def _aplicar_parches() -> dict[str, Any]:
    """Aplica los parches con backup. Devuelve lo que hizo y verifica."""
    BACKUP_DIR.mkdir(parents=True, exist_ok=True)
    aplicados: list[dict[str, Any]] = []
    errores: list[dict[str, str]] = []

    for p in _ficheros_python():
        try:
            original = p.read_text(encoding="utf-8", errors="replace")
        except Exception as e:  # noqa: BLE001
            errores.append({"fichero": str(p), "error": str(e)[:120]})
            continue
        texto = original
        reglas = []
        for pid, _desc, patron, reempl in PARCHES:
            texto, n = patron.subn(reempl, texto)
            if n:
                reglas.append({"regla": pid, "cambios": n})
        if not reglas:
            continue

        for mod in ("hmac", "os"):
            if _necesita(texto, mod):
                texto = _anadir_import(texto, mod)
                reglas.append({"regla": f"import_{mod}", "cambios": 1})

        rel = str(p.relative_to(ROOT)).replace("\\", "/")
        respaldo = BACKUP_DIR / f"{rel.replace('/', '__')}.{_sello()}.bak"
        try:
            respaldo.write_text(original, encoding="utf-8")
            p.write_text(texto, encoding="utf-8")
        except Exception as e:  # noqa: BLE001
            errores.append({"fichero": rel, "error": str(e)[:120]})
            continue
        aplicados.append(
            {"fichero": rel, "reglas": reglas, "respaldo": str(respaldo.relative_to(ROOT))}
        )

    # Verificacion: tiene que quedar 0 literales
    restantes = _auditar()
    return {
        "aplicados": aplicados,
        "errores": errores,
        "literales_restantes": len(restantes),
        "respaldos_en": str(BACKUP_DIR.relative_to(ROOT)).replace("\\", "/"),
    }


# --------------------------------------------------------------------------
#  5. Rotacion del token
# --------------------------------------------------------------------------
def _leer_env_valor(clave: str) -> str:
    env = ROOT / ".env"
    if not env.exists():
        return ""
    try:
        lineas = env.read_text(encoding="utf-8", errors="replace").splitlines()
    except Exception:  # noqa: BLE001
        return ""
    valor = ""
    for ln in lineas:
        m = re.match(rf"^\s*(?:export\s+)?{re.escape(clave)}\s*=\s*(.*)$", ln)
        if m:
            valor = m.group(1).strip().strip('"').strip("'")
    return valor


def _escribir_env(par: dict[str, str]) -> dict[str, Any]:
    """Escribe claves en .env: borra las apariciones viejas y anade al final.

    Borra TODAS y anade una sola al final porque dotenv da prioridad a la
    ultima aparicion: dejar la vieja arriba y la nueva abajo funcionaria, pero
    dejar la nueva arriba y la vieja abajo nos dejaria con la clave caducada.
    """
    env = ROOT / ".env"
    if not env.exists():
        return {"ok": False, "error": "no existe .env"}
    try:
        lineas = env.read_text(encoding="utf-8", errors="replace").splitlines()
    except Exception as e:  # noqa: BLE001
        return {"ok": False, "error": str(e)[:150]}

    claves = set(par)
    limpias = [
        ln
        for ln in lineas
        if not any(re.match(rf"^\s*(?:export\s+)?{re.escape(c)}\s*=", ln) for c in claves)
    ]

    BACKUP_DIR.mkdir(parents=True, exist_ok=True)
    respaldo = BACKUP_DIR / f".env.{_sello()}.bak"
    try:
        respaldo.write_text("\n".join(lineas) + "\n", encoding="utf-8")
    except Exception as e:  # noqa: BLE001
        return {"ok": False, "error": f"backup: {str(e)[:120]}"}

    nuevas = list(limpias)
    if nuevas and nuevas[-1].strip():
        nuevas.append("")
    nuevas.append(f"# ── E-30 tunnel_guard · {_ahora()} ──")
    for k, v in par.items():
        nuevas.append(f"{k}={v}")
    try:
        env.write_text("\n".join(nuevas) + "\n", encoding="utf-8")
    except Exception as e:  # noqa: BLE001
        return {"ok": False, "error": str(e)[:150]}
    return {"ok": True, "respaldo": str(respaldo.relative_to(ROOT))}


def _rotar_token(aplicar: bool) -> dict[str, Any]:
    nuevo = secrets.token_urlsafe(32)
    actual = _leer_env_valor(CLAVE_PC)
    info: dict[str, Any] = {
        "token_nuevo": nuevo,
        "longitud": len(nuevo),
        "claves": [CLAVE_PC, CLAVE_MOVIL],
        "token_anterior": _enmascarar(actual),
        "aplicado": False,
    }
    if not aplicar:
        info["nota"] = "dry-run: el token NO se ha escrito. Manda aplicar=true."
        return info

    r = _escribir_env({CLAVE_PC: nuevo, CLAVE_MOVIL: nuevo})
    if not r.get("ok"):
        info["error"] = r.get("error", "")
        return info
    info["aplicado"] = True
    info["respaldo"] = r.get("respaldo")
    # Recargar en el proceso actual para no tener que reiniciar DanielaOS
    os.environ[CLAVE_PC] = nuevo
    os.environ[CLAVE_MOVIL] = nuevo
    info["comando_termux"] = (
        f"echo 'export PIXEL_GATEWAY_TOKEN={nuevo}' >> ~/.bashrc && source ~/.bashrc"
    )
    info["siguiente_paso"] = (
        "Pega ese export en Termux y reinicia el gateway (el gateway lee la "
        "variable al arrancar). Hasta entonces el movil rechazara al PC."
    )
    return info


def _enmascarar(v: str) -> str:
    if not v:
        return "(vacio)"
    if len(v) <= 8:
        return v[0] + "*" * (len(v) - 1)
    return f"{v[:4]}{'*' * 6}{v[-3:]} ({len(v)})"


# --------------------------------------------------------------------------
#  6. Tailscale
# --------------------------------------------------------------------------
def _estado_tailscale() -> dict[str, Any]:
    if not _tiene("tailscale"):
        return {"instalado": False}
    r = _run(["tailscale", "status", "--json"], timeout=25)
    if r["codigo"] != 0:
        return {
            "instalado": True,
            "conectado": False,
            "error": r["error"] or "tailscale no responde",
        }
    try:
        d = json.loads(r["salida"])
    except Exception:  # noqa: BLE001
        return {"instalado": True, "conectado": False, "error": "json invalido"}
    pares = []
    for pid, info in (d.get("Peer") or {}).items():
        ips = list(info.get("TailscaleIPs") or [])
        pares.append(
            {
                "id": str(pid)[:12],
                "nombre": info.get("HostName", "?"),
                "so": info.get("OS", "?"),
                "ips": ips,
                "online": bool(info.get("Online")),
            }
        )
    propio = d.get("Self") or {}
    return {
        "instalado": True,
        "conectado": True,
        "mi_ip": (propio.get("TailscaleIPs") or [None])[0],
        "pares": pares,
    }


PLAN_TAILSCALE = [
    (
        "1",
        "Instala Tailscale en el Pixel",
        "Play Store -> Tailscale -> abrir -> Log in (cuenta de Google vale).",
    ),
    (
        "2",
        "Instala Tailscale en el PC",
        "winget install tailscale.tailscale   (o descargalo de tailscale.com)",
    ),
    ("3", "Arranca en el PC", "tailscale up"),
    (
        "4",
        "Anota la IP del movil",
        "tailscale status        # busca el Pixel; su IP empieza por 100.",
    ),
    (
        "5",
        "Dile al proyecto donde esta",
        "PIXEL_IPS=100.x.y.z   en el .env  (o en la variable de entorno)",
    ),
    (
        "6",
        "Apaga el tunel publico",
        "En Termux: pkill cloudflared   y quita el servicio: "
        "sv stop cloudflared  (o borra ~/.termux/boot/ si lo arranca ahi)",
    ),
    ("7", "Comprueba que se acabo", "GET /api/guard/scan  ->  tuneles: 0"),
]


# --------------------------------------------------------------------------
#  7. Nivel de riesgo
# --------------------------------------------------------------------------
def _riesgo(
    tuneles: list[dict[str, Any]], gateway: dict[str, Any], literales: int
) -> dict[str, Any]:
    criticos: list[str] = []
    altos: list[str] = []
    medios: list[str] = []

    for t in tuneles:
        if t.get("expone_gateway"):
            criticos.append(
                f"{t['binario']} (pid {t['pid']}, {t['donde']}) publica el "
                f"puerto {PUERTO_GATEWAY} del gateway en internet"
            )
        else:
            altos.append(
                f"{t['binario']} (pid {t['pid']}, {t['donde']}) esta abierto "
                f"hacia el puerto {t.get('puerto_local')}"
            )

    for ip in gateway.get("ips", []):
        if not ip.get("responde_sin_token"):
            continue
        tipo = ip.get("tipo", "?")
        criticos.append(
            f"{ip['ip']}:8082 responde SIN credenciales "
            f"(tipo={tipo}): cualquiera que alcance ese puerto manda "
            "peticiones al movil; con el tunel abierto, 'cualquiera' es "
            "internet entero"
        )
    if literales:
        altos.append(f"{literales} literales del token por defecto en el codigo")
    if not os.getenv(CLAVE_PC):
        medios.append(f"{CLAVE_PC} no esta en el entorno: los modulos caen al default")

    nivel = "CRITICO" if criticos else ("ALTO" if altos else ("MEDIO" if medios else "OK"))
    return {"nivel": nivel, "criticos": criticos, "altos": altos, "medios": medios}


# --------------------------------------------------------------------------
#  8. Estado en disco
# --------------------------------------------------------------------------
class Guard:
    """Mantiene el ultimo diagnostico para no re-escanear en cada ping."""

    def __init__(self) -> None:
        self._lock = threading.RLock()
        self.estado: dict[str, Any] = {"escaneos": 0, "ultimo": None, "riesgo": None}
        DATA_DIR.mkdir(parents=True, exist_ok=True)
        self._cargar()

    def _cargar(self) -> None:
        if STATE_FILE.exists():
            try:
                self.estado.update(json.loads(STATE_FILE.read_text(encoding="utf-8")))
            except Exception:  # noqa: BLE001
                pass

    def guardar(self) -> None:
        with self._lock:
            try:
                STATE_FILE.write_text(
                    json.dumps(self.estado, ensure_ascii=False, indent=2), encoding="utf-8"
                )
            except Exception:  # noqa: BLE001
                pass

    def escanear(self) -> dict[str, Any]:
        locales = _escanear_tuneles_locales()
        adb = _escanear_tuneles_adb()
        tuneles = locales + adb.get("tuneles", [])
        gateway = _probar_gateway()
        literales = _auditar()
        riesgo = _riesgo(tuneles, gateway, len(literales))

        with self._lock:
            self.estado["escaneos"] = int(self.estado.get("escaneos", 0)) + 1
            self.estado["ultimo"] = _ahora()
            self.estado["tuneles"] = tuneles
            self.estado["gateway"] = gateway
            self.estado["literales"] = len(literales)
            self.estado["riesgo"] = riesgo
            self.estado["tailscale"] = _estado_tailscale()
            self.guardar()
        return {
            "tuneles": tuneles,
            "gateway": gateway,
            "literales": len(literales),
            "riesgo": riesgo,
            "adb": {"ok": adb.get("ok"), "motivo": adb.get("motivo", "")},
            "cuando": _ahora(),
        }


_instancia: Guard | None = None
_lock_instancia = threading.RLock()


def get_instance() -> Guard:
    global _instancia
    with _lock_instancia:
        if _instancia is None:
            _instancia = Guard()
        return _instancia


# --------------------------------------------------------------------------
#  Informe
# --------------------------------------------------------------------------
def _informe_md() -> str:
    g = get_instance()
    e = g.estado
    riesgo = e.get("riesgo") or {}
    lineas = [
        "# Informe de exposicion — tunnel_guard (E-30)",
        "",
        f"Generado: {e.get('ultimo') or _ahora()}  ",
        f"Escaneos: {e.get('escaneos', 0)}  ",
        f"**Riesgo: {riesgo.get('nivel', '?')}**",
        "",
    ]
    if riesgo.get("criticos"):
        lineas += ["## Critico", ""]
        lineas += [f"- {c}" for c in riesgo["criticos"]] + [""]
    if riesgo.get("altos"):
        lineas += ["## Alto", ""] + [f"- {a}" for a in riesgo["altos"]] + [""]
    if riesgo.get("medios"):
        lineas += ["## Medio", ""] + [f"- {m}" for m in riesgo["medios"]] + [""]

    lineas += ["## Tuneles", ""]
    tuneles = e.get("tuneles") or []
    if not tuneles:
        lineas += ["Ninguno detectado.", ""]
    else:
        lineas += ["| Donde | Binario | PID | Puerto | Expone gateway |", "|---|---|---|---|---|"]
        for t in tuneles:
            lineas.append(
                f"| {t.get('donde')} | {t.get('binario')} | {t.get('pid')} | "
                f"{t.get('puerto_local')} | "
                f"{'SI' if t.get('expone_gateway') else 'no'} |"
            )
        lineas.append("")

    lineas += ["## Plan de migracion a Tailscale", ""]
    for n, titulo, cmd in PLAN_TAILSCALE:
        lineas += [f"**{n}. {titulo}**", "", "```", cmd, "```", ""]

    ts = e.get("tailscale") or {}
    lineas += ["## Estado de Tailscale", ""]
    if not ts.get("instalado"):
        lineas += ["Tailscale no esta instalado en este PC.", ""]
    elif not ts.get("conectado"):
        lineas += [f"Instalado pero sin conectar: {ts.get('error', '')}", ""]
    else:
        lineas += [f"Mi IP: `{ts.get('mi_ip')}`", ""]
        for p in ts.get("pares", []):
            lineas.append(
                f"- `{p['nombre']}` ({p['so']}) "
                f"{'online' if p['online'] else 'offline'} "
                f"{', '.join(p['ips'])}"
            )
        lineas.append("")
    return "\n".join(lineas)


# --------------------------------------------------------------------------
#  Rutas Flask
# --------------------------------------------------------------------------
guard_bp = Blueprint("tunnel_guard", __name__)


def _solo_local() -> tuple[Any, int] | None:
    ip = request.remote_addr or ""
    if ip in ("127.0.0.1", "::1", "::ffff:127.0.0.1"):
        return None
    return jsonify({"ok": False, "error": "solo desde 127.0.0.1 (esta ruta modifica cosas)"}), 403


def _resumen() -> dict[str, Any]:
    g = get_instance()
    e = g.estado
    riesgo = e.get("riesgo") or {}
    return {
        "nivel": riesgo.get("nivel", "DESCONOCIDO"),
        "ultimo_escaneo": e.get("ultimo"),
        "escaneos": e.get("escaneos", 0),
        "tuneles": len(e.get("tuneles") or []),
        "tuneles_criticos": [t for t in (e.get("tuneles") or []) if t.get("expone_gateway")],
        "literales_token": e.get("literales"),
        "token_configurado": bool(os.getenv(CLAVE_PC)),
        "token_en_env": _enmascarar(_leer_env_valor(CLAVE_PC)),
        "criticos": riesgo.get("criticos", []),
        "altos": riesgo.get("altos", []),
        "medios": riesgo.get("medios", []),
        "tailscale": (e.get("tailscale") or {}).get("instalado", False),
    }


@guard_bp.route("/api/guard/status", methods=["GET"])
def guard_status():
    """Diagnostico rapido desde el ultimo escaneo en disco."""
    if not get_instance().estado.get("ultimo"):
        get_instance().escanear()
    return jsonify(
        {
            "ok": True,
            "resumen": _resumen(),
            "rutas": [
                "/api/guard/scan",
                "/api/guard/audit",
                "/api/guard/token/rotate",
                "/api/guard/harden",
                "/api/guard/tailscale",
                "/api/guard/tunnel/stop",
                "/api/guard/report",
            ],
        }
    )


@guard_bp.route("/api/guard/scan", methods=["GET"])
def guard_scan():
    """Escaneo real: procesos, ADB y prueba del gateway con/sin token."""
    return jsonify({"ok": True, **get_instance().escanear()})


@guard_bp.route("/api/guard/audit", methods=["GET"])
def guard_audit():
    """Auditoria de secretos incrustados + plan de parches en seco."""
    hallados = _auditar()
    plan = _planificar_parches()
    return jsonify(
        {
            "ok": True,
            "literales": len(hallados),
            "detalle": hallados,
            "plan_parches": plan,
            "ficheros_python": len(_ficheros_python()),
        }
    )


@guard_bp.route("/api/guard/token/rotate", methods=["POST"])
def guard_rotate():
    """Genera un token fuerte. Con aplicar=true lo escribe en el .env."""
    denegar = _solo_local()
    if denegar:
        return denegar
    cuerpo = request.get_json(silent=True) or {}
    return jsonify({"ok": True, **_rotar_token(bool(cuerpo.get("aplicar", False)))})


@guard_bp.route("/api/guard/harden", methods=["POST"])
def guard_harden():
    """Parchea el codigo. Sin aplicar=true solo muestra el plan."""
    denegar = _solo_local()
    if denegar:
        return denegar
    cuerpo = request.get_json(silent=True) or {}
    if not cuerpo.get("aplicar", False):
        return jsonify(
            {
                "ok": True,
                "aplicado": False,
                "plan": _planificar_parches(),
                "nota": "manda aplicar=true para ejecutarlo",
            }
        )
    r = _aplicar_parches()
    get_instance().escanear()
    return jsonify({"ok": True, "aplicado": True, **r})


@guard_bp.route("/api/guard/tailscale", methods=["GET"])
def guard_tailscale():
    """Estado de Tailscale y plan de migracion paso a paso."""
    return jsonify(
        {
            "ok": True,
            "estado": _estado_tailscale(),
            "plan": [{"paso": n, "titulo": t, "comando": c} for n, t, c in PLAN_TAILSCALE],
        }
    )


@guard_bp.route("/api/guard/tunnel/stop", methods=["POST"])
def guard_stop():
    """Mata tuneles locales. Exige confirmar=true y pids del escaneo."""
    denegar = _solo_local()
    if denegar:
        return denegar
    cuerpo = request.get_json(silent=True) or {}
    if not cuerpo.get("confirmar", False):
        return jsonify(
            {
                "ok": False,
                "error": "esta ruta mata procesos; manda confirmar=true y la lista de pids",
                "pids_disponibles": [
                    {"pid": t["pid"], "binario": t["binario"]}
                    for t in (get_instance().estado.get("tuneles") or [])
                    if t.get("donde") == "este_pc"
                ],
            }
        ), 400

    pids = cuerpo.get("pids") or []
    # Re-verificamos AHORA: el pid pudo cambiar de dueño desde el escaneo.
    vivos = {int(p["pid"]): p["nombre"] for p in _procesos() if _es_tunel(p.get("nombre") or "")}
    muertos, rechazados = [], []
    for raw in pids:
        try:
            pid = int(raw)
        except (TypeError, ValueError):
            rechazados.append({"pid": raw, "motivo": "no es un pid"})
            continue
        nombre = vivos.get(pid)
        if not nombre:
            rechazados.append({"pid": pid, "motivo": "no es un tunel conocido o ya murio"})
            continue
        try:
            if os.name == "nt":
                _run(["taskkill", "/F", "/T", "/PID", str(pid)], timeout=20)
            else:
                import signal

                os.kill(pid, signal.SIGTERM)
        except Exception as e:  # noqa: BLE001
            rechazados.append({"pid": pid, "motivo": str(e)[:80]})
            continue
        muertos.append({"pid": pid, "binario": nombre})

    get_instance().escanear()
    return jsonify(
        {
            "ok": True,
            "muertos": muertos,
            "rechazados": rechazados,
            "nota": "si el tunel lo arranca un servicio (sv/runsvdir), "
            "volvera a subir: hay que quitarlo del arranque",
        }
    )


@guard_bp.route("/api/guard/report", methods=["GET"])
def guard_report():
    """Informe markdown. ?guardar=1 lo escribe en data/tunnel_guard/."""
    md = _informe_md()
    if request.args.get("guardar") == "1":
        try:
            REPORT_FILE.write_text(md, encoding="utf-8")
        except Exception as e:  # noqa: BLE001
            return jsonify({"ok": False, "error": str(e)[:150]}), 500
        return jsonify(
            {
                "ok": True,
                "guardado_en": str(REPORT_FILE.relative_to(ROOT)).replace("\\", "/"),
                "bytes": len(md),
            }
        )
    return jsonify({"ok": True, "markdown": md})


def register_guard_routes(app) -> int:
    """Registra las rutas del modulo. Devuelve el numero de rutas."""
    app.register_blueprint(guard_bp)

    # Escaneo inicial en segundo plano para no frenar el arranque
    def _arranque() -> None:
        try:
            get_instance().escanear()
        except Exception:  # noqa: BLE001
            pass

    threading.Thread(target=_arranque, daemon=True).start()
    print(
        "[Tunnel Guard] Routes registered: /api/guard/* "
        "(status, scan, audit, token/rotate, harden, tailscale, "
        "tunnel/stop, report)"
    )
    return 8


# --------------------------------------------------------------------------
#  Demo
# --------------------------------------------------------------------------
def _demo() -> None:
    print("=" * 66)
    print("E-30 · tunnel_guard — demo")
    print("=" * 66)
    g = get_instance()
    r = g.escanear()

    print("\n-- Tuneles --")
    if not r["tuneles"]:
        print("  ninguno detectado en este PC")
    for t in r["tuneles"]:
        marca = "!! EXPONE EL GATEWAY" if t["expone_gateway"] else ""
        print(
            f"  [{t['donde']}] {t['binario']} pid={t['pid']} puerto={t.get('puerto_local')} {marca}"
        )
    print(f"  adb: ok={r['adb']['ok']} {r['adb']['motivo']}")

    print("\n-- Gateway del Pixel --")
    for ip in r["gateway"].get("ips", []):
        if not ip["vivo"]:
            print(f"  {ip['ip']}: no responde")
            continue
        brecha = "  <<< RESPONDE SIN TOKEN (brecha)" if ip["responde_sin_token"] else ""
        print(f"  {ip['ip']}: vivo | tipo={ip.get('tipo')}{brecha}")
        for k, v in ip.get("detalle", {}).items():
            print(f"      {k}: {v}")

    print(f"\n-- Literales del token por defecto: {r['literales']} --")

    print("\n-- Tailscale --")
    ts = g.estado.get("tailscale") or {}
    print(f"  instalado: {ts.get('instalado')}")

    riesgo = r["riesgo"]
    print(f"\n== RIESGO: {riesgo['nivel']} ==")
    for c in riesgo["criticos"]:
        print(f"  [CRITICO] {c}")
    for a in riesgo["altos"]:
        print(f"  [ALTO]    {a}")
    for m in riesgo["medios"]:
        print(f"  [MEDIO]   {m}")

    print("\n-- Plan de parches (seco) --")
    plan = _planificar_parches()
    print(f"  ficheros que cambiarian: {plan['total_ficheros']}")
    for f in plan["ficheros"][:6]:
        reglas = ", ".join(x["regla"] for x in f["reglas"])
        print(f"    {f['fichero']}: {reglas}")
    if plan["total_ficheros"] > 6:
        print(f"    ... y {plan['total_ficheros'] - 6} mas")

    print("\n" + "=" * 66)


if __name__ == "__main__":
    _demo()
