from flask import Blueprint, jsonify, request

email_bp = Blueprint("email_intelligence", __name__)

SKILL = {"name": "Email Intelligence", "description": "Email classification, priority, and smart replies"}

@email_bp.route("/api/hermes/skills/email/status")
def e_status():
    return jsonify(SKILL)

@email_bp.route("/api/hermes/skills/email/classify", methods=["POST"])
def e_classify():
    data = request.json or {}
    subject = data.get("subject", "").lower()
    body = data.get("body", "").lower()
    text = subject + " " + body
    priority = "low"
    category = "general"
    if any(w in text for w in ["urgent", "asap", "emergency", "importante"]):
        priority = "high"
    elif any(w in text for w in ["meeting", "reunion", "call", "llamada"]):
        category = "meeting"
    elif any(w in text for w in ["invoice", "factura", "payment", "pago"]):
        category = "finance"
    elif any(w in text for w in ["bug", "error", "issue", "problema"]):
        category = "technical"
    return jsonify({"priority": priority, "category": category})

@email_bp.route("/api/hermes/skills/email/web")
def e_web():
    return """<!DOCTYPE html><html><head><meta charset="utf-8"><title>Email Intelligence</title>
<style>body{margin:0;background:#0a0a0f;color:#00f0ff;font-family:monospace;padding:20px}
input,textarea{width:100%;background:#111;border:1px solid #333;color:#00f0ff;padding:8px;border-radius:6px;font-family:monospace;margin:5px 0}
textarea{height:100px}
button{background:#00f0ff22;border:1px solid #00f0ff;color:#00f0ff;padding:8px 16px;border-radius:6px;cursor:pointer}
.result{margin-top:10px;padding:10px;background:#111;border-radius:6px}
</style></head><body>
<h1>EMAIL INTELLIGENCE</h1>
<input id="subject" placeholder="Subject"><br>
<textarea id="body" placeholder="Email body..."></textarea><br>
<button onclick="classify()">Classify</button>
<div id="result"></div>
<script>function classify(){fetch('/api/hermes/skills/email/classify',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({subject:document.getElementById('subject').value,body:document.getElementById('body').value})}).then(r=>r.json()).then(d=>{document.getElementById('result').innerHTML='<div class="result"><p>Priority: <strong>'+d.priority+'</strong></p><p>Category: <strong>'+d.category+'</strong></p></div>'})}</script></body></html>"""
