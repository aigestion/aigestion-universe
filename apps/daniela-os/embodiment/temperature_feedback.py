from flask import Blueprint, jsonify

temp_bp = Blueprint("temperature_feedback", __name__)
_state = {"device_temp": 25.0, "ambient": 22.0, "comfortable": True}


@temp_bp.route("/api/embodiment/temp/status")
def t_status():
    return jsonify(_state)


@temp_bp.route("/api/embodiment/temp/web")
def t_web():
    return """<!DOCTYPE html>
<html><head><meta charset="utf-8"><title>Temperature Feedback</title>
<style>body{margin:0;background:#0a0a0f;color:#00f0ff;font-family:monospace;display:flex;justify-content:center;align-items:center;height:100vh}
.thermo{text-align:center}
.temp-display{font-size:80px;margin:20px 0}
.temp-bar{width:30px;height:200px;background:#222;border-radius:15px;margin:20px auto;position:relative;overflow:hidden}
.temp-fill{position:absolute;bottom:0;width:100%;background:linear-gradient(to top,#4488ff,#00f0ff,#ff8800,#ff0066);border-radius:15px;transition:height .5s}
</style></head><body>
<div class="thermo">
<h2>TEMPERATURE</h2>
<div class="temp-display" id="temp">25.0°C</div>
<div class="temp-bar"><div class="temp-fill" id="fill" style="height:50%"></div></div>
<p id="status">Comfortable</p>
</div>
<script>setInterval(()=>{fetch('/api/embodiment/temp/status').then(r=>r.json()).then(d=>{document.getElementById('temp').textContent=d.ambient+'°C';document.getElementById('fill').style.height=Math.min(100,Math.max(0,(d.ambient/40)*100))+'%';document.getElementById('status').textContent=d.comfortable?'Comfortable':'Too hot/cold'})},5000)</script>
</body></html>"""
