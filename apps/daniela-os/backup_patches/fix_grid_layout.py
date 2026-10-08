import os

grid_html = """<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
    <title>Daniela OS Sovereign v10.0</title>
    <style>
        :root { --bg: #05070a; --green: #00ffcc; --pink: #ff0055; }
        body { margin: 0; padding: 4px; background: var(--bg); color: #fff; font-family: monospace; height: 100vh;
               display: grid; grid-template-rows: auto 250px 1fr auto auto; gap: 4px; overflow: hidden; }
        .hud { border: 1px solid var(--green); padding: 4px; font-size: 0.6rem; background: #0a0f19; }
        .viewport { position: relative; border: 1px solid var(--green); background: #000; overflow: hidden; }
        .pip { position: absolute; top: 5px; right: 5px; width: 200px; height: 120px; border: 1px solid var(--pink); background: #000; z-index: 10; }
        .chat { border: 1px solid var(--green); padding: 6px; overflow-y: auto; font-size: 0.75rem; background: #0a0f19; }
        .actions { display: grid; grid-template-columns: 1fr 1fr; gap: 4px; }
        .input-bar { display: flex; gap: 4px; height: 40px; }
        input { flex: 1; background: #000; border: 1px solid var(--green); color: #fff; padding: 0 8px; }
        button { background: var(--green); color: #000; border: none; font-weight: bold; padding: 0 10px; }
        video { width: 100%; height: 100%; object-fit: cover; }
    </style>
</head>
<body>
    <div class="hud">🟢 ONLINE | 📍 TAILSCALE | 🔒 SYSTEM READY</div>
    <div class="viewport" id="stage">
        <img src="/static/daniela_avatar.jpg" style="width:100%; height:100%; object-fit:cover;">
        <div class="pip">
            <div style="background:var(--pink); color:#fff; font-size:0.5rem; padding:2px;">🎬 PIP MASTER</div>
            <video id="webcamVideo" autoplay playsinline></video>
        </div>
    </div>
    <div class="chat" id="chat">
        <div style="color:var(--green)">Daniela: Sistema bloqueado en modo Grid. Ready.</div>
    </div>
    <div class="actions">
        <button onclick="clearChat()">🧹 LIMPIAR</button>
        <button>🎙️ AUDIO</button>
    </div>
    <div class="input-bar">
        <button onclick="startCamera()">📷</button>
        <input type="text" id="userInput" placeholder="Habla...">
        <button onclick="sendMessage()">ENVIAR</button>
    </div>

    <script>
        async function startCamera() {
            try {
                const stream = await navigator.mediaDevices.getUserMedia({video: {facingMode: "environment"}});
                document.getElementById('webcamVideo').srcObject = stream;
            } catch(e) { alert("Sin acceso a cámara."); }
        }
        function sendMessage() {
            const input = document.getElementById('userInput');
            const chat = document.getElementById('chat');
            chat.innerHTML += `<div><b>Tú:</b> ${input.value}</div>`;
            fetch('/api/chat', {method:'POST', headers:{'Content-Type':'application/json'}, body:JSON.stringify({message:input.value})})
            .then(res => res.json()).then(data => {
                chat.innerHTML += `<div style="color:var(--green)"><b>Daniela:</b> ${data.response}</div>`;
                if(data.action === 'start_camera') startCamera();
            });
            input.value = '';
        }
        function clearChat() { document.getElementById('chat').innerHTML = ''; }
    </script>
</body>
</html>"""

os.makedirs("templates", exist_ok=True)
with open("templates/index.html", "w", encoding="utf-8") as f:
    f.write(grid_html)
with open("index.html", "w", encoding="utf-8") as f:
    f.write(grid_html)
print("✅ Interfaz Grid (Input Fijo) configurada.")
