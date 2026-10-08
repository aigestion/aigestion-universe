import os

dash_path = os.path.expanduser("~/aig-monorepo/pixela8/app/agents/agent_dashboard.py")

with open(dash_path, encoding="utf-8") as f:
    content = f.read()

finops_func = """
def get_finops_summary():
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
"""

if "def get_finops_summary():" not in content:
    content = content.replace("def get_jobs():", f"{finops_func}\ndef get_jobs():")

    # Inyectar tarjeta FinOps en el HTML
    card_html = """
        <div class="card">
            <h2>💳 FinOps & AI Gateway</h2>
            <div class="stat">${finops['total_cost']}</div>
            <p>Peticiones: <strong>{finops['total_reqs']}</strong> | Ahorro Est.: <strong style="color:#4ade80;">${finops['total_saved']}</strong></p>
        </div>
    """
    content = content.replace(
        "finops = get_finops_summary()", ""
    )  # evitar duplicados si los hubiera
    content = content.replace(
        "notes = get_recent_notes()",
        "notes = get_recent_notes()\n        finops = get_finops_summary()",
    )
    content = content.replace(
        '<div class="card">\n            <h2>📝 Nota Rápida (Secretario)</h2>',
        f'{card_html}\n        <div class="card">\n            <h2>📝 Nota Rápida (Secretario)</h2>',
    )

with open(dash_path, "w", encoding="utf-8") as f:
    f.write(content)

print("✨ [Dashboard FinOps] Integradas métricas de costo y ahorro en el Dashboard Web.")
