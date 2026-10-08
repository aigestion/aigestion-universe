#!/usr/bin/env python3
"""
gev.command_center — Backend REAL del Command Center
===================================================================
Conecta las 5 herramientas del modal holografico de la Sede con modulos
que YA existen en el repo. Nada de datos inventados: si un subsistema no
esta disponible, se dice explicitamente en el campo `conectado: false`.

Herramientas:
  1. Astra Document Sniper  -> MemoryVault (RAG) real
  2. Voice Briefing Agent   -> PiperEngine + briefing compuesto del estado real
  3. Inbox Zero Drafter     -> EmailZeroInbox (triaje real, sin correo conectado)
  4. Life Telemetry HUD     -> core.health_checks + psutil
  5. Command & Control      -> url_map real + fases fallidas

Rutas (se registran con `registrar_command_center(app)`):
  GET  /api/cc/astra        -> estado del RAG
  GET  /api/cc/voz          -> disponibilidad TTS + briefing
  POST /api/cc/voz/hablar   -> sintetiza a WAV (si Piper esta disponible)
  GET  /api/cc/inbox        -> estado del triaje de correo
  POST /api/cc/inbox/triaje -> clasifica una lista de correos (dry-run)
  GET  /api/cc/telemetria   -> disco, memoria, CPU, git
  GET  /api/cc/consola      -> indice real de rutas y agentes
"""

from __future__ import annotations

import os
import platform
import shutil
import sys
import time
from pathlib import Path
from typing import Any

_DIR = Path(__file__).resolve().parent


def _raiz_repo() -> Path:
    """Raíz por marcador (mismo criterio que `billing.py` y `osint.py`).

    Con `_DIR.parent.parent` la raíz apuntaba al padre del proyecto desde que
    `gev/` se mudó de `<repo>/aig/gev/` a `<repo>/gev/`.
    """
    for c in (_DIR, *_DIR.parents):
        if (c / ".git").exists() or (c / "tests" / "conftest.py").exists():
            return c
    return _DIR.parent


_RAIZ = _raiz_repo()
for _p in (str(_RAIZ), str(_RAIZ / "aig")):
    if _p not in sys.path:
        sys.path.insert(0, _p)


# ── Utilidades ───────────────────────────────────────────────


def _sin_conectar(motivo: str) -> dict[str, Any]:
    """Respuesta honesta: la herramienta existe, el backend no esta listo."""
    return {"conectado": False, "motivo": motivo, "ts": time.time()}


def _ok(**campos: Any) -> dict[str, Any]:
    return {"conectado": True, "ts": time.time(), **campos}


# ── 1. Astra Document Sniper (RAG) ───────────────────────────


def estado_astra() -> dict[str, Any]:
    """Documentos indexados en la memoria semantica."""
    try:
        from agents.memory.memory_vault import MemoryVault
    except Exception as e:  # noqa: BLE001
        return _sin_conectar(f"MemoryVault no importable: {e}")

    try:
        v = MemoryVault()
        st = v.stats()
    except Exception as e:  # noqa: BLE001
        return _sin_conectar(f"MemoryVault no operativo: {e}")

    docs = int(st.get("docs") or 0)
    return _ok(
        herramienta="Astra Document Sniper",
        docs=docs,
        enlaces=st.get("links", 0),
        fuentes=st.get("fuentes", {}),
        ultimo=st.get("ultimo"),
        db=st.get("db", ""),
        indice_vacio=(docs == 0),
        nota=(
            "Indice vacio: la memoria semantica no tiene documentos."
            if docs == 0
            else f"{docs} documentos indexados."
        ),
    )


# ── 2. Voice Briefing Agent (TTS + briefing) ─────────────────


def _briefing() -> str:
    """Briefing compuesto de estado real (no plantilla fija)."""
    lineas: list[str] = []

    try:
        import business_store as bs
        import location as loc

        r = bs.resumen()
        u = loc.actual()
        # `por_estado` es {estado: {"n": n, "color": hex}} — no un entero.
        pe = r.get("por_estado", {}) or {}

        def _n(clave: str) -> int:
            v = pe.get(clave) or {}
            return int(v.get("n", 0)) if isinstance(v, dict) else int(v or 0)

        lineas.append(f"Sede en {u.etiqueta} ({u.ciudad}, {u.pais}), fuente {u.fuente}.")
        lineas.append(
            f"{r.get('total', 0)} empresas: "
            f"{_n('activo')} activas, "
            f"{_n('alerta')} en alerta, "
            f"{_n('incidencia')} con incidencia."
        )
        lineas.append(f"MRR agregado: {r.get('mrr_total', 0)} euros al mes.")
    except Exception as e:  # noqa: BLE001
        lineas.append(f"No pude leer el estado de negocio: {e}")

    t = estado_telemetria()
    if t.get("conectado"):
        d = t.get("disco", {})
        m = t.get("memoria", {})
        if d.get("porcentaje") is not None:
            lineas.append(f"Disco al {d['porcentaje']} por ciento.")
        if m.get("porcentaje") is not None:
            lineas.append(f"Memoria al {m['porcentaje']} por ciento.")

    a = estado_astra()
    if a.get("conectado"):
        lineas.append(f"Memoria semantica con {a.get('docs', 0)} documentos.")

    return " ".join(lineas)


def estado_voz() -> dict[str, Any]:
    """Disponibilidad del motor TTS + el briefing ya compuesto."""
    try:
        from agents.piper_engine import PiperEngine, piper_disponible
    except Exception as e:  # noqa: BLE001
        return {
            **_sin_conectar(f"piper_engine no importable: {e}"),
            "herramienta": "Voice Briefing Agent",
            "briefing": _briefing(),
        }

    try:
        disp = bool(piper_disponible())
        voces: list[str] = []
        if disp:
            voces = PiperEngine().instaladas()
    except Exception as e:  # noqa: BLE001
        return {
            **_sin_conectar(f"Piper fallo: {e}"),
            "herramienta": "Voice Briefing Agent",
            "briefing": _briefing(),
        }

    return _ok(
        herramienta="Voice Briefing Agent",
        tts_disponible=disp,
        voces=voces,
        briefing=_briefing(),
        nota=(
            "Piper instalado: el briefing se puede locutar."
            if disp
            else "Piper no instalado: el briefing se sirve como texto."
        ),
    )


def sintetizar_voz(texto: str, voz: str = "") -> dict[str, Any]:
    """Sintetiza `texto` a WAV. Devuelve la ruta del fichero generado."""
    if not texto.strip():
        return {"ok": False, "error": "texto vacio"}
    try:
        from agents.piper_engine import PiperEngine, piper_disponible
    except Exception as e:  # noqa: BLE001
        return {"ok": False, "error": f"piper_engine no importable: {e}"}
    if not piper_disponible():
        return {"ok": False, "error": "Piper no instalado"}
    try:
        res = PiperEngine().sintetizar(texto[:4000], voz=voz)
    except Exception as e:  # noqa: BLE001
        return {"ok": False, "error": str(e)}
    return {"ok": True, "resultado": res}


# ── 3. Inbox Zero Drafter (triaje real, correo no conectado) ─


def estado_inbox() -> dict[str, Any]:
    """Estado del clasificador. NO hay buzon conectado: se declara.

    Ojo: `EmailZeroInbox.__init__` CREA `email_rules.json` en el directorio de
    trabajo si no existe. Un chequeo de estado no debe escribir en disco, asi
    que aqui solo se instancia si el fichero ya existe.
    """
    try:
        from agents.email_zero_inbox import EmailZeroInbox
    except Exception as e:  # noqa: BLE001
        return _sin_conectar(f"email_zero_inbox no importable: {e}")

    reglas_path = Path(os.getcwd()) / "email_rules.json"
    if not reglas_path.exists():
        return _ok(
            herramienta="Inbox Zero Drafter",
            clasificador="disponible (reglas por defecto, sin escribir en disco)",
            categorias=[],
            buzon_conectado=bool(os.getenv("IMAP_HOST") or os.getenv("EMAIL_IMAP_HOST")),
            nota=(
                "Clasificador disponible. No se ha creado email_rules.json: "
                "el estado es de solo lectura. Personaliza las reglas desde "
                "el propio modulo para generarlo."
            ),
        )

    try:
        ezi = EmailZeroInbox()
        reglas = ezi.cargar_reglas() or {}
    except Exception as e:  # noqa: BLE001
        return _sin_conectar(f"clasificador no operativo: {e}")

    imap = bool(os.getenv("IMAP_HOST") or os.getenv("EMAIL_IMAP_HOST"))
    return _ok(
        herramienta="Inbox Zero Drafter",
        clasificador="listo",
        categorias=sorted(reglas.keys()) if isinstance(reglas, dict) else [],
        buzon_conectado=imap,
        nota=(
            "Clasificador operativo. Buzon IMAP conectado."
            if imap
            else "Clasificador operativo, pero NO hay buzon IMAP configurado: "
            "usa /api/cc/inbox/triaje para clasificar correos en seco."
        ),
    )


def triaje_inbox(emails: list[dict[str, Any]]) -> dict[str, Any]:
    """Clasifica una lista de correos sin tocar ningun buzon (dry-run)."""
    if not isinstance(emails, list):
        return {"ok": False, "error": "se espera una lista de correos"}
    try:
        from agents.email_zero_inbox import EmailZeroInbox
    except Exception as e:  # noqa: BLE001
        return {"ok": False, "error": f"email_zero_inbox no importable: {e}"}
    try:
        return {"ok": True, "resultado": EmailZeroInbox().procesar_inbox(emails)}
    except Exception as e:  # noqa: BLE001
        return {"ok": False, "error": str(e)}


# ── 4. Life Telemetry HUD ────────────────────────────────────


def _cpu() -> dict[str, Any]:
    """Uso de CPU. NO bloquea.

    Antes usaba `interval=0.15`, que duerme 150 ms dentro de la peticion: el
    endpoint tardaba 213 ms medidos. Con `interval=None` devuelve el uso desde
    la ultima llamada y es instantaneo; la primera lectura de un proceso recien
    arrancado puede salir 0.0, que es correcto (aun no hay ventana).
    """
    try:
        import psutil  # type: ignore
    except ImportError:
        return {"disponible": False, "motivo": "psutil no instalado"}
    try:
        return {
            "disponible": True,
            "porcentaje": psutil.cpu_percent(interval=None),
            "nucleos": psutil.cpu_count(logical=True),
        }
    except Exception as e:  # noqa: BLE001
        return {"disponible": False, "motivo": str(e)}


def estado_telemetria() -> dict[str, Any]:
    """Disco, memoria, CPU y estado del arbol de trabajo. Todo real."""
    datos: dict[str, Any] = {}

    try:
        total, usado, libre = shutil.disk_usage(str(_RAIZ))
        datos["disco"] = {
            "total_gb": round(total / 1e9, 1),
            "usado_gb": round(usado / 1e9, 1),
            "libre_gb": round(libre / 1e9, 1),
            "porcentaje": round(usado / total * 100, 1),
        }
    except Exception as e:  # noqa: BLE001
        datos["disco"] = {"error": str(e)}

    try:
        import psutil  # type: ignore

        vm = psutil.virtual_memory()
        datos["memoria"] = {
            "total_gb": round(vm.total / 1e9, 1),
            "porcentaje": vm.percent,
        }
    except ImportError:
        datos["memoria"] = {"disponible": False, "motivo": "psutil no instalado"}
    except Exception as e:  # noqa: BLE001
        datos["memoria"] = {"error": str(e)}

    datos["cpu"] = _cpu()
    datos["host"] = {
        "sistema": platform.system(),
        "release": platform.release(),
        "python": platform.python_version(),
        "uptime_s": round(time.time() - _ARRANQUE, 0),
    }

    try:
        from health_checks import run_all_checks  # type: ignore

        datos["salud"] = run_all_checks()
    except Exception as e:  # noqa: BLE001
        datos["salud"] = {"disponible": False, "motivo": str(e)[:160]}

    return _ok(herramienta="Life Telemetry HUD", **datos)


# ── 5. Command & Control Console ─────────────────────────────


def estado_consola(app=None, failed_phases: list[dict] | None = None) -> dict[str, Any]:
    """Indice real de rutas registradas, agrupadas por prefijo."""
    grupos: dict[str, int] = {}
    total = 0
    if app is not None:
        try:
            for r in app.url_map.iter_rules():
                if r.endpoint == "static":
                    continue
                total += 1
                partes = str(r).strip("/").split("/")
                prefijo = "/" + "/".join(partes[:2])
                grupos[prefijo] = grupos.get(prefijo, 0) + 1
        except Exception as e:  # noqa: BLE001
            return _sin_conectar(f"url_map no legible: {e}")

    return _ok(
        herramienta="Command & Control Console",
        rutas_total=total,
        grupos=dict(sorted(grupos.items(), key=lambda kv: -kv[1])),
        fases_fallidas=failed_phases or [],
        agentes=_agentes(),
    )


def _agentes() -> dict[str, Any]:
    """Agentes disponibles, con descubrimiento real.

    `aig/agents/` se fusionó en la raíz (2026-09-29): se mira primero
    `agents/` y se queda el viejo por compatibilidad con despliegues no
    migrados.
    """
    for d in (_RAIZ / "agents", _RAIZ / "aig" / "agents"):
        if d.is_dir():
            nombres = sorted(p.stem for p in d.glob("agent_*.py"))
            if nombres:
                return {
                    "disponible": True,
                    "total": len(nombres),
                    "agentes": nombres,
                    "origen": str(d),
                }
    return {"disponible": False, "motivo": f"no existe {_RAIZ / 'agents'}"}


# ── Registro de rutas ────────────────────────────────────────


_ARRANQUE = time.time()


def registrar_command_center(app, failed_phases: list[dict] | None = None) -> None:
    """Registra las 5 herramientas del Command Center en `app`."""
    from flask import jsonify, request, send_file

    @app.route("/api/cc/astra")
    def cc_astra():
        return jsonify(estado_astra())

    @app.route("/api/cc/voz")
    def cc_voz():
        return jsonify(estado_voz())

    @app.route("/api/cc/voz/hablar", methods=["POST"])
    def cc_voz_hablar():
        cuerpo = request.get_json(silent=True) or {}
        texto = (cuerpo.get("texto") or "").strip() or _briefing()
        res = sintetizar_voz(texto, cuerpo.get("voz", ""))
        if not res.get("ok"):
            return jsonify(res), 503
        ruta = res["resultado"]
        if isinstance(ruta, dict):
            ruta = ruta.get("ruta") or ruta.get("path") or ""
        if ruta and os.path.isfile(ruta):
            return send_file(ruta, mimetype="audio/wav")
        return jsonify({"ok": False, "error": "Piper no devolvio un fichero"}), 503

    @app.route("/api/cc/inbox")
    def cc_inbox():
        return jsonify(estado_inbox())

    @app.route("/api/cc/inbox/triaje", methods=["POST"])
    def cc_inbox_triaje():
        cuerpo = request.get_json(silent=True) or {}
        return jsonify(triaje_inbox(cuerpo.get("emails") or []))

    @app.route("/api/cc/telemetria")
    def cc_telemetria():
        return jsonify(estado_telemetria())

    @app.route("/api/cc/consola")
    def cc_consola():
        return jsonify(estado_consola(app, failed_phases))

    print("[Command Center] 5 herramientas registradas en /api/cc/*")
