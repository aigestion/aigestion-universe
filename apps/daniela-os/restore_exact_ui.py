import os

exact_html = """<!DOCTYPE html>
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
            --neon-amber: #ffb700;
            --panel-bg: rgba(10, 15, 25, 0.92);
            --border-color: #00ffcc;
        }

        body {
            margin: 0; padding: 6px; background-color: var(--bg-color); color: #fff;
            font-family: 'Courier New', Courier, monospace; display: flex; flex-direction: column;
            height: 98vh; box-sizing: border-box; overflow: hidden; position: relative;
        }

        /* Top HUD Bar */
        .hud-bar {
            display: flex; justify-content: space-between; align-items: center;
            background: var(--panel-bg); border: 1px solid var(--border-color);
            padding: 4px 8px; border-radius: 4px; font-size: 0.65rem; margin-bottom: 6px;
        }

        /* Main Viewport Stage */
        .viewport-container {
            position: relative; flex: 1.2; background: #000; border: 1px solid var(--border-color);
            border-radius: 4px; overflow: hidden; display: flex; justify-content: center; align-items: center;
        }

        .avatar-img { width: 100%; height: 100%; object-fit: cover; opacity: 0.85; }

        /* PIP Master Modal */
        .floating-modal {
            position: absolute; top: 10px; right: 10px; width: 270px; height: 170px;
            background: var(--panel-bg); border: 1px solid var(--neon-pink); border-radius: 6px;
            box-shadow: 0 0 15px rgba(255, 0, 85, 0.4); display: flex; flex-direction: column; z-index: 999;
            overflow: hidden;
        }

        .modal-header {
            background: rgba(255, 0, 85, 0.25); padding: 4px 8px; font-size: 0.65rem; font-weight: bold;
            color: var(--neon-pink); display: flex; justify-content: space-between; align-items: center;
            border-bottom: 1px solid var(--neon-pink);
        }

        .pip-tools { display: flex; gap: 4px; }

        .pip-btn {
            background: rgba(0, 255, 204, 0.15); border: 1px solid var(--neon-green);
            color: var(--neon-green); font-size: 0.65rem; padding: 2px 6px; border-radius: 3px; cursor: pointer;
        }

        .modal-body {
            flex: 1; background: #000; display: flex; align-items: center; justify-content: center;
            position: relative;
        }

        video, canvas { width: 100%; height: 100%; object-fit: cover; }

        /* Chat Container */
        .chat-container {
            flex: 1; background: var(--panel-bg); border: 1px solid var(--border-color);
            border-radius: 4px; margin-top: 6px; padding: 8px; display: flex; flex-direction: column; overflow-y: auto;
        }

        .message { margin-bottom: 6px; font-size: 0.8rem; line-height: 1.2; }
        .daniela-msg { color: var(--neon-green); }
        .user-msg { color: var(--neon-amber); text-align: right; }

        /* Action Buttons Row */
        .action-btns-row { display: flex; gap: 6px; margin-top: 6px; }

        .action-btn {
            flex: 1; background: rgba(10, 15, 25, 0.9); border: 1px solid var(--border-color);
            color: var(--neon-green); padding: 6px; font-size: 0.7rem; font-weight: bold;
            cursor: pointer; border-radius: 3px; display: flex; align-items: center; justify-content: center; gap: 4px;
        }

        /* Controls Input Bar */
        .controls-bar { display: flex; gap: 6px; margin-top: 6px; align-items: center; }

        .icon-btn {
            width: 36px; height: 36px; background: rgba(10, 15, 25, 0.9);
            border: 1px solid var(--border-color); color: var(--neon-green); border-radius: 4px;
            cursor: pointer; display: flex; align-items: center; justify-content: center; font-weight: bold;
        }

        input[type="text"] {
            flex: 1; background: #080d14; border: 1px solid var(--border-color);
            color: #fff; padding: 8px; border-radius: 4px; font-family: inherit; font-size: 0.8rem;
        }

        .send-btn {
            background: var(--neon-green); color: #000; border: none; padding: 8px 14px;
            font-weight: bold; cursor: pointer; border-radius: 4px; font-family: inherit; font-size: 0.8rem;
        }

        /* Floating Mic Button */
        .floating-mic {
            position: absolute; bottom: 60px; right: 15px; width: 42px; height: 42px;
            border-radius: 50%; background: #000; border: 2px solid var(--neon-green);
            box-shadow: 0 0 12px var(--neon-green); display: flex; align-items: center;
            justify-content: center; cursor: pointer; z-index: 1000; color: var(--neon-green);
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
                    <button class="pip-btn" onclick="startRearCamera()" title="Cámara Posterior">📷</button>
                    <button class="pip-btn" onclick="takeSnapshot()" title="Captura de Foto">👁️</button>
                    <button class="pip-btn" title="Métricas">📊</button>
                    <button class="pip-btn" onclick="stopCamera()" title="Cerrar Transmisión">🌐</button>
                </div>
            </div>
            <div class="modal-body" id="pipBody">
                <span id="pipPlaceholder" style="color:var(--neon-green); font-size:0.75rem;">Esperando selección...</span>
                <video id="webcamVideo" autoplay playsinline style="display:none;"></video>
                <canvas id="snapshotCanvas" style="display:none;"></canvas>
            </div>
        </div>
    </div>

    <!-- Chat Container -->
    <div class="chat-container" id="chatBox">
        <div class="message daniela-msg">
            <b>Daniela:</b> Plantilla original restaurada con todos los botones.
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
    f.write(exact_html)
with open("index.html", "w", encoding="utf-8") as f:
    f.write(exact_html)

print("✅ Plantilla idéntica restaurada con el 100% de la botonería.")
