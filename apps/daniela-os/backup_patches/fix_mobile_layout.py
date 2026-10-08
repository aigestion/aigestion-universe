import os

fit_html = """<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
    <title>Daniela OS Sovereign v10.0</title>
    <style>
        :root {
            --bg-color: #05070a;
            --neon-green: #00ffcc;
            --neon-pink: #ff0055;
            --neon-amber: #ffb700;
            --panel-bg: rgba(10, 15, 25, 0.92);
            --border-color: #00ffcc;
        }

        * { box-sizing: border-box; }

        body {
            margin: 0; padding: 4px; background-color: var(--bg-color); color: #fff;
            font-family: 'Courier New', Courier, monospace; display: flex; flex-direction: column;
            height: 100vh; overflow: hidden; position: relative;
        }

        /* Top HUD Bar */
        .hud-bar {
            display: flex; justify-content: space-between; align-items: center;
            background: var(--panel-bg); border: 1px solid var(--border-color);
            padding: 4px 8px; border-radius: 4px; font-size: 0.65rem; height: 26px;
        }

        /* Main Viewport Stage */
        .viewport-container {
            position: relative; height: 38vh; background: #000; border: 1px solid var(--border-color);
            border-radius: 4px; overflow: hidden; display: flex; justify-content: center; align-items: center;
            margin-top: 4px;
        }

        .avatar-img { width: 100%; height: 100%; object-fit: cover; opacity: 0.85; }

        /* PIP Master Modal */
        .floating-modal {
            position: absolute; top: 6px; right: 6px; width: 220px; height: 135px;
            background: var(--panel-bg); border: 1px solid var(--neon-pink); border-radius: 6px;
            box-shadow: 0 0 12px rgba(255, 0, 85, 0.4); display: flex; flex-direction: column; z-index: 999;
            overflow: hidden;
        }

        .modal-header {
            background: rgba(255, 0, 85, 0.25); padding: 3px 6px; font-size: 0.6rem; font-weight: bold;
            color: var(--neon-pink); display: flex; justify-content: space-between; align-items: center;
            border-bottom: 1px solid var(--neon-pink);
        }

        .pip-tools { display: flex; gap: 3px; }

        .pip-btn {
            background: rgba(0, 255, 204, 0.15); border: 1px solid var(--neon-green);
            color: var(--neon-green); font-size: 0.6rem; padding: 1px 4px; border-radius: 3px; cursor: pointer;
        }

        .modal-body {
            flex: 1; background: #000; display: flex; align-items: center; justify-content: center;
            position: relative;
        }

        video, canvas { width: 100%; height: 100%; object-fit: cover; }

        /* Chat Container Ajustado */
        .chat-container {
            flex: 1; background: var(--panel-bg); border: 1px solid var(--border-color);
            border-radius: 4px; margin-top: 4px; padding: 6px; display: flex; flex-direction: column; overflow-y: auto;
        }

        .message { margin-bottom: 4px; font-size: 0.75rem; line-height: 1.2; }
        .daniela-msg { color: var(--neon-green); }
        .user-msg { color: var(--neon-amber); text-align: right; }

        /* Action Buttons Row */
        .action-btns-row { display: flex; gap: 4px; margin-top: 4px; height: 32px; }

        .action-btn {
            flex: 1; background: rgba(10, 15, 25, 0.9); border: 1px solid var(--border-color);
            color: var(--neon-green); padding: 4px; font-size: 0.65rem; font-weight: bold;
            cursor: pointer; border-radius: 3px; display: flex; align-items: center; justify-content: center; gap: 4px;
        }

        /* Controls Input Bar */
        .controls-bar { display: flex; gap: 4px; margin-top: 4px; margin-bottom: 4px; align-items: center; height: 38px; }

        .icon-btn {
            width: 34px; height: 34px; background: rgba(10, 15, 25, 0.9);
            border: 1px solid var(--border-color); color: var(--neon-green); border-radius: 4px;
            cursor: pointer; display: flex; align-items: center; justify-content: center; font-weight: bold; font-size: 0.8rem;
        }

        input[type="text"] {
            flex: 1; height: 34px; background: #080d14; border: 1px solid var(--border-color);
            color: #fff; padding: 0 8px; border-radius: 4px; font-family: inherit; font-size: 0.75rem;
        }

        .send-btn {
            height: 34px; background: var(--neon-green); color: #000; border: none; padding: 0 12px;
            font-weight: bold; cursor: pointer; border-radius: 4px; font-family: inherit; font-size: 0.75rem;
        }

        /* Floating Mic Button */
        .floating-mic {
            position: absolute; bottom: 85px; right: 12px; width: 38px; height: 38px;
            border-radius: 50%; background: #000; border: 2px solid var(--neon-green);
            box-shadow: 0 0 10px var(--neon-green); display: flex; align-items: center;
            justify-content: center; cursor: pointer; z-index: 1000; color: var(--neon-green); font-size: 0.9rem;
        }
    </style>
</head>
<body>

    <!-- HUD Status -->
    <div class="hud-bar">
        <span>🟢 ONLINE</span>
        <span>📍 NODE: TAILSCALE</span>
        <span style="color: var(--neon-pink);">STATUS: ONLINE 🔒</span>
    </div>

    <!-- Main Viewport Stage -->
    <div class="viewport-container">
        <img src="/static/daniela_avatar.jpg" class="avatar-img" onerror="this.style.display='none'">

        <!-- PIP Master Modal -->
        <div class="floating-modal" id="pipModal">
            <div class="modal-header">
                <span>🎬 PIP MASTER</span>
                <div class="pip-tools">
                    <button class="pip-btn" onclick="startRearCamera()" title="Cámara">📷</button>
                    <button class="pip-btn" onclick="takeSnapshot()" title="Foto">👁️</button>
                    <button class="pip-btn" title="Stats">📊</button>
                    <button class="pip-btn" onclick="stopCamera()" title="Cerrar">🌐</button>
                </div>
            </div>
            <div class="modal-body" id="pipBody">
                <span id="pipPlaceholder" style="color:var(--neon-green); font-size:0.7rem;">Esperando selección...</span>
                <video id="webcamVideo" autoplay playsinline style="display:none;"></video>
                <canvas id="snapshotCanvas" style="display:none;"></canvas>
            </div>
        </div>
    </div>

    <!-- Chat Container -->
    <div class="chat-container" id="chatBox">
        <div class="message daniela-msg">
            <b>Daniela:</b> Diseño ajustado a pantalla completa. Todos los botones visibles.
        </div>
    </div>

    <!-- Action Buttons Row -->
    <div class="action-btns-row">
        <button class="action-btn" onclick="clearChat()">🧹 LIMPIAR CHAT</button>
        <button class="action-btn">🎙️ MODALIDAD AUDIO</button>
    </div>

    <!-- Controls Input Bar -->
    <div class="controls-bar">
        <button class="icon-btn">+</button>
        <button class="icon-btn" onclick="startRearCamera()">📷</button>
        <input type="text" id="userInput" placeholder="Habla con Daniela..." onkeydown="if(event.key==='Enter') sendMessage()">
        <button class="send-btn" onclick="sendMessage()">ENVIAR</button>
    </div>

    <!-- Floating Mic Button -->
    <div class="floating-mic">🎙️</div>

    <script>
        let mediaStream = null;

        async function startRearCamera() {
            const video = document.getElementById('webcamVideo');
            const placeholder = document.getElementById('pipPlaceholder');
            const canvas = document.getElementById('snapshotCanvas');

            canvas.style.display = 'none';

            try {
                mediaStream = await navigator.mediaDevices.getUserMedia({
                    video: { facingMode: { exact: "environment" } },
                    audio: false
                });
            } catch (err) {
                try {
                    mediaStream = await navigator.mediaDevices.getUserMedia({
                        video: { facingMode: "environment" },
                        audio: false
                    });
                } catch(e) {
                    alert("Acepta los permisos de cámara en tu navegador.");
                    return;
                }
            }

            video.srcObject = mediaStream;
            video.style.display = 'block';
            placeholder.style.display = 'none';
        }

        function stopCamera() {
            const video = document.getElementById('webcamVideo');
            const placeholder = document.getElementById('pipPlaceholder');

            if (mediaStream) {
                mediaStream.getTracks().forEach(track => track.stop());
                mediaStream = null;
            }
            video.style.display = 'none';
            placeholder.style.display = 'inline';
        }

        function takeSnapshot() {
            const video = document.getElementById('webcamVideo');
            const canvas = document.getElementById('snapshotCanvas');

            if (video.style.display === 'none' || !mediaStream) {
                alert("Primero activa la cámara.");
                return;
            }

            canvas.width = video.videoWidth;
            canvas.height = video.videoHeight;
            const ctx = canvas.getContext('2d');
            ctx.drawImage(video, 0, 0, canvas.width, canvas.height);

            video.style.display = 'none';
            canvas.style.display = 'block';
        }

        function clearChat() {
            document.getElementById('chatBox').innerHTML = '<div class="message daniela-msg"><b>Daniela:</b> Chat limpiado.</div>';
        }

        function sendMessage() {
            const input = document.getElementById('userInput');
            const chatBox = document.getElementById('chatBox');
            if (!input.value.trim()) return;

            const text = input.value;
            chatBox.innerHTML += `<div class="message user-msg"><b>Tú:</b> ${text}</div>`;
            input.value = '';
            chatBox.scrollTop = chatBox.scrollHeight;

            fetch('/api/chat', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({ message: text })
            })
            .then(res => res.json())
            .then(data => {
                chatBox.innerHTML += `<div class="message daniela-msg"><b>Daniela:</b> ${data.response}</div>`;
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
</html>
"""

os.makedirs("templates", exist_ok=True)
with open("templates/index.html", "w", encoding="utf-8") as f:
    f.write(fit_html)
with open("index.html", "w", encoding="utf-8") as f:
    f.write(fit_html)

print("✅ Maquetación adaptada perfectamente a pantalla móvil.")
