#!/usr/bin/env python3
"""
AIGestion Admin Panel v1.0
===========================
Panel de administracion web para gestionar:
- Usuarios (listar, suspender, cambiar tier)
- Suscripciones y billing
- Analytics y metricas
- Modulos del sistema
- Configuracion

Autor: AIGestion Team
"""

from __future__ import annotations

import sqlite3
import sys
from datetime import datetime
from pathlib import Path
from typing import Any

from flask import Flask, jsonify, request

app = Flask(__name__)

# Canonico de `billing_system` tras la ola de dedup (se borro el duplicado
# `daniela-os/billing_system.py`): vive en `scripts/core/`.
_CORE_BILLING = str(Path(__file__).resolve().parents[1] / "scripts" / "core")
if _CORE_BILLING not in sys.path:
    sys.path.insert(0, _CORE_BILLING)

# ── Templates inline (sin dependencia de templates/) ──────────

ADMIN_TEMPLATE = """
<!DOCTYPE html>
<html lang="es">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>AIGestion Admin Panel</title>
<style>
:root{--bg:#0f172a;--card:#1e293b;--text:#e2e8f0;--accent:#38bdf8;--success:#22c55e;--warning:#eab308;--danger:#ef4444;}
*{margin:0;padding:0;box-sizing:border-box;font-family:'Segoe UI',sans-serif;}
body{background:var(--bg);color:var(--text);line-height:1.6;}
.container{max-width:1400px;margin:0 auto;padding:20px;}
header{display:flex;justify-content:space-between;align-items:center;padding:20px 0;border-bottom:1px solid #334155;margin-bottom:30px;}
h1{color:var(--accent);font-size:2rem;}
.grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(280px,1fr));gap:20px;margin-bottom:30px;}
.card{background:var(--card);border-radius:12px;padding:20px;box-shadow:0 4px 6px rgba(0,0,0,0.3);}
.card h3{color:var(--accent);margin-bottom:10px;font-size:1.1rem;}
.stat{font-size:2.5rem;font-weight:700;color:var(--success);}
.stat.warning{color:var(--warning);}
.stat.danger{color:var(--danger);}
table{width:100%;border-collapse:collapse;margin-top:15px;}
th,td{padding:10px;text-align:left;border-bottom:1px solid #334155;font-size:0.9rem;}
th{color:var(--accent);font-weight:600;}
tr:hover{background:rgba(56,189,248,0.05);}
.badge{display:inline-block;padding:3px 10px;border-radius:20px;font-size:0.75rem;font-weight:600;}
.badge-free{background:#334155;color:#94a3b8;}
.badge-pro{background:#065f46;color:#6ee7b7;}
.badge-enterprise{background:#7c3aed;color:#c4b5fd;}
.badge-active{background:#14532d;color:#86efac;}
.badge-suspended{background:#7f1d1d;color:#fca5a5;}
.btn{padding:6px 14px;border:none;border-radius:6px;cursor:pointer;font-size:0.85rem;transition:opacity 0.2s;}
.btn:hover{opacity:0.8;}
.btn-primary{background:var(--accent);color:#0f172a;}
.btn-danger{background:var(--danger);color:#fff;}
.btn-warning{background:var(--warning);color:#0f172a;}
.tabs{display:flex;gap:10px;margin-bottom:20px;border-bottom:1px solid #334155;padding-bottom:10px;}
.tab{padding:8px 16px;cursor:pointer;border-radius:6px;transition:background 0.2s;}
.tab:hover{background:#334155;}
.tab.active{background:var(--accent);color:#0f172a;font-weight:600;}
.section{display:none;}
.section.active{display:block;}
</style>
</head>
<body>
<div class="container">
<header>
<h1>AIGestion Admin</h1>
<div style="color:#94a3b8;">v2.0.0 | {{ timestamp }}</div>
</header>

<div class="grid">
<div class="card">
<h3>Total Usuarios</h3>
<div class="stat">{{ stats.total_users }}</div>
</div>
<div class="card">
<h3>Usuarios Activos</h3>
<div class="stat">{{ stats.active_users }}</div>
</div>
<div class="card">
<h3>MRR</h3>
<div class="stat">${{ stats.mrr }}</div>
</div>
<div class="card">
<h3>Requests Hoy</h3>
<div class="stat">{{ stats.requests_today }}</div>
</div>
</div>

<div class="tabs">
<div class="tab active" onclick="showTab('users')">Usuarios</div>
<div class="tab" onclick="showTab('subscriptions')">Suscripciones</div>
<div class="tab" onclick="showTab('modules')">Modulos</div>
<div class="tab" onclick="showTab('analytics')">Analytics</div>
</div>

<div id="users" class="section active">
<div class="card">
<h3>Usuarios Registrados</h3>
<table>
<tr><th>Email</th><th>Nombre</th><th>Tier</th><th>Rol</th><th>Estado</th><th>Registro</th><th>Acciones</th></tr>
{% for u in users %}
<tr>
<td>{{ u.email }}</td>
<td>{{ u.name or '-' }}</td>
<td><span class="badge badge-{{ u.tier }}">{{ u.tier }}</span></td>
<td>{{ u.role }}</td>
<td><span class="badge badge-{{ u.status }}">{{ u.status }}</span></td>
<td>{{ u.created_at[:10] if u.created_at else '-' }}</td>
<td>
<button class="btn btn-primary" onclick="upgradeUser('{{ u.id }}')">Cambiar Tier</button>
{% if u.status == 'active' %}
<button class="btn btn-danger" onclick="suspendUser('{{ u.id }}')">Suspender</button>
{% endif %}
</td>
</tr>
{% endfor %}
</table>
</div>
</div>

<div id="subscriptions" class="section">
<div class="card">
<h3>Suscripciones Activas</h3>
<table>
<tr><th>Usuario</th><th>Tier</th><th>Ciclo</th><th>Periodo Fin</th><th>Estado</th></tr>
{% for s in subscriptions %}
<tr>
<td>{{ s.user_email }}</td>
<td><span class="badge badge-{{ s.tier }}">{{ s.tier }}</span></td>
<td>{{ s.billing_cycle }}</td>
<td>{{ s.period_end[:10] if s.period_end else '-' }}</td>
<td><span class="badge badge-{{ s.status }}">{{ s.status }}</span></td>
</tr>
{% endfor %}
</table>
</div>
</div>

<div id="modules" class="section">
<div class="card">
<h3>Modulos del Sistema</h3>
<table>
<tr><th>Nombre</th><th>Descripcion</th><th>Intents</th><th>Estado</th></tr>
{% for m in modules %}
<tr>
<td>{{ m.name }}</td>
<td>{{ m.description }}</td>
<td>{{ ', '.join(m.intents[:3]) }}</td>
<td><span class="badge badge-active">ON</span></td>
</tr>
{% endfor %}
</table>
</div>
</div>

<div id="analytics" class="section">
<div class="grid">
<div class="card">
<h3>Revenue (30 dias)</h3>
<div class="stat">${{ revenue.total_revenue }}</div>
<p>{{ revenue.payments_count }} pagos</p>
</div>
<div class="card">
<h3>Suscripciones por Tier</h3>
{% for tier, count in mrr.by_tier.items() %}
<p><strong>{{ tier }}:</strong> {{ count }}</p>
{% endfor %}
</div>
</div>
</div>

</div>
<script>
function showTab(id){
    document.querySelectorAll('.section').forEach(s=>s.classList.remove('active'));
    document.querySelectorAll('.tab').forEach(t=>t.classList.remove('active'));
    document.getElementById(id).classList.add('active');
    event.target.classList.add('active');
}
function suspendUser(id){
    if(confirm('Suspender usuario?')){
        fetch('/admin/api/suspend-user',{
            method:'POST',
            headers:{'Content-Type':'application/json'},
            body:JSON.stringify({user_id:id})
        }).then(()=>location.reload());
    }
}
function upgradeUser(id){
    const tier = prompt('Nuevo tier (free/pro/enterprise):');
    if(tier){
        fetch('/admin/api/change-tier',{
            method:'POST',
            headers:{'Content-Type':'application/json'},
            body:JSON.stringify({user_id:id, tier:tier})
        }).then(()=>location.reload());
    }
}
</script>
</body>
</html>
"""


# ── Data Loaders ──────────────────────────────────────────────


def load_users(limit: int = 100) -> list[dict[str, Any]]:

    if not Path("auth.db").exists():
        return []
    conn = sqlite3.connect("auth.db")
    c = conn.cursor()
    c.execute(
        """
        SELECT id, email, name, tier, role, status, created_at, last_login
        FROM users ORDER BY created_at DESC LIMIT ?
    """,
        (limit,),
    )
    rows = c.fetchall()
    conn.close()
    return [
        {
            "id": r[0],
            "email": r[1],
            "name": r[2],
            "tier": r[3],
            "role": r[4],
            "status": r[5],
            "created_at": r[6],
            "last_login": r[7],
        }
        for r in rows
    ]


def load_subscriptions() -> list[dict[str, Any]]:

    if not Path("billing.db").exists():
        return []
    conn = sqlite3.connect("billing.db")
    # El panel cruza `subscriptions` con `users`, que viven en OTRA base. SQLite
    # solo resuelve ese JOIN si la auth DB esta ATTACHed con ese alias: sin el
    # ATTACH la consulta reventaba con "no such table: <alias>.users" y el panel
    # devolvia 500 en vez de listar suscripciones.
    ruta_auth = Path("auth.db")
    if ruta_auth.exists():
        conn.execute("ATTACH DATABASE ? AS auth", (str(ruta_auth),))
        origen = "auth.users u"
    else:
        # Sin auth DB el JOIN no tiene sentido: se lista la suscripción sin email
        # en vez de tumbar la vista entera.
        origen = "(SELECT NULL AS id, NULL AS email) AS u"
    c = conn.cursor()
    c.execute(f"""
        SELECT s.id, s.user_id, s.tier, s.billing_cycle, s.current_period_end, s.status, u.email
        FROM subscriptions s LEFT JOIN {origen} u ON s.user_id = u.id
        WHERE s.status = 'active' ORDER BY s.created_at DESC
    """)
    rows = c.fetchall()
    conn.close()
    return [
        {
            "id": r[0],
            "user_id": r[1],
            "tier": r[2],
            "billing_cycle": r[3],
            "period_end": r[4],
            "status": r[5],
            "user_email": r[6] or r[1][:8],
        }
        for r in rows
    ]


def load_stats() -> dict[str, Any]:

    stats = {"total_users": 0, "active_users": 0, "mrr": 0, "requests_today": 0}

    if Path("auth.db").exists():
        conn = sqlite3.connect("auth.db")
        c = conn.cursor()
        c.execute("SELECT COUNT(*) FROM users")
        stats["total_users"] = c.fetchone()[0]
        c.execute("SELECT COUNT(*) FROM users WHERE status = 'active'")
        stats["active_users"] = c.fetchone()[0]
        today = datetime.now().strftime("%Y-%m-%d")
        c.execute("SELECT COUNT(*) FROM usage_log WHERE timestamp LIKE ?", (f"{today}%",))
        stats["requests_today"] = c.fetchone()[0]
        conn.close()

    if Path("billing.db").exists():
        from billing_system import BillingManager

        billing = BillingManager()
        mrr_data = billing.get_mrr()
        stats["mrr"] = mrr_data.get("mrr", 0)

    return stats


def load_modules() -> list[dict[str, Any]]:

    try:
        sys.path.insert(0, str(Path(__file__).parent))
        from daniela_os_core import DanielaCore

        core = DanielaCore()
        return [
            {"name": m.name, "description": m.description, "intents": m.intents}
            for m in core.registry.list_enabled()
        ]
    except Exception:
        return []


# ── Rutas ─────────────────────────────────────────────────────


@app.route("/admin")
def admin_dashboard() -> str:
    """Panel principal de administracion."""
    from jinja2 import Template

    template = Template(ADMIN_TEMPLATE)

    users = load_users()
    subscriptions = load_subscriptions()
    modules = load_modules()
    stats = load_stats()

    # Revenue
    revenue = {"total_revenue": 0, "payments_count": 0}
    mrr_data = {"by_tier": {}}
    if Path("billing.db").exists():
        from billing_system import BillingManager

        billing = BillingManager()
        rev = billing.get_revenue_report(30)
        revenue = rev
        mrr_data = billing.get_mrr()

    return template.render(
        users=users,
        subscriptions=subscriptions,
        modules=modules,
        stats=stats,
        revenue=revenue,
        mrr=mrr_data,
        timestamp=datetime.now().strftime("%Y-%m-%d %H:%M"),
    )


@app.route("/admin/api/suspend-user", methods=["POST"])
def api_suspend_user() -> Any:

    data = request.get_json() or {}
    user_id = data.get("user_id", "")
    if not user_id:
        return jsonify({"error": "user_id requerido"}), 400

    from auth_system import AuthManager

    auth = AuthManager()
    auth.suspend_user(user_id)
    return jsonify({"success": True})


@app.route("/admin/api/change-tier", methods=["POST"])
def api_change_tier() -> Any:

    data = request.get_json() or {}
    user_id = data.get("user_id", "")
    tier = data.get("tier", "")
    if not user_id or not tier:
        return jsonify({"error": "user_id y tier requeridos"}), 400

    from auth_system import AuthManager

    auth = AuthManager()
    auth.update_user_tier(user_id, tier)
    return jsonify({"success": True})


@app.route("/admin/api/stats")
def api_admin_stats() -> Any:

    return jsonify(load_stats())


# ═══════════════════════════════════════════════════════════════
# CLI
# ═══════════════════════════════════════════════════════════════


def main() -> int:

    import argparse

    parser = argparse.ArgumentParser(description="AIGestion Admin Panel")
    parser.add_argument("--host", default="0.0.0.0")
    parser.add_argument("--port", type=int, default=5001)
    parser.add_argument("--debug", action="store_true")
    args = parser.parse_args()

    print(f"""
    ╔══════════════════════════════════════════════════════════════╗
    ║                                                              ║
    ║   AIGestion Admin Panel v1.0                                 ║
    ║                                                              ║
    ║   URL: http://{args.host}:{args.port:<5}                             ║
    ║                                                              ║
    ╚══════════════════════════════════════════════════════════════╝
    """)
    app.run(host=args.host, port=args.port, debug=args.debug)
    return 0


if __name__ == "__main__":
    sys.exit(main())
