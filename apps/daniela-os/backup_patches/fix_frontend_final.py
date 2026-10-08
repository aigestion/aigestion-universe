import os

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
        }
        .pip-header {
            background: rgba(255, 0, 85, 0.3); color: var(--neon-pink); font-size: 0.65rem;
            padding: 4px 8px; font-weight: bold; border-bottom: 1px solid var(--neon-pink);
        }
        .pip-content {
            flex: 1; display: flex; align-items: center; justify-content: center;
            color: var(--neon-green); font-size: 0.75rem; text-align: center; background: #000;
        }
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
            <div class="pip-header">🎬 PIP MASTER</div>
            <div class="pip-content" id="pipDisplayArea">Esperando selección...</div>
        </div>
    </div>

    <div class="chat-box" id="chatBox">
        <div class="msg-daniela"><b>Daniela:</b> Núcleo Sovereign activo. ¿Qué ejecutamos?</div>
    </div>

    <div class="controls">
        <input type="text" id="userInput" placeholder="Habla con Daniela..." onkeydown="if(event.key==='Enter') sendMessage()">
        <button onclick="sendMessage()">ENVIAR</button>
    </div>

    <script>
        function sendMessage() {
            const input = document.getElementById('userInput');
            const chatBox = document.getElementById('chatBox');
            const pipArea = document.getElementById('pipDisplayArea');
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

                if (data.url) {
                    pipArea.innerHTML = `<img src="${data.url}?t=${new Date().getTime()}" style="width:100%; height:100%; object-fit:cover;">`;
                }
            })
            .catch(() => {
                chatBox.innerHTML += `<div class="msg-daniela"><b>Daniela:</b> Error procesando solicitud.</div>`;
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

print("✅ Plantilla HTML unificada y reescrita correctamente.")
