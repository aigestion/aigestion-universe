import asyncio
import os
import re
import sys

import edge_tts
from flask import Flask, jsonify, render_template_string, request

from google import genai

from safe_exec import run_bg, run_cmd

app = Flask(__name__)

VOICE_NEURAL = "es-ES-ElviraNeural"
SYSTEM_PROMPT = """Eres Daniela, la asistente personal de tu Comandante.
Tu personalidad es humana, alegre, coqueta, inteligente y muy simpática, con un salero andaluz espontáneo y cercano.
REGLAS: Sé expresiva ('¡ay!', 'mira...', '¿sabes?'). Respuestas cortas y fluidas (1 a 2 frases)."""

api_key = os.getenv("GEMINI_API_KEY")
if not api_key and os.path.exists(".env"):
    with open(".env") as f:
        for line in f:
            if line.startswith("GEMINI_API_KEY="):
                api_key = line.split("=", 1)[1].strip().strip('"').strip("'")

if not api_key:
    print("❌ Error: GEMINI_API_KEY no encontrada.")
    sys.exit(1)

client = genai.Client(api_key=api_key)


def detener_audio():
    run_cmd(["pkill", "-9", "mpv"])


def limpiar_texto(texto):
    return re.sub(r"[<>{}\[\]\\]", "", texto).strip()


async def generar_audio(texto):
    detener_audio()
    output_file = "daniela_voice.mp3"
    texto_limpio = limpiar_texto(texto)
    communicate = edge_tts.Communicate(texto_limpio, VOICE_NEURAL, rate="+8%", pitch="+3Hz")
    await communicate.save(output_file)
    run_bg(["mpv", "--really-quiet", "daniela_voice.mp3"])


def hablar(texto):
    asyncio.run(generar_audio(texto))


HTML_TEMPLATE = """<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
    <title>DANIELA OS :: PREMIUM CENTER</title>
    <link href="https://fonts.googleapis.com/css2?family=Orbitron:wght@600;900&family=Rajdhani:wght@500;700&display=swap" rel="stylesheet">
    <script src="https://cdnjs.cloudflare.com/ajax/libs/three.js/r128/three.min.js"></script>
    <style>
        :root {
            --cyan: #00f3ff;
            --magenta: #ff0055;
            --purple: #7000ff;
            --bg: #030712;
            --panel: rgba(15, 23, 42, 0.85);
            --border: rgba(0, 243, 255, 0.35);
        }

        * { box-sizing: border-box; margin: 0; padding: 0; user-select: none; }
        body, html { width: 100%; height: 100%; background: var(--bg); color: #fff; font-family: 'Rajdhani', sans-serif; overflow: hidden; }

        #canvas-3d { position: fixed; top: 0; left: 0; width: 100vw; height: 100vh; z-index: 1; }

        .ui-container { position: relative; z-index: 10; display: flex; flex-direction: column; height: 100vh; padding: 12px; gap: 10px; }

        .header { background: var(--panel); backdrop-filter: blur(10px); border: 1px solid var(--border); border-radius: 10px; padding: 10px 14px; display: flex; justify-content: space-between; align-items: center; }
        .title { font-family: 'Orbitron', sans-serif; font-size: 15px; font-weight: 900; color: var(--cyan); text-shadow: 0 0 10px var(--cyan); }
        .badge { background: rgba(0,243,255,0.15); border: 1px solid var(--cyan); color: var(--cyan); padding: 3px 8px; border-radius: 12px; font-size: 11px; font-weight: bold; }

        .chat-panel { flex: 1; background: var(--panel); backdrop-filter: blur(10px); border: 1px solid var(--border); border-radius: 10px; padding: 12px; display: flex; flex-direction: column; overflow: hidden; }
        .chat-logs { flex: 1; overflow-y: auto; display: flex; flex-direction: column; gap: 8px; padding-right: 4px; }

        .msg { padding: 8px 12px; border-radius: 8px; font-size: 14px; max-width: 88%; line-height: 1.3; }
        .msg.user { background: rgba(112,0,255,0.3); border: 1px solid var(--purple); align-self: flex-end; color: #f1f5f9; }
        .msg.daniela { background: rgba(0,243,255,0.2); border: 1px solid var(--cyan); align-self: flex-start; color: #fff; }

        .input-box { display: flex; gap: 8px; margin-top: 10px; }
        input { flex: 1; background: rgba(0,0,0,0.7); border: 1px solid var(--border); border-radius: 8px; padding: 10px 12px; color: #fff; font-family: 'Rajdhani', sans-serif; font-size: 15px; outline: none; }
        input:focus { border-color: var(--cyan); }
        button { background: linear-gradient(135deg, var(--cyan), var(--purple)); border: none; border-radius: 8px; padding: 0 16px; color: #fff; font-weight: bold; font-family: 'Orbitron', sans-serif; font-size: 12px; }
    </style>
</head>
<body>
    <div id="canvas-3d"></div>

    <div class="ui-container">
        <div class="header">
            <div class="title">💃 DANIELA OS v9.5</div>
            <div class="badge">ONLINE</div>
        </div>

        <div class="chat-panel">
            <div class="chat-logs" id="chatLogs">
                <div class="msg daniela">¡Ay, mi Comandante! Ahora sí que estamos en vivo y con la interfaz bien cargada. ¿Qué se te ofrece hoy, guapo?</div>
            </div>
            <div class="input-box">
                <input type="text" id="userInput" placeholder="Escribe o dicta con el micrófono..." onkeypress="if(event.key==='Enter') enviar()">
                <button onclick="enviar()">ENVIAR</button>
            </div>
        </div>
    </div>

    <script>
        let scene, camera, renderer, sphere, ring;

        function init3D() {
            scene = new THREE.Scene();
            camera = new THREE.PerspectiveCamera(60, window.innerWidth / window.innerHeight, 0.1, 1000);
            camera.position.z = 4;

            renderer = new THREE.WebGLRenderer({ antialias: true, alpha: true });
            renderer.setSize(window.innerWidth, window.innerHeight);
            document.getElementById('canvas-3d').appendChild(renderer.domElement);

            const geoS = new THREE.IcosahedronGeometry(1.2, 2);
            const matS = new THREE.MeshBasicMaterial({ color: 0x00f3ff, wireframe: true, transparent: true, opacity: 0.4 });
            sphere = new THREE.Mesh(geoS, matS);
            scene.add(sphere);

            const geoR = new THREE.TorusGeometry(1.8, 0.015, 16, 100);
            const matR = new THREE.MeshBasicMaterial({ color: 0xff0055, wireframe: true, transparent: true, opacity: 0.6 });
            ring = new THREE.Mesh(geoR, matR);
            scene.add(ring);

            animate();
        }

        function animate() {
            requestAnimationFrame(animate);
            if(sphere) { sphere.rotation.y += 0.004; sphere.rotation.x += 0.002; }
            if(ring) { ring.rotation.z -= 0.006; ring.rotation.x += 0.003; }
            renderer.render(scene, camera);
        }

        window.addEventListener('resize', () => {
            camera.aspect = window.innerWidth / window.innerHeight;
            camera.updateProjectionMatrix();
            renderer.setSize(window.innerWidth, window.innerHeight);
        });

        init3D();

        async function enviar() {
            const input = document.getElementById('userInput');
            const msg = input.value.trim();
            if (!msg) return;

            const logs = document.getElementById('chatLogs');

            const divUser = document.createElement('div');
            divUser.className = 'msg user';
            divUser.innerText = msg;
            logs.appendChild(divUser);

            input.value = '';
            logs.scrollTop = logs.scrollHeight;

            try {
                const res = await fetch('/chat', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ prompt: msg })
                });
                const data = await res.json();

                const divD = document.createElement('div');
                divD.className = 'msg daniela';
                divD.innerText = data.respuesta;
                logs.appendChild(divD);
                logs.scrollTop = logs.scrollHeight;
            } catch (e) {
                console.error(e);
            }
        }
    </script>
</body>
</html>"""


@app.route("/")
def home():
    return render_template_string(HTML_TEMPLATE)


@app.route("/chat", methods=["POST"])
def chat():
    data = request.json
    user_prompt = data.get("prompt", "")

    response = client.models.generate_content(
        model="gemini-3.7-flash", contents=f"{SYSTEM_PROMPT}\n\nComandante dice: {user_prompt}"
    )

    respuesta_texto = response.text.strip()
    hablar(respuesta_texto)
    return jsonify({"respuesta": respuesta_texto})


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5050)
