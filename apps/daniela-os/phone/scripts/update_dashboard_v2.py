import os

dash_path = os.path.expanduser("~/aig-monorepo/pixela8/app/agents/agent_dashboard.py")

code = '''#!/usr/bin/env python3
import os
import sys
import sqlite3
import json
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import parse_qs, urlparse

repo_dir = os.path.expanduser("~/aig-monorepo")
if repo_dir not in sys.path:
    sys.path.insert(0, repo_dir)

from core.hybrid_search import HybridSearch
from core.knowledge_graph import KnowledgeGraph

DB_PATH = os.path.expanduser("~/aig-monorepo/pixela8/app/daniela_memory.db")

class DashboardHandler(BaseHTTPRequestHandler):
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
        else:
            self.send_response(404)
            self.end_headers()

    def do_POST(self):
        parsed_url = urlparse(self.path)
        if parsed_url.path == "/api/chat":
            content_length = int(self.headers.get('Content-Length', 0))
            post_data = self.rfile.read(content_length).decode('utf-8')
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
                self.wfile.write(json.dumps({"status": "error", "reply": str(e)}).encode("utf-8"))
        else:
            self.send_response(404)
            self.end_headers()

    def get_graph_json(self):
        if not os.path.exists(DB_PATH):
            return {"nodes": [], "links": []}
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        try:
            cursor.execute("SELECT id, entity_name, entity_type FROM graph_nodes")
            nodes = [{"id": row[0], "name": row[1], "type": row[2]} for row in cursor.fetchall()]

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
    <title>Daniela OS - Command Center</title>
    <script src="https://d3js.org/d3.v7.min.js"></script>
    <style>
        body {{ font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; background: #0f172a; color: #f8fafc; margin: 0; padding: 20px; }}
        h1 {{ color: #38bdf8; text-align: center; margin-bottom: 30px; }}
        .grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(350px, 1fr)); gap: 20px; max-width: 1400px; margin: 0 auto; }}
        .card {{ background: #1e293b; border-radius: 12px; padding: 20px; box-shadow: 0 4px 6px rgba(0,0,0,0.3); border: 1px solid #334155; }}
        .card h2 {{ margin-top: 0; color: #a855f7; font-size: 1.2rem; border-bottom: 1px solid #334155; padding-bottom: 8px; }}
        .stat {{ font-size: 1.8rem; font-weight: bold; color: #38bdf8; margin: 10px 0; }}
        #graph-container {{ width: 100%; height: 350px; background: #0f172a; border-radius: 8px; border: 1px solid #334155; }}
        .chat-box {{ height: 250px; overflow-y: auto; background: #0f172a; border: 1px solid #334155; border-radius: 8px; padding: 10px; margin-bottom: 10px; display: flex; flex-direction: column; gap: 8px; }}
        .msg {{ padding: 8px 12px; border-radius: 6px; max-width: 80%; font-size: 0.9rem; line-height: 1.4; }}
        .user-msg {{ background: #0284c7; align-self: flex-end; color: white; }}
        .bot-msg {{ background: #334155; align-self: flex-start; color: #e2e8f0; }}
        .chat-input-area {{ display: flex; gap: 8px; }}
        input[type="text"] {{ flex: 1; padding: 10px; border-radius: 6px; border: 1px solid #475569; background: #0f172a; color: white; }}
        button {{ background: #a855f7; color: white; border: none; padding: 10px 18px; border-radius: 6px; cursor: pointer; font-weight: bold; }}
        button:hover {{ background: #9333ea; }}
    </style>
</head>
<body>
    <h1>📱 Daniela OS - Edge Mesh & Command Center</h1>
    <div class="grid">
        <div class="card">
            <h2>💳 FinOps & AI Gateway</h2>
            <div class="stat">${finops['total_cost']}</div>
            <p>Peticiones: <strong>{finops['total_reqs']}</strong> | Ahorro Est.: <strong style="color:#4ade80;">${finops['total_saved']}</strong></p>
        </div>

        <div class="card" style="grid-column: span 2;">
            <h2>🧠 Knowledge Graph Interactivo (D3.js)</h2>
            <div id="graph-container"></div>
        </div>

        <div class="card" style="grid-column: span 2;">
            <h2>💬 Chat en Tiempo Real con Daniela (Hybrid Search)</h2>
            <div class="chat-box" id="chat-box">
                <div class="msg bot-msg">¡Hola! Soy Daniela. Pregúntame lo que necesites o comparte información para que la integre en el Knowledge Graph.</div>
            </div>
            <div class="chat-input-area">
                <input type="text" id="user-input" placeholder="Escribe tu mensaje o pregunta..." onkeypress="if(event.key === 'Enter') sendChat()">
                <button onclick="sendChat()">Enviar</button>
            </div>
        </div>
    </div>

    <script>
        // Cargar Grafo Interactivo D3.js
        fetch('/api/graph-data')
            .then(res => res.json())
            .then(data => {{
                const width = document.getElementById('graph-container').clientWidth;
                const height = 350;

                const svg = d3.select("#graph-container")
                    .append("svg")
                    .attr("width", width)
                    .attr("height", height);

                const simulation = d3.forceSimulation(data.nodes)
                    .force("link", d3.forceLink(data.links).id(d => d.id).distance(80))
                    .force("charge", d3.forceManyBody().strength(-150))
                    .force("center", d3.forceCenter(width / 2, height / 2));

                const link = svg.append("g")
                    .selectAll("line")
                    .data(data.links)
                    .enter().append("line")
                    .attr("stroke", "#475569")
                    .attr("stroke-width", 2);

                const node = svg.append("g")
                    .selectAll("circle")
                    .data(data.nodes)
                    .enter().append("circle")
                    .attr("r", 8)
                    .attr("fill", "#38bdf8")
                    .call(d3.drag()
                        .on("start", dragstarted)
                        .on("drag", dragged)
                        .on("end", dragended));

                const label = svg.append("g")
                    .selectAll("text")
                    .data(data.nodes)
                    .enter().append("text")
                    .text(d => d.name)
                    .attr("font-size", "10px")
                    .attr("fill", "#cbd5e1")
                    .attr("dx", 12)
                    .attr("dy", 4);

                simulation.on("tick", () => {{
                    link
                        .attr("x1", d => d.source.x)
                        .attr("y1", d => d.source.y)
                        .attr("x2", d => d.target.x)
                        .attr("y2", d => d.target.y);

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

        // Chat asíncrono
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
                chatBox.innerHTML += `<div class="msg bot-msg" style="color:#f87171;">Error de conexión.</div>`;
                chatBox.scrollTop = chatBox.scrollHeight;
            }});
        }}
    </script>
</body>
</html>
'''

with open(dash_path, "w", encoding="utf-8") as f:
    f.write(code)

print("✨ [Dashboard v2] Dashboard Web actualizado con Grafo D3.js y Chat en tiempo real.")
