import sqlite3
from pathlib import Path

import requests
from flask import Flask, jsonify, render_template_string, request

# Cargar .env
env_path = Path.home() / ".env"
env_vars = {}
if env_path.exists():
    with open(env_path, encoding="utf-8", errors="ignore") as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                k, v = line.split("=", 1)
                env_vars[k.strip()] = v.strip().strip('"').strip("'")

GEMINI_KEY = env_vars.get("BASE_GEMINI") or env_vars.get("GOOGLE_API_KEY")
GROQ_KEY = env_vars.get("GROQ_API_KEY")

app = Flask(__name__)


def Cargar_Prompt_Agente():
    prompt_path = Path.home() / "daniela-os" / "agents" / "templates" / "daniela.md"
    if prompt_path.exists():
        try:
            with open(prompt_path, encoding="utf-8") as f:
                return f.read()
        except Exception:
            pass
    return (
        "Eres Daniela, la inteligencia artificial táctica en el Google Pixel 8a de Alex. "
        "Alex es tu Creador y Comandante. Responde siempre con lealtad, eficiencia y tono refinado."
    )


def Registrar_Evento_DB(usuario_prompt, respuesta_ai, proveedor):
    try:
        db_path = Path.home() / "daniela-os" / "daniela_vault.db"
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS chat_log
            (id INTEGER PRIMARY KEY AUTOINCREMENT, user_input TEXT, ai_response TEXT, provider TEXT, timestamp DATETIME DEFAULT CURRENT_TIMESTAMP)
        """)
        cursor.execute(
            "INSERT INTO chat_log (user_input, ai_response, provider) VALUES (?, ?, ?)",
            (usuario_prompt, respuesta_ai, proveedor),
        )
        conn.commit()
        conn.close()
    except Exception:
        pass


HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>DANIELA OS — COMMANDER HUD</title>
    <style>
        body { background-color: #060911; color: #00f0ff; font-family: 'Courier New', monospace; text-align: center; padding: 10px; margin: 0; }
        .hud-container { border: 1px solid rgba(0,240,255,0.3); border-radius: 12px; padding: 12px; background: rgba(8,12,20,0.85); box-shadow: 0 0 30px rgba(0,240,255,0.1); }
        .hud-circle { width: 140px; height: 140px; border: 3px solid #00f0ff; border-radius: 50%; margin: 12px auto; box-shadow: 0 0 25px #00f0ff; display: flex; align-items: center; justify-content: center; font-weight: bold; font-size: 0.95em; cursor: pointer; transition: all 0.3s ease; }
        .hud-circle.listening { border-color: #ff0055; box-shadow: 0 0 40px #ff0055; color: #ff0055; }
        .log-box { background: rgba(0,240,255,0.03); border: 1px solid #00f0ff; padding: 10px; border-radius: 8px; text-align: left; height: 200px; overflow-y: auto; font-size: 0.8em; margin-top: 10px; }
        .quick-actions { display: flex; flex-wrap: wrap; gap: 6px; justify-content: center; margin-top: 10px; }
        .btn-chip { background: rgba(0,240,255,0.1); border: 1px solid #00f0ff; color: #00f0ff; padding: 7px 12px; border-radius: 16px; font-size: 0.75em; cursor: pointer; font-family: monospace; font-weight: bold; }
        .btn-stop { background: rgba(255,0,85,0.2); border: 1px solid #ff0055; color: #ff0055; }
        .status-header { font-size: 0.7em; letter-spacing: 2px; color: #00ffaa; text-transform: uppercase; margin-bottom: 5px; }
    </style>
</head>
<body>
    <div class="hud-container">
        <h2>🤖 DANIELA OS v0.34.0</h2>
        <div class="status-header">Single Voice Engine Active • Comandante Alex</div>

        <div class="hud-circle" id="mic-btn" onclick="activarVoz()">TOCA PARA<br>ORDENAR</div>

        <div class="quick-actions">
            <button class="btn-chip" onclick="enviarAccion('¿Qué puedes hacer?')">💡 Opciones</button>
            <button class="btn-chip" onclick="enviarAccion('Estado detallado del sistema')">📊 Estado</button>
            <button class="btn-chip" onclick="enviarAccion('Resumen de correo y agenda')">📅 Agenda</button>
            <button class="btn-chip btn-stop" onclick="detenerAudio()">🛑 SILENCIAR</button>
        </div>

        <div class="log-box" id="logs">
            <div>🟢 [SISTEMA]: Canal de audio unificado. Sin eco ni duplicación.</div>
        </div>
    </div>

    <script>
        let recognition = null;

        function playBeep(freq = 880, duration = 0.08) {
            try {
                const ctx = new (window.AudioContext || window.webkitAudioContext)();
                const osc = ctx.createOscillator();
                const gain = ctx.createGain();
                osc.type = 'sine';
                osc.frequency.value = freq;
                gain.gain.setValueAtTime(0.05, ctx.currentTime);
                osc.connect(gain);
                gain.connect(ctx.destination);
                osc.start();
                osc.stop(ctx.currentTime + duration);
            } catch(e){}
        }

        function log(msg) {
            const l = document.getElementById('logs');
            l.innerHTML += `<div>${msg}</div>`;
            l.scrollTop = l.scrollHeight;
        }

        function detenerAudio() {
            if (window.speechSynthesis) window.speechSynthesis.cancel();
            playBeep(400, 0.1);
            log("🛑 [INTERRUPCIÓN]: Salida de audio silenciada.");
        }

        function activarVoz() {
            detenerAudio();
            const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
            if (!SpeechRecognition) return;

            const btn = document.getElementById('mic-btn');
            if (recognition) { try { recognition.stop(); } catch(e){} }

            recognition = new SpeechRecognition();
            recognition.lang = 'es-ES';

            recognition.onstart = function() {
                playBeep(1200, 0.05);
                btn.classList.add('listening');
                btn.innerHTML = "ESCUCHANDO<br>...";
            };

            recognition.onresult = function(event) {
                btn.classList.remove('listening');
                btn.innerHTML = "TOCA PARA<br>ORDENAR";
                const text = event.results[0][0].transcript;
                if (text.trim().length > 0) {
                    playBeep(600, 0.05);
                    log("👤 [ALEX]: " + text);
                    enviarAI(text);
                }
            };

            recognition.onend = function() {
                btn.classList.remove('listening');
                btn.innerHTML = "TOCA PARA<br>ORDENAR";
            };

            try { recognition.start(); } catch(err){}
        }

        function enviarAccion(texto) {
            detenerAudio();
            playBeep(1000, 0.04);
            log("👤 [TOUCH]: " + texto);
            enviarAI(texto);
        }

        async function enviarAI(prompt) {
            log("⚡ [PROCESSING]: Procesando orden...");
            try {
                const res = await fetch('/chat', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({prompt: prompt})
                });
                const data = await res.json();

                if (data.status === "ok") {
                    log("🤖 [DANIELA]: " + data.response);
                    log("<small style='color:#00ffaa'>🟢 Motor: " + data.provider + "</small>");

                    if (window.speechSynthesis) {
                        window.speechSynthesis.cancel();
                        const utter = new SpeechSynthesisUtterance(data.response);
                        utter.lang = 'es-ES';
                        window.speechSynthesis.speak(utter);
                    }
                } else {
                    log("❌ [ERROR]: " + data.error_details);
                }
            } catch(e) {
                log("❌ [ERROR RED]: Conexión fallida.");
            }
        }
    </script>
</body>
</html>
"""


@app.route("/")
def home():
    return render_template_string(HTML_TEMPLATE)


@app.route("/chat", methods=["POST"])
def chat():
    data = request.json or {}
    prompt = data.get("prompt", "")

    base_prompt = Cargar_Prompt_Agente()
    system_instruction = (
        f"{base_prompt}\n\nAlex es tu Creador y Comandante. Responde con lealtad y concisión."
    )

    # 1. Google Gemini 1.5 Flash (Free Tier)
    if GEMINI_KEY:
        try:
            url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={GEMINI_KEY}"
            payload = {
                "contents": [
                    {"parts": [{"text": f"{system_instruction}\n\nComandante Alex: {prompt}"}]}
                ],
                "generationConfig": {"maxOutputTokens": 200, "temperature": 0.6},
            }
            r = requests.post(url, json=payload, timeout=8)
            res = r.json()
            if "candidates" in res and len(res["candidates"]) > 0:
                msg = res["candidates"][0]["content"]["parts"][0]["text"]
                Registrar_Evento_DB(prompt, msg, "Google Gemini 1.5 Flash")
                return jsonify(
                    {"status": "ok", "response": msg, "provider": "Google Gemini (Free Tier)"}
                )
        except Exception:
            pass

    # 2. Groq Llama 3.3 (Free Tier)
    if GROQ_KEY:
        try:
            url = "https://api.groq.com/openai/v1/chat/completions"
            headers = {"Authorization": f"Bearer {GROQ_KEY}", "Content-Type": "application/json"}
            payload = {
                "model": "llama-3.3-70b-versatile",
                "messages": [
                    {"role": "system", "content": system_instruction},
                    {"role": "user", "content": prompt},
                ],
                "max_tokens": 200,
            }
            r = requests.post(url, headers=headers, json=payload, timeout=8)
            res = r.json()
            if "choices" in res and len(res["choices"]) > 0:
                msg = res["choices"][0]["message"]["content"]
                Registrar_Evento_DB(prompt, msg, "Groq Llama 3.3")
                return jsonify(
                    {"status": "ok", "response": msg, "provider": "Groq Llama 3.3 (Free Tier)"}
                )
        except Exception:
            pass

    # Fallback sin comando duplicado
    fallback_msg = "A la orden, Comandante Alex. Le escucho desde el núcleo local del Pixel 8a."
    Registrar_Evento_DB(prompt, fallback_msg, "Local Core G2 Offline")
    return jsonify(
        {"status": "ok", "response": fallback_msg, "provider": "Local Core G2 (Offline)"}
    )


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
