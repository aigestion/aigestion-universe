"""
System 27: Pixel Art Dashboard
Dashboard estilo 8-bit que muestra stats del sistema
"""

import time

import psutil
from flask import Flask, jsonify

app = Flask(__name__)


@app.route("/")
def index():
    return PIXEL_HTML


@app.route("/api/pixel/stats")
def stats():
    cpu = psutil.cpu_percent(interval=0.1)
    mem = psutil.virtual_memory()
    disk = psutil.disk_usage("/")
    net = psutil.net_io_counters()
    return jsonify(
        {
            "cpu": cpu,
            "memory_percent": mem.percent,
            "memory_used_gb": round(mem.used / (1024**3), 1),
            "memory_total_gb": round(mem.total / (1024**3), 1),
            "disk_percent": disk.percent,
            "disk_used_gb": round(disk.used / (1024**3), 1),
            "disk_total_gb": round(disk.total / (1024**3), 1),
            "net_sent_mb": round(net.bytes_sent / (1024**2), 1),
            "net_recv_mb": round(net.bytes_recv / (1024**2), 1),
            "uptime": int(time.time() - psutil.boot_time()),
        }
    )


PIXEL_HTML = r"""
<!DOCTYPE html>
<html><head><meta charset="UTF-8"><title>Pixel Art Dashboard</title>
<style>
*{margin:0;padding:0;box-sizing:border-box}
body{background:#1a1a2e;color:#e2e8f0;font-family:'Share Tech Mono',monospace;padding:20px;display:flex;flex-direction:column;align-items:center;min-height:100vh}
h1{font-size:24px;color:#00ff41;letter-spacing:4px;margin:20px 0;text-shadow:2px 2px #000}
.dashboard{display:grid;grid-template-columns:repeat(4,1fr);gap:12px;max-width:800px}
.pixel-card{background:#16213e;border:3px solid #0f3460;border-radius:0;padding:12px;position:relative;image-rendering:pixelated}
.pixel-card::before{content:'';position:absolute;top:-3px;left:-3px;right:-3px;bottom:-3px;border:3px solid #00ff41;opacity:0.2;pointer-events:none}
.pixel-label{font-size:10px;color:#64748b;letter-spacing:2px;text-transform:uppercase}
.pixel-value{font-size:28px;color:#00ff41;margin:8px 0;text-shadow:1px 1px #000}
.pixel-bar{height:12px;background:#0a0a2e;border:2px solid #0f3460;margin-top:8px;position:relative;overflow:hidden}
.pixel-fill{height:100%;transition:width 0.5s;image-rendering:pixelated}
.pixel-fill.green{background:#22c55e}
.pixel-fill.yellow{background:#f59e0b}
.pixel-fill.red{background:#ef4444}
.pixel-fill.cyan{background:#00f0ff}
.pixel-char{font-size:32px;text-align:center;margin:4px 0}
</style></head><body>
<h1>PIXEL DASHBOARD</h1>
<div class="dashboard" id="dash"></div>
<script>
function barColor(pct){return pct>80?'red':pct>60?'yellow':'green'}
function pixelChar(pct){return pct>80?'[!!!]':pct>60?'[..]':'[OK]'}
async function load(){
  const s=await(await fetch('/api/pixel/stats')).json();
  const uptimeH=Math.floor(s.uptime/3600);const uptimeM=Math.floor((s.uptime%3600)/60);
  document.getElementById('dash').innerHTML=
    '<div class="pixel-card"><div class="pixel-label">CPU</div><div class="pixel-char">'+pixelChar(s.cpu)+'</div><div class="pixel-value">'+Math.round(s.cpu)+'%</div><div class="pixel-bar"><div class="pixel-fill '+barColor(s.cpu)+'" style="width:'+s.cpu+'%"></div></div></div>'+
    '<div class="pixel-card"><div class="pixel-label">MEMORY</div><div class="pixel-char">'+pixelChar(s.memory_percent)+'</div><div class="pixel-value">'+Math.round(s.memory_percent)+'%</div><div class="pixel-bar"><div class="pixel-fill '+barColor(s.memory_percent)+'" style="width:'+s.memory_percent+'%"></div></div><div style="font-size:10px;color:#64748b;margin-top:4px">'+s.memory_used_gb+'/'+s.memory_total_gb+' GB</div></div>'+
    '<div class="pixel-card"><div class="pixel-label">DISK</div><div class="pixel-char">'+pixelChar(s.disk_percent)+'</div><div class="pixel-value">'+Math.round(s.disk_percent)+'%</div><div class="pixel-bar"><div class="pixel-fill '+barColor(s.disk_percent)+'" style="width:'+s.disk_percent+'%"></div></div><div style="font-size:10px;color:#64748b;margin-top:4px">'+s.disk_used_gb+'/'+s.disk_total_gb+' GB</div></div>'+
    '<div class="pixel-card"><div class="pixel-label">NETWORK</div><div class="pixel-char">[TX]</div><div class="pixel-value" style="font-size:18px">'+s.net_sent_mb+' MB</div><div style="font-size:10px;color:#64748b">TX Sent</div></div>'+
    '<div class="pixel-card" style="grid-column:span 2"><div class="pixel-label">UPTIME</div><div class="pixel-value">'+uptimeH+'h '+uptimeM+'m</div></div>'+
    '<div class="pixel-card" style="grid-column:span 2"><div class="pixel-label">NETWORK RX</div><div class="pixel-value" style="font-size:18px">'+s.net_recv_mb+' MB</div><div style="font-size:10px;color:#64748b">Received</div></div>';
}
load();setInterval(load,2000);
</script></body></html>
"""

if __name__ == "__main__":
    print("[System 27] Pixel Art Dashboard starting on port 5037...")
    app.run(host="0.0.0.0", port=5037, debug=False)
