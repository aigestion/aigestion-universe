"""
System 59: Firewall Monitor
Firewall rules and traffic monitoring
"""

import json
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
    return FW_HTML


@app.route("/api/firewall/rules")
def rules():
    return jsonify(
        {
            "rules": [
                {
                    "id": 1,
                    "name": "Allow HTTPS Out",
                    "action": "allow",
                    "direction": "outbound",
                    "port": "443",
                    "proto": "TCP",
                    "enabled": True,
                },
                {
                    "id": 2,
                    "name": "Allow HTTP Out",
                    "action": "allow",
                    "direction": "outbound",
                    "port": "80",
                    "proto": "TCP",
                    "enabled": True,
                },
                {
                    "id": 3,
                    "name": "Block Telnet In",
                    "action": "block",
                    "direction": "inbound",
                    "port": "23",
                    "proto": "TCP",
                    "enabled": True,
                },
                {
                    "id": 4,
                    "name": "Block FTP In",
                    "action": "block",
                    "direction": "inbound",
                    "port": "21",
                    "proto": "TCP",
                    "enabled": True,
                },
                {
                    "id": 5,
                    "name": "Allow SSH Out",
                    "action": "allow",
                    "direction": "outbound",
                    "port": "22",
                    "proto": "TCP",
                    "enabled": True,
                },
                {
                    "id": 6,
                    "name": "Block SMB In",
                    "action": "block",
                    "direction": "inbound",
                    "port": "445",
                    "proto": "TCP",
                    "enabled": True,
                },
            ]
        }
    )


@app.route("/api/firewall/blocked")
def blocked():
    return jsonify(
        {
            "blocked": [
                {"ip": "45.33.32.156", "reason": "Known scanner", "attempts": 23, "last": "14:32"},
                {"ip": "185.220.101.1", "reason": "Tor exit node", "attempts": 5, "last": "14:28"},
                {
                    "ip": "103.224.182.250",
                    "reason": "Brute force",
                    "attempts": 156,
                    "last": "14:15",
                },
            ]
        }
    )


FW_HTML = r"""
<!DOCTYPE html>
<html><head><meta charset="UTF-8"><title>Firewall Monitor</title>
<style>
*{margin:0;padding:0;box-sizing:border-box}
body{background:#0a0a1a;color:#e2e8f0;font-family:'Rajdhani',sans-serif;padding:20px}
h1{font-family:'Orbitron',monospace;color:#00f0ff;font-size:20px;letter-spacing:3px;margin-bottom:20px}
.stats{display:grid;grid-template-columns:repeat(4,1fr);gap:10px;margin-bottom:20px}
.stat-box{background:rgba(3,8,20,0.8);border:1px solid rgba(0,240,255,0.12);border-radius:10px;padding:12px;text-align:center}
.stat-val{font-family:'Orbitron',monospace;font-size:22px;color:#00f0ff}
.stat-label{font-size:9px;color:#64748b;letter-spacing:1px;margin-top:4px}
.section{background:rgba(3,8,20,0.8);border:1px solid rgba(0,240,255,0.12);border-radius:10px;padding:14px;margin-bottom:12px}
.section-title{font-family:'Orbitron',monospace;font-size:12px;color:#00f0ff;margin-bottom:10px;letter-spacing:1px}
table{width:100%;border-collapse:collapse;font-size:11px}
th{text-align:left;padding:6px;border-bottom:1px solid rgba(0,240,255,0.12);color:#64748b;font-size:9px;letter-spacing:1px}
td{padding:6px;border-bottom:1px solid rgba(0,240,255,0.05);font-family:'Share Tech Mono',monospace;font-size:10px}
.action{padding:2px 6px;border-radius:4px;font-size:9px}
.action.allow{background:rgba(34,197,94,0.1);color:#22c55e}
.action.block{background:rgba(255,0,85,0.1);color:#ff0055}
.switch{width:32px;height:18px;background:rgba(0,240,255,0.1);border:1px solid rgba(0,240,255,0.2);border-radius:9px;cursor:pointer;position:relative;display:inline-block}
.switch.on{background:rgba(34,197,94,0.2);border-color:#22c55e}
.switch::after{content:'';position:absolute;top:2px;left:2px;width:12px;height:12px;background:#22c55e;border-radius:50%;transition:0.3s}
.switch.on::after{left:16px}
.blocked-ip{display:flex;justify-content:space-between;padding:6px 0;border-bottom:1px solid rgba(0,240,255,0.05);font-size:11px}
.ip{color:#ff0055;font-family:'Share Tech Mono',monospace}.reason{color:#f59e0b;font-size:10px}.attempts{color:#64748b;font-size:10px}
</style></head><body>
<h1>FIREWALL MONITOR</h1>
<div class="stats">
  <div class="stat-box"><div class="stat-val" id="rulesCount">6</div><div class="stat-label">RULES</div></div>
  <div class="stat-box"><div class="stat-val" id="blockedCount">3</div><div class="stat-label">BLOCKED IPs</div></div>
  <div class="stat-box"><div class="stat-val" style="color:#22c55e">Active</div><div class="stat-label">STATUS</div></div>
  <div class="stat-box"><div class="stat-val" id="attempts">184</div><div class="stat-label">TOTAL ATTEMPTS</div></div>
</div>
<div class="section"><div class="section-title">FIREWALL RULES</div>
  <table><thead><tr><th>NAME</th><th>ACTION</th><th>DIR</th><th>PORT</th><th>PROTO</th><th>ON</th></tr></thead>
  <tbody id="rulesTable"></tbody></table>
</div>
<div class="section"><div class="section-title">BLOCKED IPs</div><div id="blocked"></div></div>
<script>
async function load(){
  const r=await(await fetch('/api/firewall/rules')).json();
  document.getElementById('rulesCount').textContent=(r.rules||[]).length;
  document.getElementById('rulesTable').innerHTML=(r.rules||[]).map(rule=>
    '<tr><td>'+rule.name+'</td><td><span class="action '+rule.action+'">'+rule.action.toUpperCase()+'</span></td>'+
    '<td>'+rule.direction+'</td><td>'+rule.port+'</td><td>'+rule.proto+'</td>'+
    '<td><div class="switch'+(rule.enabled?' on':'')+'" onclick="this.classList.toggle(\'on\')"></div></td></tr>'
  ).join('');
  const b=await(await fetch('/api/firewall/blocked')).json();
  document.getElementById('blockedCount').textContent=(b.blocked||[]).length;
  document.getElementById('attempts').textContent=(b.blocked||[]).reduce((a,c)=>a+c.attempts,0);
  document.getElementById('blocked').innerHTML=(b.blocked||[]).map(c=>
    '<div class="blocked-ip"><span class="ip">'+c.ip+'</span><span class="reason">'+c.reason+'</span><span class="attempts">'+c.attempts+' attempts</span><span class="attempts">'+c.last+'</span></div>'
  ).join('');
}
load();
</script></body></html>
"""

if __name__ == "__main__":
    print("[System 59] Firewall Monitor starting on port 5069...")
    app.run(host="0.0.0.0", port=5069, debug=False)
