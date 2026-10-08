"""
System 52: Screen Privacy
Privacy filter and screen protection
"""

import json
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


@app.route("/")
def index():
    return PRIVACY_HTML


@app.route("/api/privacy/status")
def status():
    settings = load_json(
        DATA_DIR / "privacy_settings.json",
        {
            "blur_enabled": False,
            "angle": 45,
            "opacity": 0.8,
            "auto_lock": 300,
            "hot_corners": True,
            "peep_detection": True,
        },
    )
    return jsonify({"settings": settings})


@app.route("/api/privacy/toggle", methods=["POST"])
def toggle():
    data = request.json or {}
    settings = load_json(
        DATA_DIR / "privacy_settings.json",
        {
            "blur_enabled": False,
            "angle": 45,
            "opacity": 0.8,
            "auto_lock": 300,
            "hot_corners": True,
            "peep_detection": True,
        },
    )
    key = data.get("key", "")
    if key in settings:
        if isinstance(settings[key], bool):
            settings[key] = not settings[key]
        else:
            settings[key] = data.get("value", settings[key])
    save_json(DATA_DIR / "privacy_settings.json", settings)
    return jsonify({"ok": True, "settings": settings})


PRIVACY_HTML = r"""
<!DOCTYPE html>
<html><head><meta charset="UTF-8"><title>Screen Privacy</title>
<style>
*{margin:0;padding:0;box-sizing:border-box}
body{background:#0a0a1a;color:#e2e8f0;font-family:'Rajdhani',sans-serif;padding:20px}
h1{font-family:'Orbitron',monospace;color:#00f0ff;font-size:20px;letter-spacing:3px;margin-bottom:20px}
.preview{background:rgba(3,8,20,0.8);border:1px solid rgba(0,240,255,0.12);border-radius:12px;padding:20px;margin-bottom:20px;position:relative;overflow:hidden;min-height:200px}
.privacy-lines{position:absolute;top:0;left:0;width:100%;height:100%;pointer-events:none}
.privacy-lines.active{background:repeating-linear-gradient(var(--angle,45deg),transparent,transparent 4px,rgba(0,0,0,var(--opacity,0.8)) 4px,rgba(0,0,0,var(--opacity,0.8)) 8px)}
.screen-mock{background:#1a1a3e;border-radius:8px;padding:20px;text-align:center;font-size:12px;color:#64748b;position:relative;z-index:1}
.controls{display:grid;grid-template-columns:repeat(auto-fill,minmax(220px,1fr));gap:10px;margin-bottom:20px}
.control{background:rgba(3,8,20,0.8);border:1px solid rgba(0,240,255,0.12);border-radius:10px;padding:14px}
.control-title{font-family:'Orbitron',monospace;font-size:11px;color:#00f0ff;margin-bottom:8px}
.control-desc{font-size:10px;color:#64748b;margin-bottom:10px}
.switch{width:44px;height:24px;background:rgba(0,240,255,0.1);border:1px solid rgba(0,240,255,0.2);border-radius:12px;cursor:pointer;position:relative;display:inline-block}
.switch.on{background:rgba(0,240,255,0.2);border-color:#00f0ff}
.switch::after{content:'';position:absolute;top:2px;left:2px;width:18px;height:18px;background:#00f0ff;border-radius:50%;transition:0.3s}
.switch.on::after{left:22px}
.slider{width:100%;-webkit-appearance:none;height:4px;background:#1a1a3e;border-radius:2px;margin-top:8px}
.slider::-webkit-slider-thumb{-webkit-appearance:none;width:14px;height:14px;background:#00f0ff;border-radius:50%;cursor:pointer}
.slider-val{font-family:'Share Tech Mono',monospace;font-size:11px;color:#64748b;text-align:right;margin-top:4px}
.log{background:rgba(3,8,20,0.8);border:1px solid rgba(0,240,255,0.12);border-radius:10px;padding:12px;max-height:150px;overflow-y:auto}
.log-entry{font-size:10px;font-family:'Share Tech Mono',monospace;padding:3px 0;border-bottom:1px solid rgba(0,240,255,0.05);color:#64748b}
.log-time{color:#00f0ff}.log-event{color:#22c55e}.log-alert{color:#ff0055}
</style></head><body>
<h1>SCREEN PRIVACY</h1>
<div class="preview">
  <div class="privacy-lines" id="privacyOverlay"></div>
  <div class="screen-mock">
    <div style="font-size:24px;margin-bottom:8px">128274</div>
    <div>Screen Preview - Privacy filter shown here</div>
    <div style="margin-top:8px;font-size:10px">Toggle privacy mode to see the effect</div>
  </div>
</div>
<div class="controls">
  <div class="control">
    <div class="control-title">Privacy Filter</div>
    <div class="control-desc">Angled lines prevent shoulder surfing</div>
    <div class="switch" id="filterSwitch" onclick="toggleSetting('blur_enabled')"></div>
  </div>
  <div class="control">
    <div class="control-title">Filter Angle</div>
    <div class="control-desc">Adjust the angle of privacy lines</div>
    <input type="range" class="slider" id="angleSlider" min="0" max="90" value="45" oninput="updateAngle(this.value)">
    <div class="slider-val" id="angleVal">45 degrees</div>
  </div>
  <div class="control">
    <div class="control-title">Filter Opacity</div>
    <div class="control-desc">How dark the filter appears</div>
    <input type="range" class="slider" id="opacitySlider" min="0" max="100" value="80" oninput="updateOpacity(this.value)">
    <div class="slider-val" id="opacityVal">80%</div>
  </div>
  <div class="control">
    <div class="control-title">Peep Detection</div>
    <div class="control-desc">Alert when someone is behind you</div>
    <div class="switch on" id="peepSwitch" onclick="toggleSetting('peep_detection')"></div>
  </div>
  <div class="control">
    <div class="control-title">Hot Corners</div>
    <div class="control-desc">Quick-lock when mouse hits corner</div>
    <div class="switch on" id="hotSwitch" onclick="toggleSetting('hot_corners')"></div>
  </div>
  <div class="control">
    <div class="control-title">Auto Lock (sec)</div>
    <div class="control-desc">Lock screen after inactivity</div>
    <input type="range" class="slider" id="lockSlider" min="30" max="600" value="300" step="30" oninput="document.getElementById('lockVal').textContent=this.value+'s'">
    <div class="slider-val" id="lockVal">300s</div>
  </div>
</div>
<div class="log">
  <div style="font-size:11px;color:#00f0ff;font-family:'Orbitron',monospace;margin-bottom:6px">ACTIVITY LOG</div>
  <div class="log-entry"><span class="log-time">14:32:01</span> <span class="log-event">Privacy filter activated</span></div>
  <div class="log-entry"><span class="log-time">14:30:15</span> <span class="log-alert">Peep detected - alert sent</span></div>
  <div class="log-entry"><span class="log-time">14:28:44</span> <span class="log-event">Hot corner triggered - screen locked</span></div>
  <div class="log-entry"><span class="log-time">14:25:00</span> <span class="log-event">Auto-lock timer reset</span></div>
</div>
<script>
function updateAngle(v){document.getElementById('angleVal').textContent=v+' degrees';document.documentElement.style.setProperty('--angle',v+'deg')}
function updateOpacity(v){document.getElementById('opacityVal').textContent=v+'%';document.documentElement.style.setProperty('--opacity',v/100)}
async function toggleSetting(key){await fetch('/api/privacy/toggle',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({key})});load()}
async function load(){
  const r=await(await fetch('/api/privacy/status')).json();
  const s=r.settings||{};
  document.getElementById('filterSwitch').className='switch'+(s.blur_enabled?' on':'');
  document.getElementById('peepSwitch').className='switch'+(s.peep_detection?' on':'');
  document.getElementById('hotSwitch').className='switch'+(s.hot_corners?' on':'');
  if(s.blur_enabled)document.getElementById('privacyOverlay').className='privacy-lines active';
  updateAngle(s.angle||45);updateOpacity((s.opacity||0.8)*100);
}
load();
</script></body></html>
"""

if __name__ == "__main__":
    print("[System 52] Screen Privacy starting on port 5062...")
    app.run(host="0.0.0.0", port=5062, debug=False)
