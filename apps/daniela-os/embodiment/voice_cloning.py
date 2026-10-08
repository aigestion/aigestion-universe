from flask import Blueprint, jsonify

voice_clone_bp = Blueprint("voice_cloning", __name__)
_state = {"active": False, "sample_ready": False, "quality": 0}


@voice_clone_bp.route("/api/embodiment/voice-clone/status")
def vc_status():
    return jsonify(_state)


@voice_clone_bp.route("/api/embodiment/voice-clone/record", methods=["POST"])
def vc_record():
    _state["sample_ready"] = True
    _state["quality"] = 85
    return jsonify({"ok": True})


@voice_clone_bp.route("/api/embodiment/voice-clone/web")
def vc_web():
    return """<!DOCTYPE html>
<html><head><meta charset="utf-8"><title>Voice Cloning</title>
<style>body{margin:0;background:#0a0a0f;color:#00f0ff;font-family:monospace;display:flex;justify-content:center;align-items:center;height:100vh}
.clone{text-align:center}
.mic{width:150px;height:150px;border-radius:50%;border:4px solid #333;display:flex;align-items:center;justify-content:center;font-size:60px;cursor:pointer;transition:all .3s;margin:0 auto}
.mic:hover{border-color:#ff0066;background:#ff006611}
.mic.recording{border-color:#ff0066;background:#ff006622;animation:pulse 1s infinite}
@keyframes pulse{0%,100%{box-shadow:0 0 20px #ff006644}50%{box-shadow:0 0 60px #ff006688}}
.quality{margin-top:20px}
.quality-bar{width:200px;height:12px;background:#222;border-radius:6px;margin:10px auto}
.quality-fill{height:100%;background:#00ff88;border-radius:6px}
</style></head><body>
<div class="clone">
<h2>VOICE CLONING</h2>
<div class="mic" id="mic" onclick="record()">🎙</div>
<p>Click to record sample</p>
<div class="quality"><p>Quality: <span id="q">0</span>%</p><div class="quality-bar"><div class="quality-fill" id="qf" style="width:0%"></div></div></div>
</div>
<script>function record(){const m=document.getElementById('mic');m.classList.add('recording');fetch('/api/embodiment/voice-clone/record',{method:'POST'}).then(r=>r.json()).then(d=>{setTimeout(()=>{m.classList.remove('recording');document.getElementById('q').textContent=d.quality;document.getElementById('qf').style.width=d.quality+'%'},2000)})}
</script></body></html>"""
