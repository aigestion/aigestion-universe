from flask import Blueprint, jsonify, request

theme_bp = Blueprint("theme_engine", __name__)

THEMES = {
    "dark": {"bg": "#0a0a0f", "cyan": "#00f0ff", "magenta": "#ff0066", "green": "#00ff88"},
    "light": {"bg": "#f0f0f0", "cyan": "#0066cc", "magenta": "#cc0044", "green": "#008844"},
    "neon": {"bg": "#0a001a", "cyan": "#00ffff", "magenta": "#ff00ff", "green": "#00ff88"},
    "terminal": {"bg": "#000000", "cyan": "#00ff00", "magenta": "#ff0000", "green": "#ffff00"}
}

_state = {"active": "dark", "auto": True, "transition": True}

@theme_bp.route("/api/frontend/theme/status")
def t_status():
    return jsonify({"theme": _state["active"], "themes": list(THEMES.keys()), "auto": _state["auto"]})

@theme_bp.route("/api/frontend/theme/set", methods=["POST"])
def t_set():
    data = request.json or {}
    if data.get("theme") in THEMES:
        _state["active"] = data["theme"]
    _state["auto"] = data.get("auto", _state["auto"])
    return jsonify({"ok": True, "theme": _state["active"]})

@theme_bp.route("/api/frontend/theme/web")
def t_web():
    return """<!DOCTYPE html><html><head><meta charset="utf-8"><title>Theme Engine</title>
<style>body{margin:0;background:#0a0a0f;color:#00f0ff;font-family:monospace;padding:20px}
.themes{display:flex;gap:10px;margin:20px 0;flex-wrap:wrap}
.theme-btn{padding:15px 20px;border:2px solid #333;border-radius:12px;cursor:pointer;font-size:14px;background:#111;color:#fff;transition:all .3s}
.theme-btn.active{border-color:#00f0ff;background:#00f0ff22}
</style></head><body><h1>THEME ENGINE</h1>
<div class="themes" id="themes"></div>
<p>Active: <strong id="active">dark</strong></p>
<p>Auto: <span id="auto">true</span></p>
<script>const themes=['dark','light','neon','terminal'];const colors={dark:{bg:'#0a0a0f',c:'#00f0ff'},light:{bg:'#f0f0f0',c:'#0066cc'},neon:{bg:'#0a001a',c:'#00ffff'},terminal:{bg:'#000000',c:'#00ff00'}};
const t=document.getElementById('themes');themes.forEach(th=>{const b=document.createElement('button');b.className='theme-btn';b.textContent=th;b.style.borderColor=colors[th].c;b.onclick=()=>{fetch('/api/frontend/theme/set',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({theme:th})}).then(()=>{document.querySelectorAll('.theme-btn').forEach(x=>x.classList.remove('active'));b.classList.add('active');document.getElementById('active').textContent=th})};t.appendChild(b)});
document.querySelector('.theme-btn').classList.add('active')</script></body></html>"""
