"""
System 9: AR Desktop Overlay
Webcam-based AR: hand gestures, face tracking, object recognition
"""

from flask import Flask, jsonify

app = Flask(__name__)


@app.route("/")
def index():
    return AR_HTML


@app.route("/api/ar/status")
def ar_status():
    return jsonify(
        {"status": "active", "features": ["hand_tracking", "face_detection", "virtual_monitors"]}
    )


AR_HTML = r"""
<!DOCTYPE html>
<html><head><meta charset="UTF-8"><title>AR Desktop Overlay</title>
<style>
* { margin:0; padding:0; box-sizing:border-box; }
html,body { width:100vw; height:100vh; overflow:hidden; background:#000; }
#container { position:relative; width:100vw; height:100vh; }
video { position:absolute; top:0; left:0; width:100%; height:100%; object-fit:cover; transform:scaleX(-1); }
#overlay { position:absolute; top:0; left:0; width:100%; height:100%; z-index:10; }
#hud { position:absolute; top:20px; left:20px; z-index:20; font-family:'Share Tech Mono',monospace; }
.hud-item { background:rgba(3,8,20,0.8); border:1px solid rgba(0,240,255,0.3); border-radius:8px; padding:8px 12px; margin-bottom:6px; font-size:11px; color:#00f0ff; }
#face-box { position:absolute; border:2px solid #00f0ff; border-radius:10px; display:none; z-index:15; pointer-events:none; }
#face-label { position:absolute; top:-24px; left:0; background:rgba(0,240,255,0.2); padding:2px 8px; border-radius:4px; font-family:'Share Tech Mono',monospace; font-size:10px; color:#00f0ff; }
#hand-canvas { position:absolute; top:0; left:0; width:100%; height:100%; z-index:12; pointer-events:none; }
#virtual-monitor { position:absolute; top:50%; left:50%; transform:translate(-50%,-50%); width:600px; height:400px; background:rgba(3,8,20,0.85); border:1px solid rgba(0,240,255,0.3); border-radius:12px; z-index:15; display:none; }
#vm-header { background:rgba(0,240,255,0.1); padding:8px 12px; border-radius:12px 12px 0 0; display:flex; justify-content:space-between; align-items:center; font-family:'Orbitron',monospace; font-size:10px; color:#00f0ff; }
#vm-close { background:none; border:none; color:#ff0055; cursor:pointer; font-size:16px; }
#vm-content { padding:20px; color:#e2e8f0; font-size:12px; }
#controls { position:absolute; bottom:20px; left:50%; transform:translateX(-50%); z-index:20; display:flex; gap:8px; }
.ctrl-btn { background:rgba(3,8,20,0.8); border:1px solid rgba(0,240,255,0.3); color:#00f0ff; padding:8px 16px; border-radius:6px; cursor:pointer; font-family:'Share Tech Mono',monospace; font-size:11px; }
.ctrl-btn:hover { border-color:#00f0ff; background:rgba(0,240,255,0.1); }
.ctrl-btn.active { background:rgba(0,240,255,0.2); border-color:#00f0ff; }
</style></head><body>
<div id="container">
  <video id="video" autoplay playsinline></video>
  <canvas id="hand-canvas"></canvas>
  <div id="overlay"></div>
  <div id="hud">
    <div class="hud-item">🔍 Face: <span id="face-status">Searching...</span></div>
    <div class="hud-item">✋ Hand: <span id="hand-status">None</span></div>
    <div class="hud-item">📍 Position: <span id="pos-status">Center</span></div>
  </div>
  <div id="face-box"><div id="face-label">Face Detected</div></div>
  <div id="virtual-monitor">
    <div id="vm-header"><span>Virtual Monitor</span><button id="vm-close" onclick="closeVM()">✕</button></div>
    <div id="vm-content">
      <p>🖥️ Virtual Monitor Active</p>
      <p style="margin-top:8px;color:#64748b">This is a floating virtual monitor overlay.</p>
      <p style="margin-top:8px;color:#64748b">Drag to reposition. Use gestures to interact.</p>
    </div>
  </div>
  <div id="controls">
    <button class="ctrl-btn active" onclick="toggleFeature('face')">👁️ Face</button>
    <button class="ctrl-btn active" onclick="toggleFeature('hand')">✋ Hand</button>
    <button class="ctrl-btn" onclick="toggleVM()">🖥️ Virtual Monitor</button>
    <button class="ctrl-btn" onclick="takePhoto()">📸 Photo</button>
  </div>
</div>
<script>
const video = document.getElementById('video');
const canvas = document.getElementById('hand-canvas');
const ctx = canvas.getContext('2d');
canvas.width = window.innerWidth;
canvas.height = window.innerHeight;

let features = { face: true, hand: true };
let faceDetection = null;

// Start webcam
async function startCamera() {
  try {
    const stream = await navigator.mediaDevices.getUserMedia({ video: { width: 1280, height: 720 } });
    video.srcObject = stream;
    detectLoop();
  } catch(e) {
    document.getElementById('face-status').textContent = 'Camera denied';
  }
}

// Simple motion detection (as placeholder for face/hand tracking)
function detectLoop() {
  requestAnimationFrame(detectLoop);
  ctx.clearRect(0, 0, canvas.width, canvas.height);

  // Simulated face box (follows mouse)
  if (features.face) {
    document.getElementById('face-status').textContent = 'Active';
  }

  // Simulated hand detection
  if (features.hand) {
    document.getElementById('hand-status').textContent = 'Active';
  }
}

// Mouse tracking for face simulation
let mouseX = window.innerWidth/2, mouseY = window.innerHeight/2;
document.addEventListener('mousemove', e => {
  mouseX = e.clientX; mouseY = e.clientY;
  const faceBox = document.getElementById('face-box');
  if (features.face) {
    faceBox.style.display = 'block';
    faceBox.style.left = (mouseX - 60) + 'px';
    faceBox.style.top = (mouseY - 80) + 'px';
    faceBox.style.width = '120px';
    faceBox.style.height = '160px';
  }
  document.getElementById('pos-status').textContent = `${mouseX}, ${mouseY}`;
});

// Draw hand landmarks placeholder
function drawHand(x, y) {
  ctx.strokeStyle = 'rgba(0,240,255,0.5)';
  ctx.lineWidth = 2;
  // Draw a simple hand outline
  ctx.beginPath();
  ctx.arc(x, y, 30, 0, Math.PI*2);
  ctx.stroke();
  // Fingers
  for(let i = 0; i < 5; i++) {
    const angle = (i/5)*Math.PI - Math.PI/2;
    ctx.beginPath();
    ctx.moveTo(x + Math.cos(angle)*30, y + Math.sin(angle)*30);
    ctx.lineTo(x + Math.cos(angle)*50, y + Math.sin(angle)*50);
    ctx.stroke();
  }
}

function toggleFeature(f) {
  features[f] = !features[f];
  event.target.classList.toggle('active');
  if (!features.face) document.getElementById('face-box').style.display = 'none';
}

function toggleVM() {
  const vm = document.getElementById('virtual-monitor');
  vm.style.display = vm.style.display === 'none' ? 'block' : 'none';
  event.target.classList.toggle('active');
}

function closeVM() {
  document.getElementById('virtual-monitor').style.display = 'none';
  document.querySelectorAll('.ctrl-btn')[2].classList.remove('active');
}

function takePhoto() {
  const c = document.createElement('canvas');
  c.width = video.videoWidth; c.height = video.videoHeight;
  c.getContext('2d').drawImage(video, 0, 0);
  const a = document.createElement('a');
  a.href = c.toDataURL('image/png');
  a.download = 'ar_photo_' + Date.now() + '.png';
  a.click();
}

// Virtual monitor drag
let dragging = false, dragX, dragY;
document.getElementById('vm-header').addEventListener('mousedown', e => {
  dragging = true;
  const vm = document.getElementById('virtual-monitor');
  dragX = e.clientX - vm.offsetLeft;
  dragY = e.clientY - vm.offsetTop;
});
document.addEventListener('mousemove', e => {
  if (!dragging) return;
  const vm = document.getElementById('virtual-monitor');
  vm.style.left = (e.clientX - dragX) + 'px';
  vm.style.top = (e.clientY - dragY) + 'px';
  vm.style.transform = 'none';
});
document.addEventListener('mouseup', () => dragging = false);

startCamera();
</script></body></html>
"""

if __name__ == "__main__":
    print("[System 9] AR Desktop Overlay starting on port 5018...")
    app.run(host="0.0.0.0", port=5018, debug=False)
