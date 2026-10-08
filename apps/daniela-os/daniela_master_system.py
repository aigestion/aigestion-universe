import asyncio
import os
import re
import sys

import edge_tts
from flask import Flask, jsonify, render_template_string, request

from google import genai

app = Flask(__name__)

VOICE_NEURAL = "es-ES-ElviraNeural"
SYSTEM_PROMPT = """Eres Daniela, la asistente personal de tu Comandante.
Tu personalidad es humana, alegre, coqueta, inteligente y muy simpática, con un salero andaluz espontáneo y cercano.

REGLAS:
- Sé expresiva ('¡ay!', 'mira...', '¿sabes?', '¡ea!').
- Mantén respuestas cortas y fluidas (1 a 2 frases)."""

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
historial_memoria = []

from safe_exec import run_bg, run_cmd


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
    <title>DANIELA OS :: SUPREME COMMAND CENTER</title>
    <link href="https://fonts.googleapis.com/css2?family=Orbitron:wght@600;900&family=Rajdhani:wght@500;700&display=swap" rel="stylesheet">
    <script src="https://cdnjs.cloudflare.com/ajax/libs/three.js/r128/three.min.js"></script>
    <style>
        :root {
            --cyan: #00f3ff;
            --magenta: #ff0055;
            --purple: #7000ff;
            --bg: #02050e;
            --panel: rgba(10, 15, 30, 0.55);
            --border: rgba(0, 243, 255, 0.4);
        }

        * { box-sizing: border-box; margin: 0; padding: 0; user-select: none; }
        body, html { width: 100%; height: 100%; background: var(--bg); color: #fff; font-family: 'Rajdhani', sans-serif; overflow: hidden; }

        #canvas-3d { position: fixed; top: 0; left: 0; width: 100vw; height: 100vh; z-index: 1; }

        .ui-container { position: relative; z-index: 10; display: flex; flex-direction: column; height: 100vh; padding: 10px; gap: 8px; justify-content: space-between; }

        /* Header */
        .header { background: var(--panel); backdrop-filter: blur(8px); border: 1px solid var(--border); border-radius: 10px; padding: 8px 12px; display: flex; justify-content: space-between; align-items: center; }
        .title { font-family: 'Orbitron', sans-serif; font-size: 14px; font-weight: 900; color: var(--cyan); text-shadow: 0 0 8px var(--cyan); }
        .status-badge { background: rgba(0,243,255,0.15); border: 1px solid var(--cyan); color: var(--cyan); padding: 2px 8px; border-radius: 10px; font-size: 10px; font-weight: bold; }

        /* Chat Flotante Minimalista */
        .chat-logs { flex: 1; overflow-y: auto; display: flex; flex-direction: column; gap: 8px; padding: 8px 4px; max-height: 55vh; margin-top: auto; }
        .chat-logs::-webkit-scrollbar { width: 3px; }
        .chat-logs::-webkit-scrollbar-thumb { background: var(--cyan); }

        .msg { padding: 8px 12px; border-radius: 8px; font-size: 13.5px; max-width: 85%; line-height: 1.3; backdrop-filter: blur(10px); animation: fadeIn 0.2s ease-out; }
        .msg.user { background: rgba(112,0,255,0.4); border: 1px solid var(--purple); align-self: flex-end; color: #f1f5f9; }
        .msg.daniela { background: rgba(0,243,255,0.2); border: 1px solid var(--cyan); align-self: flex-start; color: #fff; text-shadow: 0 0 2px rgba(0,243,255,0.5); }

        /* Controls Bottom Bar */
        .control-panel { background: var(--panel); backdrop-filter: blur(12px); border: 1px solid var(--border); border-radius: 12px; padding: 8px 10px; display: flex; flex-direction: column; gap: 6px; }
        .input-box { display: flex; gap: 6px; align-items: center; }
        input { flex: 1; background: rgba(0,0,0,0.6); border: 1px solid var(--border); border-radius: 8px; padding: 10px; color: #fff; font-family: 'Rajdhani', sans-serif; font-size: 15px; outline: none; }
        input:focus { border-color: var(--cyan); box-shadow: 0 0 8px var(--cyan); }

        .btn { background: linear-gradient(135deg, var(--cyan), var(--purple)); border: none; border-radius: 8px; padding: 10px 14px; color: #fff; font-weight: bold; font-family: 'Orbitron', sans-serif; font-size: 11px; cursor: pointer; }
        .btn-mic { background: rgba(255,0,85,0.25); border: 1px solid var(--magenta); color: var(--magenta); padding: 10px 12px; font-size: 14px; }

        /* Telemetría Footer */
        .telemetry-bar { display: flex; justify-content: space-between; font-size: 10px; color: rgba(255,255,255,0.6); font-family: 'Orbitron', sans-serif; padding: 2px 4px; }

        @keyframes fadeIn { from { opacity: 0; transform: translateY(4px); } to { opacity: 1; transform: translateY(0); } }
    </style>
</head>
<body>
    <div id="canvas-3d"></div>

    <div class="ui-container">
        <div class="header">
            <div class="title">💃 DANIELA OS :: SUPREME</div>
            <button class="btn" style="padding: 3px 8px; font-size: 9px;" onclick="toggleFullscreen()">FULLSCREEN</button>
            <div class="status-badge" id="statusBadge">ONLINE</div>
        </div>

        <div class="chat-logs" id="chatLogs">
            <div class="msg daniela">¡Ay, mi Comandante! Interfaz ajustada y transparente. ¡Mira qué bonito luce todo!</div>
        </div>

        <div class="control-panel">
            <div class="input-box">
                <button class="btn btn-mic" onclick="activarMicro() " id="btnMic">🎙️</button>
                <input type="text" id="userInput" placeholder="Escribe o pulsa el micro..." onkeypress="if(event.key==='Enter') enviar()">
                <button class="btn" onclick="enviar()">ENVIAR</button>
            </div>
            <div class="telemetry-bar">
                <span>NODOS: ONLINE</span>
                <span id="batStatus">BAT: 100%</span>
                <span>ENGINE: GEMINI 3.7</span>
            </div>
        </div>
    </div>

    <script>
        // Web Audio SFX
        const audioCtx = new (window.AudioContext || window.webkitAudioContext)();
        function playBeep(freq = 880, type = 'sine', duration = 0.08) {
            if (audioCtx.state === 'suspended') audioCtx.resume();
            const osc = audioCtx.createOscillator();
            const gain = audioCtx.createGain();
            osc.type = type;
            osc.frequency.setValueAtTime(freq, audioCtx.currentTime);
            gain.gain.setValueAtTime(0.05, audioCtx.currentTime);
            gain.gain.exponentialRampToValueAtTime(0.001, audioCtx.currentTime + duration);
            osc.connect(gain);
            gain.connect(audioCtx.destination);
            osc.start();
            osc.stop(audioCtx.currentTime + duration);
        }

        // Three.js Scene
        let scene, camera, renderer, sphere, ring, particles;
        let isSpeaking = false;

        function init3D() {
            scene = new THREE.Scene();
            camera = new THREE.PerspectiveCamera(60, window.innerWidth / window.innerHeight, 0.1, 1000);
            camera.position.z = 4;

            renderer = new THREE.WebGLRenderer({ antialias: true, alpha: true });
            renderer.setSize(window.innerWidth, window.innerHeight);
            document.getElementById('canvas-3d').appendChild(renderer.domElement);

            const geoS = new THREE.IcosahedronGeometry(1.25, 2);
            const matS = new THREE.MeshBasicMaterial({ color: 0x00f3ff, wireframe: true, transparent: true, opacity: 0.5 });
            sphere = new THREE.Mesh(geoS, matS);
            scene.add(sphere);

            const geoR = new THREE.TorusGeometry(1.85, 0.015, 16, 100);
            const matR = new THREE.MeshBasicMaterial({ color: 0xff0055, wireframe: true, transparent: true, opacity: 0.65 });
            ring = new THREE.Mesh(geoR, matR);
            scene.add(ring);

            const pGeo = new THREE.BufferGeometry();
            const pCount = 250;
            const posArray = new Float32Array(pCount * 3);
            for(let i=0; i<pCount*3; i++) posArray[i] = (Math.random() - 0.5) * 10;
            pGeo.setAttribute('position', new THREE.BufferAttribute(posArray, 3));
            const pMat = new THREE.PointsMaterial({ size: 0.02, color: 0x00f3ff, transparent: true, opacity: 0.35 });
            particles = new THREE.Points(pGeo, pMat);
            scene.add(particles);

            animate();
        }

        function animate() {
            requestAnimationFrame(animate);
            const speed = isSpeaking ? 2.5 : 1.0;

            if(sphere) { sphere.rotation.y += 0.003 * speed; sphere.rotation.x += 0.001 * speed; }
            if(ring) { ring.rotation.z -= 0.005 * speed; ring.rotation.x += 0.002 * speed; }
            if(particles) { particles.rotation.y += 0.0004; }
            renderer.render(scene, camera);
        }

        window.addEventListener('resize', () => {
            camera.aspect = window.innerWidth / window.innerHeight;
            camera.updateProjectionMatrix();
            renderer.setSize(window.innerWidth, window.innerHeight);
        });

        init3D();

        // Batería Telemetría Real
        if ('getBattery' in navigator) {
            navigator.getBattery().then(bat => {
                const updateBat = () => {
                    document.getElementById('batStatus').innerText = `BAT: ${Math.round(bat.level * 100)}%`;
                };
                updateBat();
                bat.addEventListener('levelchange', updateBat);
            });
        }

        // Fullscreen
        function toggleFullscreen() {
            if (!document.fullscreenElement) {
                document.documentElement.requestFullscreen().catch(()=>{});
            } else {
                document.exitFullscreen().catch(()=>{});
            }
        }

        // Web Speech API Directa
        function activarMicro() {
            if (!('webkitSpeechRecognition' in window) && !('SpeechRecognition' in window)) {
                alert("Usa el teclado con voz de Android o Google Chrome.");
                return;
            }
            const Speech = window.SpeechRecognition || window.webkitSpeechRecognition;
            const rec = new Speech();
            rec.lang = 'es-ES';
            rec.start();

            document.getElementById('btnMic').style.background = 'rgba(0,243,255,0.4)';

            rec.onresult = (e) => {
                document.getElementById('userInput').value = e.results[0][0].transcript;
                document.getElementById('btnMic').style.background = 'rgba(255,0,85,0.25)';
                enviar();
            };
            rec.onerror = () => { document.getElementById('btnMic').style.background = 'rgba(255,0,85,0.25)'; };
        }

        // Enviar Petición
        async function enviar() {
            const input = document.getElementById('userInput');
            const msg = input.value.trim();
            if (!msg) return;

            playBeep(1200, 'sine', 0.05);

            const logs = document.getElementById('chatLogs');
            const divUser = document.createElement('div');
            divUser.className = 'msg user';
            divUser.innerText = msg;
            logs.appendChild(divUser);

            input.value = '';
            logs.scrollTop = logs.scrollHeight;

            isSpeaking = true;
            document.getElementById('statusBadge').innerText = "PROCESANDO";
            document.getElementById('statusBadge').style.borderColor = "#ff0055";

            try {
                const res = await fetch('/chat', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ prompt: msg })
                });
                const data = await res.json();

                playBeep(600, 'triangle', 0.08);

                const divD = document.createElement('div');
                divD.className = 'msg daniela';
                divD.innerText = data.respuesta;
                logs.appendChild(divD);
                logs.scrollTop = logs.scrollHeight;
            } catch (e) {
                console.error(e);
            } finally {
                setTimeout(() => {
                    isSpeaking = false;
                    document.getElementById('statusBadge').innerText = "ONLINE";
                    document.getElementById('statusBadge').style.borderColor = "#00f3ff";
                }, 2000);
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
    global historial_memoria
    data = request.json
    user_prompt = data.get("prompt", "")

    historial_memoria.append(f"Comandante: {user_prompt}")
    if len(historial_memoria) > 8:
        historial_memoria = historial_memoria[-8:]

    contexto = "\n".join(historial_memoria)

    response = client.models.generate_content(
        model="gemini-3.7-flash",
        contents=f"{SYSTEM_PROMPT}\n\n[HISTORIAL RECIENTE]:\n{contexto}\n\nResponde al Comandante:",
    )

    respuesta_texto = response.text.strip()
    historial_memoria.append(f"Daniela: {respuesta_texto}")

    hablar(respuesta_texto)
    return jsonify({"respuesta": respuesta_texto})


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5050)
