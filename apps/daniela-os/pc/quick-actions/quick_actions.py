"""
System 35: Quick Actions Bar
Floating bar with contextual quick actions
"""

import json
import subprocess
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


DEFAULT_ACTIONS = [
    {"id": 1, "name": "Calculator", "icon": "calc", "cmd": "calc", "category": "apps"},
    {"id": 2, "name": "Notepad", "icon": "notepad", "cmd": "notepad", "category": "apps"},
    {"id": 3, "name": "Terminal", "icon": "terminal", "cmd": "wt", "category": "apps"},
    {"id": 4, "name": "Explorer", "icon": "explorer", "cmd": "explorer", "category": "apps"},
    {"id": 5, "name": "Screenshot", "icon": "camera", "cmd": "screenshot", "category": "tools"},
    {
        "id": 6,
        "name": "Lock PC",
        "icon": "lock",
        "cmd": "rundll32.exe user32.dll,LockWorkStation",
        "category": "system",
    },
    {"id": 7, "name": "Volume Up", "icon": "volume", "cmd": "volume_up", "category": "system"},
    {"id": 8, "name": "Volume Down", "icon": "mute", "cmd": "volume_down", "category": "system"},
]


@app.route("/")
def index():
    return ACTIONS_HTML


@app.route("/api/actions/list")
def list_actions():
    actions = load_json(DATA_DIR / "actions.json", {"actions": DEFAULT_ACTIONS})
    return jsonify(actions)


@app.route("/api/actions/add", methods=["POST"])
def add_action():
    data = request.json or {}
    actions = load_json(DATA_DIR / "actions.json", {"actions": DEFAULT_ACTIONS})
    action = {
        "id": int(time.time()),
        "name": data.get("name", ""),
        "icon": data.get("icon", "play"),
        "cmd": data.get("cmd", ""),
        "category": data.get("category", "custom"),
    }
    actions["actions"].append(action)
    save_json(DATA_DIR / "actions.json", actions)
    return jsonify({"ok": True})


@app.route("/api/actions/execute", methods=["POST"])
def execute():
    data = request.json or {}
    cmd = data.get("cmd", "")
    if cmd == "screenshot":
        subprocess.run(
            [
                "powershell",
                "-Command",
                "Add-Type -AssemblyName System.Windows.Forms; [System.Windows.Forms.SendKeys]::SendWait('{PRTSC}')",
            ],
            timeout=5,
        )
    elif cmd == "volume_up":
        subprocess.run(
            [
                "powershell",
                "-Command",
                "$obj = New-Object -ComObject WScript.Shell; $obj.SendKeys([char]175)",
            ],
            timeout=3,
        )
    elif cmd == "volume_down":
        subprocess.run(
            [
                "powershell",
                "-Command",
                "$obj = New-Object -ComObject WScript.Shell; $obj.SendKeys([char]174)",
            ],
            timeout=3,
        )
    else:
        try:
            subprocess.Popen([cmd], shell=True)
        except Exception:
            pass
    return jsonify({"ok": True})


@app.route("/api/actions/delete", methods=["POST"])
def delete_action():
    data = request.json or {}
    actions = load_json(DATA_DIR / "actions.json", {"actions": DEFAULT_ACTIONS})
    actions["actions"] = [a for a in actions["actions"] if a["id"] != data.get("id")]
    save_json(DATA_DIR / "actions.json", actions)
    return jsonify({"ok": True})


ACTIONS_HTML = r"""
<!DOCTYPE html>
<html><head><meta charset="UTF-8"><title>Quick Actions Bar</title>
<style>
*{margin:0;padding:0;box-sizing:border-box}
html,body{width:100vw;height:100vh;overflow:hidden;background:#030814;font-family:'Rajdhani',sans-serif}
#bar{position:fixed;bottom:30px;left:50%;transform:translateX(-50%);z-index:1000;display:flex;gap:8px;padding:10px 16px;background:rgba(3,8,20,0.9);border:1px solid rgba(0,240,255,0.2);border-radius:16px;backdrop-filter:blur(10px)}
.action-btn{width:44px;height:44px;border-radius:10px;background:rgba(0,240,255,0.08);border:1px solid rgba(0,240,255,0.15);color:#00f0ff;font-size:18px;cursor:pointer;display:flex;align-items:center;justify-content:center;transition:all 0.2s;position:relative}
.action-btn:hover{background:rgba(0,240,255,0.2);border-color:#00f0ff;transform:scale(1.1)}
.action-btn .tooltip{position:absolute;bottom:50px;left:50%;transform:translateX(-50%);background:rgba(3,8,20,0.95);border:1px solid rgba(0,240,255,0.3);border-radius:6px;padding:4px 8px;font-size:10px;color:#e2e8f0;white-space:nowrap;opacity:0;pointer-events:none;transition:0.2s}
.action-btn:hover .tooltip{opacity:1}
#manage{position:fixed;top:20px;left:20px;z-index:10}
.btn{background:rgba(0,240,255,0.1);border:1px solid #00f0ff;color:#00f0ff;padding:8px 14px;border-radius:6px;cursor:pointer;font-family:inherit;font-size:11px}
.btn:hover{background:rgba(0,240,255,0.2)}
.input{background:rgba(0,240,255,0.03);border:1px solid rgba(0,240,255,0.12);color:#e2e8f0;padding:6px 10px;border-radius:6px;font-family:inherit;font-size:11px}
#addPanel{position:fixed;top:60px;left:20px;background:rgba(3,8,20,0.95);border:1px solid rgba(0,240,255,0.2);border-radius:10px;padding:14px;display:none;z-index:10}
#addPanel.show{display:block}
.action-icons{display:flex;gap:4px;flex-wrap:wrap;margin:6px 0}
.icon-opt{width:30px;height:30px;border-radius:6px;background:rgba(0,240,255,0.05);border:1px solid rgba(0,240,255,0.1);display:flex;align-items:center;justify-content:center;cursor:pointer;font-size:14px}
.icon-opt:hover,.icon-opt.active{border-color:#00f0ff;background:rgba(0,240,255,0.15)}
</style></head><body>
<div id="manage"><button class="btn" onclick="toggleAdd()">Manage Actions</button></div>
<div id="addPanel">
  <div style="font-size:12px;color:#00f0ff;margin-bottom:8px">Add Action</div>
  <input class="input" id="aName" placeholder="Name" style="margin-bottom:4px;width:200px">
  <input class="input" id="aCmd" placeholder="Command" style="margin-bottom:4px;width:200px">
  <div class="action-icons" id="iconPicker"></div>
  <button class="btn" onclick="addAction()">Add</button>
</div>
<div id="bar" id="actionBar"></div>
<script>
const icons=['calc','notepad','terminal','explorer','camera','lock','volume','mute','play','stop','refresh','power','globe','code','image','music','video','mail','chat','star','heart','bolt','rocket','wand'];
let selectedIcon='calc';
async function load(){
  const r=await(await fetch('/api/actions/list')).json();
  document.getElementById('bar').innerHTML=(r.actions||[]).map(a=>
    '<div class="action-btn" onclick="execAction(\''+a.cmd+'\')">'+getIcon(a.icon)+'<div class="tooltip">'+a.name+'</div></div>'
  ).join('');
  document.getElementById('iconPicker').innerHTML=icons.map(i=>
    '<div class="icon-opt'+(selectedIcon===i?' active':'')+'" onclick="selectIcon(\''+i+'\')">'+getIcon(i)+'</div>'
  ).join('');
}
function getIcon(name){const map={calc:'128290',notepad:'128221',terminal:'128187',explorer:'128194',camera:'128247',lock:'128274',volume:'128266',mute:'128263',play:'9654',stop:'9632',refresh:'128260',power:'9211',globe:'127760',code:'128187',image:'127748',music:'127925',video:'127909',mail:'128231',chat:'128172',star:'11088',heart:'10084',bolt:'9889',rocket:'128640',wand:'128302'};return String.fromCodePoint(parseInt(map[name]||'128375'))}
function selectIcon(i){selectedIcon=i;document.querySelectorAll('.icon-opt').forEach(e=>e.classList.remove('active'));event.target.classList.add('active')}
function toggleAdd(){document.getElementById('addPanel').classList.toggle('show')}
async function addAction(){
  const data={name:document.getElementById('aName').value,cmd:document.getElementById('aCmd').value,icon:selectedIcon};
  await fetch('/api/actions/add',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(data)});
  document.getElementById('aName').value='';document.getElementById('aCmd').value='';load();
}
async function execAction(cmd){await fetch('/api/actions/execute',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({cmd})})}
load();
</script></body></html>
"""

if __name__ == "__main__":
    print("[System 35] Quick Actions Bar starting on port 5045...")
    app.run(host="0.0.0.0", port=5045, debug=False)
