import os

nexus_path = os.path.expanduser("~/aig-monorepo/apps/nexus-command-center/nexus_dashboard.py")

with open(nexus_path, encoding="utf-8") as f:
    code = f.read()

# 1. Inyectar endpoint /api/chat/stream en do_GET si no existe
if "/api/chat/stream" not in code:
    old_get = 'elif path == "/api/tasks-status":'
    new_get = 'elif path == "/api/chat/stream":\n            self.handle_chat_stream()\n        elif path == "/api/tasks-status":'
    code = code.replace(old_get, new_get)

# 2. Inyectar el manejador de streaming handle_chat_stream en NexusHandler
if "def handle_chat_stream(self):" not in code:
    stream_method = """    def handle_chat_stream(self):
        from urllib.parse import parse_qs, urlparse
        parsed = urlparse(self.path)
        params = parse_qs(parsed.query)
        msg = params.get("message", [""])[0].strip()

        self.send_response(200)
        self.send_header("Content-Type", "text/event-stream")
        self.send_header("Cache-Control", "no-cache")
        self.send_header("Connection", "keep-alive")
        self.end_headers()

        if not msg:
            self.wfile.write("data: Mensaje vacío\\n\\n".encode("utf-8"))
            return

        try:
            from core.hybrid_search import HybridSearch
            hs = HybridSearch()
            answer = hs.answer_with_hybrid_context(msg)

            # Simular/Transmitir por chunks para efecto máquina de escribir
            words = answer.split(" ")
            for i, word in enumerate(words):
                chunk = word + (" " if i < len(words) - 1 else "")
                data_line = f"data: {json.dumps({'chunk': chunk})}\\n\\n"
                self.wfile.write(data_line.encode("utf-8"))
                self.wfile.flush()
        except Exception as e:
            err_line = f"data: {json.dumps({'chunk': f'⚠️ Error stream: {e}'})}\\n\\n"
            self.wfile.write(err_line.encode("utf-8"))

"""
    code = code.replace(
        "    def get_tasks_summary(self):", stream_method + "    def get_tasks_summary(self):"
    )

# 3. Actualizar la función sendChat() en JavaScript para consumir EventSource / Fetch Stream
old_send_chat = """        function sendChat() {
            const input = document.getElementById('user-input');
            const chatBox = document.getElementById('chat-box');
            const text = input.value.trim();
            if (!text) return;

            chatBox.innerHTML += `<div class="msg user-msg">${text}</div>`;
            input.value = '';
            chatBox.scrollTop = chatBox.scrollHeight;

            fetch('/api/chat', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ message: text })
            })
            .then(res => res.json())
            .then(data => {
                chatBox.innerHTML += `<div class="msg bot-msg">${data.reply}</div>`;
                chatBox.scrollTop = chatBox.scrollHeight;
                renderGraph();
            })
            .catch(err => {
                chatBox.innerHTML += `<div class="msg bot-msg" style="color:#f87171;">⚠️ Error al conectar con Nexus.</div>`;
                chatBox.scrollTop = chatBox.scrollHeight;
            });
        }"""

new_send_chat = """        function sendChat() {{
            const input = document.getElementById('user-input');
            const chatBox = document.getElementById('chat-box');
            const text = input.value.trim();
            if (!text) return;

            chatBox.innerHTML += `<div class="msg user-msg">${{text}}</div>`;
            input.value = '';
            chatBox.scrollTop = chatBox.scrollHeight;

            const botMsgDiv = document.createElement('div');
            botMsgDiv.className = 'msg bot-msg';
            chatBox.appendChild(botMsgDiv);

            const evtSource = new EventSource('/api/chat/stream?message=' + encodeURIComponent(text));
            evtSource.onmessage = function(e) {{
                try {{
                    const data = JSON.parse(e.data);
                    if (data.chunk) {{
                        botMsgDiv.innerText += data.chunk;
                        chatBox.scrollTop = chatBox.scrollHeight;
                    }}
                }} catch(err) {{
                    botMsgDiv.innerText += e.data;
                }}
            }};
            evtSource.onerror = function() {{
                evtSource.close();
                renderGraph();
            }};
        }}"""

if old_send_chat in code:
    code = code.replace(old_send_chat, new_send_chat)

with open(nexus_path, "w", encoding="utf-8") as f:
    f.write(code)

print("✨ [Streaming SSE] Inyectado soporte /api/chat/stream en nexus_dashboard.py con éxito.")
