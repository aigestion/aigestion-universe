#!/usr/bin/env python3
"""
Daniela OS v2.0 - Sistema Operativo Integrado AIGestion
=========================================================
Punto de entrada principal de AIGestion. Expone:
- Dashboard web (Flask)
- API REST unificada
- Chat con Daniela con acceso a los 10 Quick Wins
- Integracion total con DanielaCore

Autor: AIGestion Team
"""

from __future__ import annotations

import json
import os
import sqlite3
import sys
from datetime import datetime
from pathlib import Path
from typing import Any

from flask import Flask, Response, jsonify, render_template, request, send_file

try:
    from dotenv import load_dotenv

    load_dotenv()
except ImportError:
    # python-dotenv es opcional: DanielaOS debe arrancar igual en Termux
    def load_dotenv(*_args, **_kwargs):
        return False

# ── Configuracion ─────────────────────────────────────────────

DB_NAME = "daniela_vault.db"

# Sin valor por defecto a proposito: antes habia un PIN quemado en el codigo
# que acabo publicado en el historial de git. Un PIN por defecto es un PIN
# publico, asi que si no esta definido en el entorno el acceso por PIN
# queda CERRADO (falla cerrado) en lugar de admitir uno conocido.
ACCESS_PIN = os.getenv("DANIELA_PIN", "")
if not ACCESS_PIN:
    print(
        "[aviso] DANIELA_PIN no definido en el entorno. El acceso por PIN "
        "esta desactivado hasta que lo anadas a .env"
    )
API_KEY = os.getenv("GEMINI_API_KEY", os.getenv("GOOGLE_API_KEY", ""))

# ── Inicializar Flask ─────────────────────────────────────────

app = Flask(__name__, template_folder="templates")

# ── PHASE 1: Pixel Bridge Hub ─────────────────────────────────
try:
    from pixel_bridge_hub import register_pixel_routes

    register_pixel_routes(app)
except ImportError:
    print("[Pixel Bridge] Not available")

# ── PHASE 2: Sensor Stream / FCM / Clipboard ──────────────────
try:
    from sensor_stream_live import register_sensor_routes

    register_sensor_routes(app)
except ImportError:
    print("[Sensor Stream] Not available")

try:
    from fcm_real_bridge import register_fcm_routes

    register_fcm_routes(app)
except ImportError:
    print("[FCM Bridge] Not available")

try:
    from clipboard_sync import register_clipboard_routes

    register_clipboard_routes(app)
except ImportError:
    print("[Clipboard Sync] Not available")

# ── PHASE 3: ADB Mirror / Voice / File Sync ───────────────────
try:
    from adb_mirror import register_adb_routes

    register_adb_routes(app)
except ImportError:
    print("[ADB Mirror] Not available")

try:
    from voice_pipeline import register_voice_routes

    register_voice_routes(app)
except ImportError:
    print("[Voice Pipeline] Not available")

try:
    from file_sync_daemon import register_filesync_routes

    register_filesync_routes(app)
except ImportError:
    print("[File Sync] Not available")

# ── PHASE 4: IoT / Security Cam / Geofence / Vision / 2nd Screen
try:
    from iot_real_integration import register_iot_routes

    register_iot_routes(app)
except ImportError:
    print("[IoT] Not available")

try:
    from security_camera import register_security_routes

    register_security_routes(app)
except ImportError:
    print("[Security Camera] Not available")

try:
    from geofence_engine import register_geofence_routes

    register_geofence_routes(app)
except ImportError:
    print("[Geofence] Not available")

try:
    from screen_ai_vision import register_vision_routes

    register_vision_routes(app)
except ImportError:
    print("[Screen Vision] Not available")

try:
    from pixel_second_screen import register_second_screen_routes

    register_second_screen_routes(app)
except ImportError:
    print("[Second Screen] Not available")

# ── FASE 5: Daniela 24/7 + Git Brain Sync ─────────────────────
try:
    from daemon_24_7 import register_daemon_routes

    register_daemon_routes(app)
except ImportError:
    print("[Daniela 24/7] Not available")

try:
    from git_brain_sync import register_brain_routes

    register_brain_routes(app)
except ImportError:
    print("[Brain Sync] Not available")

# ── FASE 6: Daniela Mobile Core (E-04) ───────────────────────
try:
    from daniela_mobile_core import register_core_routes

    register_core_routes(app)
except ImportError:
    print("[Mobile Core] Not available")

# ── FASE 6: Context Engine + detector de caidas (E-05) ───────
try:
    from context_engine import register_context_routes

    register_context_routes(app)
except ImportError:
    print("[Context Engine] Not available")

# ── FASE 6: Caja Negra Forense (E-06) ────────────────────────
try:
    from blackbox_forense import register_blackbox_routes

    register_blackbox_routes(app)
except ImportError:
    print("[Black Box] Not available")

# ── FASE 7: Termux Dialog UI + Widgets (E-10) ────────────────
try:
    from native_ui import register_ui_routes

    register_ui_routes(app)
except ImportError:
    print("[Native UI] Not available")

# ── FASE 7: Mando Universal IR (E-07) ────────────────────────
try:
    from ir_bridge import register_ir_routes

    register_ir_routes(app)
except ImportError:
    print("[IR Bridge] Not available")

# ── FASE 7: NFC Physical Automation (E-08) ───────────────────
try:
    from nfc_automation import register_nfc_routes

    register_nfc_routes(app)
except ImportError:
    print("[NFC] Not available")

# ── FASE 7: USB Serial → Arduino/ESP32 (E-09) ────────────────
try:
    from serial_bridge import register_serial_routes

    register_serial_routes(app)

except ImportError:
    print("[Serial Bridge] Not available")

# ── FASE 8: Daniela Mesh — CRDTs offline-first (E-11) ─────────
try:
    from daniela_mesh import register_mesh_routes

    register_mesh_routes(app)
except ImportError:
    print("[Daniela Mesh] Not available")

# ── FASE 10: máximo esplendor (E-19 … E-26) ───────────────────
# Ocho capacidades del hardware que estaban declaradas y sin usar.
# Todos degradan bien: si el Pixel no expone la API, la ruta sigue
# respondiendo con un estado honesto en vez de un 500.

try:
    from wifi_rtt import register_rtt_routes

    register_rtt_routes(app)
except ImportError:
    print("[WiFi RTT] Not available")

try:
    from wifi_aware import register_aware_routes

    register_aware_routes(app)
except ImportError:
    print("[WiFi Aware] Not available")

try:
    from context_hub import register_hub_routes

    register_hub_routes(app)
except ImportError:
    print("[Context Hub] Not available")

try:
    from silicon_vault import register_vault_routes

    register_vault_routes(app)
except ImportError:
    print("[Silicon Vault] Not available")

try:
    from desktop_mode import register_desktop_routes

    register_desktop_routes(app)
except ImportError:
    print("[Desktop Mode] Not available")

try:
    from live_wallpaper import register_wallpaper_routes

    register_wallpaper_routes(app)
except ImportError:
    print("[Live Wallpaper] Not available")

try:
    from nfc_hce import register_nfckey_routes

    register_nfckey_routes(app)
except ImportError:
    print("[NFC Key] Not available")

try:
    from stereo_vision import register_stereo_routes

    register_stereo_routes(app)
except ImportError:
    print("[Stereo Vision] Not available")

# ── FASE 8 y 9: cierre (E-14 y E-17) ─────────────────────────
# E-14 · Bluetooth: el sensor de contexto mas barato del telefono. El manos
#        libres del coche no miente, al contrario que el acelerometro.
# E-17 · Salud del nodo: la auditoria encontro swap al 98,5 % y un wakelock
#        de 10 dias que nadie habia visto. Esto es lo que los mira.
#
# OJO: se captura Exception, no solo ImportError. Un SyntaxError dentro de un
# modulo NO es un ImportError y reventaria el arranque entero de DanielaOS
# (ya paso una vez con los docstrings "AP-10"). Mejor avisar y seguir.

try:
    from bt_bridge import register_bt_routes

    register_bt_routes(app)
except Exception as e:  # noqa: BLE001 - ver comentario de arriba
    print(f"[Bluetooth] Not available: {e}")

try:
    from health_monitor import register_vitals_routes

    register_vitals_routes(app)
except Exception as e:  # noqa: BLE001
    print(f"[Health Monitor] Not available: {e}")

# ── FASE 8 y 9: cierre (E-15) ─────────────────────────────────
# E-15 · CI en ARM real: el workflow de GitHub corre en x86 y no puede ver los
#        fallos de un Pixel (toybox, 32 bits, /proc distinto). Y un runner
#        self-hosted de verdad ejecutaria codigo de terceros en tu movil: nunca.
#        Aqui los trabajos son una lista cerrada y solo se publica el estado.
try:
    from ci_runner import register_ci_routes

    register_ci_routes(app)
except Exception as e:  # noqa: BLE001
    print(f"[CI ARM] Not available: {e}")

# ── FASE 8 y 9: cierre (E-32) ─────────────────────────────────
# E-32 · Enrutador de modelos: si Gemini falla, cae a Groq, OpenRouter,
#        Anthropic, Cohere, Ollama local o HuggingFace. Y si uno respondio hace
#        poco, empieza por el. Es el fin del "no me reconoce la API key": con
#        ocho claves en el .env, depender de una sola era un error de diseno.
try:
    from model_router import register_router_routes

    register_router_routes(app)
except Exception as e:  # noqa: BLE001
    print(f"[Model Router] Not available: {e}")

# ── Base de Datos ─────────────────────────────────────────────


def init_db() -> None:
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("""CREATE TABLE IF NOT EXISTS variables (
        clave TEXT PRIMARY KEY,
        valor TEXT
    )""")
    c.execute("""CREATE TABLE IF NOT EXISTS chat_log (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        emisor TEXT,
        mensaje TEXT,
        timestamp TEXT
    )""")
    c.execute("""CREATE TABLE IF NOT EXISTS command_log (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        comando TEXT,
        modulo TEXT,
        resultado TEXT,
        timestamp TEXT
    )""")
    conn.commit()
    conn.close()


init_db()


def db_set(k: str, v: str) -> None:
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("INSERT OR REPLACE INTO variables (clave, valor) VALUES (?, ?)", (k, v))
    conn.commit()
    conn.close()


def db_get_all() -> dict[str, str]:
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("SELECT clave, valor FROM variables")
    rows = {r[0]: r[1] for r in c.fetchall()}
    conn.close()
    return rows


def log_chat(emisor: str, msg: str) -> None:
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute(
        "INSERT INTO chat_log (emisor, mensaje, timestamp) VALUES (?, ?, ?)",
        (emisor, msg, datetime.now().strftime("%Y-%m-%d %H:%M:%S")),
    )
    conn.commit()
    conn.close()


def get_recent_history(limit: int = 10) -> str:
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("SELECT emisor, mensaje FROM chat_log ORDER BY id DESC LIMIT ?", (limit,))
    rows = c.fetchall()
    conn.close()
    rows.reverse()
    return "\n".join([f"{r[0]}: {r[1]}" for r in rows])


def log_command(cmd: str, module: str, result: str) -> None:
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute(
        "INSERT INTO command_log (comando, modulo, resultado, timestamp) VALUES (?, ?, ?, ?)",
        (cmd, module, result, datetime.now().strftime("%Y-%m-%d %H:%M:%S")),
    )
    conn.commit()
    conn.close()


# ── Integracion con AIGestion Core ────────────────────────────

_core_obj: Any = None


def get_core() -> Any:
    """Lazy loader para DanielaCore."""
    global _core_obj
    if _core_obj is None:
        core_path = Path(__file__).parent / "daniela_os_core.py"
        if core_path.exists():
            try:
                import importlib.util

                spec = importlib.util.spec_from_file_location("daniela_os_core", core_path)
                if spec and spec.loader:
                    mod = importlib.util.module_from_spec(spec)
                    sys.modules["daniela_os_core"] = mod
                    spec.loader.exec_module(mod)
                    _core_obj = mod.DanielaCore()
            except Exception as e:
                print(f"[DANIELA-OS] Error cargando core: {e}")
                _core_obj = None
    return _core_obj


def core_ask(query: str, **kwargs: Any) -> dict[str, Any]:
    """Envia una consulta al core de AIGestion."""
    core = get_core()
    if core:
        return core.ask(query, **kwargs)
    return {"status": "offline", "error": "AIGestion Core no disponible"}


def core_pipeline(steps: list[dict[str, Any]]) -> dict[str, Any]:
    """Ejecuta un pipeline a traves del core."""
    core = get_core()
    if core:
        from daniela_os_core import PipelineStep

        pipeline_steps = [PipelineStep(**s) for s in steps]
        result = core.run_pipeline(pipeline_steps)
        return {
            "success": result.success,
            "duration_ms": result.duration_ms,
            "outputs": result.outputs,
            "errors": result.errors,
        }
    return {"status": "offline", "error": "AIGestion Core no disponible"}


# ── Gemini Client (opcional) ──────────────────────────────────

_gemini_client: Any = None


def get_gemini_client() -> Any:
    """Lazy loader para cliente Gemini."""
    global _gemini_client
    if _gemini_client is None and API_KEY:
        try:
            from google import genai

            _gemini_client = genai.Client(api_key=API_KEY)
        except Exception:
            _gemini_client = None
    return _gemini_client


SYSTEM_INSTRUCTION = """Eres Daniela-OS v2.0, Directora de Operaciones de AIGestion.
Tienes acceso a 10 modulos de IA especializados via DanielaCore:
- Proactive Engine (calendario, alertas)
- Email Zero Inbox (clasificacion, respuestas)
- Smart Invoice Auditor (facturas, OCR, fraude)
- Meeting Intelligence (transcripcion, action items)
- Sentiment Dashboard (analisis emocional)
- Social Media Command Center (redes sociales)
- Customer Support Automation (soporte, FAQ)
- Code Generation Agent (generar codigo)
- Content Factory AI (contenido multi-plataforma)
- Swarm Intelligence (coordinacion multi-agente)

Personalidad: Perspicaz, tecnica, leal, enfocada en resultados."""


# ═══════════════════════════════════════════════════════════════
# RUTAS WEB
# ═══════════════════════════════════════════════════════════════


@app.route("/")
def home() -> str:
    """Dashboard principal."""
    return render_template("index.html")


@app.route("/api/status")
def api_status() -> Response:
    """Estado del sistema Daniela OS + Core."""
    core = get_core()
    core_status = "online" if core else "offline"
    modules = []
    if core:
        try:
            for m in core.registry.list_enabled():
                modules.append(
                    {
                        "name": m.name,
                        "description": m.description,
                        "intents": m.intents[:3],
                    }
                )
        except Exception:
            pass

    return jsonify(
        {
            "daniela_os": "online",
            "version": "2.0.0",
            "core_status": core_status,
            "modules_count": len(modules),
            "modules": modules,
            "timestamp": datetime.now().isoformat(),
        }
    )


@app.route("/api/check_pin", methods=["POST"])
def check_pin() -> Response:
    data = request.get_json() or {}
    # Falla cerrado: si no hay PIN configurado, nadie entra.
    valido = bool(ACCESS_PIN) and data.get("pin") == ACCESS_PIN
    return jsonify(
        {
            "status": "ok" if valido else "error",
            "pin_configurado": bool(ACCESS_PIN),
        }
    )


@app.route("/api/chat", methods=["POST"])
def chat() -> Response:
    """
    Endpoint principal de chat.
    Procesa comandos slash y consultas naturales.
    """
    data = request.get_json() or {}
    msg = data.get("message", "").strip()
    if not msg:
        return jsonify({"type": "error", "response": "Mensaje vacio"})

    log_chat("Alejandro", msg)

    # ── Comandos Slash ────────────────────────────────────────

    if msg.startswith("/core "):
        # Consulta directa al core de AIGestion
        query = msg[6:].strip()
        result = core_ask(query)
        response_text = f"🧠 <b>Core Result:</b><br><pre>{json.dumps(result, indent=2, ensure_ascii=False)}</pre>"
        log_chat("Daniela-OS", response_text)
        log_command(msg, "core", json.dumps(result))
        return jsonify({"type": "core", "response": response_text, "raw": result})

    if msg.startswith("/pipeline "):
        # Ejecutar pipeline JSON
        try:
            steps = json.loads(msg[10:].strip())
            result = core_pipeline(steps)
            response_text = f"⚡ <b>Pipeline Result:</b><br><pre>{json.dumps(result, indent=2, ensure_ascii=False)}</pre>"
            log_chat("Daniela-OS", response_text)
            return jsonify({"type": "pipeline", "response": response_text, "raw": result})
        except Exception as e:
            return jsonify({"type": "error", "response": f"Error en pipeline: {e}"})

    if msg.startswith("/content "):
        topic = msg[9:].strip()
        result = core_ask(f"genera contenido para blog sobre {topic}")
        if result.get("success"):
            content = result.get("result", {})
            response_text = f"📝 <b>Content Factory:</b><br>{content}"
        else:
            response_text = f"📝 Generando contenido sobre: '{topic}'"
        log_chat("Daniela-OS", response_text)
        log_command(msg, "content_factory", json.dumps(result))
        return jsonify({"type": "content", "response": response_text, "raw": result})

    if msg.startswith("/swarm "):
        goal = msg[7:].strip()
        result = core_ask(f"coordinar swarm para: {goal}")
        response_text = (
            f"🐝 <b>Swarm:</b><br><pre>{json.dumps(result, indent=2, ensure_ascii=False)}</pre>"
        )
        log_chat("Daniela-OS", response_text)
        log_command(msg, "swarm_intel", json.dumps(result))
        return jsonify({"type": "swarm", "response": response_text, "raw": result})

    if msg.startswith("/code "):
        desc = msg[6:].strip()
        result = core_ask(f"genera codigo: {desc}")
        response_text = (
            f"💻 <b>CodeGen:</b><br><pre>{json.dumps(result, indent=2, ensure_ascii=False)}</pre>"
        )
        log_chat("Daniela-OS", response_text)
        log_command(msg, "code_gen", json.dumps(result))
        return jsonify({"type": "code", "response": response_text, "raw": result})

    if msg.startswith("/email "):
        query = msg[7:].strip()
        result = core_ask(f"clasifica email: {query}")
        response_text = (
            f"📧 <b>Email AI:</b><br><pre>{json.dumps(result, indent=2, ensure_ascii=False)}</pre>"
        )
        log_chat("Daniela-OS", response_text)
        return jsonify({"type": "email", "response": response_text, "raw": result})

    if msg.startswith("/invoice "):
        query = msg[9:].strip()
        result = core_ask(f"audita factura: {query}")
        response_text = f"📄 <b>Invoice Auditor:</b><br><pre>{json.dumps(result, indent=2, ensure_ascii=False)}</pre>"
        log_chat("Daniela-OS", response_text)
        return jsonify({"type": "invoice", "response": response_text, "raw": result})

    if msg.startswith("/sentiment "):
        text = msg[11:].strip()
        result = core_ask(f"analiza sentimiento: {text}")
        response_text = (
            f"🎭 <b>Sentiment:</b><br><pre>{json.dumps(result, indent=2, ensure_ascii=False)}</pre>"
        )
        log_chat("Daniela-OS", response_text)
        return jsonify({"type": "sentiment", "response": response_text, "raw": result})

    if msg.startswith("/social "):
        topic = msg[8:].strip()
        result = core_ask(f"genera post de redes sobre {topic}")
        response_text = f"📱 <b>Social Media:</b><br><pre>{json.dumps(result, indent=2, ensure_ascii=False)}</pre>"
        log_chat("Daniela-OS", response_text)
        return jsonify({"type": "social", "response": response_text, "raw": result})

    if msg.startswith("/support "):
        query = msg[9:].strip()
        result = core_ask(f"soporte: {query}")
        response_text = (
            f"🎧 <b>Support:</b><br><pre>{json.dumps(result, indent=2, ensure_ascii=False)}</pre>"
        )
        log_chat("Daniela-OS", response_text)
        return jsonify({"type": "support", "response": response_text, "raw": result})

    if msg.startswith("/meeting "):
        transcript = msg[9:].strip()
        result = core_ask(f"analiza reunion: {transcript}")
        response_text = f"🤝 <b>Meeting Intel:</b><br><pre>{json.dumps(result, indent=2, ensure_ascii=False)}</pre>"
        log_chat("Daniela-OS", response_text)
        return jsonify({"type": "meeting", "response": response_text, "raw": result})

    if msg.startswith("/proactive"):
        result = core_ask("analiza mi calendario y alertas")
        response_text = (
            f"🔮 <b>Proactive:</b><br><pre>{json.dumps(result, indent=2, ensure_ascii=False)}</pre>"
        )
        log_chat("Daniela-OS", response_text)
        return jsonify({"type": "proactive", "response": response_text, "raw": result})

    if msg.startswith("/set "):
        try:
            p = msg[5:].split("=", 1)
            db_set(p[0].strip(), p[1].strip())
            return jsonify(
                {
                    "type": "sys",
                    "response": f"Variable guardada: <b>{p[0].strip()}</b> = <i>'{p[1].strip()}'</i>",
                }
            )
        except Exception:
            return jsonify({"type": "sys", "response": "Sintaxis: <code>/set clave=valor</code>"})

    if msg.startswith("/vars"):
        vars_ctx = db_get_all()
        return jsonify(
            {
                "type": "sys",
                "response": f"Variables:<br><pre>{json.dumps(vars_ctx, indent=2, ensure_ascii=False)}</pre>",
            }
        )

    if msg == "/help":
        help_text = """<b>Comandos disponibles:</b><br>
        <code>/core &lt;query&gt;</code> - Consulta al DanielaCore<br>
        <code>/pipeline &lt;json&gt;</code> - Ejecutar pipeline<br>
        <code>/content &lt;tema&gt;</code> - Generar contenido<br>
        <code>/swarm &lt;objetivo&gt;</code> - Coordinar swarm<br>
        <code>/code &lt;descripcion&gt;</code> - Generar codigo<br>
        <code>/email &lt;texto&gt;</code> - Clasificar email<br>
        <code>/invoice &lt;datos&gt;</code> - Auditar factura<br>
        <code>/sentiment &lt;texto&gt;</code> - Analizar sentimiento<br>
        <code>/social &lt;tema&gt;</code> - Generar post social<br>
        <code>/support &lt;query&gt;</code> - Soporte automatico<br>
        <code>/meeting &lt;transcripcion&gt;</code> - Analizar reunion<br>
        <code>/proactive</code> - Ver alertas del calendario<br>
        <code>/set clave=valor</code> - Guardar variable<br>
        <code>/vars</code> - Ver variables guardadas<br>
        <code>/help</code> - Mostrar esta ayuda"""
        return jsonify({"type": "help", "response": help_text})

    # ── Chat con Gemini (fallback) ────────────────────────────

    vars_ctx = db_get_all()
    history_ctx = get_recent_history(limit=10)
    prompt_completo = f"Variables: {vars_ctx}\nHistorial Reciente:\n{history_ctx}\nInstruccion de Alejandro: {msg}"

    client = get_gemini_client()
    if client:
        try:
            from google.genai import types

            response = client.models.generate_content(
                model="gemini-2.5-flash",
                contents=prompt_completo,
                config=types.GenerateContentConfig(
                    system_instruction=SYSTEM_INSTRUCTION, temperature=0.65
                ),
            )
            reply = response.text
        except Exception as e:
            reply = f"[Gemini Error] {e}. Usando modo local."
    else:
        # Sin Gemini, usar el core directamente
        result = core_ask(msg)
        if result.get("success"):
            reply = f"🧠 {result.get('result', {}).get('message', 'Procesado por AIGestion Core')}"
        else:
            reply = f"Recibido: '{msg}'. AIGestion Core activo. Usa /help para ver comandos."

    log_chat("Daniela-OS", reply)
    return jsonify({"type": "ai", "response": reply})


@app.route("/api/history")
def api_history() -> Response:
    """Devuelve historial de chat."""
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("SELECT emisor, mensaje, timestamp FROM chat_log ORDER BY id DESC LIMIT 50")
    rows = c.fetchall()
    conn.close()
    return jsonify(
        {"history": [{"emisor": r[0], "mensaje": r[1], "timestamp": r[2]} for r in rows]}
    )


@app.route("/api/commands")
def api_commands() -> Response:
    """Devuelve historial de comandos ejecutados."""
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute(
        "SELECT comando, modulo, resultado, timestamp FROM command_log ORDER BY id DESC LIMIT 50"
    )
    rows = c.fetchall()
    conn.close()
    return jsonify(
        {
            "commands": [
                {"comando": r[0], "modulo": r[1], "resultado": r[2], "timestamp": r[3]}
                for r in rows
            ]
        }
    )


@app.route("/api/backup_db")
def backup_db() -> Response:
    if os.path.exists(DB_NAME):
        return send_file(DB_NAME, as_attachment=True, download_name="daniela_vault_backup.db")
    return jsonify({"status": "error", "response": "DB no encontrada"})


# ═══════════════════════════════════════════════════════════════
# CLI
# ═══════════════════════════════════════════════════════════════


def main() -> int:
    import argparse

    parser = argparse.ArgumentParser(description="Daniela OS v2.0")
    parser.add_argument("--host", default="0.0.0.0", help="Host (default: 0.0.0.0)")
    parser.add_argument("--port", type=int, default=5000, help="Puerto (default: 5000)")
    parser.add_argument("--debug", action="store_true", help="Modo debug")
    parser.add_argument("--test-core", action="store_true", help="Testear conexion con core")

    args = parser.parse_args()

    if args.test_core:
        print("[TEST] Verificando conexion con AIGestion Core...")
        core = get_core()
        if core:
            print(f"  Core version: {core.VERSION}")
            print(f"  Modulos activos: {len(core.registry.list_enabled())}")
            for m in core.registry.list_enabled():
                print(f"    - {m.name}: {m.description[:50]}...")
            print("\n[OK] Daniela OS acoplada 100% al core.")
        else:
            print("[ERROR] No se pudo cargar el core.")
        return 0

    print(f"""
    ╔══════════════════════════════════════════════════════════════╗
    ║                                                              ║
    ║   Daniela OS v2.0 - AIGestion Integrated                     ║
    ║                                                              ║
    ║   URL: http://{args.host}:{args.port:<5}                             ║
    ║   Core: {"CONECTADO" if get_core() else "OFFLINE":<10}                          ║
    ║                                                              ║
    ╚══════════════════════════════════════════════════════════════╝
    """)

    app.run(host=args.host, port=args.port, debug=args.debug)
    return 0


if __name__ == "__main__":
    sys.exit(main())
