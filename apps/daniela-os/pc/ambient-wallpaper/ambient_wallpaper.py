"""
System 21: Ambient Wallpaper Engine
Dynamic wallpaper that reacts to weather, time, music, and system activity
"""

from datetime import datetime

import psutil
from flask import Flask, jsonify, request

app = Flask(__name__)


@app.route("/")
def index():
    return AMBIENT_HTML


@app.route("/api/ambient/state")
def ambient_state():
    hour = datetime.now().hour
    cpu = psutil.cpu_percent(interval=0.1)
    mem = psutil.virtual_memory().percent

    if 5 <= hour < 8:
        time_phase = "dawn"
        palette = ["#ff6b6b", "#ffa07a", "#ffd93d"]
    elif 8 <= hour < 12:
        time_phase = "morning"
        palette = ["#87ceeb", "#98fb98", "#ffd93d"]
    elif 12 <= hour < 17:
        time_phase = "afternoon"
        palette = ["#00bfff", "#1e90ff", "#00ff7f"]
    elif 17 <= hour < 20:
        time_phase = "sunset"
        palette = ["#ff6347", "#ff4500", "#ff1493"]
    elif 20 <= hour < 23:
        time_phase = "evening"
        palette = ["#191970", "#483d8b", "#6a5acd"]
    else:
        time_phase = "night"
        palette = ["#0a0a2e", "#1a1a4e", "#2a2a6e"]

    activity = "calm"
    if cpu > 80:
        activity = "intense"
    elif cpu > 50:
        activity = "active"
    elif cpu > 20:
        activity = "moderate"

    particle_speed = 0.5 + (cpu / 100) * 2
    particle_count = 50 + int(cpu * 2)

    return jsonify(
        {
            "time_phase": time_phase,
            "hour": hour,
            "palette": palette,
            "activity": activity,
            "cpu": cpu,
            "memory": mem,
            "particle_speed": round(particle_speed, 2),
            "particle_count": particle_count,
            "breathe_rate": 1 + (mem / 100),
        }
    )


@app.route("/api/ambient/weather", methods=["POST"])
def set_weather():
    data = request.json or {}
    return jsonify({"ok": True, "weather": data.get("weather", "clear")})


AMBIENT_HTML = r"""
<!DOCTYPE html>
<html><head><meta charset="UTF-8"><title>Ambient Wallpaper Engine</title>
<style>
*{margin:0;padding:0;box-sizing:border-box}
html,body{width:100vw;height:100vh;overflow:hidden;background:#000}
canvas{position:fixed;top:0;left:0;z-index:0}
#hud{position:fixed;top:20px;right:20px;z-index:10;background:rgba(3,8,20,0.7);border:1px solid rgba(0,240,255,0.2);border-radius:10px;padding:12px;font-family:'Share Tech Mono',monospace;font-size:11px;color:#e2e8f0}
.hud-item{margin:4px 0}
.hud-label{color:#64748b;font-size:9px}
.hud-value{color:#00f0ff}
</style></head><body>
<canvas id="c"></canvas>
<div id="hud">
  <div class="hud-item"><span class="hud-label">PHASE</span> <span class="hud-value" id="phase">--</span></div>
  <div class="hud-item"><span class="hud-label">CPU</span> <span class="hud-value" id="cpu">--</span></div>
  <div class="hud-item"><span class="hud-label">ACTIVITY</span> <span class="hud-value" id="activity">--</span></div>
  <div class="hud-item"><span class="hud-label">PARTICLES</span> <span class="hud-value" id="parts">--</span></div>
</div>
<script>
const canvas=document.getElementById('c');const ctx=canvas.getContext('2d');
canvas.width=window.innerWidth;canvas.height=window.innerHeight;
window.onresize=()=>{canvas.width=innerWidth;canvas.height=innerHeight};

let state={palette:['#191970','#483d8b','#6a5acd'],particle_count:80,particle_speed:1,activity:'calm'};
let particles=[];

class Particle{
  constructor(){this.reset()}
  reset(){this.x=Math.random()*canvas.width;this.y=Math.random()*canvas.height;this.size=Math.random()*3+0.5;this.speedX=(Math.random()-0.5)*state.particle_speed;this.speedY=(Math.random()-0.5)*state.particle_speed;this.opacity=Math.random()*0.5+0.1;this.hue=Math.random()*60+180}
  update(){this.x+=this.speedX;this.y+=this.speedY;if(this.x<0||this.x>canvas.width||this.y<0||this.y>canvas.height)this.reset()}
  draw(){ctx.beginPath();ctx.arc(this.x,this.y,this.size,0,Math.PI*2);ctx.fillStyle=`hsla(${this.hue},80%,60%,${this.opacity})`;ctx.fill()}
}

function initParticles(){particles=[];for(let i=0;i<state.particle_count;i++)particles.push(new Particle())}

async function fetchState(){
  try{const r=await(await fetch('/api/ambient/state')).json();state=r;updateHUD();initParticles()}catch(e){}
}
setInterval(fetchState,3000);

function updateHUD(){
  document.getElementById('phase').textContent=state.time_phase;
  document.getElementById('cpu').textContent=state.cpu+'%';
  document.getElementById('activity').textContent=state.activity;
  document.getElementById('parts').textContent=state.particle_count;
}

let time=0;
function animate(){
  requestAnimationFrame(animate);time+=0.01;
  const grad=ctx.createLinearGradient(0,0,canvas.width,canvas.height);
  (state.palette||['#191970','#483d8b','#6a5acd']).forEach((c,i)=>grad.addColorStop(i/(state.palette.length-1),c));
  ctx.fillStyle=grad;ctx.fillRect(0,0,canvas.width,canvas.height);
  ctx.globalAlpha=0.03;ctx.fillStyle='#000';ctx.fillRect(0,0,canvas.width,canvas.height);ctx.globalAlpha=1;
  particles.forEach(p=>{p.update();p.draw()});
  if(state.activity==='intense'){for(let i=0;i<3;i++){ctx.beginPath();ctx.arc(Math.random()*canvas.width,Math.random()*canvas.height,Math.random()*50+10,0,Math.PI*2);ctx.fillStyle=`rgba(255,255,255,${Math.random()*0.03})`;ctx.fill()}}
}
fetchState();animate();
</script></body></html>
"""

if __name__ == "__main__":
    print("[System 21] Ambient Wallpaper Engine starting on port 5031...")
    app.run(host="0.0.0.0", port=5031, debug=False)
