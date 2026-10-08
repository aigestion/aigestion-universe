"""
System 55: File Integrity
File integrity checker and monitor
"""

import hashlib
import json
import time
from pathlib import Path

from flask import Flask, jsonify, request

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


def file_hash(path):
    h = hashlib.sha256()
    try:
        with open(path, "rb") as f:
            for chunk in iter(lambda: f.read(8192), b""):
                h.update(chunk)
        return h.hexdigest()
    except Exception:
        return None


@app.route("/")
def index():
    return INTEGRITY_HTML


@app.route("/api/integrity/scan", methods=["POST"])
def scan():
    data = request.json or {}
    watch_dir = data.get("dir", str(Path.home()))
    results = []
    try:
        for f in list(Path(watch_dir).glob("*"))[:100]:
            if f.is_file():
                h = file_hash(f)
                results.append(
                    {
                        "name": f.name,
                        "path": str(f),
                        "hash": h[:16] if h else "N/A",
                        "size": f.stat().st_size,
                        "modified": f.stat().st_mtime,
                    }
                )
    except Exception:
        pass
    scan_data = load_json(DATA_DIR / "scans.json", {"scans": []})
    scan_data["scans"].append({"dir": watch_dir, "time": time.time(), "files": len(results)})
    if len(scan_data["scans"]) > 20:
        scan_data["scans"] = scan_data["scans"][-20:]
    save_json(DATA_DIR / "scans.json", scan_data)
    return jsonify({"files": results, "total": len(results)})


@app.route("/api/integrity/history")
def history():
    return jsonify(load_json(DATA_DIR / "scans.json", {"scans": []}))


INTEGRITY_HTML = r"""
<!DOCTYPE html>
<html><head><meta charset="UTF-8"><title>File Integrity</title>
<style>
*{margin:0;padding:0;box-sizing:border-box}
body{background:#0a0a1a;color:#e2e8f0;font-family:'Rajdhani',sans-serif;padding:20px}
h1{font-family:'Orbitron',monospace;color:#00f0ff;font-size:20px;letter-spacing:3px;margin-bottom:20px}
.scan-bar{display:flex;gap:8px;margin-bottom:16px}
.input{flex:1;background:rgba(0,240,255,0.03);border:1px solid rgba(0,240,255,0.12);color:#e2e8f0;padding:8px 12px;border-radius:6px;font-family:inherit;font-size:12px}
.btn{background:rgba(0,240,255,0.1);border:1px solid #00f0ff;color:#00f0ff;padding:8px 14px;border-radius:6px;cursor:pointer;font-size:11px;font-family:inherit}
.results{background:rgba(3,8,20,0.8);border:1px solid rgba(0,240,255,0.12);border-radius:10px;padding:14px;max-height:400px;overflow-y:auto}
.file{display:flex;justify-content:space-between;padding:6px 0;border-bottom:1px solid rgba(0,240,255,0.05);font-size:11px}
.file-name{color:#e2e8f0;flex:1}.file-hash{color:#64748b;font-family:'Share Tech Mono',monospace;font-size:10px;width:120px}
.file-size{color:#94a3b8;width:80px;text-align:right}
.history{margin-top:16px;background:rgba(3,8,20,0.8);border:1px solid rgba(255,0,85,0.2);border-radius:10px;padding:14px}
.history-entry{display:flex;justify-content:space-between;padding:4px 0;border-bottom:1px solid rgba(0,240,255,0.05);font-size:10px;color:#64748b}
</style></head><body>
<h1>FILE INTEGRITY CHECKER</h1>
<div class="scan-bar">
  <input class="input" id="dir" placeholder="Directory to scan" value="">
  <button class="btn" onclick="scan()">Scan</button>
</div>
<div class="results" id="results"><div style="color:#64748b">Enter a directory and click Scan</div></div>
<div class="history">
  <div style="font-size:12px;color:#00f0ff;font-family:'Orbitron',monospace;margin-bottom:8px">SCAN HISTORY</div>
  <div id="history"></div>
</div>
<script>
function fmt(b){if(b>1e6)return(b/1e6).toFixed(1)+' MB';if(b>1e3)return(b/1e3).toFixed(1)+' KB';return b+' B'}
async function scan(){
  const dir=document.getElementById('dir').value||'C:\\Users\\Alejandro';
  document.getElementById('results').innerHTML='<div style="color:#00f0ff">Scanning...</div>';
  const r=await(await fetch('/api/integrity/scan',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({dir})})).json();
  document.getElementById('results').innerHTML=(r.files||[]).map(f=>
    '<div class="file"><span class="file-name">'+f.name+'</span><span class="file-hash">'+f.hash+'</span><span class="file-size">'+fmt(f.size)+'</span></div>'
  ).join('')||'<div style="color:#64748b">No files found</div>';
  loadHistory();
}
async function loadHistory(){
  const r=await(await fetch('/api/integrity/history')).json();
  document.getElementById('history').innerHTML=(r.scans||[]).reverse().map(s=>
    '<div class="history-entry"><span>'+new Date(s.time*1000).toLocaleString()+'</span><span>'+s.dir+'</span><span>'+s.files+' files</span></div>'
  ).join('')||'<div style="color:#64748b">No scans yet</div>';
}
loadHistory();
</script></body></html>
"""

if __name__ == "__main__":
    print("[System 55] File Integrity starting on port 5065...")
    app.run(host="0.0.0.0", port=5065, debug=False)
