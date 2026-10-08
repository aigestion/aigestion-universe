"""
System 54: Network Sentinel
Network monitoring and traffic analysis
"""

import json
import socket
from pathlib import Path

from flask import Flask, jsonify

app = Flask(__name__)
DATA_DIR = Path(__file__).parent / "data"
DATA_DIR.mkdir(exist_ok=True)


def load_json(path, default=None):
    if path.exists():
        with open(path, encoding="utf-8") as f:
            return json.load(f)
    return default or {}


def save_json(path, data):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


@app.route("/")
def index():
    return NET_HTML


@app.route("/api/net/stats")
def net_stats():
    connections = [
        {
            "local": "192.168.1.100:5020",
            "remote": "192.168.1.1:443",
            "state": "ESTABLISHED",
            "process": "python",
            "protocol": "TCP",
        },
        {
            "local": "192.168.1.100:5000",
            "remote": "192.168.1.1:80",
            "state": "LISTENING",
            "process": "python",
            "protocol": "TCP",
        },
        {
            "local": "192.168.1.100:443",
            "remote": "0.0.0.0:0",
            "state": "LISTENING",
            "process": "nginx",
            "protocol": "TCP",
        },
        {
            "local": "192.168.1.100:53",
            "remote": "0.0.0.0:0",
            "state": "LISTENING",
            "process": "dns",
            "protocol": "UDP",
        },
    ]
    traffic = {
        "in_bytes": 12478923,
        "out_bytes": 3456128,
        "packets_in": 15234,
        "packets_out": 8923,
        "errors": 12,
    }
    return jsonify(
        {"connections": connections, "traffic": traffic, "hostname": socket.gethostname()}
    )


NET_HTML = r"""
<!DOCTYPE html>
<html><head><meta charset="UTF-8"><title>Network Sentinel</title>
<style>
*{margin:0;padding:0;box-sizing:border-box}
body{background:#0a0a1a;color:#e2e8f0;font-family:'Rajdhani',sans-serif;padding:20px}
h1{font-family:'Orbitron',monospace;color:#00f0ff;font-size:20px;letter-spacing:3px;margin-bottom:20px}
.stats{display:grid;grid-template-columns:repeat(4,1fr);gap:10px;margin-bottom:20px}
.stat-box{background:rgba(3,8,20,0.8);border:1px solid rgba(0,240,255,0.12);border-radius:10px;padding:12px;text-align:center}
.stat-val{font-family:'Orbitron',monospace;font-size:18px;color:#00f0ff}
.stat-label{font-size:9px;color:#64748b;letter-spacing:1px;margin-top:4px}
.section{background:rgba(3,8,20,0.8);border:1px solid rgba(0,240,255,0.12);border-radius:10px;padding:14px;margin-bottom:12px}
.section-title{font-family:'Orbitron',monospace;font-size:12px;color:#00f0ff;margin-bottom:10px;letter-spacing:1px}
table{width:100%;border-collapse:collapse;font-size:11px}
th{text-align:left;padding:6px;border-bottom:1px solid rgba(0,240,255,0.12);color:#64748b;font-size:9px;letter-spacing:1px}
td{padding:6px;border-bottom:1px solid rgba(0,240,255,0.05);font-family:'Share Tech Mono',monospace;font-size:10px}
.state{padding:2px 6px;border-radius:4px;font-size:9px}
.state.est{background:rgba(34,197,94,0.1);color:#22c55e}
.state.list{background:rgba(0,240,255,0.1);color:#00f0ff}
.state.close{background:rgba(255,0,85,0.1);color:#ff0055}
.chart{height:80px;display:flex;align-items:flex-end;gap:2px;margin-top:8px}
.bar{flex:1;background:linear-gradient(to top,rgba(0,240,255,0.2),rgba(0,240,255,0.6));border-radius:2px 2px 0 0;min-height:4px;transition:height 0.3s}
</style></head><body>
<h1>NETWORK SENTINEL</h1>
<div class="stats">
  <div class="stat-box"><div class="stat-val" id="connCount">0</div><div class="stat-label">CONNECTIONS</div></div>
  <div class="stat-box"><div class="stat-val" id="inTraffic">0</div><div class="stat-label">INBOUND</div></div>
  <div class="stat-box"><div class="stat-val" id="outTraffic">0</div><div class="stat-label">OUTBOUND</div></div>
  <div class="stat-box"><div class="stat-val" id="errors">0</div><div class="stat-label">ERRORS</div></div>
</div>
<div class="section">
  <div class="section-title">TRAFFIC HISTORY</div>
  <div class="chart" id="chart"></div>
</div>
<div class="section">
  <div class="section-title">ACTIVE CONNECTIONS</div>
  <table><thead><tr><th>LOCAL</th><th>REMOTE</th><th>STATE</th><th>PROCESS</th><th>PROTO</th></tr></thead>
  <tbody id="connTable"></tbody></table>
</div>
<script>
function fmt(b){if(b>1e6)return(b/1e6).toFixed(1)+' MB';if(b>1e3)return(b/1e3).toFixed(1)+' KB';return b+' B'}
let history=Array(30).fill(0).map(()=>Math.floor(Math.random()*100));
async function load(){
  const r=await(await fetch('/api/net/stats')).json();
  document.getElementById('connCount').textContent=(r.connections||[]).length;
  document.getElementById('inTraffic').textContent=fmt(r.traffic.in_bytes);
  document.getElementById('outTraffic').textContent=fmt(r.traffic.out_bytes);
  document.getElementById('errors').textContent=r.traffic.errors;
  document.getElementById('connTable').innerHTML=(r.connections||[]).map(c=>
    '<tr><td>'+c.local+'</td><td>'+c.remote+'</td><td><span class="state '+(c.state==='ESTABLISHED'?'est':c.state==='LISTENING'?'list':'close')+'">'+c.state+'</span></td><td>'+c.process+'</td><td>'+c.protocol+'</td></tr>'
  ).join('');
}
function updateChart(){
  history.push(Math.floor(Math.random()*100));if(history.length>30)history.shift();
  const max=Math.max(...history)||1;
  document.getElementById('chart').innerHTML=history.map(v=>'<div class="bar" style="height:'+(v/max*100)+'%"></div>').join('');
}
setInterval(updateChart,2000);updateChart();load();setInterval(load,5000);
</script></body></html>
"""

if __name__ == "__main__":
    print("[System 54] Network Sentinel starting on port 5064...")
    app.run(host="0.0.0.0", port=5064, debug=False)
