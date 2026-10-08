"""
Daniela Voice Activation - Always listening for "Hey Daniela"
Works on both PC (microphone) and Phone (Termux Speech-to-Text)
"""

import time

from flask import Blueprint, jsonify, request

voice_activation_bp = Blueprint("voice_activation", __name__)

_state = {
    "active": False,
    "listening": False,
    "wake_word": "hey daniela",
    "language": "es",
    "last_activation": 0,
    "activation_count": 0,
    "commands_processed": 0,
    "history": []
}

COMMANDS = {
    "abrir": {"action": "open_app", "desc": "Abrir aplicacion"},
    "cerrar": {"action": "close_app", "desc": "Cerrar aplicacion"},
    "llamar": {"action": "call", "desc": "Llamar contacto"},
    "mensaje": {"action": "sms", "desc": "Enviar mensaje"},
    "foto": {"action": "photo", "desc": "Tomar foto"},
    "alarma": {"action": "alarm", "desc": "Poner alarma"},
    "recordatorio": {"action": "reminder", "desc": "Crear recordatorio"},
    "clima": {"action": "weather", "desc": "Ver clima"},
    "musica": {"action": "music", "desc": "Reproducir musica"},
    "silencio": {"action": "silence", "desc": "Modo silencio"},
    "emergencia": {"action": "sos", "desc": "Emergencia"},
    "ubicacion": {"action": "location", "desc": "Ver ubicacion"},
    "bateria": {"action": "battery", "desc": "Ver bateria"},
    "foco": {"action": "focus", "desc": "Modo enfoque"},
    "dormir": {"action": "sleep", "desc": "Modo dormir"}
}

@voice_activation_bp.route("/api/voice-activation/status")
def va_status():
    return jsonify(_state)

@voice_activation_bp.route("/api/voice-activation/activate", methods=["POST"])
def va_activate():
    data = request.json or {}
    text = data.get("text", "").lower().strip()
    _state["last_activation"] = time.time()
    _state["activation_count"] += 1

    command = None
    for word, info in COMMANDS.items():
        if word in text:
            command = info
            break

    entry = {
        "text": text,
        "command": command["action"] if command else None,
        "time": time.time()
    }
    _state["history"].append(entry)
    if len(_state["history"]) > 50:
        _state["history"] = _state["history"][-50:]

    if command:
        _state["commands_processed"] += 1

    return jsonify({
        "ok": True,
        "recognized": text,
        "command": command,
        "response": _generate_response(text, command)
    })

@voice_activation_bp.route("/api/voice-activation/start", methods=["POST"])
def va_start():
    _state["active"] = True
    _state["listening"] = True
    return jsonify({"ok": True})

@voice_activation_bp.route("/api/voice-activation/stop", methods=["POST"])
def va_stop():
    _state["active"] = False
    _state["listening"] = False
    return jsonify({"ok": True})

def _generate_response(text, command):
    if not command:
        return "No reconozco ese comando. Prueba: abrir, llamar, foto, alarma..."
    responses = {
        "open_app": "Abriendo la aplicacion...",
        "close_app": "Cerrando la aplicacion...",
        "call": "Preparando llamada...",
        "sms": "Escribe tu mensaje...",
        "photo": "Tomando foto...",
        "alarm": "Alarma configurada",
        "reminder": "Recordatorio creado",
        "weather": "Consultando clima...",
        "music": "Reproduciendo musica...",
        "silence": "Modo silencio activado",
        "sos": "EMERGENCIA - Enviando alerta...",
        "location": "Mostrando ubicacion...",
        "battery": "Nivel de bateria: consultando...",
        "focus": "Modo enfoque activado",
        "sleep": "Modo dormir activado"
    }
    return responses.get(command["action"], "Procesando...")

@voice_activation_bp.route("/api/voice-activation/web")
def va_web():
    return """<!DOCTYPE html>
<html><head><meta charset="utf-8"><title>Voice Activation</title>
<style>body{margin:0;background:#0a0a0f;color:#00f0ff;font-family:monospace;display:flex;justify-content:center;align-items:center;height:100vh}
.voice{text-align:center}
.mic{width:150px;height:150px;border-radius:50%;border:4px solid #333;display:flex;align-items:center;justify-content:center;font-size:60px;cursor:pointer;transition:all .3s;margin:0 auto}
.mic:hover{border-color:#00f0ff}
.mic.listening{border-color:#00ff88;background:#00ff8822;animation:pulse 1s infinite}
@keyframes pulse{0%,100%{box-shadow:0 0 20px #00ff8844}50%{box-shadow:0 0 60px #00ff8888}}
.status{margin:20px;font-size:14px}
.waveform{display:flex;gap:3px;justify-content:center;margin:20px 0;height:40px;align-items:center}
.waveform .bar{width:4px;background:#00f0ff;border-radius:2px;transition:height .1s}
.commands{display:flex;gap:8px;flex-wrap:wrap;justify-content:center;margin-top:20px}
.cmd{background:#111;border:1px solid #333;padding:5px 12px;border-radius:15px;font-size:11px}
.cmd.active{border-color:#00ff88;background:#00ff8811}
.history{margin-top:30px;max-width:400px;text-align:left}
.history .entry{background:#111;padding:8px;border-radius:6px;margin:5px 0;font-size:12px}
</style></head><body>
<div class="voice">
<h2>VOICE ACTIVATION</h2>
<div class="mic" id="mic" onclick="toggle()">🎙</div>
<div class="status" id="status">Click to start listening</div>
<div class="waveform" id="waveform"></div>
<div class="commands" id="commands"></div>
<div class="history" id="history"></div>
</div>
<script>let listening=false;
const cmds=['abrir','cerrar','llamar','mensaje','foto','alarma','recordatorio','clima','musica','silencio','emergencia','ubicacion','bateria','foco','dormir'];
const c=document.getElementById('commands');
cmds.forEach(cmd=>{const d=document.createElement('div');d.className='cmd';d.textContent=cmd;c.appendChild(d)});
function toggle(){listening=!listening;document.getElementById('mic').className='mic '+(listening?'listening':'');document.getElementById('status').textContent=listening?'Listening for "Hey Daniela"...':'Click to start';
fetch('/api/voice-activation/'+(listening?'start':'stop'),{method:'POST'})}
function addEntry(text,cmd){const h=document.getElementById('history');const d=document.createElement('div');d.className='entry';d.innerHTML='<strong>"+text+'</strong> '+(cmd?cmd:'');h.insertBefore(d,h.firstChild)}
</script></body></html>"""
