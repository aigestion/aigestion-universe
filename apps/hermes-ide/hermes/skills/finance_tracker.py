from flask import Blueprint, jsonify, request

finance_bp = Blueprint("finance_tracker", __name__)

SKILL = {"name": "Finance Tracker", "description": "Track expenses, analyze patterns, suggest savings"}

transactions = [
    {"id": 1, "desc": "Coffee", "amount": 4.50, "category": "food", "date": "2026-09-13"},
    {"id": 2, "desc": "Uber", "amount": 12.00, "category": "transport", "date": "2026-09-13"},
    {"id": 3, "desc": "Lunch", "amount": 15.00, "category": "food", "date": "2026-09-13"}
]

@finance_bp.route("/api/hermes/skills/finance/status")
def f_status():
    total = sum(t["amount"] for t in transactions)
    return jsonify({"transactions": transactions, "total": total})

@finance_bp.route("/api/hermes/skills/finance/add", methods=["POST"])
def f_add():
    data = request.json or {}
    transactions.append({
        "id": len(transactions) + 1,
        "desc": data.get("desc", ""),
        "amount": data.get("amount", 0),
        "category": data.get("category", "other"),
        "date": data.get("date", "2026-09-13")
    })
    return jsonify({"ok": True})

@finance_bp.route("/api/hermes/skills/finance/web")
def f_web():
    return """<!DOCTYPE html><html><head><meta charset="utf-8"><title>Finance Tracker</title>
<style>body{margin:0;background:#0a0a0f;color:#00f0ff;font-family:monospace;padding:20px}
input{background:#111;border:1px solid #333;color:#00f0ff;padding:8px;border-radius:6px;font-family:monospace;margin:5px}
button{background:#00f0ff22;border:1px solid #00f0ff;color:#00f0ff;padding:8px 16px;border-radius:6px;cursor:pointer}
.tx{background:#111;padding:8px;margin:5px 0;border-radius:6px;display:flex;justify-content:space-between}
.total{font-size:24px;color:#00ff88;text-align:center;margin:20px 0}
</style></head><body>
<h1>FINANCE TRACKER</h1>
<div class="total" id="total">$0.00</div>
<div><input id="desc" placeholder="Description"><input id="amount" type="number" placeholder="Amount"><button onclick="add()">Add</button></div>
<div id="txns"></div>
<script>function load(){fetch('/api/hermes/skills/finance/status').then(r=>r.json()).then(d=>{document.getElementById('total').textContent='$'+d.total.toFixed(2);document.getElementById('txns').innerHTML=d.transactions.map(t=>'<div class="tx"><span>'+t.desc+'</span><span>$'+t.amount.toFixed(2)+'</span></div>').join('')})}
function add(){fetch('/api/hermes/skills/finance/add',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({desc:document.getElementById('desc').value,amount:parseFloat(document.getElementById('amount').value)})}).then(()=>{document.getElementById('desc').value='';document.getElementById('amount').value='';load()})}
load()</script></body></html>"""
