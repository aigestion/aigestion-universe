import os

nexus_path = os.path.expanduser("~/aig-monorepo/apps/nexus-command-center/nexus_dashboard.py")

code = '''#!/usr/bin/env python3
import os
import sys
import sqlite3
import json
import psutil
from socketserver import ThreadingMixIn
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import parse_qs, urlparse

repo_dir = os.path.expanduser("~/aig-monorepo")
if repo_dir not in sys.path:
    sys.path.insert(0, repo_dir)

from core.hybrid_search import HybridSearch
from core.knowledge_graph import KnowledgeGraph

DB_PATH = os.path.expanduser("~/aig-monorepo/pixela8/app/daniela_memory.db")

class ThreadedHTTPServer(ThreadingMixIn, HTTPServer):
    """Servidor multihilo para rendimiento extremo sin bloqueos I/O"""
    daemon_threads = True

class NexusHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        parsed_url = urlparse(self.path)
        path = parsed_url.path

        if path == "/":
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.end_headers()
            self.wfile.write(self.get_html_page().encode("utf-8"))
        elif path == "/api/graph-data":
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps(self.get_graph_json()).encode("utf-8"))
        elif path == "/api/system-stats":
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps(self.get_system_stats()).encode("utf-8"))
        else:
            self.send_response(404)
            self.end_headers()

    def do_POST(self):
        parsed_url = urlparse(self.path)
        if parsed_url.path == "/api/chat":
            content_length = int(self.headers.get("Content-Length", 0))
            post_data = self.rfile.read(content_length).decode("utf-8")
            try:
                data = json.loads(post_data)
                user_msg = data.get("message", "")

                hs = HybridSearch()
                answer = hs.answer_with_hybrid_context(user_msg)

                response_data = {"status": "success", "reply": answer}
                self.send_response(200)
                self.send_header("Content-Type", "application/json")
                self.end_headers()
                self.wfile.write(json.dumps(response_data).encode("utf-8"))
            except Exception as e:
                self.send_response(500)
                self.send_header("Content-Type", "application/json")
                self.end_headers()
                self.wfile.write(json.dumps({"status": "error", "reply": f"⚠️ Error Nexus: {e}"}).encode("utf-8"))
        else:
            self.send_response(404)
            self.end_headers()

    def get_system_stats(self):
        try:
            cpu = psutil.cpu_percent(interval=None)
            ram = psutil.virtual_memory().percent
            return {"cpu": cpu, "ram": ram, "status": "OPTIMAL"}
        except Exception:
            return {"cpu": 0, "ram": 0, "status": "UNKNOWN"}

    def get_graph_json(self):
        if not os.path.exists(DB_PATH):
            return {"nodes": [], "links": []}
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        try:
            cursor.execute("SELECT id, entity_name, entity_type FROM graph_nodes")
            nodes = [{"id": row[0], "name": row[1], "type": row[2] or "GENERIC"} for row in cursor.fetchall()]

            cursor.execute("SELECT source_id, target_id, relation FROM graph_edges")
            links = [{"source": row[0], "target": row[1], "relation": row[2]} for row in cursor.fetchall()]

            conn.close()
            return {"nodes": nodes, "links": links}
        except Exception:
            conn.close()
            return {"nodes": [], "links": []}

    def get_finops_summary(self):
        if not os.path.exists(DB_PATH): return {"total_cost": 0, "total_saved": 0, "total_reqs": 0}
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        try:
            cursor.execute("SELECT COUNT(*), SUM(estimated_cost_usd), SUM(saved_cost_usd) FROM finops_metrics")
            row = cursor.fetchone()
            conn.close()
            return {
                "total_reqs": row[0] or 0,
                "total_cost": round(row[1] or 0.0, 5),
                "total_saved": round(row[2] or 0.0, 5)
            }
        except Exception:
            conn.close()
            return {"total_cost": 0, "total_saved": 0, "total_reqs": 0}

    def get_html_page(self):
        finops = self.get_finops_summary()
        return f"""<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Nexus Command Center Ultra</title>
    <script src="https://d3js.org/d3.v7.min.js"></script>
    <style>
        :root {{ --bg: #090d16; --card-bg: #111827; --border: #1f2937; --accent: #38bdf8; --purple: #a855f7; }}
        body {{ font-family: system-ui, -apple-system, sans-serif; background: var(--bg); color: #f3f4f6; margin: 0; padding: 20px; }}
        h1 {{ color: var(--accent); text-align: center; margin-bottom: 20px; font-size: 1.8rem; letter-spacing: 1px; }}
        .grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(320px, 1fr)); gap: 16px; max-width: 1400px; margin: 0 auto; }}
        .card {{ background: var(--card-bg); border-radius: 10px; padding: 18px; border: 1px solid var(--border); box-shadow: 0 4px 12px rgba(0,0,0,0.5); }}
        .card h2 {{ margin-top: 0; color: var(--purple); font-size: 1.1rem; border-bottom: 1px solid var(--border); padding-bottom: 8px; font-weight: 600; }}
        .stat {{ font-size: 1.8rem; font-weight: bold; color: var(--accent); margin: 8px 0; }}
        #graph-container {{ width: 100%; height: 380px; background: #030712; border-radius: 8px; border: 1px solid var(--border); position: relative; }}
        .chat-box {{ height: 260px; overflow-y: auto; background: #030712; border: 1px solid var(--border); border-radius: 8px; padding: 12px; margin-bottom: 10px; display: flex; flex-direction: column; gap: 8px; }}
        .msg {{ padding: 10px 14px; border-radius: 8px; max-width: 82%; font-size: 0.88rem; line-height: 1.45; }}
        .user-msg {{ background: #0284c7; align-self: flex-end; color: white; }}
        .bot-msg {{ background: #1f2937; align-self: flex-start; color: #e5e7eb; border: 1px solid #374151; }}
        .chat-input-area {{ display: flex; gap: 8px; }}
        input[type="text"] {{ flex: 1; padding: 10px 14px; border-radius: 6px; border: 1px solid #374151; background: #030712; color: white; outline: none; }}
        input[type="text"]:focus {{ border-color: var(--accent); }}
        button {{ background: var(--purple); color: white; border: none; padding: 10px 18px; border-radius: 6px; cursor: pointer; font-weight: 600; transition: background 0.2s; }}
        button:hover {{ background: #9333ea; }}
        .badge {{ display: inline-block; padding: 3px 8px; border-radius: 4px; font-size: 0.75rem; font-weight: bold; background: #0369a1; color: white; }}
    </style>
</head>
<body>
    <h1>⚡ Nexus Command Center Ultra</h1>
    <div class="grid">
        <div class="card">
            <h2>💳 FinOps & Optimización AI</h2>
            <div class="stat">${finops["total_cost"]} USD</div>
            <p>Peticiones: <strong>{finops["total_reqs"]}</strong> | Ahorro Est.: <strong style="color:#4ade80;">${finops["total_saved"]} USD</strong></p>
            <span class="badge">Ahorro Activo ~92%</span>
        </div>

        <div class="card">
            <h2>📱 Estado Nodo Pixel 8a</h2>
            <div id="sys-metrics">
                <p>CPU: <strong id="cpu-val">--%</strong></p>
                <p>RAM: <strong id="ram-val">--%</strong></p>
                <p>Estado Red Mesh: <strong style="color:#4ade80;">ONLINE (127.0.0.1)</strong></p>
            </div>
        </div>

        <div class="card" style="grid-column: span 2;">
            <h2>🧠 Knowledge Graph Interactivo Dynamic V3</h2>
            <div id="graph-container"></div>
        </div>

        <div class="card" style="grid-column: span 2;">
            <h2>💬 Chat Ultra en Tiempo Real (Hybrid Context)</h2>
            <div class="chat-box" id="chat-box">
                <div class="msg bot-msg">¡Nexus V3 activo y optimizado! Haz tu consulta o comparte información para enriquecer el Knowledge Graph.</div>
            </div>
            <div class="chat-input-area">
                <input type="text" id="user-input" placeholder="Pregunta o enseña algo a Nexus..." onkeypress="if(event.key === 'Enter') sendChat()">
                <button onclick="sendChat()">Enviar</button>
            </div>
        </div>
    </div>

    <script>
        // Cargar Métricas de Sistema
        function updateStats() {{
            fetch('/api/system-stats')
                .then(res => res.json())
                .then(data => {{
                    document.getElementById('cpu-val').innerText = data.cpu + '%';
                    document.getElementById('ram-val').innerText = data.ram + '%';
                }}).catch(() => {{}});
        }}
        setInterval(updateStats, 3000);
        updateStats();

        // Cargar Grafo D3.js V3
        fetch('/api/graph-data')
            .then(res => res.json())
            .then(data => {{
                const container = document.getElementById('graph-container');
                const width = container.clientWidth;
                const height = 380;

                const svg = d3.select("#graph-container")
                    .append("svg")
                    .attr("width", width)
                    .attr("height", height);

                const colorMap = {{
                    "HARDWARE": "#f43f5e",
                    "SOFTWARE": "#3b82f6",
                    "IP": "#10b981",
                    "PERSONA": "#eab308",
                    "GENERIC": "#a855f7"
                }};

                const simulation = d3.forceSimulation(data.nodes)
                    .force("link", d3.forceLink(data.links).id(d => d.id).distance(100))
                    .force("charge", d3.forceManyBody().strength(-200))
                    .force("center", d3.forceCenter(width / 2, height / 2));

                const link = svg.append("g")
                    .selectAll("line")
                    .data(data.links)
                    .enter().append("line")
                    .attr("stroke", "#374151")
                    .attr("stroke-width", 2);

                const linkText = svg.append("g")
                    .selectAll("text")
                    .data(data.links)
                    .enter().append("text")
                    .text(d => d.relation)
                    .attr("font-size", "9px")
                    .attr("fill", "#9ca3af")
                    .attr("text-anchor", "middle");

                const node = svg.append("g")
                    .selectAll("circle")
                    .data(data.nodes)
                    .enter().append("circle")
                    .attr("r", 9)
                    .attr("fill", d => colorMap[d.type] || colorMap["GENERIC"])
                    .call(d3.drag()
                        .on("start", dragstarted)
                        .on("drag", dragged)
                        .on("end", dragended));

                const label = svg.append("g")
                    .selectAll("text")
                    .data(data.nodes)
                    .enter().append("text")
                    .text(d => d.name)
                    .attr("font-size", "11px")
                    .attr("fill", "#f3f4f6")
                    .attr("dx", 13)
                    .attr("dy", 4);

                simulation.on("tick", () => {{
                    link
                        .attr("x1", d => d.source.x)
                        .attr("y1", d => d.source.y)
                        .attr("x2", d => d.target.x)
                        .attr("y2", d => d.target.y);

                    linkText
                        .attr("x", d => (d.source.x + d.target.x) / 2)
                        .attr("y", d => (d.source.y + d.target.y) / 2);

                    node
                        .attr("cx", d => d.x)
                        .attr("cy", d => d.y);

                    label
                        .attr("x", d => d.x)
                        .attr("y", d => d.y);
                }});

                function dragstarted(event, d) {{
                    if (!event.active) simulation.alphaTarget(0.3).restart();
                    d.fx = d.x; d.fy = d.y;
                }}
                function dragged(event, d) {{
                    d.fx = event.x; d.fy = event.y;
                }}
                function dragended(event, d) {{
                    if (!event.active) simulation.alphaTarget(0);
                    d.fx = null; d.fy = null;
                }}
            }});

        // Chat
        function sendChat() {{
            const input = document.getElementById('user-input');
            const chatBox = document.getElementById('chat-box');
            const text = input.value.trim();
            if (!text) return;

            chatBox.innerHTML += `<div class="msg user-msg">${{text}}</div>`;
            input.value = '';
            chatBox.scrollTop = chatBox.scrollHeight;

            fetch('/api/chat', {{
                method: 'POST',
                headers: {{ 'Content-Type': 'application/json' }},
                body: JSON.stringify({{ message: text }})
            }})
            .then(res => res.json())
            .then(data => {{
                chatBox.innerHTML += `<div class="msg bot-msg">${{data.reply}}</div>`;
                chatBox.scrollTop = chatBox.scrollHeight;
            }})
            .catch(err => {{
                chatBox.innerHTML += `<div class="msg bot-msg" style="color:#f87171;">⚠️ Error al conectar con Nexus.</div>`;
                chatBox.scrollTop = chatBox.scrollHeight;
            }});
        }}
    </script>
</body>
</html>\"\"\"

def run(server_class=ThreadedHTTPServer, handler_class=NexusHandler, port=8000):
    server_address = ("", port)
    httpd = server_class(server_address, handler_class)
    print(f"🚀 [Nexus Ultra V3] Servidor Multihilo activo en http://localhost:{port}")
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        pass
    httpd.server_close()

if __name__ == "__main__":
    run()
'''

with open(nexus_path, "w", encoding="utf-8") as f:
    f.write(code)

os.chmod(nexus_path, 0o755)
print(
    "✨ [Nexus V3 Generator] nexus_dashboard.py actualizado con multihilo, telemetría y D3.js V3."
)
