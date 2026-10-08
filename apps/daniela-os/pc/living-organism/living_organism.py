"""
System 10: PC Living Organism
Your PC becomes a digital pet - reacts to system health with emotions and animations
"""

import time

import psutil
from flask import Flask, jsonify

app = Flask(__name__)


@app.route("/")
def index():
    return ORGANISM_HTML


@app.route("/api/organism/state")
def organism_state():
    cpu = psutil.cpu_percent(interval=0.1)
    mem = psutil.virtual_memory()
    disk = psutil.disk_usage("/")

    # Calculate "mood" based on system health
    health = 100 - (cpu * 0.4 + mem.percent * 0.3 + disk.percent * 0.3)

    if health > 80:
        mood = "happy"
        emoji = "😊"
        color = "#22c55e"
        behavior = "glow"
    elif health > 60:
        mood = "content"
        emoji = "😌"
        color = "#0ea5e9"
        behavior = "breathe"
    elif health > 40:
        mood = "tired"
        emoji = "😐"
        color = "#f59e0b"
        behavior = "slow"
    elif health > 20:
        mood = "stressed"
        emoji = "😰"
        color = "#f97316"
        behavior = "pulse"
    else:
        mood = "critical"
        emoji = "😱"
        color = "#ef4444"
        behavior = "flicker"

    # Uptime as "age"
    uptime = time.time() - psutil.boot_time()
    days = int(uptime // 86400)
    hours = int((uptime % 86400) // 3600)

    # "Energy" from RAM free percentage
    energy = 100 - mem.percent

    # "Hunger" from disk usage
    hunger = disk.percent

    return jsonify(
        {
            "mood": mood,
            "emoji": emoji,
            "color": color,
            "behavior": behavior,
            "health": round(health, 1),
            "energy": round(energy, 1),
            "hunger": round(hunger, 1),
            "age_days": days,
            "age_hours": hours,
            "cpu": cpu,
            "memory": mem.percent,
            "disk": disk.percent,
            "message": get_message(mood, cpu, mem.percent),
        }
    )


def get_message(mood, cpu, mem):
    messages = {
        "happy": [
            "I feel great! All systems nominal.",
            "Running smoothly!",
            "Everything is perfect!",
        ],
        "content": ["Everything is fine.", "Running at a comfortable pace.", "All good here."],
        "tired": ["I'm getting a bit tired...", "Could use a break.", "Working hard..."],
        "stressed": [
            "I'm overloaded! Too many processes!",
            "Memory is running low!",
            "Need to breathe...",
        ],
        "critical": [
            "HELP! I'm drowning!",
            "System critical! Too much load!",
            "I can't take much more!",
        ],
    }
    import random

    return random.choice(messages.get(mood, ["..."]))


ORGANISM_HTML = r"""
<!DOCTYPE html>
<html><head><meta charset="UTF-8"><title>PC Living Organism</title>
<style>
* { margin:0; padding:0; box-sizing:border-box; }
html,body { width:100vw; height:100vh; overflow:hidden; background:#030814; font-family:'Rajdhani',sans-serif; }
canvas { position:fixed; top:0; left:0; z-index:0; }
#hud { position:fixed; top:20px; left:20px; z-index:10; }
.stat { background:rgba(3,8,20,0.8); border:1px solid rgba(0,240,255,0.15); border-radius:8px; padding:8px 12px; margin-bottom:6px; font-family:'Share Tech Mono',monospace; font-size:11px; }
.stat-label { color:#64748b; font-size:9px; letter-spacing:1px; }
.stat-value { color:#e2e8f0; font-size:14px; font-weight:600; }
#message { position:fixed; bottom:100px; left:50%; transform:translateX(-50%); z-index:10; background:rgba(3,8,20,0.85); border:1px solid rgba(0,240,255,0.2); border-radius:12px; padding:12px 20px; font-size:13px; color:#e2e8f0; text-align:center; max-width:400px; }
#mood-emoji { position:fixed; bottom:30px; left:50%; transform:translateX(-50%); z-index:10; font-size:48px; }
#stats { position:fixed; bottom:20px; right:20px; z-index:10; font-family:'Share Tech Mono',monospace; font-size:10px; color:#64748b; }
</style></head><body>
<canvas id="c"></canvas>
<div id="hud"></div>
<div id="message"></div>
<div id="mood-emoji"></div>
<div id="stats"></div>
<script src="https://cdnjs.cloudflare.com/ajax/libs/three.js/r128/three.min.js"></script>
<script>
const canvas = document.getElementById('c');
const scene = new THREE.Scene();
const camera = new THREE.PerspectiveCamera(50, innerWidth/innerHeight, 0.1, 1000);
const renderer = new THREE.WebGLRenderer({canvas, antialias:true, alpha:true});
renderer.setSize(innerWidth, innerHeight);
renderer.setPixelRatio(Math.min(devicePixelRatio, 2));
camera.position.z = 5;

// Main body (the organism)
const bodyGeo = new THREE.SphereGeometry(1, 32, 32);
const bodyMat = new THREE.MeshBasicMaterial({color:0x00f0ff, transparent:true, opacity:0.5});
const body = new THREE.Mesh(bodyGeo, bodyMat);
scene.add(body);

// Eyes
const eyeGeo = new THREE.SphereGeometry(0.12, 12, 12);
const eyeMat = new THREE.MeshBasicMaterial({color:0xffffff});
const leftEye = new THREE.Mesh(eyeGeo, eyeMat);
leftEye.position.set(-0.3, 0.2, 0.85);
body.add(leftEye);
const rightEye = new THREE.Mesh(eyeGeo, eyeMat);
rightEye.position.set(0.3, 0.2, 0.85);
body.add(rightEye);

// Pupils
const pupilGeo = new THREE.SphereGeometry(0.06, 8, 8);
const pupilMat = new THREE.MeshBasicMaterial({color:0x000000});
const leftPupil = new THREE.Mesh(pupilGeo, pupilMat);
leftPupil.position.z = 0.08;
leftEye.add(leftPupil);
const rightPupil = new THREE.Mesh(pupilGeo, pupilMat);
rightPupil.position.z = 0.08;
rightEye.add(rightPupil);

// Mouth (torus arc)
const mouthGeo = new THREE.TorusGeometry(0.25, 0.02, 8, 16, Math.PI);
const mouthMat = new THREE.MeshBasicMaterial({color:0xffffff});
const mouth = new THREE.Mesh(mouthGeo, mouthMat);
mouth.position.set(0, -0.2, 0.85);
mouth.rotation.z = Math.PI;
body.add(mouth);

// Glow sphere
const glowGeo = new THREE.SphereGeometry(1.3, 16, 16);
const glowMat = new THREE.MeshBasicMaterial({color:0x00f0ff, transparent:true, opacity:0.08});
const glow = new THREE.Mesh(glowGeo, glowMat);
scene.add(glow);

// Particles around body
const partCount = 100;
const partGeo = new THREE.BufferGeometry();
const partPos = new Float32Array(partCount * 3);
for(let i=0; i<partCount; i++) {
  const a = (i/partCount)*Math.PI*2;
  const r = 1.5 + Math.random()*0.5;
  partPos[i*3] = Math.cos(a)*r;
  partPos[i*3+1] = (Math.random()-0.5)*2;
  partPos[i*3+2] = Math.sin(a)*r;
}
partGeo.setAttribute('position', new THREE.BufferAttribute(partPos, 3));
const partMat = new THREE.PointsMaterial({color:0x00f0ff, size:0.03, transparent:true, opacity:0.5, blending:THREE.AdditiveBlending});
const particles = new THREE.Points(partGeo, partMat);
scene.add(particles);

let state = {};
let mouseX = 0, mouseY = 0;
document.addEventListener('mousemove', e => {
  mouseX = (e.clientX/innerWidth)*2-1;
  mouseY = -(e.clientY/innerHeight)*2+1;
});

async function fetchState() {
  try { state = await (await fetch('/api/organism/state')).json(); updateHUD(); } catch(e) {}
}
setInterval(fetchState, 2000);

function updateHUD() {
  const c = state.color || '#00f0ff';
  document.getElementById('hud').innerHTML =
    '<div class="stat"><div class="stat-label">MOOD</div><div class="stat-value" style="color:'+c+'">' + (state.emoji||'😊') + ' ' + (state.mood||'happy') + '</div></div>' +
    '<div class="stat"><div class="stat-label">HEALTH</div><div class="stat-value">' + (state.health||100) + '%</div></div>' +
    '<div class="stat"><div class="stat-label">ENERGY</div><div class="stat-value">' + (state.energy||100) + '%</div></div>' +
    '<div class="stat"><div class="stat-label">AGE</div><div class="stat-value">' + (state.age_days||0) + 'd ' + (state.age_hours||0) + 'h</div></div>';

  document.getElementById('message').textContent = state.message || '';
  document.getElementById('mood-emoji').textContent = state.emoji || '😊';
  document.getElementById('stats').textContent = 'CPU: ' + (state.cpu||0).toFixed(0) + '% | RAM: ' + (state.memory||0).toFixed(0) + '% | DISK: ' + (state.disk||0).toFixed(0) + '%';
}

function animate() {
  requestAnimationFrame(animate);
  const t = Date.now()*0.001;
  const behavior = state.behavior || 'breathe';

  // Body behavior
  if (behavior === 'glow') {
    body.material.opacity = 0.4 + Math.sin(t*2)*0.1;
    body.scale.setScalar(1 + Math.sin(t*1.5)*0.03);
  } else if (behavior === 'breathe') {
    body.material.opacity = 0.35 + Math.sin(t)*0.05;
    body.scale.setScalar(1 + Math.sin(t)*0.02);
  } else if (behavior === 'slow') {
    body.material.opacity = 0.3 + Math.sin(t*0.5)*0.05;
    body.scale.setScalar(1 + Math.sin(t*0.5)*0.01);
  } else if (behavior === 'pulse') {
    body.material.opacity = 0.4 + Math.sin(t*4)*0.15;
    body.scale.setScalar(1 + Math.sin(t*3)*0.05);
  } else if (behavior === 'flicker') {
    body.material.opacity = 0.2 + Math.random()*0.3;
    body.scale.setScalar(0.95 + Math.random()*0.1);
  }

  // Color
  const c = new THREE.Color(state.color || '#00f0ff');
  body.material.color.lerp(c, 0.05);
  glowMat.color.lerp(c, 0.05);

  // Eyes follow mouse
  leftPupil.position.x = mouseX * 0.04;
  leftPupil.position.y = mouseY * 0.04;
  rightPupil.position.x = mouseX * 0.04;
  rightPupil.position.y = mouseY * 0.04;

  // Mouth animation (happy = smile, sad = frown)
  if (state.mood === 'happy' || state.mood === 'content') {
    mouth.rotation.x = Math.sin(t)*0.1;
  } else if (state.mood === 'stressed' || state.mood === 'critical') {
    mouth.rotation.x = -0.3;
  }

  // Glow pulse
  glow.material.opacity = 0.05 + Math.sin(t)*0.03;

  // Particles orbit
  particles.rotation.y += 0.005;

  renderer.render(scene, camera);
}
animate(); fetchState();
</script></body></html>
"""

if __name__ == "__main__":
    print("[System 10] PC Living Organism starting on port 5019...")
    app.run(host="0.0.0.0", port=5019, debug=False)
