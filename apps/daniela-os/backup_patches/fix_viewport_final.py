fit_ui = """<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
    <title>Daniela OS Sovereign</title>
    <style>
        :root { --bg: #05070a; --green: #00ffcc; --pink: #ff0055; }
        * { box-sizing: border-box; }

        html, body {
            margin: 0; padding: 4px; background: var(--bg); color: #fff; font-family: monospace;
            height: 100dvh; width: 100vw; display: flex; flex-direction: column; overflow: hidden;
        }

        .hud { border: 1px solid var(--green); padding: 3px 6px; font-size: 0.6rem; background: #0a0f19; display: flex; justify-content: space-between; flex-shrink: 0; }

        .viewport { position: relative; height: 32vh; border: 1px solid var(--green); background: #000; overflow: hidden; flex-shrink: 0; margin-top: 4px; }
        .pip { position: absolute; top: 4px; right: 4px; width: 180px; height: 110px; border: 1px solid var(--pink); background: #000; z-index: 10; display: flex; flex-direction: column; }
        .pip-header { background: var(--pink); color: #fff; font-size: 0.5rem; padding: 2px 4px; display: flex; justify-content: space-between; }

        .chat { flex: 1; border: 1px solid var(--green); padding: 6px; overflow-y: auto; font-size: 0.75rem; background: #0a0f19; margin-top: 4px; }

        .actions { display: flex; gap: 4px; margin-top: 4px; flex-shrink: 0; height: 32px; }
        .actions button { flex: 1; background: #0a0f19; border: 1px solid var(--green); color: var(--green); font-size: 0.65rem; font-weight: bold; cursor: pointer; }

        .input-bar { display: flex; gap: 4px; margin-top: 4px; flex-shrink: 0; height: 36px; align-items: center; }
        input { flex: 1; height: 100%; background: #000; border: 1px solid var(--green); color: #fff; padding: 0 8px; font-family: inherit; font-size: 0.75rem; }
        .btn-send { background: var(--green); color: #000; border: none; font-weight: bold; padding: 0 12px; height: 100%; cursor: pointer; font-size: 0.75rem; }
        .btn-icon { width: 36px; height: 100%; background: #0a0f19; border: 1px solid var(--green); color: var(--green); font-weight: bold; cursor: pointer; }

        video { width: 100%; height: 100%; object-fit: cover; }
    </style>
</head>
<body>
    <div class="hud"><span>🟢 ONLINE</span><span>📍 TAILSCALE</span><span>🔒 SYSTEM READY</span></div>

    <div class="viewport">
        <img src="/static/daniela_avatar.jpg" style="width:100%; height:100%; object-fit:cover;">
        <div class="pip">
            <div class="pip-header"><span>🎬 PIP MASTER</span><span id="pipStatus">OFF</span></div>
            <video id="webcamVideo" autoplay playsinline></video>
        </div>
    </div>

    <div class="chat" id="chat">
        <div style="color:var(--green)">Daniela: Maquetación ajustada al viewport móvil.</div>
    </div>

    <div class="actions">
        <button onclick="document.getElementById('chat').innerHTML=''">🧹 LIMPIAR CHAT</button>
        <button>🎙️ MODALIDAD AUDIO</button>
    </div>

    <div class="input-bar">
        <button class="btn-icon" onclick="startCamera()">+</button>
        <button class="btn-icon" onclick="startCamera()">📷</button>
        <input type="text" id="userInput" placeholder="Habla con Daniela..." onkeydown="if(event.key==='Enter') sendMessage()">
        <button class="btn-send" onclick="sendMessage()">ENVIAR</button>
    </div>

    <script>
        async function startCamera() {
            try {
                const stream = await navigator.mediaDevices.getUserMedia({video: {facingMode: "environment"}});
                document.getElementById('webcamVideo').srcObject = stream;
                document.getElementById('pipStatus').innerText = 'LIVE';
            } catch(e) { alert("Acceso a cámara denegado."); }
        }

        function sendMessage() {
            const input = document.getElementById('userInput');
            const chat = document.getElementById('chat');
            if(!input.value.trim()) return;

            const txt = input.value;
            chat.innerHTML += `<div><b>Tú:</b> ${txt}</div>`;
            input.value = '';
            chat.scrollTop = chat.scrollHeight;

            fetch('/api/chat', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({message: txt})
            })
            .then(res => res.json())
            .then(data => {
                chat.innerHTML += `<div style="color:var(--green)"><b>Daniela:</b> ${data.response}</div>`;
                chat.scrollTop = chat.scrollHeight;
                if(data.action === 'start_camera') startCamera();
            });
        }
    </script>
</body>
</html>"""

with open("index.html", "w", encoding="utf-8") as f:
    f.write(fit_ui)

with open("templates/index.html", "w", encoding="utf-8") as f:
    f.write(fit_ui)

print("✅ UI reestructurada para encajar en pantalla.")
