from flask import Blueprint, jsonify, request

code_review_bp = Blueprint("code_review", __name__)

SKILL = {
    "name": "Code Review",
    "description": "Automatic code review with bug detection and improvements",
    "commands": ["/review", "/audit", "/security"]
}

@code_review_bp.route("/api/hermes/skills/code-review/status")
def cr_status():
    return jsonify(SKILL)

@code_review_bp.route("/api/hermes/skills/code-review/review", methods=["POST"])
def cr_review():
    data = request.json or {}
    code = data.get("code", "")
    findings = []
    if "eval(" in code:
        findings.append({"severity": "critical", "message": "eval() is dangerous, avoid it"})
    if "password" in code.lower() and "=" in code:
        findings.append({"severity": "warning", "message": "Hardcoded password detected"})
    if "TODO" in code:
        findings.append({"severity": "info", "message": "TODO found in code"})
    if len(code.split("\n")) > 100:
        findings.append({"severity": "info", "message": "Function too long (>100 lines)"})
    if not findings:
        findings.append({"severity": "ok", "message": "No issues found"})
    return jsonify({"findings": findings, "score": max(0, 100 - len(findings) * 15)})

@code_review_bp.route("/api/hermes/skills/code-review/web")
def cr_web():
    return """<!DOCTYPE html><html><head><meta charset="utf-8"><title>Code Review</title>
<style>body{margin:0;background:#0a0a0f;color:#00f0ff;font-family:monospace;padding:20px}
textarea{width:100%;height:300px;background:#111;border:1px solid #333;color:#00f0ff;padding:10px;border-radius:8px;font-family:monospace;font-size:12px}
button{background:#00f0ff22;border:1px solid #00f0ff;color:#00f0ff;padding:10px 20px;border-radius:6px;cursor:pointer;margin-top:10px}
.finding{padding:8px;margin:5px 0;border-radius:6px;font-size:12px}
.critical{background:#ff006622;border-left:3px solid #ff0066}
.warning{background:#ff880022;border-left:3px solid #ff8800}
.info{background:#00f0ff22;border-left:3px solid #00f0ff}
.ok{background:#00ff8822;border-left:3px solid #00ff88}
</style></head><body>
<h1>CODE REVIEW</h1>
<textarea id="code" placeholder="Paste your code here..."></textarea><br>
<button onclick="review()">Review Code</button>
<div id="results"></div>
<script>function review(){fetch('/api/hermes/skills/code-review/review',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({code:document.getElementById('code').value})}).then(r=>r.json()).then(d=>{document.getElementById('results').innerHTML='<h3>Score: '+d.score+'/100</h3>'+d.findings.map(f=>'<div class="'+f.severity+'">'+f.message+'</div>').join('')})}</script></body></html>"""
