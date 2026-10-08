import os

dash_path = os.path.expanduser("~/aig-monorepo/pixela8/app/agents/agent_dashboard.py")

with open(dash_path, encoding="utf-8") as f:
    content = f.read()

kg_functions = """
def get_graph_nodes():
    if not os.path.exists(DB_PATH): return []
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT n1.entity_name, e.relation, n2.entity_name FROM graph_edges e JOIN graph_nodes n1 ON e.source_id = n1.id JOIN graph_nodes n2 ON e.target_id = n2.id ORDER BY e.id DESC LIMIT 6")
        rows = cursor.fetchall()
        conn.close()
        return rows
    except Exception:
        conn.close()
        return []

def get_graph_stats():
    if not os.path.exists(DB_PATH): return {"nodes": 0, "edges": 0}
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT COUNT(*) FROM graph_nodes")
        nodes_cnt = cursor.fetchone()[0] or 0
        cursor.execute("SELECT COUNT(*) FROM graph_edges")
        edges_cnt = cursor.fetchone()[0] or 0
        conn.close()
        return {"nodes": nodes_cnt, "edges": edges_cnt}
    except Exception:
        conn.close()
        return {"nodes": 0, "edges": 0}
"""

if "def get_graph_nodes():" not in content:
    content = content.replace("def get_jobs():", f"{kg_functions}\ndef get_jobs():")
    content = content.replace(
        "finops = get_finops_summary()",
        "finops = get_finops_summary()\n        kg_stats = get_graph_stats()\n        kg_connections = get_graph_nodes()",
    )

    kg_card_html = """
        <div class="card">
            <h2>🧠 Knowledge Graph & Conexiones</h2>
            <div class="stat">{kg_stats['nodes']} Nodos / {kg_stats['edges']} Aristas</div>
            <ul>
                {"".join([f"<li><code>{row[0]}</code> <span style='color:#a855f7;'>──[{row[1]}]──►</span> <code>{row[2]}</code></li>" for row in kg_connections]) or "<li>Sin conexiones.</li>"}
            </ul>
        </div>
    """

    content = content.replace(
        '<div class="card">\n            <h2>📝 Nota Rápida (Secretario)</h2>',
        f'{kg_card_html}\n        <div class="card">\n            <h2>📝 Nota Rápida (Secretario)</h2>',
    )

with open(dash_path, "w", encoding="utf-8") as f:
    f.write(content)

print("✨ [Dashboard Knowledge Graph] Actualizado con éxito.")
