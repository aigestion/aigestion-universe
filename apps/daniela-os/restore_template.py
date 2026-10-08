import os

original_html = """<!DOCTYPE html>
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
            margin: 0;
            padding: 8px;
            background-color: var(--bg-color);
            color: #ffffff;
            font-family: 'Courier New', Courier, monospace;
            display: flex;
            flex-direction: column;
            height: 98vh;
            box-sizing: border-box;
            overflow: hidden;
            position: relative;
        }

        .hud-bar {
            display: flex;
            justify-content: space-between;
            align-items: center;
            background: var(--panel-bg);
            border: 1px solid var(--border-color);
            padding: 6px 12px;
            border-radius: 4px;
            font-size: 0.75rem;
            margin-bottom: 6px;
            box-shadow: 0 0 10px rgba(0, 255, 204, 0.2);
        }

        .viewport-container {
            position: relative;
            flex: 1.3;
            background: #000;
            border: 1px solid var(--border-color);
            border-radius: 4px;
            overflow: hidden;
            display: flex;
            justify-content: center;
            align-items: center;
        }

        .avatar-img {
            width: 100%;
            height: 100%;
            object-fit: cover;
            opacity: 0.85;
        }

        /* PIP MASTER ORIGINAL RESTAURADO */
        .floating-modal {
            position: absolute;
            top: 10px;
            right: 10px;
            width: 280px;
            height: 170px;
            background: var(--panel-bg);
            border: 1px solid var(--neon-pink);
            border-radius: 6px;
            box-shadow: 0 0 15px rgba(255, 0, 85, 0.4);
            display: flex;
            flex-direction: column;
            z-index: 999;
            overflow: hidden;
        }

        .modal-header {
            background: rgba(255, 0, 85, 0.25);
            padding: 4px 8px;
            font-size: 0.65rem;
            font-weight: bold;
            color: var(--neon-pink);
            display: flex;
            justify-content: space-between;
            align-items: center;
            border-bottom: 1px solid var(--neon-pink);
        }

        .modal-body {
            flex: 1;
            background: #000;
            display: flex;
            align-items: center;
            justify-content: center;
            position: relative;
        }

        video, canvas {
            width: 100%;
            height: 100%;
            object-fit: cover;
        }

        .chat-container {
            flex: 1;
            background: var(--panel-bg);
            border: 1px solid var(--border-color);
            border-radius: 4px;
            margin-top: 6px;
            padding: 8px;
            display: flex;
            flex-direction: column;
            overflow-y: auto;
        }

        .message {
            margin-bottom: 6px;
            font-size: 0.8rem;
            line-height: 1.2;
        }

        .daniela-msg { color: var(--neon-green); }
        .user-msg { color: var(--neon-amber); text-align: right; }

        .controls-bar {
            display: flex;
            gap: 6px;
            margin-top: 6px;
        }

        input[type="text"] {
            flex: 1;
            background: #080d14;
            border: 1px solid var(--border-color);
            color: #fff;
            padding: 6px 10px;
            border-radius: 4px;
            font-family: inherit;
            font-size: 0.8rem;
        }

        button {
            background: var(--neon-green);
            color: #000;
            border: none;
            padding: 6px 14px;
            font-weight: bold;
            cursor: pointer;
            border-radius: 4px;
            font-family: inherit;
            font-size: 0.8rem;
        }
    </style>
</head>
<body>

    <div class="hud-bar">
        <span>🟢 SOVEREIGN OS: ONLINE</span>
        <span>📍 NODE: TAILSCALE</span>
        <span style="color: var(--neon-pink);">PROTECTED 🔒</span>
    </div>

    <div class="viewport-container">
        <img src="/static/daniela_avatar.jpg" class="avatar-img" onerror="this.style.display='none'">

        <div class="floating-modal" id="pipModal">
            <div class="modal-header">
                <span>🎬 PIP MASTER</span>
                <span id="pipStatus" style="color:var(--neon-pink);">STANDBY</span>
            </div>
            <div class="modal-body" id="pipBody">
                <span id="pipPlaceholder" style="color:var(--neon-green); font-size:0.75rem;">Esperando selección...</span>
                <video id="webcamVideo" autoplay playsinline style="display:none;"></video>
                <canvas id="snapshotCanvas" style="display:none;"></canvas>
            </div>
        </div>
    </div>

    <div class="chat-container" id="chatBox">
        <div class="message daniela-msg">
            <b>Daniela:</b> Interfaz original restaurada. Escribe o di "enciende la cámara".
        </div>
    </div>

    <div class="controls-bar">
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
                    alert("Activa los permisos de cámara en tu navegador.");
                    return;
                }
            }

            video.srcObject = mediaStream;
            video.style.display = 'block';
            placeholder.style.display = 'none';
            status.innerText = 'LIVE';
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
                alert("La cámara no está encendida.");
                return;
            }

            canvas.width = video.videoWidth;
            canvas.height = video.videoHeight;
            const ctx = canvas.getContext('2d');
            ctx.drawImage(video, 0, 0, canvas.width, canvas.height);

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
    f.write(original_html)
with open("index.html", "w", encoding="utf-8") as f:
    f.write(original_html)

print("✅ Plantilla original cian neón restaurada con éxito.")
