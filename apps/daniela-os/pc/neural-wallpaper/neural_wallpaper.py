"""
System 2: Neural Live Wallpaper
Dynamic wallpaper that reacts to system state, time, and audio
"""

import psutil
from flask import Flask, jsonify

app = Flask(__name__, static_folder="static")

WALLPAPER_HTML = r"""
<!DOCTYPE html>
<html><head>
<meta charset="UTF-8">
<title>Neural Wallpaper</title>
<style>
* { margin:0; padding:0; box-sizing:border-box; }
html, body { width:100vw; height:100vh; overflow:hidden; background:#000; }
canvas { position:fixed; top:0; left:0; width:100vw; height:100vh; z-index:0; }
#hud { position:fixed; bottom:20px; left:20px; font-family:'Share Tech Mono',monospace; font-size:11px; color:rgba(0,240,255,0.4); z-index:1; pointer-events:none; }
</style>
</head><body>
<canvas id="c"></canvas>
<div id="hud"></div>
<script>
const canvas = document.getElementById('c');
const ctx = canvas.getContext('2d');
let W, H;
function resize() { W = canvas.width = window.innerWidth; H = canvas.height = window.innerHeight; }
window.addEventListener('resize', resize); resize();

// Particles
const PARTICLES = 300;
const particles = [];
for (let i = 0; i < PARTICLES; i++) {
  particles.push({
    x: Math.random() * W, y: Math.random() * H,
    vx: (Math.random()-0.5)*0.5, vy: (Math.random()-0.5)*0.5,
    size: Math.random()*2+0.5, hue: 190+Math.random()*30,
    life: Math.random()*100, maxLife: 100+Math.random()*200
  });
}

// Stars
const STARS = 200;
const stars = [];
for (let i = 0; i < STARS; i++) {
  stars.push({ x: Math.random()*W, y: Math.random()*H, size: Math.random()*1.5, twinkle: Math.random()*Math.PI*2 });
}

let cpuLoad = 0, ramLoad = 0, hour = 12, audioLevel = 0;

async function fetchSystemData() {
  try {
    const r = await fetch('/api/system/telemetry');
    const d = await r.json();
    cpuLoad = d.cpu / 100;
    ramLoad = d.memory / 100;
    hour = d.hour;
    audioLevel = d.audio || 0;
  } catch(e) {}
}
setInterval(fetchSystemData, 1000);

function getTheme() {
  if (hour >= 6 && hour < 12) return { bg1:'#0a1628', bg2:'#1a0a28', accent:'#f59e0b', particleHue:40 };
  if (hour >= 12 && hour < 18) return { bg1:'#0a1628', bg2:'#0a2818', accent:'#22c55e', particleHue:140 };
  if (hour >= 18 && hour < 21) return { bg1:'#1a0a28', bg2:'#280a18', accent:'#f97316', particleHue:30 };
  return { bg1:'#030814', bg2:'#0a0828', accent:'#00f0ff', particleHue:190 };
}

function draw() {
  requestAnimationFrame(draw);
  const theme = getTheme();

  // Background gradient
  const grad = ctx.createRadialGradient(W/2, H/2, 0, W/2, H/2, Math.max(W,H)*0.7);
  grad.addColorStop(0, theme.bg2);
  grad.addColorStop(1, theme.bg1);
  ctx.fillStyle = grad;
  ctx.fillRect(0, 0, W, H);

  // Stars (twinkle)
  stars.forEach(s => {
    s.twinkle += 0.02;
    const alpha = 0.3 + Math.sin(s.twinkle) * 0.3;
    ctx.fillStyle = `rgba(255,255,255,${alpha})`;
    ctx.beginPath(); ctx.arc(s.x, s.y, s.size, 0, Math.PI*2); ctx.fill();
  });

  // Particles (react to CPU/audio)
  const speed = 0.3 + cpuLoad * 2 + audioLevel * 3;
  const hueBase = theme.particleHue;
  particles.forEach(p => {
    p.life++;
    if (p.life > p.maxLife) {
      p.x = Math.random()*W; p.y = Math.random()*H;
      p.life = 0; p.maxLife = 100+Math.random()*200;
    }

    p.x += p.vx * speed;
    p.y += p.vy * speed;
    if (p.x < 0) p.x = W; if (p.x > W) p.x = 0;
    if (p.y < 0) p.y = H; if (p.y > H) p.y = 0;

    const alpha = Math.sin(p.life / p.maxLife * Math.PI) * 0.6;
    const size = p.size * (1 + cpuLoad * 0.5);
    ctx.fillStyle = `hsla(${p.hue}, 80%, 60%, ${alpha})`;
    ctx.beginPath(); ctx.arc(p.x, p.y, size, 0, Math.PI*2); ctx.fill();

    // Glow
    ctx.shadowBlur = 10;
    ctx.shadowColor = `hsla(${p.hue}, 80%, 60%, 0.3)`;
  });
  ctx.shadowBlur = 0;

  // CPU-reactive waves at bottom
  ctx.strokeStyle = `rgba(0,240,255,${0.1 + cpuLoad*0.3})`;
  ctx.lineWidth = 1;
  ctx.beginPath();
  for (let x = 0; x < W; x += 5) {
    const y = H - 50 - Math.sin(x*0.01 + Date.now()*0.002) * (20 + cpuLoad*40);
    x === 0 ? ctx.moveTo(x, y) : ctx.lineTo(x, y);
  }
  ctx.stroke();

  // RAM bar at top
  const barWidth = W * ramLoad;
  const barGrad = ctx.createLinearGradient(0, 0, barWidth, 0);
  barGrad.addColorStop(0, 'rgba(0,240,255,0.15)');
  barGrad.addColorStop(1, 'rgba(0,240,255,0.02)');
  ctx.fillStyle = barGrad;
  ctx.fillRect(0, 0, barWidth, 2);

  // HUD
  document.getElementById('hud').textContent =
    `CPU: ${(cpuLoad*100).toFixed(0)}% | RAM: ${(ramLoad*100).toFixed(0)}% | ${String(hour).padStart(2,'0')}:00`;
}

draw();
</script>
</body></html>
"""


@app.route("/")
def index():
    return WALLPAPER_HTML


@app.route("/api/system/telemetry")
def telemetry():
    cpu = psutil.cpu_percent(interval=0.1)
    mem = psutil.virtual_memory()
    from datetime import datetime

    hour = datetime.now().hour
    return jsonify({"cpu": cpu, "memory": mem.percent, "hour": hour, "audio": 0})


if __name__ == "__main__":
    print("[System 2] Neural Wallpaper starting on port 5011...")
    app.run(host="0.0.0.0", port=5011, debug=False)
