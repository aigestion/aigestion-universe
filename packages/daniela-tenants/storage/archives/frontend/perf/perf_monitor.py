# -*- coding: utf-8 -*-
from flask import Blueprint, jsonify, request
import time

perf_bp = Blueprint("perf_monitor", __name__)

_metrics = {"lcp": 1200, "fid": 50, "cls": 0.01, "ttfb": 200, "fcp": 800, "inp": 100}

@perf_bp.route("/api/frontend/perf/status")
def p_status():
    return jsonify(_metrics)

@perf_bp.route("/api/frontend/perf/measure", methods=["POST"])
def p_measure():
    data = request.json or {}
    metric = data.get("metric", "")
    value = data.get("value", 0)
    _metrics[metric] = value
    return jsonify({"ok": True, "metric": metric, "value": value})

@perf_bp.route("/api/frontend/perf/web")
def p_web():
    return """<!DOCTYPE html><html><head><meta charset="utf-8"><title>Performance Monitor</title>
<style>body{margin:0;background:#0a0a0f;color:#00f0ff;font-family:monospace;padding:20px}
.metrics{display:grid;grid-template-columns:repeat(auto-fill,minmax(150px,1fr));gap:10px;margin:20px 0}
.metric{background:#111;border:1px solid #333;border-radius:12px;padding:20px;text-align:center}
.metric .val{font-size:28px;color:#00ff88}
.metric .label{font-size:10px;color:#666;margin-top:4px}
.good{color:#00ff88} .warn{color:#ff8800} .bad{color:#ff0066}
</style></head><body><h1>PERFORMANCE MONITOR</h1>
<div class="metrics" id="metrics"></div>
<p id="score">Lighthouse Score: --</p>
<script>const good={"lcp":2500,"fid":100,"cls":0.1,"ttfb":800,"fcp":1800,"inp":200};
function load(){fetch('/api/frontend/perf/status').then(r=>r.json()).then(d=>{document.getElementById('metrics').innerHTML=Object.entries(d).map(([k,v])=>'<div class="metric"><div class="val '+(v<=good[k]?'good':'warn')+'">'+v+'</div><div class="label">'+k.toUpperCase()+'</div></div>').join('');const score=Object.entries(d).filter(([k])=>k in good).reduce((s,[k,v])=>s+(v<=good[k]?1:0),0)/Object.keys(good).length*100;document.getElementById('score').textContent='Lighthouse Score: '+Math.round(score)});setTimeout(load,3000)}
load()</script></body></html>"""
