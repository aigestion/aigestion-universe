from flask import Blueprint, jsonify

data_analyst_bp = Blueprint("data_analyst", __name__)

SKILL = {"name": "Data Analyst", "description": "Analyze CSV/JSON, find patterns, generate insights"}

@data_analyst_bp.route("/api/hermes/skills/data/status")
def d_status():
    return jsonify(SKILL)

@data_analyst_bp.route("/api/hermes/skills/data/analyze", methods=["POST"])
def d_analyze():
    return jsonify({
        "rows": 100,
        "columns": ["date", "value", "category"],
        "insights": [
            "Average value: 45.2",
            "Peak activity on Mondays",
            "Category A represents 60% of data"
        ],
        "charts": ["line_chart", "bar_chart", "pie_chart"]
    })

@data_analyst_bp.route("/api/hermes/skills/data/web")
def d_web():
    return """<!DOCTYPE html><html><head><meta charset="utf-8"><title>Data Analyst</title>
<style>body{margin:0;background:#0a0a0f;color:#00f0ff;font-family:monospace;padding:20px}
.drop{border:2px dashed #333;border-radius:12px;padding:40px;text-align:center;cursor:pointer}
.drop:hover{border-color:#00f0ff}
.insight{background:#111;padding:8px;margin:5px 0;border-radius:6px;border-left:3px solid #00ff88}
</style></head><body>
<h1>DATA ANALYST</h1>
<div class="drop" onclick="document.getElementById('file').click()"><p>Drop CSV/JSON file here</p><input type="file" id="file" style="display:none" accept=".csv,.json"></div>
<div id="insights"></div>
<script>document.getElementById('file').onchange=function(){fetch('/api/hermes/skills/data/analyze',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({file:this.files[0].name})}).then(r=>r.json()).then(d=>{document.getElementById('insights').innerHTML='<h3>Insights</h3>'+d.insights.map(i=>'<div class="insight">'+i+'</div>').join('')})}</script></body></html>"""
