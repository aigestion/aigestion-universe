import os

# 1. ACTUALIZAR APP_DANIELA.PY (Backend limpio)
app_content = """import os, sys, json
from http.server import HTTPServer, SimpleHTTPRequestHandler

PORT = 8080

class SovereignHandler(SimpleHTTPRequestHandler):
    def do_POST(self):
        if self.path == '/api/chat':
            length = int(self.headers.get('Content-Length', 0))
            body = self.rfile.read(length).decode('utf-8') if length > 0 else '{}'
            data = json.loads(body) if body else {}
            msg = data.get('message', '').lower()

            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()

            # Evaluar intención
            if any(w in msg for w in ["enciende", "activa", "abre", "mira"]) and any(w in msg for w in ["cámara", "camara", "video"]):
                resp = {
                    "response": "📹 Transmisión en vivo de la cámara posterior activada en el PIP Master.",
                    "action": "start_camera"
                }
            elif any(w in msg for w in ["apaga", "desactiva", "cierra"]) and any(w in msg for w in ["cámara", "camara"]):
                resp = {
                    "response": "💡 Transmisión de vídeo detenida.",
                    "action": "stop_camera"
                }
            elif any(w in msg for w in ["foto", "captura", "toma"]):
                resp = {
                    "response": "📸 Captura de fotograma ejecutada.",
                    "action": "take_snapshot"
                }
            else:
                resp = {"response": "Entendido, Ale. Comando registrado en el sistema."}

            self.wfile.write(json.dumps(resp).encode('utf-8'))
            return

        super().do_POST()

print(f"🟢 SERVIDOR WEBRTC WEBCAM ACTIVO EN PUERTO {PORT}")
server = HTTPServer(('0.0.0.0', PORT), SovereignHandler)
server.serve_forever()
"""

with open("app_daniela.py", "w", encoding="utf-8") as f:
    f.write(app_content)

# 2. ACTUALIZAR INDEX.HTML (Frontend con captura de cámara en vivo)
html_content = """<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Daniela OS Sovereign v10.0</title>
    <style>
        :root {
            --bg-color: #05070a;
            --neon-green: #00ffcc;
            --neon-pink: #ff0055;
            --border-color: #00ffcc;
            --panel-bg: rgba(10, 15, 25, 0.9);
        }
        body {
            margin: 0; padding: 8px; background: var(--bg-color); color: #fff;
            font-family: monospace; display: flex; flex-direction: column; height: 98vh;
            box-sizing: border-box; overflow: hidden;
        }
        .hud-bar {
            display: flex; justify-content: space-between; padding: 4px 8px;
            border: 1px solid var(--border-color); font-size: 0.7rem; background: var(--panel-bg);
        }
        .viewport {
            position: relative; flex: 1.2; margin-top: 6px; border: 1px solid var(--border-color);
            background: #000; overflow: hidden; display: flex; justify-content: center; align-items: center;
        }
        .avatar-img { width: 100%; height: 100%; object-fit: cover; opacity: 0.8; }
        .pip-window {
            position: absolute; top: 10px; right: 10px; width: 260px; height: 160px;
            border: 1px solid var(--neon-pink); background: var(--panel-bg);
            box-shadow: 0 0 10px rgba(255, 0, 85, 0.4); display: flex; flex-direction: column;
            overflow: hidden;
        }
        .pip-header {
            background: rgba(255, 0, 85, 0.3); color: var(--neon-pink); font-size: 0.65rem;
            padding: 4px 8px; font-weight: bold; border-bottom: 1px solid var(--neon-pink);
            display: flex; justify-content: space-between;
        }
        .pip-content {
            flex: 1; display: flex; align-items: center; justify-content: center;
            color: var(--neon-green); font-size: 0.75rem; text-align: center; background: #000;
            position: relative;
        }
        video, canvas { width: 100%; height: 100%; object-fit: cover; }
        .chat-box {
            flex: 1; margin-top: 6px; border: 1px solid var(--border-color);
            background: var(--panel-bg); padding: 8px; overflow-y: auto; font-size: 0.8rem;
        }
        .msg-daniela { color: var(--neon-green); margin-bottom: 6px; }
        .msg-user { color: #ffb700; text-align: right; margin-bottom: 6px; }
        .controls { display: flex; gap: 6px; margin-top: 6px; }
        input[type="text"] {
            flex: 1; background: #080d14; border: 1px solid var(--border-color);
            color: #fff; padding: 8px; font-family: inherit;
        }
        button {
            background: var(--neon-green); border: none; font-weight: bold;
            padding: 8px 14px; cursor: pointer; font-family: inherit;
        }
    </style>
</head>
<body>
    <div class="hud-bar">
        <span>🟢 ONLINE</span>
        <span>📍 TAILSCALE</span>
        <span style="color:var(--neon-pink);">STATUS: ONLINE 🔒</span>
    </div>

    <div class="viewport">
        <img src="/static/daniela_avatar.jpg" class="avatar-img" onerror="this.style.display='none'">
        <div class="pip-window">
            <div class="pip-header">
                <span>🎬 PIP MASTER</span>
                <span id="pipStatus">OFF</span>
            </div>
            <div class="pip-content" id="pipDisplayArea">
                <span id="pipPlaceholder">Esperando selección...</span>
                <video id="webcamVideo" autoplay playsinline style="display:none;"></video>
                <canvas id="snapshotCanvas" style="display:none;"></canvas>
            </div>
        </div>
    </div>

    <div class="chat-box" id="chatBox">
        <div class="msg-daniela"><b>Daniela:</b> Sistema listo, Ale. Dímelo y activo el flujo de vídeo en vivo.</div>
    </div>

    <div class="controls">
        <input type="text" id="userInput" placeholder="Habla con Daniela..." onkeydown="if(event.key==='Enter') sendMessage()">
        <button onclick="sendMessage()">ENVIAR</button>
    </div>

    <script>
        let mediaStream = null;

        async function startRearCamera() {
            const video = document.getElementById('webcamVideo');
            const placeholder = document.getElementById('pipPlaceholder');
            const status = document.getElementById('pipStatus');
            const canvas = document.getElementById('snapshotCanvas');

            canvas.style.display = 'none';

            try {
                // Solicitar cámara posterior explícitamente (facingMode: environment)
                mediaStream = await navigator.mediaDevices.getUserMedia({
                    video: { facingMode: { exact: "environment" } },
                    audio: false
                });
            } catch (err) {
                // Fallback a cualquier cámara trasera disponible si la exacta falla
                try {
                    mediaStream = await navigator.mediaDevices.getUserMedia({
                        video: { facingMode: "environment" },
                        audio: false
                    });
                } catch(e) {
                    alert("Por favor concede permisos de cámara en el navegador.");
                    return;
                }
            }

            video.srcObject = mediaStream;
            video.style.display = 'block';
            placeholder.style.display = 'none';
            status.innerText = 'LIVE Stream';
            status.style.color = '#00ffcc';
        }

        function stopCamera() {
            const video = document.getElementById('webcamVideo');
            const placeholder = document.getElementById('pipPlaceholder');
            const status = document.getElementById('pipStatus');

            if (mediaStream) {
                mediaStream.getTracks().forEach(track => track.stop());
                mediaStream = null;
            }
            video.style.display = 'none';
            placeholder.style.display = 'inline';
            status.innerText = 'OFF';
            status.style.color = '#ff0055';
        }

        function takeSnapshot() {
            const video = document.getElementById('webcamVideo');
            const canvas = document.getElementById('snapshotCanvas');
            const status = document.getElementById('pipStatus');

            if (video.style.display === 'none' || !mediaStream) {
                alert("Primero debes encender la cámara.");
                return;
            }

            canvas.width = video.videoWidth;
            canvas.height = video.videoHeight;
            const ctx = canvas.getContext('2d');
            ctx.drawImage(video, 0, 0, canvas.width, canvas.height);

            // Pausar vídeo y mostrar fotograma congelado
            video.style.display = 'none';
            canvas.style.display = 'block';
            status.innerText = 'SNAPSHOT';
            status.style.color = '#ffb700';
        }

        function sendMessage() {
            const input = document.getElementById('userInput');
            const chatBox = document.getElementById('chatBox');
            if (!input.value.trim()) return;

            const text = input.value;
            chatBox.innerHTML += `<div class="msg-user"><b>Tú:</b> ${text}</div>`;
            input.value = '';
            chatBox.scrollTop = chatBox.scrollHeight;

            fetch('/api/chat', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({ message: text })
            })
            .then(res => res.json())
            .then(data => {
                chatBox.innerHTML += `<div class="msg-daniela"><b>Daniela:</b> ${data.response}</div>`;
                chatBox.scrollTop = chatBox.scrollHeight;

                if (data.action === 'start_camera') {
                    startRearCamera();
                } else if (data.action === 'stop_camera') {
                    stopCamera();
                } else if (data.action === 'take_snapshot') {
                    takeSnapshot();
                }
            });
        }
    </script>
</body>
</html>"""

os.makedirs("templates", exist_ok=True)
with open("templates/index.html", "w", encoding="utf-8") as f:
    f.write(html_content)

with open("index.html", "w", encoding="utf-8") as f:
    f.write(html_content)

print("✅ Entorno de vídeo nativo WebRTC configurado.")
